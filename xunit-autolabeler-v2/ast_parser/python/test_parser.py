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
import sys
from typing import Any, Dict, List, Tuple

from ast_parser.core import constants as core_constants

from . import constants as python_constants
from . import drift_test


def _get_test_nodes(parsed_nodes: List[Any]) -> List[Any]:
    """Helper function to extract test methods wrapped in classes

    Args:
        parsed_nodes (List[ast.AST]): a list of nodes parsed
                                      from a Python test file

    Returns:
        List[ast.AST]: a list of possible test nodes
    """

    possible_test_nodes = []
    for node in parsed_nodes:
        possible_test_nodes.append(node)
        if 'ClassDef' in str(type(node)):
            # Concatenate node.body (which is an array)
            possible_test_nodes += node.body

    return [node for node in possible_test_nodes if hasattr(node, 'name') and
            python_constants.TEST_METHOD_REGEX.search(node.name)]


def get_test_methods(test_path: str) -> List[Any]:
    """Gets the top-level methods within a test file

    Args:
        source_path: path to the file to process

    Returns:
        List[ast.AST]: a list of the top-level
                       methods within the provided file
    """
    try:
        with open(test_path, 'r') as file:
            content = ''.join(file.readlines())
            parsed_nodes = list(ast.iter_child_nodes(ast.parse(content)))

            test_nodes = _get_test_nodes(parsed_nodes)

            for node in test_nodes:
                node.test_path = os.path.abspath(test_path)

            # Verify file contains no duplicate method names
            # (Only relevant for test methods wrapped in classes)
            used_test_names = set()
            for node in test_nodes:
                if node.name in used_test_names:
                    raise ValueError(
                        f'Test name {node.name} in file'
                        f' {test_path} must be unique.')
                used_test_names.add(node.name)

            return test_nodes
    except IOError as err:
        # Fail gracefully if a file can't be read
        # (This shouldn't happen, but if it doess
        #  we don't want to 'break the build'.)
        sys.stderr.write(
            f'WARNING: could not read file: {test_path}\n')
        sys.stderr.write(
            f'\t{str(err)}\n')

        return []


def get_test_key_to_snippet_map(
    test_methods: List[Any]
) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """Map the supplied test methods to their relevant 'test keys'

    Test keys are tuples that a) identify a particular snippet and b)
    can be matched with that snippet's tests. The attributes used in
    a test key differ based on which parser detected a given snippet.

    Args:
        test_methods (List[ast.AST]): a list of methods extracted
                                      from test files

    Returns: a mapping between test keys and their corresponding
             test data (file paths and method names)
    """
    test_to_method_key_map: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}

    def __recursor__(expr: Any) -> List[drift_test.DriftTest]:
        """Recursively find test keys within an expression

        Args:
            expr (ast.AST): the AST node to search for test keys within

        Returns: a list of test keys within the given expression
        """
        type_str = str(type(expr))
        is_func = hasattr(expr, 'func')

        if '.Attribute' in type_str and hasattr(expr.value, 'id'):
            # Direct method invocation
            return [drift_test.DriftTest(
                class_name=expr.value.id,
                method_name=expr.attr
            )]

        if is_func and hasattr(expr.func, 'value'):
            # HTTP-route invoked methods
            # (both flask and webapp2)
            func = expr.func

            if hasattr(func.value, 'id') and \
               func.value.id in core_constants.HTTP_CLASS_NAMES and \
               func.attr in core_constants.HTTP_METHOD_NAMES and \
               hasattr(expr.args[0], 's'):
                return [drift_test.DriftTest(
                    url=expr.args[0].s,
                    http_method=func.attr
                )]

        if hasattr(expr, 'value'):
            return __recursor__(expr.value)

        if is_func:
            return __recursor__(expr.func)

        if hasattr(expr, 'test') and hasattr(expr.test, 'comparators'):
            results = []
            results += __recursor__(expr.test.comparators[0])
            results += __recursor__(expr.test.left)
            return results

        results = []
        if hasattr(expr, 'finalbody'):
            # Used in try-catch-finally statements
            for subexpr in expr.finalbody:
                results += [subexpr for subexpr
                            in __recursor__(subexpr) if subexpr]

        if core_constants.BODY_IS_ARRAY_REGEX.search(type_str):
            for subexpr in expr.body:
                results += [subexpr for subexpr
                            in __recursor__(subexpr) if subexpr]

        return results  # may contain duplicates

    for method in test_methods:
        for subexpr in method.body:
            children_drift_data = [child_node for child_node
                                   in __recursor__(subexpr) if child_node]
            for child_drift_test in children_drift_data:
                child_key = child_drift_test.get_key_tuple()

                if child_key not in test_to_method_key_map:
                    test_to_method_key_map[child_key] = []
                test_to_method_key_map[child_key].append(
                    (method.test_path, method.name))

    return test_to_method_key_map
