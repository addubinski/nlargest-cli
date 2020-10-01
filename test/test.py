import unittest
from click.testing import CliRunner
from n_largest import get, clear_cache, set_cache_dir
from param_types import LocalPath, RemoteUrl


class CustomAssertions:

    @staticmethod
    def assertContains(result, target):
        if isinstance(result, Exception):
            raise result
        if not (target in result):
            raise AssertionError('"{}" was not found in the result "{}"'.format(target, result))


class TestInvalidArguments(unittest.TestCase, CustomAssertions):

    def test_required_arguments(self):
        runner = CliRunner()
        result = runner.invoke(get, [])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Missing argument \'URL\'.')
        result = runner.invoke(get, ['https://alexander-dubinski.com'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Missing argument \'N\'.')
        result = runner.invoke(set_cache_dir, [])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Missing argument \'ABSOLUTE_PATH\'.')

    def test_url_missing_https(self):
        runner = CliRunner()
        result = runner.invoke(get, ['alexander-dubinski.com', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Invalid value for \'URL\': alexander-dubinski.com is not a valid url')

    def test_url_is_fq_domain(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://alexander-dubinski/', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Invalid value for \'URL\': https://alexander-dubinski/ is not a valid url')

    def test_n_lt_one(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://alexander-dubinski.com', '0'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Invalid value for \'N\': 0 is smaller than the minimum valid value 1.')
        result = runner.invoke(get, ['https://alexander-dubinski.com', '--',  '-2'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Invalid value for \'N\': -2 is smaller than the minimum valid value 1.')

    def test_url_host_not_support_range(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://alexander-dubinski.com', '2'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output,
                            'Error: Invalid value for \'N\': 0 is smaller than the minimum valid value 1.')


class TestInvalidOptions(unittest.TestCase, CustomAssertions):

    def test_chunk_size_too_small(self):
        runner = CliRunner()
        result = runner.invoke(get, ['--chunk-size', '1023', 'https://alexander-dubinski.com', '50'])
        self.assertEqual(result.exit_code, 2)
        self.assertContains(result.output, 'Error: Invalid value for \'-c\' / \'--chunk-size\': 1023 is smaller than'
                                           ' the minimum valid value 1024.\n')


class TestNLargestReporting(unittest.TestCase, CustomAssertions):

    def test_output_is_only_ids(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://storage.googleapis.com/personal-webpage-static-jp/example.txt', '100'])
        self.assertEqual(result.exit_code, 0)
        self.assertContains(result.exception,
                            'Error: Invalid value for \'N\': 0 is smaller than the minimum valid value 1.')

    def test_correct_order(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://storage.googleapis.com/personal-webpage-static-jp/example.txt', '100'])
        self.assertEqual(result.exit_code, 0)
        self.assertContains(result.exception,
                            'Error: Invalid value for \'N\': 0 is smaller than the minimum valid value 1.')

    def test_n_gt_items(self):
        runner = CliRunner()
        result = runner.invoke(get, ['https://storage.googleapis.com/personal-webpage-static-jp/example.txt', '100'])
        self.assertEqual(result.exit_code, 0)
        self.assertContains(result.exception,
                            'Error: Invalid value for \'N\': 0 is smaller than the minimum valid value 1.')


class TestClearCache(unittest.TestCase):

    def test_config_file_missing(self):
        runner = CliRunner()
        result = runner.invoke(clear_cache, [])

    def test_config_file_key_missing(self):
        runner = CliRunner()
        result = runner.invoke(clear_cache, [])

    def test_directory_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(clear_cache, [])

    def test_cache_is_cleared(self):
        runner = CliRunner()
        result = runner.invoke(clear_cache, [])


class TestSetCacheDir(unittest.TestCase):

    def test_set_cache_dir_is_file(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])

    def test_default_config_file_created(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])

    def test_nonexistent_dir_created(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])

    def test_all_existing_files_moved_to_new_cache(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])

    def success_message(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])


class TestCustomParamType(unittest.TestCase):
    local_path = LocalPath()
    remote_url = RemoteUrl()
    pass


class AllTests(unittest.TestSuite):

    def __init__(self):
        super().__init__()
        self.addTests([
            TestInvalidArguments(),
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
