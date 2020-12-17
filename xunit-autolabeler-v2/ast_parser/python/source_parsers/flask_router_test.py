# Copyright 2020 Google LLC. All Rights Reserved.
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


import ast
import os
import unittest

import pytest

from . import flask_router


def _create_fixture(example_path):
    def init(self):
        path = os.path.join(
            os.path.dirname(__file__),
            example_path
        )
        with open(path, 'r') as file:
            content = file.read()
            nodes = ast.iter_child_nodes(ast.parse(content))
            nodes = [node for node in nodes]  # iterator -> list

            self.nodes = nodes

            # Pre-compute common assertion targets
            self.methods = flask_router.parse(
                self.nodes, 'test_flask_class')
            self.method_names = \
                [method.drift.name for method in self.methods]

    return init


class DecoratorTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init(self):
        _create_fixture('test_data/flask_router_example.py')(self)

    def test_ignores_undecorated_methods(self):
        assert 'route_no_decorator' not in self.method_names

    def test_ignores_methods_with_unknown_decorators(self):
        assert 'route_unknown_decorator' not in self.method_names

    def test_ignores_route_decorator_without_args(self):
        assert 'route_no_args' not in self.method_names

    def test_parses_route_decorator_with_args(self):
        # This method should be the only detected one
        assert len(self.methods) == 1
        first_method = self.methods[0]

        assert hasattr(first_method, 'drift')

        drift = first_method.drift

        assert drift.method_name == 'valid_route'
        assert drift.name == 'valid_route'
        assert drift.url == '/valid'

        assert drift.parser == 'flask_router'
        assert drift.class_name == 'test_flask_class'

        # This differs between py3.8 and py3.9
        # The difference doesn't affect parser logic,
        # so we allow both possible results.
        #
        # Likely caused by
        # https://bugs.python.org/issue34822
        assert drift.start_line in [47, 48]

        # Don't check http_methods here
        # (covered in HttpMethodTests)


class HttpMethodTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init(self):
        _create_fixture('test_data/flask_http_methods_example.py')(self)

    def test_detects_all_routes(self):
        assert len(self.methods) == 2

    def test_has_default_http_methods(self):
        first_method = self.methods[0]

        assert hasattr(first_method, 'drift')

        drift = first_method.drift
        assert drift.name == 'default_methods'

        # method list is a hard-coded copy of:
        #   ast_parser.python.constants.FLASK_DEFAULT_METHODS
        assert drift.http_methods == ['get']

    def test_detects_provided_http_methods(self):
        second_method = self.methods[-1]

        assert hasattr(second_method, 'drift')

        drift = second_method.drift
        assert drift.name == 'put_or_patch'
        assert drift.http_methods == ['put', 'patch']


class MiscTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init(self):
        _create_fixture('test_data/flask_http_methods_example.py')(self)

    def test_flask_router_errors_on_already_labelled_method(self):
        with self.assertRaisesRegex(ValueError,
                                    'Already-labelled method found!'):
            flask_router.parse(self.methods, 'direct_invocation_example')
