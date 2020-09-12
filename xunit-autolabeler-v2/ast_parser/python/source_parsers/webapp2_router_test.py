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
import pytest
import unittest


from . import webapp2_router, direct_invocation


class WebApp2RouterTests(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def init(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'test_data/webapp2_router_example.py'
        )
        with open(path, 'r') as file:
            content = file.read()
            nodes = ast.iter_child_nodes(ast.parse(content))
            nodes = [node for node in nodes]  # iterator -> list

            self.nodes = nodes
            self.methods = webapp2_router.parse(self.nodes)

            self.class_names = \
                [method.drift['class_name'] for method in self.methods]

    def test_detects_handlers_using_WSGIApplication_and_requestHandler(self):
        # This method should be the only detected one
        assert len(self.methods) == 1

        first_method = self.methods[0]
        assert hasattr(first_method, 'drift')

        drift = first_method.drift

        assert drift['url'] == '/'
        assert drift['webapp2_http_method'] == 'get'
        assert drift['name'] == 'get'

        assert drift['class_name'] == 'ValidRoute'
        assert drift['parser'] == 'webapp2_router'
        assert drift['start_line'] == 36

        # Make sure flask_http_methods wasn't accidentally set
        assert drift['flask_http_methods'] == []

    def test_ignores_WSGIApplication_nodes_without_webapp2(self):
        assert 'RouteWithoutProperSubclass' not in self.class_names

    def test_ignores_handlers_without_requesthandler_base_class(self):
        assert 'RouteWithoutWSGIApplicationReference' not in self.class_names

    def test_webapp2_router_errors_on_already_labelled_method(self):
        # Trick the direct invocation parser into detecting webapp2 routes
        method_nodes = [class_node.body[0] for class_node in self.nodes if
                        hasattr(class_node, 'body') and class_node.body]

        direct_invocation.parse(method_nodes, 'direct_invocation_example')

        # Propagate incorrect labels to parent classes
        # (Makes no sense in actual code, but easy way to generate test data)
        for class_node in self.nodes:
            if hasattr(class_node, 'body') and class_node.body and \
               hasattr(class_node.body[0], 'drift'):
                class_node.drift = class_node.body[0].drift

        with self.assertRaisesRegex(ValueError,
                                    'Already-labelled method found!'):
            webapp2_router.parse(self.nodes)
