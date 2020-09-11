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


class DriftDataObject:
    def __init__(
        self,
        name,
        class_name,
        parser,
        start_line,
        method_name=None,
        url=None,
        flask_http_methods=[],
        webapp2_http_method=None
    ):
        self.name = name
        self.class_name = class_name
        self.method_name = method_name
        self.parser = parser
        self.start_line = start_line
        self.url = url
        self.flask_http_methods = flask_http_methods
        self.webapp2_http_method = webapp2_http_method

    def __str__(self):
        # Convert object to JSON
        return json.dumps(self.__dict__)

    # __str__ overloads that the core library uses
    # see https://stackoverflow.com/questions/4912852/
    def __unicode__(self):
        return self.__str__(self)

    def __repr(self):
        return self.__str__(self)
