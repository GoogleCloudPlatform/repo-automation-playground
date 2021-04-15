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


import ast
import os
import sys
from typing import Any, List

from .source_parsers import direct_invocation, flask_router, webapp2_router


def _get_method_children(expr: Any) -> List[Any]:
    """Recursively get potential "child" snippets of a snippet method

    This method recursively retrieves a list of expressions within
    a method that may represent calls to other snippets. This is
    necessary because tests that cover the parent snippet should
    also be considered to (recursively) cover any snippets called
    by the parent snippet itself.

    Args:
        expr (ast.AST): a Python expression object

    Returns:
        List[ast.AST]: a list of potential child snippet methods

    """
    results = []

    if hasattr(expr, 'id'):
        results.append(expr.id)  # Base case

    if hasattr(expr, 'body') and isinstance(expr.body, list):
        for sub_expr in expr.body:
            results += _get_method_children(sub_expr)

    if hasattr(expr, 'orelse') and isinstance(expr.orelse, list):
        for sub_expr in expr.orelse:
            results += _get_method_children(sub_expr)

    if hasattr(expr, 'value'):
        results += _get_method_children(expr.value)

    if hasattr(expr, 'func'):
        func_list = expr.func
        if not isinstance(func_list, list):
            # Not all func values are lists!
            func_list = [func_list]

        for func in func_list:
            results += _get_method_children(func)
            if hasattr(func, 'args'):
                for arg in func.args:
                    results += _get_method_children(arg)

    return results


def _get_ending_line(expr: Any) -> int:
    """Get the ending line number of a Python expression

    This method gets the final line number of a
    (possibly-multiline) Python expression.

    Args:
        expr (ast.AST): a Python expression object

    Returns:
        int: the line number on which the given expression ends
    """
    final_stmt = expr
    highest_line_no = -1
    not_at_end = True
    while not_at_end:
        if hasattr(final_stmt, 'lineno'):
            highest_line_no = final_stmt.lineno

        body_is_valid = hasattr(final_stmt, 'body') and final_stmt.body
        if hasattr(final_stmt, 'orelse') and final_stmt.orelse:
            # 'orelse' should take priority over 'body'
            # (as it always has a lower ending line)
            final_stmt = final_stmt.orelse
            if isinstance(final_stmt, list):
                # .orelse may or may not be a list
                final_stmt = final_stmt[-1]
        elif body_is_valid and isinstance(final_stmt.body, list):
            final_stmt = final_stmt.body[-1]
        elif body_is_valid:
            final_stmt = final_stmt.body
        elif hasattr(final_stmt, 'exc'):
            final_stmt = final_stmt.exc
        elif hasattr(final_stmt, 'args') and final_stmt.args:
            final_stmt = final_stmt.args[-1]
        elif hasattr(final_stmt, 'elts') and final_stmt.elts:
            final_stmt = final_stmt.elts[-1]
        elif hasattr(final_stmt, 'generators') and final_stmt.generators:
            final_stmt = final_stmt.generators[-1]
        elif hasattr(final_stmt, 'iter'):
            final_stmt = final_stmt.iter
        elif hasattr(final_stmt, 'values') and final_stmt.values:
            final_stmt = final_stmt.values[-1]
        elif hasattr(final_stmt, 'value'):
            # some (but not all) value attributes have
            # child elements - we handle both kinds here
            final_stmt = final_stmt.value
        else:
            not_at_end = False

    return highest_line_no


def get_top_level_methods(source_path: str) -> List[Any]:
    """Gets the top-level methods within a file

    Args:
        source_path: path to the file to process

    Returns:
        List[ast.AST]: a list of the top-level
                       methods within the provided file
    """
    try:
        with open(source_path, 'r') as f:
            content = ''.join(f.readlines())
            nodes = list(ast.iter_child_nodes(ast.parse(content)))

            # Webapp2 is the only parser that detects class names explicitly
            # Other parsers use the module name (filename minus ".py" suffix)
            module_name = os.path.splitext(
                os.path.basename(source_path))[0]

            methods = []

            methods += webapp2_router.parse(nodes)
            methods += flask_router.parse(nodes, module_name)

            # run direct_invocation parser after flask_router to avoid dupes
            methods += direct_invocation.parse(nodes, module_name)

            for method in methods:
                method.drift.source_path = os.path.abspath(source_path)
                method.drift.children = _get_method_children(method)
                method.drift.end_line = _get_ending_line(method)

            return methods
    except IOError as err:
        # Fail gracefully if a file can't be read
        # (This shouldn't happen, but if it doess
        #  we don't want to "break the build".)
        sys.stderr.write(
            f'WARNING: could not read file: {source_path}\n')
        sys.stderr.write(
            f'\t{str(err)}\n')

        return []
    except SyntaxError as err:
        # Fail gracefully if a file doesn't use py3-compliant syntax.
        sys.stderr.write(
            f'WARNING: could not parse file: {source_path}\n')
        sys.stderr.write(
            f'\t{str(err)}\n')

        return []
