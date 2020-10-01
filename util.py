import click
import re
import requests
import hashlib
import heapq
import gzip
from constants import SUCCESS_STATUS, FILE_START, RANGE_HEADER_TEMPLATE, RANGE_HEADER
from operator import itemgetter
from pathlib import Path
from os import fsync


def get_n_largest(file, n):
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
