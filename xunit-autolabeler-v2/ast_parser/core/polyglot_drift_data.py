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

from typing import List, Tuple

from recordclass import RecordClass


class PolyglotDriftData(RecordClass):
    """Struct for storing snippet metadata

    This object stores language-agnostic ("polyglot")
    snippet data extracted from snippet source files
    for use by the second-stage "polyglot" parser.
    """
    name: str
    class_name: str
    method_name: str
    source_path: str
    start_line: int
    end_line: int
    parser: str
    region_tags: List[str] = []
    test_methods: List[Tuple[str, str]] = []
    children: List[str] = []
    url: str = None
    http_methods: List[str] = []
