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


from typing import Any, Dict, List


from ast_parser.python import drift_data_tuple


def _is_wsgi_config(node: Any) -> bool:
    if not hasattr(node, 'value'):
        return False

    if not hasattr(node.value, 'func'):
        return False

    if not hasattr(node.value.func, 'attr'):
        return False

    if not node.value.func.attr == 'WSGIApplication':
        return False

    if not hasattr(node.value, 'args'):
        return False

    if not len(node.value.args):
        return False

    return True


def _is_webapp2_handler(
    node: Any, class_name_url_map: Dict[str, str]
) -> bool:
    if not hasattr(node, 'bases'):
        return False

    if not len(node.bases):
        return False

    if not hasattr(node.bases[0], 'attr'):
        return False

    if not node.bases[0].attr == 'RequestHandler':
        return False

    if node.name not in class_name_url_map:
        return False

    return True


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

    wsgi_configs = [node for node in nodes if _is_wsgi_config(node)]

    class_name_url_map = {}
    for method in wsgi_configs:
        method.drift = {}
        arg = method.value.args[0]

        elts_args = [elem for elem in arg.elts
                     if hasattr(elem, 'elts')
                     and len(elem.elts) >= 2]
        for elem in elts_args:
            url = elem.elts[0].s
            handler_class = elem.elts[1].id

            class_name_url_map[handler_class] = url

    handlers = [node for node in nodes if
                _is_webapp2_handler(node, class_name_url_map)]

    handler_methods = []
    for handler_class in handlers:
        temp_methods = [node for node in handler_class.body
                        if hasattr(node, 'name')]
        for method in temp_methods:
            if not hasattr(method, 'drift'):
                method.drift = drift_data_tuple.DriftData(
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
