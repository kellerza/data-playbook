"""Dynamically load additional modules."""
from importlib import import_module
from inspect import getmembers
import logging
import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml
from dataplaybook.const import PlaybookError
from dataplaybook.task import TaskDef

_LOGGER = logging.getLogger(__name__)


class TaskDefs(dict):

    def remove_module(self, mod_name):
        """Remove module from tasks."""
        sys.modules.pop(mod_name, None)  # Ensure it will be reloaded...

        pop = []
        for key, val in self.items():
            # _LOGGER.debug("k %s v '%s' '%s'", key, val.module, mod_name)
            if mod_name == val.module:
                pop.append(key)

        for key in pop:
            self.pop(key, None)
        return pop

    def load_module(self, mod_name):
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
        members = getmembers(mod_obj)

        # collect task functions
        for nme, fun in members:
            if nme.startswith('task_'):
                task = TaskDef(name=nme[5:], function=fun, module=mod_name)
                if task.name in self:
                    _LOGGER.warning(
                        "Module %s: Skipping task %s. Already loaded from "
                        "%s", mod_name, nme, self[task.name].module)
                    continue

                # Success
                loaded.append(task.name)
                self[task.name] = task

        _LOGGER.debug(
            "Module %s: Loaded %s tasks: %s", mod_name, len(loaded),
            ', '.join(loaded)
        )

        return mod_name


def _import(mod_name):

    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    except ModuleNotFoundError:
        pass

    path = Path(mod_name + '.py').resolve(strict=True)
    mod_name = path.stem

    sys.path.insert(0, str(path.parent))
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    finally:
        if sys.path[0] == path.parent:
            sys.path.pop(0)


def load_yaml(filename=None, text=None):
    """Load a YAML file."""
    if text:
        assert filename is None
        return yaml.safe_load(text) or OrderedDict()

    try:
        with Path(filename).open(encoding='utf-8') as conf_file:
            return yaml.safe_load(conf_file) \
                or OrderedDict()
    except yaml.YAMLError as exc:
        _LOGGER.error(exc)
        raise PlaybookError()
    except UnicodeDecodeError as exc:
        _LOGGER.error("Unable to read file %s: %s", filename, exc)
        raise PlaybookError()


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
