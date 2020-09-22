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


from typing import NamedTuple, Optional


class DriftTest(NamedTuple):
    """Snippet test key struct

    Struct for storing properties that uniquely
    identify a snippet test within a specific file.
    Typically, these take one of two formats:
     - (class_name, method_name)
     - (http_method, url)
    """
    method_name: Optional[str] = None
    class_name: Optional[str] = None
    url: Optional[str] = None
    http_method: Optional[str] = None

    def get_key_tuple(self):
        return (
            self.http_method or self.class_name,
            self.url or self.method_name
        )
