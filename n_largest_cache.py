import click
import re
import pickle
from pathlib import Path
from constants import CONFIG_FILE_NAME, CACHE_PATH, DEFAULT_CACHE_PATH


class LocalPath(click.ParamType):
    name = 'local-path'

    def __init__(self):
        self.is_valid_path = False

    def convert(self, path, param, ctx):
        self.is_valid_path = re.match(r'^/([A-Za-z0-9/_.]+)?$', path)

        if not self.is_valid_path:
            self.fail(
                '{} is not a valid absolute path'.format(path),
                param,
                ctx
            )
        return path


@click.command()
def clear_cache():
    """
    Clears all the content of cache
    """
    if not Path(CONFIG_FILE_NAME).exists():
        raise FileNotFoundError('Config file "config.pickle" not found. Please run n-largest-set-cache ABSOLUTE_PATH'
                                ' to re-initialize application cache configuration.')
    config_file = open(CONFIG_FILE_NAME, 'rb')
    config = pickle.load(config_file)
    if not config[CACHE_PATH]:
        raise KeyError('cache_path not found in config file. Please run n-largest-set-cache ABSOLUTE_PATH to'
                       ' re-initialize application cache configuration.')
    cache_dir = Path(config[CACHE_PATH])
    if not cache_dir.exists() or not cache_dir.is_dir():
        raise NotADirectoryError('The configured cache path does not exist or is a file. Please run n-largest-set-cache'
                                 ' ABSOLUTE_PATH to re-initialize application cache configuration.')
    for path in cache_dir.iterdir():
        if path.is_file():
            path.unlink(missing_ok=True)


@click.command()
@click.argument('absolute_path', type=LocalPath(), required=True)
def set_cache_dir(absolute_path):
    """
    Sets the absolute_path in the local filesystem where cached files will be stored. All files in the current cache
    will be migrated to the new cache directory
    """
    target_cache_path = Path(absolute_path)
    if target_cache_path.is_file():
        raise NotADirectoryError('Provided path {} is a file, cache path must be a directory.')
    if not Path(CONFIG_FILE_NAME).exists():
        default_cache_file = open(CONFIG_FILE_NAME, 'wb+')
        pickle.dump({CACHE_PATH: DEFAULT_CACHE_PATH}, default_cache_file)
        default_cache_file.close()
    config_file = open(CONFIG_FILE_NAME, 'rb')
    config = pickle.load(config_file)
    config_file.close()
    if not target_cache_path.exists():
        target_cache_path.mkdir(parents=True, exist_ok=True)
    old_cache_path = Path(config[CACHE_PATH])
    for file in old_cache_path.glob('*.gz'):
        file.rename(target_cache_path / file.name)
    config[CACHE_PATH] = absolute_path
    config_file = open(CONFIG_FILE_NAME, 'wb+')
    pickle.dump(config, config_file)
    config_file.close()
    click.echo('Cache set to path {}'.format(absolute_path))
