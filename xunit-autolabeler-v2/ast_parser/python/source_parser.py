import ast
import os

from .source_parsers import direct_invocation, webapp2_router, flask_router


def get_top_level_methods(source_path):
    def __get_method_children(expr):
        results = []

        if hasattr(expr, 'id'):
            results.append(expr.id)  # Base case

        if hasattr(expr, 'body') and isinstance(expr.body, list):
            for sub_expr in expr.body:
                results += __get_method_children(sub_expr)

        if hasattr(expr, 'value'):
            results += __get_method_children(expr.value)

        if hasattr(expr, 'func'):
            results += __get_method_children(expr.func)
            for a in expr.args:
                results += __get_method_children(a)

        return results

    def __get_ending_line(expr):
        m_end_stmt = expr
        not_at_end = True
        while not_at_end:
            if hasattr(m_end_stmt, 'body'):
                m_end_stmt = m_end_stmt.body[-1]
            elif hasattr(m_end_stmt, 'exc'):
                m_end_stmt = m_end_stmt.exc
            elif hasattr(m_end_stmt, 'args'):
                m_end_stmt = m_end_stmt.args[-1]
            else:
                not_at_end = False

        return m_end_stmt.lineno

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
            method.drift['source_path'] = os.path.abspath(source_path)
            method.drift['children'] = __get_method_children(method)
            method.drift['end_line'] = __get_ending_line(method)

            # Initialize array values
            method.drift['test_methods'] = []

        return methods
