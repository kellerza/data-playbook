"""Dynamically load additional modules."""
from importlib import import_module
import inspect
import logging
import re
import sys
from collections import OrderedDict
from pathlib import Path

import attr
from voluptuous import Invalid
import yaml
import dataplaybook.config_validation as cv

TASKS = {}
_LOGGER = logging.getLogger(__name__)


@attr.s
class Task():
    """Representation of a task."""

    name = attr.ib()
    function = attr.ib()
    # module = attr.ib()
    # schema = attr.ib(default=None)
    type = attr.ib(default=0)

    @property
    def schema(self):
        """Return the schema."""
        if self.function.schema:
            return self.function.schema
        _LOGGER.warning("No schema for %s", self.name)
        return dict

    @property
    def module(self):
        """Return the source module."""
        return sys.modules[self.function.__module__]


def validate_tasks(config: dict) -> dict:
    """Validate tasks using."""
    task_name = config['task']
    if task_name not in TASKS:
        _LOGGER.error("%s not in %s", task_name, TASKS.keys())
        raise Invalid("Transform function {} not found".format(task_name))

    if 'target' in config and 'tables' in config:
        # Schema not yet executed on 'tables'
        tables0 = cv.ensure_list(config['tables'])[0]
        cv.col_copy(tables0, config['target'])

    task = TASKS[task_name]
    config = task.schema(config)

    return cv.AttrDict(config)


def remove_module(mod_name):
    """Remove module from tasks."""
    tasks = {k: v for k, v in TASKS.items() if v.module == mod_name}
    for key in tasks:
        TASKS.pop(key, None)
    # Ensure it will be reloaded...
    sys.modules.pop(mod_name, None)


def _import(mod_name):

    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    except ModuleNotFoundError:
        pass

    path = Path(mod_name + '.py').resolve(strict=True)
    mod_name = path.stem
    # print(path.parent)
    # print(mod_name)

    sys.path.insert(0, str(path.parent))
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    finally:
        if sys.path[0] == path.parent:
            sys.path.pop(0)


def load_module(mod_name):
    """Import tasks."""
    try:
        mod_obj = _import(mod_name)
    except ModuleNotFoundError as err:
        _LOGGER.error("Could not load module %s: %s", mod_name, err)
        return
    except FileNotFoundError as err:
        _LOGGER.error("Could not load module %s: %s", mod_name, err)
        return
    mod_name = mod_obj.__name__

    loaded = []
    members = inspect.getmembers(mod_obj)

    # collect task functions
    for nme, fun in members:
        if nme.startswith('task_'):
            task = Task(name=nme[5:], function=fun)  # , module=mod_obj)
            if task.name in TASKS:
                _LOGGER.warning(
                    "Module %s: Skipping task %s. Already loaded from "
                    "%s", mod_name, nme, TASKS[task.name].module)
                continue

            # Type
            sig = inspect.signature(fun)
            task.type = len(sig.parameters) - 1
            # if len(sig.parameters) == 1 and sig.parameters[0] == 'tables':
            #    task.type = -1  # All tables

            # Validator
            if not hasattr(task.function, 'schema'):
                _LOGGER.error("Module %s: No schema attached to function %s",
                              mod_name, nme)
                continue
            # task.schema = task.function.schema

            # Success
            loaded.append(task.name)
            TASKS[task.name] = task

    _LOGGER.debug(
        "Module %s: Loaded %s tasks: %s", mod_name, len(loaded),
        ', '.join(loaded)
    )

    return mod_name


def load_yaml(filename=None, text=None):
    """Load a YAML file."""
    if text:
        assert filename is None
        return yaml.load(text, Loader=yaml.SafeLoader) or OrderedDict()

    with open(filename, encoding='utf-8') as conf_file:
        return yaml.load(conf_file, Loader=yaml.SafeLoader) or OrderedDict()
    # except yaml.YAMLError as exc:
    #     _LOGGER.error(exc)
    #     raise HomeAssistantError(exc)
    # except UnicodeDecodeError as exc:
    #     _LOGGER.error("Unable to read file %s: %s", fname, exc)
    #     raise HomeAssistantError(exc)


# pylint: disable=protected-access
def _re(loader: yaml.SafeLoader, node: yaml.nodes.Node):
    return re.compile(node.value)


yaml.SafeLoader.add_constructor('!re', _re)


# From: https://gist.github.com/miracle2k/3184458
# pylint: disable=redefined-outer-name
def represent_odict(dump, tag, mapping, flow_style=None):
    """Like BaseRepresenter.represent_mapping but does not issue the sort()."""
    value = []
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if dump.alias_key is not None:
        dump.represented_objects[dump.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = mapping.items()
    for item_key, item_value in mapping:
        node_key = dump.represent_data(item_key)
        node_value = dump.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, yaml.ScalarNode) and
                not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dump.default_flow_style is not None:
            node.flow_style = dump.default_flow_style
        else:
            node.flow_style = best_style
    return node


def _find_file(loader, node: yaml.nodes.Node):
    """Get the full file path using everything."""
    from dataplaybook.everything import search
    res = search(node.value)
    if not res.files:
        raise FileNotFoundError()
    path = str(res.files[0].resolve(strict=True))
    _LOGGER.info(path)
    return path


yaml.SafeDumper.add_representer(
    OrderedDict,
    lambda dumper, value:
    represent_odict(dumper, 'tag:yaml.org,2002:map', value))
yaml.SafeLoader.add_constructor('!es', _find_file)
