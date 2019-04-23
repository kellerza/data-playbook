"""Task definition and validators."""
import logging
from inspect import isgeneratorfunction, signature

import attr
import voluptuous as vol
from yaml import safe_dump

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)

KEY_DEBUG = 'debug'
KEY_TASKS = 'tasks'
KEY_TABLES = 'tables'
KEY_TARGET = 'target'
STANDARD_KEYS = (KEY_DEBUG, KEY_TASKS, KEY_TABLES, KEY_TARGET, 'name')


@attr.s
class TaskDef():
    """Task Definition."""

    name = attr.ib()
    function = attr.ib()
    module = attr.ib()
    parameter_len = attr.ib(init=False)

    opt_schema = attr.ib(init=False, default=dict())
    target = attr.ib(init=False, default=True)
    tables = attr.ib(init=False, default=(0, 0))
    kwargs = attr.ib(init=False, default=False)

    pre_validators = attr.ib(init=False, default=None)
    post_validators = attr.ib(init=False, default=tuple())

    @property
    def isgenerator(self):
        """Generator funciton."""
        return isgeneratorfunction(self.function)

    def __attrs_post_init__(self):
        """Init fron function task_schema."""
        props = getattr(self.function, 'task_schema', None)
        if props is not None:
            (self.opt_schema, self.target, self.tables, self.kwargs,
             self.pre_validators, self.post_validators) = props
            self.pre_validators = tuple(cv.ensure_list(self.pre_validators))
            self.post_validators = tuple(cv.ensure_list(self.post_validators))
        else:
            _LOGGER.warning("Module %s: No schema attached to function %s",
                            self.module, self.name)

        # Type
        # if len(sig.parameters) == 1 and sig.parameters[0] == 'tables':
        #    task.type = -1  # All tables
        sig = signature(self.function)
        self.parameter_len = len(sig.parameters)

    def validate(self, config, check_in=True, check_out=True):
        """Validate the task config."""
        config = BASE_SCHEMA(config)

        for p_v in self.pre_validators:
            config = p_v(config)

        fschema = {
            vol.Required(self.name): cv.templateSchema(  # Expand templates
                vol.Schema(self.opt_schema),
                lambda d: cv.AttrDict(d))  # pylint: disable=unnecessary-lambda
        }

        if check_in:
            if self.tables[1] == 0 and config.get('tables', None):
                raise vol.Invalid(
                    "No input expected. Please remove 'tables'")
            _len = vol.Length(min=self.tables[0], max=self.tables[1])
            if self.tables[0]:
                fschema[vol.Required(KEY_TABLES)] = _len
            else:
                fschema[vol.Optional(KEY_TABLES)] = _len

        if check_out:
            if self.target:
                fschema[vol.Required(KEY_TARGET)] = cv.table_add
            elif config.get('target', None):
                raise vol.Invalid(
                    "No output expected. Please remove `target`")

        return cv.AttrDictSchema(
            fschema, extra=vol.ALLOW_EXTRA)(config)


def resolve_task(config: dict, all_tasks) -> tuple:
    """Validate tasks using."""
    config = BASE_SCHEMA(config)
    name = get_task_name(config)
    try:
        taskdef = all_tasks[name]
    except IndexError:
        _LOGGER.error("Task %s not in %s", name, all_tasks.keys())
        raise vol.Invalid("Task {} not found".format(name))

    # Copy column definitions from first input to target. This is a estimate.
    if config.get('target', None) and config.get('tables', None):
        tables0 = cv.ensure_list(config['tables'])[0]
        cv.col_copy(tables0, config['target'])

    return taskdef, taskdef.validate(config)


def get_task_name(value):
    """Ensure we have 1 thing to do."""
    # _LOGGER.debug("Value %s keys: %s", value, value.keys())
    extras = set(list(value.keys())) - set(STANDARD_KEYS)
    # _LOGGER.debug("Task name %s orig %s", next(iter(extras)), value)
    if not extras:
        raise vol.Invalid("One task expected")
    if len(extras) > 1:
        msg = "Multiple tasks: {}".format(str(extras))
        _LOGGER.error(msg)
        raise vol.Invalid(msg)
    return next(iter(extras))


def _migrate_task(task):
    """Migrate task format."""
    if 'task' not in task:
        return task

    if not task['task']:
        _LOGGER.error('Empty `task:` found, cannot migrate')
        return task

    # old format
    opt = {k: v for k, v in task.items()
           if k not in ('task', 'tables', 'target', 'debug*')}
    newtask = {task['task']: opt}
    for key in ('tables', 'target', 'debug*'):
        if key in task:
            newtask[key.replace('*', '')] = task[key]
    _LOGGER.debug("Migrate task format. New format %s, from old format: %s",
                  newtask, task)
    print(safe_dump({'new task format': [newtask]}, default_flow_style=False))
    return newtask


BASE_SCHEMA = vol.All(_migrate_task, vol.Schema({
    vol.Optional('name'): vol.Coerce(str),
    vol.Optional(KEY_DEBUG): vol.Coerce(str),
    vol.Optional(KEY_TABLES): vol.All(cv.ensure_list, [cv.table_use]),
    vol.Optional(KEY_TARGET): cv.table_add,
}, extra=vol.ALLOW_EXTRA))
