import unittest
import subprocess
import filecmp


class TestCLI(unittest.TestCase):

    def test_required_arguments(self):

        result_file = open('test_result.txt', 'w+')
        process = subprocess.Popen(['get-n-largest'], shell=True, stdout=subprocess.PIPE, stderr=result_file)
        stdout, _ = process.communicate()
        self.assertFalse(bool(stdout))
        self.assertTrue(filecmp.cmp('test_result.txt', 'test_reference_files/missing_url.txt'),
                        'Stderr reference for missing argument "URL" did not match.')
        result_file.close()

        result_file = open('test_result.txt', 'w+')
        process = subprocess.Popen(['get-n-largest', 'https://dummy-path.com/test.txt'],
                                   shell=True, stdout=subprocess.PIPE, stderr=result_file)
        stdout, _ = process.communicate()
        self.assertFalse(bool(stdout))
        self.assertTrue(filecmp.cmp('test_result.txt', 'test_reference_files/missing_n.txt'),
                        'Stderr reference for missing argument "N" did not match.')
        result_file.close()

        result_file = open('test_result.txt', 'w+')
        process = subprocess.Popen(['n-largest-set-cache'],
                                   shell=True, stdout=subprocess.PIPE, stderr=result_file)
        stdout, _ = process.communicate()
        self.assertFalse(bool(stdout))
        self.assertTrue(filecmp.cmp('test_result.txt', 'test_reference_files/set_cache_missing_url.txt'),
                        'Stderr reference for missing argument "ABSOLUTE_PATH" did not match.')
        result_file.close()





class TestGetNLargest(unittest.TestCase):
    pass


class TestSplitGenerator(unittest.TestCase):
    pass


class TestProcessLines(unittest.TestCase):
    pass


class TestCustomParamType(unittest.TestCase):
    pass
