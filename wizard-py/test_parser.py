import ast
import constants


def get_test_methods(test_path):
    with open(test_path, 'r') as f:
        content = "".join(f.readlines())
        test_nodes = ast.iter_child_nodes(ast.parse(content))
        test_nodes = [x for x in test_nodes if hasattr(x, 'name')]
        test_nodes = [x for x in test_nodes if x.name.startswith('test_')]

        for n in test_nodes:
            n.test_path = test_path

        return test_nodes


def get_test_to_method_map(test_methods):
    test_method_map = {}

    def __recursor__(expr):
        type_str = str(type(expr))
        is_func = hasattr(expr, 'func')

        if '.Attribute' in type_str and hasattr(expr.value, 'id'):
            # Direct method invocation
            return [{
                'class_name': expr.value.id,
                'method_name': expr.attr
            }]

        if is_func and hasattr(expr.func, 'value'):
            # HTTP-route invoked methods
            # (both flask and webapp2)
            func = expr.func

            if hasattr(func.value, 'id') and \
               func.value.id in constants.HTTP_CLASS_NAMES and \
               func.attr in constants.HTTP_METHOD_NAMES and \
               hasattr(expr.args[0], 's'):
                return [{
                    'url': expr.args[0].s,
                    'http_method': func.attr
                }]

        if hasattr(expr, 'value'):
            return __recursor__(expr.value)

        if is_func:
            return __recursor__(expr.func)

        if hasattr(expr, 'test') and hasattr(expr.test, 'comparators'):
            results = []
            results += __recursor__(expr.test.comparators[0])
            results += __recursor__(expr.test.left)
            return results

        if '.With' in type_str or '.For' in type_str:
            results = []
            for x in expr.body:
                results += [x for x in __recursor__(x) if x]

            return results  # may contain duplicates

        return []

    for method in test_methods:
        for x in method.body:
            rList = [r for r in __recursor__(x) if r]
            for r in rList:
                rKey = (
                    r.get('http_method', r.get('class_name')),
                    r.get('url', r.get('method_name'))
                )
                if rKey not in test_method_map:
                    test_method_map[rKey] = []
                test_method_map[rKey].append(
                    (method.test_path, method.name))

    return test_method_map


def add_method_names_to_tests(source_methods, test_method_map):
    for m in source_methods:
        d = m.drift
        if 'test_methods' not in m.drift:
            m.drift['test_methods'] = []

        keys = []
        if d['parser'] == 'direct_invocation':
            keys = [(d.get('class_name'), d.get('method_name'))]
        elif d['parser'] == 'webapp2_router':
            keys = [(d.get('http_method'), d.get('url'))]
        elif d['parser'] == 'flask_router':
            keys = [(x, d.get('url')) for x in d['http_methods']]

        for key in keys:
            if key in test_method_map:
                if test_method_map[key]:
                    m.drift['test_methods'] += test_method_map[key]
