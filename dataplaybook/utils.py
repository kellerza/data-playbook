"""DataEnvironment class."""
import logging
from dataplaybook.config_validation import util_slugify
from dataplaybook.const import PlaybookError


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


class DataVars(dict):
    """DataEnvironment supports key access and variables."""
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, val):
        self[key] = val

    def __setitem__(self, key, val):
        """Ensure key is slug."""
        if key != util_slugify(key):
            raise PlaybookError(
                f"Invalid variable name '{key}' use '{util_slugify(key)}")
        dict.__setitem__(self, key, val)


class DataEnvironment(dict):
    """DataEnvironment supports key access and variables."""
    def __init__(self):
        self._var = DataVars()
        dict.__setitem__(self, 'var', self._var)
        super().__init__()

    @property
    def var(self):
        """Return variables class."""
        return self._var

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, val):
        if key == '_var':
            if '_var' in self:
                raise Exception('Cant rewrite _var')
            return dict.__setattr__(self, key, val)
        raise Exception(f'use [{key}]')

    def __getitem__(self, key):
        if key == 'var':
            return [{'name': k, 'value': v} for k, v in self._var.items()]
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        if key == 'var':
            raise Exception("Cannot set vaiables directly. Use .var.")
        dict.__setitem__(self, key, val)
