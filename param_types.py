import click
import re

URL_REGEX = r'^http(s)?://([A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+)(\.)([A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+)$'
ABS_PATH_REGEX = r'^/([A-Za-z0-9/_.]+)?$'


class LocalPath(click.ParamType):
    name = 'local-path'

    def __init__(self):
        self.is_valid_path = False

    def convert(self, path, param, ctx):
        self.is_valid_path = re.match(ABS_PATH_REGEX, path)

        if not self.is_valid_path:
            self.fail(
                '{} is not a valid absolute path'.format(path),
                param,
                ctx
            )
        return path


class RemoteUrl(click.ParamType):
    name = 'remote-url'

    def __init__(self):
        self.is_url = False

    def convert(self, url, param, ctx):
        self.is_url = re.match(URL_REGEX, url)

        if not self.is_url:
            self.fail(
                '{} is not a valid url'.format(url),
                param,
                ctx
            )
        return url
