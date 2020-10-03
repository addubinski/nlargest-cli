import pickle
import re
import unittest

import click
import requests
import shutil
from click.testing import CliRunner
from n_largest import get, clear_cache, set_cache_dir
from constants import CACHE_PATH, CONFIG_FILE_NAME
from param_types import LocalPath, RemoteUrl
from util import NoContentError
from pathlib import Path

TEST_FILE_HASH = '04f62a08ad528d36cf6ff8c7e1dcf4b77f443fbf8f638a234e3aa1f4f1185284'
DEFAULT_VAR_DIR = Path('/usr/var')
CACHE_DIR = Path('cache')
CACHE_FULL_PATH = DEFAULT_VAR_DIR / CACHE_DIR
CONFIG_FILE_PATH = Path(CONFIG_FILE_NAME)
NEW_CACHE = DEFAULT_VAR_DIR / Path('nlargest/cache')


class CustomAssertions:

    @staticmethod
    def inject_default_config_file():
        file = CONFIG_FILE_PATH.open('wb+')
        pickle.dump({CACHE_PATH: CACHE_FULL_PATH}, file)
        file.close()

    @staticmethod
    def assertContains(result, target):
        if isinstance(result, Exception):
            raise result
        if not (target in result):
            raise AssertionError('"{}" was not found in the result "{}"'.format(target, result))

    @staticmethod
    def assertDoesNotContain(result, target):
        if isinstance(result, Exception):
            raise result
        if target in result:
            raise AssertionError('"{}" was found in the result "{}"'.format(target, result))


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
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://alexander-dubinski.com', '2'])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, requests.exceptions.HTTPError)

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if DEFAULT_VAR_DIR.exists():
                shutil.rmtree(DEFAULT_VAR_DIR)
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


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
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '2'])
            self.assertEqual(result.exit_code, 0)
            self.assertRegex(result.output, r'^([a-z0-9]{32})(\r?\n)([a-z0-9]{32})(\r?\n)$')

    def test_correct_order(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '6'])
            self.assertEqual(result.exit_code, 0)
            self.assertRegex(result.output,
                             r'^(a00f29a8ed4b4ae79738121dd03d576c)(\r?\n)(8dab177516c04262abdef3f3e6200548)'
                             r'(\r?\n)(56b536ef84324182b0211679935fc370)(\r?\n)'
                             r'(50f5f7dbcc7542a5a1241d5151d9b9e3)(\r?\n)(4945f09d164b49459c35d3f9b5ec12b7)'
                             r'(\r?\n)(5fc9ae59efb644be90cb9c22a70f6dac)(\r?\n)$')

    def test_correct_num_ids(self):
        number_of_ids = 4
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         str(number_of_ids)])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(re.split(r'\r?\n', result.output.strip())) == number_of_ids)

    def test_n_gt_items(self):
        total_number_of_ids = 6
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '100'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(re.split(r'\r?\n', result.output.strip())) == total_number_of_ids)

    def test_empty_remote_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/empty_test.txt',
                                         '5'])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, NoContentError)

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if DEFAULT_VAR_DIR.exists():
                shutil.rmtree(DEFAULT_VAR_DIR)
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


class TestCacheBehavior(unittest.TestCase, CustomAssertions):

    def test_file_cached_in_cache_dir(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH)))
                            .exists())

    def test_no_cache_flag_prevents_cache(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['--no-cache',
                                         'https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(not any((True for _ in CACHE_FULL_PATH.iterdir())))

    def test_notifies_when_using_cached_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertContains(result.output, '\nUsing cached file...\n')

    def test_no_cache_flag_deletes_old_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            result = runner.invoke(get, ['--no-cache',
                                         'https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(not any((True for _ in CACHE_FULL_PATH.iterdir())))

    def test_refresh_cache_ignores_cache(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertContains(result.output, '\nUsing cached file...\n')
            result = runner.invoke(get, ['--refresh-cache',
                                         'https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertDoesNotContain(result.output, '\nUsing cached file...\n')

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if DEFAULT_VAR_DIR.exists():
                shutil.rmtree(DEFAULT_VAR_DIR)
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


class TestClearCache(unittest.TestCase, CustomAssertions):

    def test_config_file_missing(self):
        runner = CliRunner()
        if CONFIG_FILE_PATH.exists():
            CONFIG_FILE_PATH.unlink()
        self.assertTrue(not CONFIG_FILE_PATH.exists())
        result = runner.invoke(clear_cache, [])
        self.assertEqual(result.exit_code, 1)
        self.assertIsInstance(result.exception, FileNotFoundError)

    def test_config_file_key_missing(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with CONFIG_FILE_PATH.open('wb+') as file:
                pickle.dump({'wrong_key': CACHE_FULL_PATH}, file)
            result = runner.invoke(clear_cache, [])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, KeyError)

    def test_directory_does_not_exist(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            self.inject_default_config_file()
            result = runner.invoke(clear_cache, [])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, NotADirectoryError)

    def test_cache_is_cleared(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            CACHE_FULL_PATH.mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            result = runner.invoke(clear_cache, [])
            self.assertContains(result.output, 'Cache cleared.')
            self.assertTrue(not any((True for _ in Path(CACHE_FULL_PATH).iterdir())))

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if DEFAULT_VAR_DIR.exists():
                shutil.rmtree(DEFAULT_VAR_DIR)
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


class TestSetCacheDir(unittest.TestCase, CustomAssertions):

    def test_set_cache_dir_is_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            DEFAULT_VAR_DIR.mkdir(parents=True)
            (DEFAULT_VAR_DIR / Path('cache.txt')).touch()
            self.inject_default_config_file()
            result = runner.invoke(set_cache_dir, [str(DEFAULT_VAR_DIR / Path('cache.txt')).replace('\\', '/')])
            self.assertEqual(result.exit_code, 1)
            self.assertIsInstance(result.exception, NotADirectoryError)

    def test_default_config_file_created(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            self.assertTrue(not CONFIG_FILE_PATH.exists())
            result = runner.invoke(set_cache_dir, [str(DEFAULT_VAR_DIR).replace('\\', '/')])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(CONFIG_FILE_PATH.exists())

    def test_nonexistent_dir_created(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            self.assertTrue(not NEW_CACHE.parent.exists())
            self.assertTrue(not NEW_CACHE.exists())
            result = runner.invoke(set_cache_dir, [str(DEFAULT_VAR_DIR / Path('nlargest/cache')).replace('\\', '/')])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(NEW_CACHE.parent.exists())
            self.assertTrue(NEW_CACHE.exists())

    def test_all_existing_files_moved_to_new_cache(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(CACHE_FULL_PATH).mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt', '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((CACHE_FULL_PATH / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            self.assertTrue(
                not (NEW_CACHE / Path('{}.gz'.format(TEST_FILE_HASH))).exists())
            result = runner.invoke(set_cache_dir, [str(NEW_CACHE).replace('\\', '/')])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((NEW_CACHE / Path('{}.gz'.format(TEST_FILE_HASH))).exists())

    def test_new_files_go_to_new_cache(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(CACHE_FULL_PATH).mkdir(parents=True)
            self.inject_default_config_file()
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(any(TEST_FILE_HASH in str(path) for path in CACHE_FULL_PATH.iterdir()))
            result = runner.invoke(set_cache_dir, [str(NEW_CACHE).replace('\\', '/')])
            self.assertEqual(result.exit_code, 0)
            for file in NEW_CACHE.iterdir():
                file.unlink()
            self.assertTrue(not any((True for _ in Path(CACHE_FULL_PATH).iterdir())))
            result = runner.invoke(get, ['https://triad-space-maps.s3-ap-northeast-1.amazonaws.com/test.txt',
                                         '3'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((NEW_CACHE / Path('{}.gz'.format(TEST_FILE_HASH))).exists())

    def test_success_message(self):
        runner = CliRunner()
        result = runner.invoke(set_cache_dir, [str(NEW_CACHE).replace('\\', '/')])
        self.assertEqual(result.exit_code, 0)
        self.assertContains(result.output, 'Cache path set to {}'.format(str(NEW_CACHE)
                                                                         .replace('\\', '/')))

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if DEFAULT_VAR_DIR.exists():
                shutil.rmtree(DEFAULT_VAR_DIR)
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


class TestCustomParamType(unittest.TestCase):
    local_path = LocalPath()
    remote_url = RemoteUrl()

    def test_local_path_is_random(self):
        self.assertRaises(click.exceptions.BadParameter, self.local_path.convert, 'ABC123abc123', None, None)

    def test_remote_url_is_random(self):
        self.assertRaises(click.exceptions.BadParameter, self.remote_url.convert, 'ABC123abc123', None, None)

    def test_local_with_illegal_characters(self):
        self.assertRaises(click.exceptions.BadParameter, self.local_path.convert, '/user/var/al{}ex', None, None)

    def test_local_path_not_absolute_path(self):
        self.assertRaises(click.exceptions.BadParameter, self.local_path.convert, './user/var/cache', None, None)
        self.assertRaises(click.exceptions.BadParameter, self.local_path.convert, 'user/var/alex', None, None)

    def test_remote_url_missing_http_or_https(self):
        self.assertRaises(click.exceptions.BadParameter, self.remote_url.convert, 'alexander-dubinski.com', None, None)

    def test_remote_url_missing_top_level_domain(self):
        self.assertRaises(click.exceptions.BadParameter, self.remote_url.convert, 'https://random-url', None, None)

    def test_remote_url_with_illegal_character(self):
        self.assertRaises(click.exceptions.BadParameter, self.remote_url.convert, 'https://alex{}-dubinski.com',
                          None, None)

    def tearDown(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            if CONFIG_FILE_PATH.exists():
                CONFIG_FILE_PATH.unlink()


if __name__ == '__main__':
    test_results = test_program = unittest.main()
