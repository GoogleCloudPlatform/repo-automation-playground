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


from ast_parser.python.drift_data_dict import make_drift_data_dict


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

    wsgi_configs = [x for x in nodes if
                    hasattr(x, 'value') and
                    hasattr(x.value, 'func') and
                    hasattr(x.value.func, 'attr') and
                    x.value.func.attr == 'WSGIApplication']

    class_name_url_map = {}
    for m in wsgi_configs:
        m.drift = {}
        arg = m.value.args[0]

        elts_args = [x for x in arg.elts if hasattr(x, 'elts')]
        for elem in elts_args:
            url = elem.elts[0].s
            handler_class = elem.elts[1].id

            class_name_url_map[handler_class] = url

    handlers = [x for x in nodes if
                hasattr(x, 'bases') and len(x.bases) and
                hasattr(x.bases[0], 'attr') and
                x.bases[0].attr == 'RequestHandler' and
                x.name in class_name_url_map]

    handler_methods = []
    for handler_class in handlers:
        temp_methods = [x for x in handler_class.body if hasattr(x, 'name')]
        for m in temp_methods:
            m.drift = make_drift_data_dict(
                m.name,
                handler_class.name,
                'webapp2_router',
                m.lineno,
                webapp2_http_method=m.name,
                url=class_name_url_map[handler_class.name]
            )

        handler_methods += temp_methods

    return handler_methods
