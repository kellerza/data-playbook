"""Table tasks."""
import logging
import sys
from inspect import isgeneratorfunction
from traceback import extract_tb

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook import loader

_LOGGER = logging.getLogger(__name__)

FULL_SCHEMA = vol.Schema({
    vol.Optional("modules", default=[]): vol.All(
        cv.ensure_list, [loader.load_module]),
    vol.Required("tasks"): vol.All(cv.ensure_list, [loader.validate_tasks]),
})


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


class DataPlaybook(object):
    """Data table task class."""

    tables = {}
    config = {}

    def __init__(self, yaml_text=None, yaml_file=None):
        """Process."""
        yml = loader.load_yaml(filename=yaml_file, text=yaml_text)

        if '_' in yml:
            del yml['_']

        try:
            self.config = FULL_SCHEMA(yml)
        except vol.MultipleInvalid as err:
            _LOGGER.error("Invalid yaml: %s", err)
            raise err

    def print_table(self, table):
        """Print one."""
        task = cv.AttrDict({
            'task': 'print',
            'tables': [table]
        })
        self._task(task)

    def _task(self, opt):
        task = loader.TASKS[opt.task]

        debug = 'debug*' in opt
        loglevel = logging.DEBUG if debug else logging.INFO
        cv._LOGGER.setLevel(loglevel)  # pylint: disable=W0212
        _LOGGER.setLevel(loglevel)
        try:
            task.module._LOGGER.setLevel(loglevel)  # pylint: disable=W0212
        except AttributeError:
            pass

        if 'tables' in opt:
            tables = [self.tables.get(src, {}) for src in opt.tables]
            if debug:
                print("***************tables len =", len(opt.tables))
                for src in opt.tables:
                    self.print_table(src)
        else:
            tables = [self.tables]
            if debug:
                print("***************Calling with all tables")

        try:
            if getattr(task.function, 'kwargs', False):
                kwargs = {k: v for k, v in opt.items()
                          if k not in ['task', 'debug*', 'target', 'tables']}
                res = task.function(*tables, **kwargs)
            else:
                res = task.function(*tables, opt=opt)

            if isgeneratorfunction(task.function):
                res = list(res)
                if 'target' not in opt:
                    _LOGGER.warning(
                        "Task %s is a generator wiithout any target table",
                        opt.task)

        except Exception:  # pylint: disable=broad-except
            _print_exception(opt.task, task.module.__name__)
            res = []

        if 'target' in opt:
            self.tables[opt.target] = res
            if debug:
                print("**************TARGET (after)")
                self.print_table(opt.target)

    def run(self):
        """Execute a lists of tasks."""
        if 'tasks' not in self.config:
            _LOGGER.error('No "tasks". Did validation fail?')
            return
        len_tasks = len(self.config['tasks'])
        for idx, opt in enumerate(self.config['tasks'], 1):
            _LOGGER.info("Task %s/%s: %s", idx, len_tasks, opt)
            self._task(opt)


def setup_logger():
    """Configure the color log handler."""
    logging.basicConfig(level=logging.DEBUG)
    # fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
    #        "[%(name)s] %(message)s")
    fmt = ("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    # datefmt = '%Y-%m-%d %H:%M:%S'
    datefmt = "%H:%M:%S"

    try:
        from colorlog import ColoredFormatter
        logging.getLogger().handlers[0].setFormatter(ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green,bold',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        ))
    except ImportError:
        pass
