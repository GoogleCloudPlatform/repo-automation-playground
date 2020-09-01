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


def parse(nodes):
    wsgi_configs = [x for x in nodes if hasattr(x, 'value')]
    wsgi_configs = [x for x in wsgi_configs if hasattr(x.value, 'func')
                    and hasattr(x.value.func, 'attr')]
    wsgi_configs = [x for x in wsgi_configs if
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

    handlers = [x for x in nodes if hasattr(x, 'bases') and len(x.bases)]
    handlers = [x for x in handlers if hasattr(x.bases[0], 'attr')]
    handlers = [x for x in handlers if x.bases[0].attr == 'RequestHandler']
    handlers = [x for x in handlers if x.name in class_name_url_map]

    handler_methods = []
    for handler_class in handlers:
        temp_methods = [x for x in handler_class.body if hasattr(x, 'name')]
        for m in temp_methods:
            m.drift = {
                # webapp2-specific properties
                'url': class_name_url_map[handler_class.name],
                'http_method': m.name,

                # Generic properties
                'name': m.name,
                'class_name': handler_class.name,
                'parser': 'webapp2_router',
                'start_line': m.lineno
            }
        handler_methods += temp_methods

    return handler_methods
