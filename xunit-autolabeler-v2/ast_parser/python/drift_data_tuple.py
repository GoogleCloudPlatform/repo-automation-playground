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


import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class DriftData:
    """Struct for storing snippet metadata

    This object stores snippet data extracted from
    snippet source files. Once all Python files have
    been parsed, this object can be serialized into
    JSON for use by the second-stage "language agnostic"
    parser.
    """

    # Properties set by individual source parsers
    name: str
    class_name: str
    parser: str
    start_line: int
    method_name: Optional[str] = None
    url: Optional[str] = None
    http_methods: List[str] = None

    # Properties set by source_parser.py
    source_path: Optional[str] = None
    end_line: Optional[int] = None
    children: List[str] = None
