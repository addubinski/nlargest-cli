import click
import pickle
import gzip
from constants import DEFAULT_CACHE_PATH, CACHE_PATH, CONFIG_FILE_NAME
from param_types import LocalPath, RemoteUrl
from pathlib import Path
from os import remove
from util import get_remote_file, get_n_largest, print_n_largest


@click.group()
def n_largest_cli():
    """
    CLI for getting id, number pairs from a remote text file and printing the ids of the largest N numbers to stdout.
    Additionally includes cache configuration utilities to improve performance.
    """
    pass


@n_largest_cli.command()
@click.option('--no-cache', help='Prevents the input file from being cached for later use. If the file already exists'
                                 ' in the cache it will be removed and the remote target file will be used.',
              is_flag=True)
@click.option('--refresh-cache', help='Forces the remote file to be taken from the remote resource and re-populate'
                                      ' the cache.', is_flag=True)
@click.option('-c', '--chunk-size', help='Size of chunks (in bytes) for each request to the remote file. Larger files'
                                         ' should use larger chunk sizes to improve performance. Minimum chunk size '
                                         'is 1024 bytes (Default: 256kb -> 256000 bytes)',
              type=click.IntRange(min=1024), default=256000)
@click.argument('url', type=RemoteUrl(), required=True)
@click.argument('n', type=click.IntRange(min=1), required=True)
def get(no_cache, refresh_cache, chunk_size, url, n):
    """
    Prints the ids of the N largest numbers in the target remote file found at URL.

    URL is the http(s) path containing a fully qualified domain name to the target file.

    N is the number of ids which will be printed to stdout
    (each id corresponding to the ith largest number in the file).

    Remote files are received in discrete chunks in order to preserve memory in the case of large files. Larger files
    should use the --chunk-size option to increase performance. Minimum chunk size is 1024 bytes with default value of
    256kb (256000 bytes).
    """
    config_path = Path(CONFIG_FILE_NAME)
    if not config_path.exists():
        default_cache_file = config_path.open('wb+')
        pickle.dump({CACHE_PATH: DEFAULT_CACHE_PATH}, default_cache_file)
        default_cache_file.close()
    config_file = config_path.open('rb')
    config = pickle.load(config_file)
    if not config[CACHE_PATH]:
        raise KeyError('cache_path not found in config file.')
    config_file.close()
    cache_root = Path(config[CACHE_PATH])
    file_name = get_remote_file(url, chunk_size, cache_root, refresh_cache)
    file = gzip.open((cache_root / file_name), 'rb')
    n_largest = get_n_largest(file, n)
    print_n_largest(n_largest)
    file.close()
    if no_cache:
        remove(cache_root / file_name)


@n_largest_cli.command()
@click.argument('absolute_path', type=LocalPath(), required=True)
def set_cache_dir(absolute_path):
    """
    Sets the absolute_path in the local filesystem where cached files will be stored. All files in the current cache
    will be migrated to the new cache directory.
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
    click.echo('Cache path set to {}'.format(absolute_path))


@n_largest_cli.command()
def clear_cache():
    """
    Clears all the content of cache.
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
    click.echo('Cache cleared.')
