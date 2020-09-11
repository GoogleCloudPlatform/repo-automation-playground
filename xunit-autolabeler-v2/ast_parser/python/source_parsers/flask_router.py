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


from ast_parser.python.constants import FLASK_DEFAULT_METHODS
from ast_parser.python.drift_data_object import DriftDataObject


def parse(nodes: List[Any], class_name: str) -> List[Any]:
    """Identify Flask route-handling snippets in Python
       files and extract their language-agnostic data
    Args:
        nodes: A list of AST nodes obtained via the 'ast' package
        class_name: the class name of the Python file being parsed
    Returns:
        A list of snippet routes (as AST nodes) with added
        language-agnostic data (in the 'drift' attribute)
    """

    routes = [x for x in nodes if
              hasattr(x, 'decorator_list') and
              x.decorator_list and
              hasattr(x.decorator_list[0], 'func') and
              hasattr(x.decorator_list[0].func, 'attr') and
              x.decorator_list[0].func.attr == 'route' and
              x.decorator_list[0].args]

    for method in routes:
        m_dec = method.decorator_list[0]
        m_args = m_dec.args
        url = m_args[0].s

        http_methods = list(FLASK_DEFAULT_METHODS)
        if m_dec.keywords and m_dec.keywords[0].arg == 'methods':
            http_methods = [x.s.lower() for x in m_dec.keywords[0].value.elts]

        if not hasattr(method, 'drift'):
            method.drift = DriftDataObject(
                method.name,
                class_name,
                'flask_router',
                method.lineno,
                method.name,
                url,
                flask_http_methods=http_methods
            )
        else:
            # Possible cause: method was labelled by another source parser
            raise ValueError('Already-labelled method found!')

    return [x for x in routes if hasattr(x, 'drift')]
