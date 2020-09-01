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


from ast_parser.python.constants import FLASK_DEFAULT_METHODS


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

        http_methods = FLASK_DEFAULT_METHODS
        if m_dec.keywords and m_dec.keywords[0].arg == 'methods':
            http_methods = [x.s.lower() for x in m_dec.keywords[0].value.elts]

        if not hasattr(method, 'drift'):
            method.drift = {
                # Flask-specific properties
                'url': url,
                'method_name': method.name,
                'http_methods': http_methods,

                # Generic properties
                'parser': 'flask_router',
                'name': method.name,
                'class_name': class_name,
                'start_line': method.lineno,
            }
        else:
            # Possible cause: method was labelled by another source parser
            raise ValueError('Already-labelled method found!')

    return [x for x in routes if hasattr(x, 'drift')]
