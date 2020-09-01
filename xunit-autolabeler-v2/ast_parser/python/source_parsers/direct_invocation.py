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


from ast_parser.lib.constants import IGNORED_METHOD_NAMES


def parse(nodes, class_name):
    methods = [x for x in nodes if
               '.FunctionDef' in str(type(x)) and hasattr(x, 'name')]
    methods = [x for x in methods if x.name not in IGNORED_METHOD_NAMES]

    # Avoid dupes - don't return already-labelled methods
    # (this function's result is concat-ed to other method lists!)
    methods = [x for x in methods if not hasattr(x, 'drift')]

    for m in methods:
        m.drift = {
            # (Directly invoked methods have
            #  no parser-specific properties)

            # Generic properties
            'name': m.name,
            'class_name': class_name,
            'method_name': m.name,
            'parser': 'direct_invocation',
            'start_line': m.lineno,
        }

    return methods
