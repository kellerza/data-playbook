"""Table tasks."""
import logging
from typing import Any, Dict

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook import loader
from dataplaybook.const import PlaybookError
from dataplaybook.task import resolve_task
from dataplaybook.utils import (DataEnvironment, print_exception,
                                set_logger_level, time_it)

_LOGGER = logging.getLogger(__name__)

PLAYBOOK_SCHEMA = vol.Schema({
    vol.Optional("version", default="0.4"): vol.Coerce(str),
    vol.Optional("modules", default=[]): vol.All(
        cv.ensure_list, [str]),
    vol.Required("tasks"): vol.All(cv.ensure_list, [dict]),
    vol.Remove('_'): object,
})


class DataPlaybook():
    """Data table task class."""

    def __init__(self, yaml_text=None, yaml_file=None, modules=None):
        """Process."""
        self.tables: Dict[str, Any] = DataEnvironment()
        self.config = {}
        yml = loader.load_yaml(filename=yaml_file, text=yaml_text)

        self.config = PLAYBOOK_SCHEMA(yml)

        self.all_tasks = loader.TaskDefs()
        modules = set(cv.ensure_list(modules)) | set(self.config['modules'])
        for mod in modules:
            self.all_tasks.load_module(mod)

        # Ensure config is ok before we start running
        self.config = cv.on_key(
            'tasks',
            [lambda t: resolve_task(t, self.all_tasks)[1]])(self.config)

    def print_table(self, table, title=''):
        """Print one."""
        task = cv.AttrDict({
            'print': {
                'title': title,
            },
            'tables': [table],
        })
        self.execute_task(task)

    def execute_task(self, config):
        """Execute the task."""
        debug = config.get('debug', False)

        set_logger_level(debug)

        # Enable runtime schema, like template
        with cv.ENV.environment(self.tables):
            taskdef, opt = resolve_task(config, self.all_tasks)
        name = taskdef.name

        set_logger_level(debug, taskdef.module)

        fn_args_str = ', '.join(opt.get('tables', ['tables']))
        if 'tables' in opt:
            fn_args = [self.tables.get(t, []) for t in opt.tables]
        else:
            fn_args = [self.tables]

        with time_it(name):
            try:
                fn_kwargs = opt[name] if taskdef.kwargs else {'opt': opt[name]}
                try:
                    info = f"{name}({fn_args_str}, **{fn_kwargs})"
                    _LOGGER.debug("Calling task: %s", info)
                    res = taskdef.function(*fn_args, **fn_kwargs)
                except TypeError as exc:
                    msg = f"TypeError in/calling task {info}: {exc}"
                    _LOGGER.warning(msg)
                    raise PlaybookError(msg)

                if taskdef.isgenerator:
                    res = list(res)
                    if 'target' not in opt:
                        _LOGGER.warning(
                            "Task %s is a generator without any target table",
                            name)

            except Exception as exc:  # pylint: disable=broad-except
                print_exception(name, taskdef.module, _LOGGER)
                raise exc

            if 'target' in opt:
                if isinstance(res, list):
                    self.tables[opt.target] = res
                    if debug:
                        self.print_table(opt.target, 'TARGET')
                else:
                    self.tables.var[opt.target] = res
                    if debug:
                        self.print_table(opt.target, 'TARGET')
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
