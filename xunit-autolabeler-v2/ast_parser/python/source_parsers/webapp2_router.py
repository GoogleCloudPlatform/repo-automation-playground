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


from typing import Any, List


from ast_parser.python.drift_data_dict import make_drift_data_dict


def parse(nodes: List[Any]) -> List[Any]:
    """Identify webapp2 route-handling snippets in Python
       files and extract their language-agnostic data
    Args:
        nodes: A list of AST nodes obtained via the 'ast' package
        class_name: the class name of the Python file being parsed
    Returns:
        A list of webapp2-handling methods (as AST nodes) with
        added language-agnostic data (in the 'drift' attribute)
    """

    wsgi_configs = [node for node in nodes if
                    hasattr(node, 'value') and
                    hasattr(node.value, 'func') and
                    hasattr(node.value.func, 'attr') and
                    node.value.func.attr == 'WSGIApplication']

    class_name_url_map = {}
    for method in wsgi_configs:
        method.drift = {}
        arg = method.value.args[0]

        elts_args = [elem for elem in arg.elts if hasattr(elem, 'elts')]
        for elem in elts_args:
            url = elem.elts[0].s
            handler_class = elem.elts[1].id

            class_name_url_map[handler_class] = url

    handlers = [node for node in nodes if
                hasattr(node, 'bases') and len(node.bases) and
                hasattr(node.bases[0], 'attr') and
                node.bases[0].attr == 'RequestHandler' and
                node.name in class_name_url_map]

    handler_methods = []
    for handler_class in handlers:
        temp_methods = [node for node in handler_class.body
                        if hasattr(node, 'name')]
        for method in temp_methods:
            if not hasattr(method, 'drift'):
                method.drift = make_drift_data_dict(
                    method.name,
                    handler_class.name,
                    'webapp2_router',
                    method.lineno,
                    webapp2_http_method=method.name,
                    url=class_name_url_map[handler_class.name]
                )
            else:
                # webapp2 methods can match other parsers' method definitions
                #
                # This webapp2-specific parser is supposed to take priority
                # over more generic parsers, and label such methods first.
                #
                # If those methods have already been labelled, this constraint
                # has been violated and we raise an error.
                raise ValueError('Already-labelled method found!')

        handler_methods += temp_methods

    return handler_methods
