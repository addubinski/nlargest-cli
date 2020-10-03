from requests import codes
from pathlib import Path

SUCCESS_STATUS = codes.partial
FILE_START = 500
DEFAULT_CACHE_PATH = '/var/nlargest/cache'
CACHE_PATH = 'cache_path'
CONFIG_FILE_NAME = 'config.pickle'
CONFIG_FILE_PATH = Path('/usr/src/app') / Path(CONFIG_FILE_NAME)
RANGE_HEADER = 'Range'
RANGE_HEADER_TEMPLATE = 'bytes={}-{}'
