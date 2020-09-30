import unittest
from click.testing import CliRunner
from n_largest import get, clear_cache, set_cache_dir


class TestGetNLargest(unittest.TestCase):

    def test_invalid_parameters(self):
        runner = CliRunner()
        result = runner.invoke(get, ['alexander/dubinski', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.output,
                         'Usage: get [OPTIONS] URL N\nTry \'get --help\' for help.\n\nError: Invalid value for \'URL\':'
                         ' alexander/dubinski is not a valid url\n')


class TestClearCache(unittest.TestCase):
    pass


class TestSetCacheDir(unittest.TestCase):
    pass


class TestCustomParamType(unittest.TestCase):
    pass


class AllTests(unittest.TestSuite):

    def __init__(self):
        super().__init__()
        self.addTests([TestGetNLargest(), TestClearCache(), TestSetCacheDir(), TestCustomParamType()])


if __name__ == '__main__':
    test = AllTests()
    result = unittest.TestResult()
    test.run(result)
    assert len(result.errors) == 0
    assert len(result.failures) == 0
    assert result.wasSuccessful()
