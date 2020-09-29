import click
import re
import requests
from pathlib import Path
from io import StringIO
from operator import itemgetter
import heapq


class RemoteUrlOrPath(click.ParamType):
    name = 'remote-url'

    def __init__(self):
        self.is_url = False

    def convert(self, url, param, ctx):
        is_local = bool('local' in ctx.params and ctx.params['local'])
        if is_local:
            self.is_url = re.match(r'^/[A-Za-z0-9/]+(\.[A-Za-z0-9]+)?$', url) and Path(url).exists()
        else:
            self.is_url = re.match(r'^http(s)?://[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+\.[A-Za-z0-9]+$', url)

        if not self.is_url:
            self.fail(
                '{} is not a valid {}'.format(url, 'url' if is_local else 'absolute path'),
                param,
                ctx
            )
        return url


@click.command()
@click.option('-l', '--local', help='Search for the input file in the local filesystem '
                                    '(must provide absolute path)', is_flag=True)
@click.argument('url', type=RemoteUrlOrPath(), required=True)
@click.argument('n', type=click.IntRange(min=0, max=10000), required=True)
def get(local, url, n):
    """
    Print the ids of the N largest numbers in the input file at url/path URL.

    URL is the http(s) path with a fully qualified domain name of the target file
     (or absolute path in the local filesystem)

    N is the number of ids which will be printed to stdout (each id corresponding to the ith largest number in the file)
    """
    if local:
        click.echo('Opening file..')
        file = open(url, 'r')
        click.echo('Processing...')
        n_largest = process_lines(file, n)
        print_n_largest(n_largest)
        file.close()
        click.echo('done.')
    else:
        click.echo('Downloading remote file..')
        req = requests.get(url)
        if req.status_code == requests.codes.ok:
            target_numbers = StringIO(req.text)
            click.echo('Processing...')
            n_largest = process_lines(target_numbers, n)
            print_n_largest(n_largest)
            click.echo('done.')
        else:
            click.echo('request to remote file failed, please try again.')


def process_lines(target_numbers, n):
    target_numbers.read(500)
    return heapq.nlargest(n,
                          ((num_id, int(number)) for num_id, number in split_generator(target_numbers.readlines())),
                          key=itemgetter(1))


def print_n_largest(n_largest):
    for num_id, number in n_largest:
        click.echo(num_id)


def split_generator(lines):
    for line in lines:
        yield re.split('\\s+', line.strip())
