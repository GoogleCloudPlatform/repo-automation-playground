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


from ast_parser.python import constants, drift_data_tuple


def _is_flask_route(node: Any) -> bool:
    if not hasattr(node, 'decorator_list'):
        return False

    if not node.decorator_list:
        return False

    if not hasattr(node.decorator_list[0], 'func'):
        return False

    if not hasattr(node.decorator_list[0].func, 'attr'):
        return False

    if not node.decorator_list[0].func.attr == 'route':
        return False

    if not node.decorator_list[0].args:
        return False

    return True


def parse(
    nodes: List[Any],
    class_name: str
) -> List[Any]:
    """Identify Flask route-handling snippets in Python
       files and extract their language-agnostic data
    Args:
        nodes: A list of AST nodes obtained via the 'ast' package
        class_name: the class name of the Python file being parsed
    Returns:
        A list of snippet routes (as AST nodes) with added
        language-agnostic data (in the 'drift' attribute)
    """

    routes = [node for node in nodes if _is_flask_route(node)]

    for method in routes:
        m_dec = method.decorator_list[0]
        m_args = m_dec.args
        url = m_args[0].s

        http_methods = list(constants.FLASK_DEFAULT_METHODS)
        if m_dec.keywords and m_dec.keywords[0].arg == 'methods':
            http_methods = [elem.s.lower() for elem
                            in m_dec.keywords[0].value.elts]

        if not hasattr(method, 'drift'):
            method.drift = drift_data_tuple.DriftData(
                method.name,
                class_name,
                'flask_router',
                method.lineno,
                method.name,
                url,
                http_methods=http_methods
            )
        else:
            # Flask methods can match other parsers' method definitions
            #
            # This Flask-specific parser is supposed to take priority
            # over more generic parsers, and label such methods first.
            #
            # If those methods have already been labelled, this constraint
            # has been violated and we raise an error.
            raise ValueError('Already-labelled method found!')

    return [route for route in routes
            if hasattr(route, 'drift')]
