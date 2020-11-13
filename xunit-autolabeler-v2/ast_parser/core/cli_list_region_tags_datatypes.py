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

from typing import Any, Dict, List

from recordclass import RecordClass


"""
These structs loosely follow the Protocol Buffers pattern of separate request
and response objects for each method. Unlike Protocol Buffers however, the
objects in this file are designed to be used by CLI-invoked methods - not
HTTP/gRPC-based ones.
"""


class ListRegionTagsInvocation(RecordClass):
    """Struct for storing command-line invocation data for list_region_tags()
    calls

    This object stores a user-provided CLI invocation request to
    list_region_tags.
    """

    # A path to a polyglot_drift_data.json file for the specified root
    # directory.
    data_json: str

    # A path to the target root directory.
    root_dir: str

    # Whether to show region tags that *were* detected by the AST parser.
    show_detected: bool

    # Whether to show region tags *not* detected by the AST parser.
    show_undetected: bool

    # Whether to show test counts for each AST-parser-detected region tag.
    show_test_counts: bool

    # Whether to show source filenames for each AST-parser-detected region tag.
    show_filenames: bool


class ListRegionTagsResult(RecordClass):
    """Struct for storing output data for list_region_tags() calls

    This object stores the processed results of a list_region_tags() call.
    """

    # Serialized entries from polyglot_snippet_data.json files.
    source_methods: List[Any]

    # A list of region tags detected by a language-specific AST parser.
    source_tags: List[str]

    # A list of region tags present in source files that were *not* detected by
    # language-specific AST parsers.
    undetected_tags: List[str]

    # A list of region tags that were explicitly ignored either by parser
    # configuration, or by .drift-data.yml files.
    ignored_tags: List[str]

    # A map of region tags to human-readable strings displaying the number of
    # tests associated with the given region tag.
    test_count_map: Dict[str, str]
