from requests import codes

SUCCESS_STATUS = codes.partial
FILE_START = 500
DEFAULT_CACHE_PATH = '/var/nlargest/cache'
CACHE_PATH = 'cache_path'
CONFIG_FILE_NAME = 'config.pickle'
RANGE_HEADER = 'Range'
RANGE_HEADER_TEMPLATE = 'bytes={}-{}'
