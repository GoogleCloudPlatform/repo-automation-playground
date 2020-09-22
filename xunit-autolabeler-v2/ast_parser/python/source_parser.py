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

from .source_parsers import direct_invocation, webapp2_router, flask_router
from typing import Any, List


def _get_method_children(expr: Any) -> List[Any]:
    results = []

    if hasattr(expr, 'id'):
        results.append(expr.id)  # Base case

    if hasattr(expr, 'body') and isinstance(expr.body, list):
        for sub_expr in expr.body:
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
    m_end_stmt = expr
    highest_line_no = -1
    not_at_end = True
    while not_at_end:
        if hasattr(m_end_stmt, 'lineno'):
            highest_line_no = m_end_stmt.lineno

        if hasattr(m_end_stmt, 'body'):
            m_end_stmt = m_end_stmt.body[-1]
        elif hasattr(m_end_stmt, 'exc'):
            m_end_stmt = m_end_stmt.exc
        elif hasattr(m_end_stmt, 'args'):
            m_end_stmt = m_end_stmt.args[-1]
        elif hasattr(m_end_stmt, 'elts'):
            m_end_stmt = m_end_stmt.elts[-1]
        elif hasattr(m_end_stmt, 'generators'):
            m_end_stmt = m_end_stmt.generators[-1]
        elif hasattr(m_end_stmt, 'iter'):
            m_end_stmt = m_end_stmt.iter
        elif hasattr(m_end_stmt, 'values'):
            m_end_stmt = m_end_stmt.values[-1]
        elif hasattr(m_end_stmt, 'value'):
            # some (but not all) value attributes have
            # child elements - we handle both kinds here
            m_end_stmt = m_end_stmt.value
        else:
            not_at_end = False

    return highest_line_no


def get_top_level_methods(source_path: str) -> List[Any]:
    with open(source_path, 'r') as f:
        content = "".join(f.readlines())
        nodes = ast.iter_child_nodes(ast.parse(content))
        nodes = [x for x in nodes]

        class_name = os.path.splitext(os.path.basename(source_path))[0]

        methods = []

        methods += webapp2_router.parse(nodes)
        methods += flask_router.parse(nodes, class_name)

        # run direct_invocation parser after flask_router to avoid duplicates
        methods += direct_invocation.parse(nodes, class_name)

        for method in methods:
            method.drift = method.drift._replace(
                source_path=os.path.abspath(source_path),
                children=_get_method_children(method),
                end_line=_get_ending_line(method)
            )

        return methods
