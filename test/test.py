import pickle
import re
import unittest
import requests
from click.testing import CliRunner
from n_largest import get, clear_cache, set_cache_dir
from constants import CACHE_PATH
from param_types import LocalPath, RemoteUrl
from util import NoContentError


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

    def test_url_host_supports_range(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://alexander-dubinski.com', '2'])
        self.assertEqual(result.exit_code, 1)
        self.assertIsInstance(result.exception, requests.exceptions.HTTPError)


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
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '2'])
            self.assertEqual(result.exit_code, 0)
            self.assertRegex(result.output, r'^([a-z0-9]{32})(\r?\n)([a-z0-9]{32})(\r?\n)$')

    def test_correct_order(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '6'])
        self.assertEqual(result.exit_code, 0)
        self.assertRegex(result.output, r'^(a00f29a8ed4b4ae79738121dd03d576c)(\r?\n)(8dab177516c04262abdef3f3e6200548)'
                                        r'(\r?\n)(56b536ef84324182b0211679935fc370)(\r?\n)'
                                        r'(50f5f7dbcc7542a5a1241d5151d9b9e3)(\r?\n)(4945f09d164b49459c35d3f9b5ec12b7)'
                                        r'(\r?\n)(5fc9ae59efb644be90cb9c22a70f6dac)(\r?\n)$')

    def test_correct_num_ids(self):
        number_of_ids = 4
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         str(number_of_ids)])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(re.split(r'\r?\n', result.output.strip())) == number_of_ids)

    def test_n_gt_items(self):
        total_number_of_ids = 6
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '100'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(re.split(r'\r?\n', result.output.strip())) == total_number_of_ids)

    def test_empty_remote_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('config.pickle', 'wb+') as f:
                pickle.dump({CACHE_PATH: './'}, f)
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/empty_test.txt',
                                         '5'])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, NoContentError)


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

    def test_success_message(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [])


class TestCustomParamType(unittest.TestCase):
    local_path = LocalPath()
    remote_url = RemoteUrl()
    pass


if __name__ == '__main__':
    test_program = unittest.main()
