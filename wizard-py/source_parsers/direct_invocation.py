from constants import IGNORED_METHOD_NAMES


def parse(nodes, class_name):
    methods = [x for x in nodes if
               '.FunctionDef' in str(type(x)) and hasattr(x, 'name')]
    methods = [x for x in methods if x.name not in IGNORED_METHOD_NAMES]

    # Avoid dupes - don't return already-labelled methods
    # (this function's result is concat-ed to other method lists!)
    methods = [x for x in methods if not hasattr(x, 'drift')]

    for m in methods:
        m.drift = {
            'parser': 'direct_invocation',
            'method_name': m.name,
            'name': m.name,
            'class_name': class_name
        }

    return methods
