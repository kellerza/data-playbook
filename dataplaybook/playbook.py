"""Table tasks."""
import logging
import sys
from traceback import extract_tb
from contextlib import contextmanager
from timeit import default_timer

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook import loader
from dataplaybook.task import resolve_task
from dataplaybook.utils import DataEnvironment
from dataplaybook.const import PlaybookError

_LOGGER = logging.getLogger(__name__)

PLAYBOOK_SCHEMA = vol.Schema({
    vol.Optional("version", default="0.4"): vol.Coerce(str),
    vol.Optional("modules", default=[]): vol.All(
        cv.ensure_list, [str]),
    vol.Required("tasks"): vol.All(cv.ensure_list, [dict]),
})


class DataPlaybook():
    """Data table task class."""

    def __init__(self, yaml_text=None, yaml_file=None, modules=None):
        """Process."""
        self.tables = DataEnvironment()
        self.config = {}
        yml = loader.load_yaml(filename=yaml_file, text=yaml_text)

        if '_' in yml:
            del yml['_']

        try:
            self.config = PLAYBOOK_SCHEMA(yml)
        except vol.MultipleInvalid as err:
            _LOGGER.error("Invalid yaml: %s", err)
            raise err

        self.all_tasks = loader.TaskDefs()
        modules = set(cv.ensure_list(modules)) | set(self.config['modules'])
        for mod in modules:
            self.all_tasks.load_module(mod)

        # Ensure config is ok before we start running
        tasks = []
        for task in self.config['tasks']:
            _, opt = resolve_task(task, self.all_tasks)
            tasks.append(opt)
        self.config['tasks'] = tasks

    def print_table(self, table):
        """Print one."""
        task = cv.AttrDict({
            'print': {},
            'tables': [table]
        })
        self.execute_task(task)

    def execute_task(self, config):
        """Execute the task."""
        debug = config.get('debug', False)

        _loglevel(debug)

        # Enable runtime schema, like template
        with cv.ENV.environment(self.tables):
            taskdef, opt = resolve_task(config, self.all_tasks)
        name = taskdef.name

        _loglevel(debug, taskdef.module)

        if 'tables' in opt:
            fn_args = [self.tables.get(t, []) for t in opt.tables]
            if debug:
                print("***************tables len =", len(opt.tables))
                for src in opt.tables:
                    self.print_table(src)
        else:
            fn_args = [self.tables]
            if debug:
                print("***************Calling with all tables/environment")

        with time_it(name):
            try:
                fn_kwargs = opt[name] if taskdef.kwargs else {'opt': opt[name]}
                try:
                    res = taskdef.function(*fn_args, **fn_kwargs)
                except TypeError as exc:
                    msg = (f"Bad parameters: Task {name} "
                           f"({fn_args}, {fn_kwargs})")
                    _LOGGER.warning(msg)
                    raise PlaybookError(f"{msg} - exc")

                if taskdef.isgenerator:
                    res = list(res)
                    if 'target' not in opt:
                        _LOGGER.warning(
                            "Task %s is a generator without any target table",
                            opt.task)

            except Exception as exc:  # pylint: disable=broad-except
                _print_exception(name, taskdef.module)
                raise exc

            if 'target' in opt:
                if debug:
                    print(f"**************TARGET ({opt.target}")
                if isinstance(res, list):
                    self.tables[opt.target] = res
                    if debug:
                        self.print_table(opt.target)
                else:
                    self.tables.var[opt.target] = res
                    if debug:
                        self.print_table(opt.target)
            return True

    def run(self):
        """Execute a lists of tasks."""
        if 'tasks' not in self.config:
            _LOGGER.error('No "tasks". Did validation fail?')
            return
        len_tasks = len(self.config['tasks'])
        for idx, opt in enumerate(self.config['tasks'], 1):
            _LOGGER.info("========== TASK %s/%s - %s ==========",
                         idx, len_tasks, opt.get('name', ''))
            self.execute_task(opt)


def _print_exception(task_name, mod_name):
    mod_name = mod_name.replace('.', '/')
    _, exc, traceback = sys.exc_info()
    tb_all = extract_tb(traceback)
    tb_show = list((fs for fs in tb_all
                    if fs.filename and mod_name in fs.filename))
    if not tb_show:
        tb_show = tb_all

    res = ["Exception in task {}: {}: {}".format(
        task_name, exc.__class__.__name__, exc)]

    for frame in tb_show:
        res.append(" File {} line {} in method {}".format(
            frame.filename, frame.lineno, frame.name))

    _LOGGER.error(',\n '.join(res))


def _loglevel(debug, module=None):
    """Set the log level."""
    loglevel = logging.DEBUG if debug else logging.INFO
    if module:
        try:
            module._LOGGER.setLevel(loglevel)  # pylint: disable=W0212
        except AttributeError:
            pass
    else:
        cv._LOGGER.setLevel(loglevel)  # pylint: disable=W0212
        _LOGGER.setLevel(loglevel)


@contextmanager
def time_it(name=None, delta=0.5, logger=_LOGGER):
    """Context manager to time execution and report if too high."""
    t_start = default_timer()
    yield
    total = default_timer() - t_start
    if total > 0.5:
        logger.warning("Execution time for %s: %.2fs", name, total)
