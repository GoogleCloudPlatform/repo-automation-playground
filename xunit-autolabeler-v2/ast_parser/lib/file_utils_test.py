# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest

from . import file_utils

TEST_DIR = os.path.join(
    os.path.dirname(__file__),
    'test_data'
)


class GetFilesTest(unittest.TestCase):
    def test_getfiles_ignores_dotfiles(self):
        files = file_utils._get_file_paths(
            TEST_DIR, lambda x: True)

        assert 'dotfile_tag' not in str(files)


class GetPythonFilesTest(unittest.TestCase):
    def test_finds_python_files(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'test.py' in files[0]

    def test_excludes_appengine_lib_folders(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'should_be_ignored.py' not in str(files)

    def test_includes_appengine_lib_files(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'lib.py' in str(files)
        assert 'library.py' in str(files)

    def test_includes_appengine_folders(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'gae_sample.py' in str(files)

    def test_includes_non_appengine_lib_folders(self):
        files = file_utils.get_python_files(TEST_DIR)

        assert 'gcf_lib.py' in str(files)


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

    def test_includes_dockerfile_case_insensitive(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'dockerfile_tag1' in region_tags
        assert 'dockerfile_tag_odd_casing' in region_tags

    def test_excludes_appengine_lib(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'appengine_lib' not in region_tags

    def test_includes_block_comments(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'gae_block_comment_tag' in region_tags

    def test_excludes_node_modules(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'node_modules' not in region_tags

    def test_includes_appengine_html(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'gae_html_1' in region_tags
        assert 'gae_html_2' in region_tags

    def test_includes_appengine_css(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'gae_css_1' in region_tags
        assert 'gae_css_2' in region_tags

    def test_excludes_webapps_outside_of_appengine(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'css_outside_gae' not in region_tags
        assert 'html_outside_gae' not in region_tags

    def test_includes_yml_and_yaml(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'yml_tag' in region_tags
        assert 'yaml_tag' in region_tags

    def test_includes_node_config_json_files(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'package_json' in region_tags
        assert 'config_json' in region_tags

    def test_includes_directories_with_node_modules_suffix(self):
        region_tags = file_utils.get_region_tags(TEST_DIR)

        assert 'not_really_node_modules' in region_tags
