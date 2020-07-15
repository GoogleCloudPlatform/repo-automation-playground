import constants


def parse(nodes, class_name):
    routes = [x for x in nodes if hasattr(x, 'decorator_list')]
    routes = [x for x in routes if x.decorator_list]
    routes = [x for x in routes if hasattr(x.decorator_list[0], 'func')]
    routes = [x for x in routes if hasattr(x.decorator_list[0].func, 'attr')]
    routes = [x for x in routes if x.decorator_list[0].func.attr == 'route']
    routes = [x for x in routes if x.decorator_list[0].args]

    for method in routes:
        m_dec = method.decorator_list[0]
        m_args = m_dec.args
        url = m_args[0].s

        http_methods = constants.FLASK_DEFAULT_METHODS
        if m_dec.keywords and m_dec.keywords[0].arg == 'methods':
            http_methods = [x.s.lower() for x in m_dec.keywords[0].value.elts]

        if not hasattr(method, 'drift'):
            method.drift = {
                'name': method.name,
                'parser': 'flask_router',
                'url': url,
                'class_name': class_name,
                'method_name': method.name,
                'http_methods': http_methods
            }
        else:
            # Possible cause: method was labelled by another source parser
            raise ValueError('Already-labelled method found!')

    return [x for x in routes if hasattr(x, 'drift')]
