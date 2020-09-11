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


import json


def make_drift_data_dict(
    name,
    class_name,
    parser,
    start_line,
    method_name=None,
    url=None,
    flask_http_methods=[],
    webapp2_http_method=None
):
    return {
        'name': name,
        'class_name': class_name,
        'method_name': method_name,
        'parser': parser,
        'start_line': start_line,
        'url': url,
        'flask_http_methods': flask_http_methods,
        'webapp2_http_method': webapp2_http_method
    }
