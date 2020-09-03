import unittest
import os

from . import file_utils

TEST_DIR = os.path.join(
    os.path.dirname(__file__),
    'test_data'
)


class GetFilesTest(unittest.TestCase):
    def test_getfiles_ignores_dotfiles(self):
        files = file_utils._getFiles(TEST_DIR, lambda x: True)
        
        assert 'dotfile_tag' not in str(files)


class GetPythonFilesTest(unittest.TestCase):
    def test_finds_python_files(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'test.py' in files[0]

    def test_excludes_appengine_lib_folders(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'gae_lib.py' not in str(files)

    def test_includes_non_appengine_lib_folders(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'gcf_lib.py' not in str(files)


class GetDriftYamlFilesTest(unittest.TestCase):
    def test_finds_yml_files(self):
        files = file_utils.get_drift_yaml_files(TEST_DIR)

        assert '.drift-data.yml' in str(files)

    def test_finds_yaml_files(self):
        files = file_utils.get_drift_yaml_files(TEST_DIR)
        
        assert '.drift-data.yaml' in str(files)


    def test_excludes_yml_files_with_wrong_name(self):
        files = file_utils.get_drift_yaml_files(TEST_DIR)
        
        assert '.bad-name.yml' not in str(files)


class GetRegionTagsTest(unittest.TestCase):
    def test_finds_region_tags(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)
        
        assert 'region_tag' in region_tags
