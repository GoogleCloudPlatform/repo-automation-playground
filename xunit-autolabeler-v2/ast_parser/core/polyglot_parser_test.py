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


import json
import unittest
from os import path

from ast_parser.core import polyglot_drift_data as pdd
from ast_parser.core import polyglot_parser


TEST_DATA_PATH = path.join(
    path.abspath(path.dirname(__file__)), 'test_data/parser')


# Helper functions used in tests
def _parse_json(path):
    with open(path, 'r') as file:
        return json.loads('\n'.join(file.readlines()))


def _create_fixtures(test_folder, add_main=False):
    test_file = f'{test_folder}_main.py' if add_main else f'{test_folder}.py'

    test_folder_path = path.join(TEST_DATA_PATH, test_folder)
    repo_json = path.join(test_folder_path, 'polyglot_snippet_data.json')
    source_path = path.join(test_folder_path, test_file)

    source_methods_json = _parse_json(repo_json)['snippets']
    source_methods = [pdd.PolyglotDriftData(**json_dict)
                      for json_dict in source_methods_json]

    source_region_tags = \
        polyglot_parser.get_region_tag_regions(source_path)[0]
    for idx, method in enumerate(source_methods):
        source_methods[idx] = \
            polyglot_parser.add_region_tags_to_method(
                method, source_region_tags
            )

    return source_methods


class PolyglotParserTests(unittest.TestCase):
    def test_ignores_ignored_method_names(self):
        source_methods = _create_fixtures('edge_cases')

        method = source_methods[0]

        # this should NOT contain 'main_method'
        self.assertEqual(method.region_tags, ['not_main'])

    def test_region_tags_nested(self):
        source_methods = _create_fixtures('nested_tags')

        method_1 = source_methods[0]
        method_2 = source_methods[1]

        method_1.region_tags.sort()

        self.assertEqual(
            method_1.region_tags, ['nested_tag', 'root_tag'])
        self.assertEqual(method_2.region_tags, ['root_tag'])

    def test_handle_multi_block_region_tags(self):
        source_methods = _create_fixtures('nested_tags')

        assert len(source_methods) == 3
        method_1 = source_methods[1]
        method_2 = source_methods[2]

        self.assertEqual(method_1.region_tags, ['root_tag'])
        self.assertEqual(method_2.region_tags, ['root_tag'])

    def test_flask_router_parser(self):
        source_methods = _create_fixtures('flask', True)

        source_methods = [method for method in source_methods if
                          method.parser == 'flask_router']

        method = source_methods[0]
        self.assertEqual(method.region_tags, ['sample_route'])

    def test_direct_invocation_parser(self):
        source_methods = _create_fixtures('http', True)

        method = source_methods[0]
        assert 'functions_helloworld_get' in method.region_tags

    def test_webapp2_parser(self):
        source_methods = _create_fixtures('webapp2', True)

        method = source_methods[-1]
        self.assertEqual(method.region_tags, ['sign_handler'])

    def test_ignores_exclude_tags(self):
        source_methods = _create_fixtures('exclude_tags', True)

        # make sure the file was parsed properly
        assert len(source_methods) == 2
