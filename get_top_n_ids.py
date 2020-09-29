import click
import re
import requests
from pathlib import Path


class RemoteUrlOrPath(click.ParamType):
    name = 'remote-url'

    def __init__(self):
        self.is_url = False

    def convert(self, url, param, ctx):
        is_local = bool(ctx.params['local'])
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
        click.echo('Sorting...')
        file.close()
    else:
        click.echo('Downloading remote file..')
        req = requests.get(url)
        click.echo(req.status_code)




