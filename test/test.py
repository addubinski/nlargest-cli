import unittest
from click.testing import CliRunner
from n_largest import get, clear_cache, set_cache_dir


class TestInvalidParameters(unittest.TestCase):

    def test_url_missing_https(self):
        runner = CliRunner()
        result = runner.invoke(get, ['alexander-dubinski.com', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.output,
                         'Usage: get [OPTIONS] URL N\nTry \'get --help\' for help.\n\nError: Invalid value for \'URL\':'
                         ' alexander-dubinski.com is not a valid url\n')


class TestInvalidOptions(unittest.TestCase):

    def test_chunk_size_too_small(self):
        runner = CliRunner()
        result = runner.invoke(get, ['--chunk-size', '1023', 'https://alexander-dubinski.com', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.output,
                         'Usage: get [OPTIONS] URL N\nTry \'get --help\' for help.\n\nError: Invalid value for \'-c\''
                         ' / \'--chunk-size\': 1023 is smaller than the minimum valid value 1024.\n')


class TestNLargestReporting(unittest.TestCase):
    pass


class TestClearCache(unittest.TestCase):
    pass


class TestSetCacheDir(unittest.TestCase):
    pass


class TestCustomParamType(unittest.TestCase):
    pass


class AllTests(unittest.TestSuite):

    def __init__(self):
        super().__init__()
        self.addTests([
            TestInvalidParameters(),
            TestInvalidOptions(),
            TestNLargestReporting(),
            TestClearCache(),
            TestSetCacheDir(),
            TestCustomParamType()
        ])


if __name__ == '__main__':
    test = AllTests()
    suite_result = unittest.TestResult()
    test.run(suite_result)
    assert len(suite_result.errors) == 0
    assert len(suite_result.failures) == 0
    assert suite_result.wasSuccessful()
