import click
import re
import requests
import hashlib
from constants import SUCCESS_STATUS, FILE_START, DEFAULT_CACHE_PATH, CACHE_PATH, CONFIG_FILE_NAME
from operator import itemgetter
import heapq
import pickle
from pathlib import Path
from os import remove, fsync
import gzip

RANGE_HEADER = 'Range'
RANGE_HEADER_TEMPLATE = 'bytes={}-{}'


class RemoteUrl(click.ParamType):
    name = 'remote-url'

    def __init__(self):
        self.is_url = False

    def convert(self, url, param, ctx):
        self.is_url = re.match(r'^http(s)?://[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+\.[A-Za-z0-9]+$', url)

        if not self.is_url:
            self.fail(
                '{} is not a valid url'.format(url),
                param,
                ctx
            )
        return url


@click.command()
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
def get_n_largest(no_cache, refresh_cache, chunk_size, url, n):
    """
    Prints the ids of the N largest numbers in the target remote file found at URL.

    URL is the http(s) path containing a fully qualified domain name to the target file.

    N is the number of ids which will be printed to stdout (each id corresponding to the ith largest number in the file)

    Remote files are received in discrete chunks in order to preserve memory in the case of large files. Larger files
    should use the --chunk-size option to increase performance. Minimum chunk size is 1024 bytes with default value of
    256kb (256000 bytes)
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
    n_largest = process_file(file, n)
    print_n_largest(n_largest)
    file.close()
    if no_cache:
        remove(cache_root / file_name)


def process_file(file, n):
    return heapq.nlargest(n,  id_number_tuple_generator(file), key=itemgetter(1))


def print_n_largest(n_largest):
    for num_id, number in n_largest:
        click.echo(num_id)


def id_number_tuple_generator(file):
    for num_id, number in split_generator(file):
        yield num_id, int(number)


def split_generator(file):
    while True:
        next_line = file.readline()
        if not bool(next_line):
            break
        yield re.split('\\s+', next_line.decode().strip())


def get_remote_file(url, chunk_size, cache_root, should_refresh):
    current_chunk = FILE_START
    file_name = Path('{}.gz'.format(hashlib.sha256(url.encode()).hexdigest()))
    cache_file = (cache_root / file_name)
    if cache_file.exists() and not should_refresh:
        return file_name
    new_file = gzip.open(cache_file, 'wb+')
    req = requests.get(url, headers=make_range_header(current_chunk, chunk_size))
    content = req.text
    while req.status_code != requests.codes.range_not_satisfiable:
        if req.status_code == SUCCESS_STATUS:
            new_file.write(content.encode())
        else:
            if req.status_code == requests.codes.ok:
                raise requests.exceptions.HTTPError('Target file host does not support "Range" http headers. Please use'
                                                    ' an AWS S3 bucket or a host which supports the required headers.')
            req.raise_for_status()
        current_chunk += chunk_size + 1
        req = requests.get(url, headers=make_range_header(current_chunk, chunk_size))
        content = req.text
    new_file.flush()
    fsync(new_file.fileno())
    new_file.close()
    return file_name


def make_range_header(current_chunk, chunk_size):
    return {RANGE_HEADER: RANGE_HEADER_TEMPLATE.format(current_chunk, current_chunk + chunk_size)}
