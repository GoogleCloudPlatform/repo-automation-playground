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

from ast_parser.core import polyglot_parser


TEST_DATA_PATH = path.join(
    path.abspath(path.dirname(__file__)), 'test_data/parser')


class PolyglotParserTests(unittest.TestCase):
    def __parse_json(_, p):
        with open(p, 'r') as f:
            return json.loads('\n'.join(f.readlines()))

    def test_ignores_ignored_method_names(self):
        repo_json = path.join(TEST_DATA_PATH, 'edge_cases/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'edge_cases/edge_cases.py')

        source_methods = self.__parse_json(repo_json)

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)
        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        method = source_methods[0]

        # this should NOT contain 'main_method'
        self.assertEqual(method['region_tags'], ['not_main'])

    def test_region_tags_nested(self):
        repo_json = path.join(TEST_DATA_PATH, 'nested_tags/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'nested_tags/nested_tags.py')

        source_methods = self.__parse_json(repo_json)

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)
        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        method_1 = source_methods[0]
        method_2 = source_methods[1]

        method_1['region_tags'].sort()
        self.assertEqual(
            method_1['region_tags'], ['nested_tag', 'root_tag'])
        self.assertEqual(method_2['region_tags'], ['root_tag'])

    def test_handle_multi_block_region_tags(self):
        repo_json = path.join(TEST_DATA_PATH, 'nested_tags/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'nested_tags/nested_tags.py')

        source_methods = self.__parse_json(repo_json)

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)
        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        assert len(source_methods) == 3
        method_1 = source_methods[1]
        method_2 = source_methods[2]

        self.assertEqual(method_1['region_tags'], ['root_tag'])
        self.assertEqual(method_2['region_tags'], ['root_tag'])

    def test_flask_router_parser(self):
        repo_json = path.join(TEST_DATA_PATH, 'flask/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'flask/flask_main.py')

        source_methods = self.__parse_json(repo_json)
        source_methods = [x for x in source_methods if
                          x['parser'] == 'flask_router']

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)
        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        method = source_methods[0]
        self.assertEqual(method['region_tags'], ['sample_route'])

    def test_direct_invocation_parser(self):
        repo_json = path.join(TEST_DATA_PATH, 'http/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'http/http_main.py')

        source_methods = self.__parse_json(repo_json)
        source_methods = [x for x in source_methods if
                          x['parser'] == 'direct_invocation']

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)

        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        method = source_methods[0]
        assert 'functions_helloworld_get' in method['region_tags']

    def test_webapp2_parser(self):
        repo_json = path.join(TEST_DATA_PATH, 'webapp2/repo.json')
        source_path = path.join(TEST_DATA_PATH, 'webapp2/webapp2_main.py')

        source_methods = self.__parse_json(repo_json)
        source_methods = [x for x in source_methods if
                          x['parser'] == 'webapp2_router']

        (source_region_tags, _) = \
            polyglot_parser.get_region_tag_regions(source_path)
        polyglot_parser.add_region_tags_to_methods(
            source_methods, source_region_tags)

        method = source_methods[-1]
        self.assertEqual(method['region_tags'], ['sign_handler'])
