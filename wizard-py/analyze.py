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

from constants import TEST_FILE_MARKER, IGNORED_REGION_TAGS
import file_utils
import source_parser
import test_parser
import yaml_utils


def parse_source(source_path):
    source_methods = source_parser.get_top_level_methods(source_path)

    source_region_tags = source_parser.get_region_tag_regions(source_path)

    source_parser.add_region_tags_to_methods(
        source_methods, source_region_tags)

    return [x for x in source_methods if x.drift['region_tags']]


def parse_test(test_path, source_methods):
    test_methods = test_parser.get_test_methods(test_path)
    test_method_map = test_parser.get_test_to_method_map(test_methods)

    test_parser.add_method_names_to_tests(source_methods, test_method_map)


def analyze_dir(root_dir):
    python_files = file_utils.get_python_files(root_dir)

    source_methods = []
    source_files = [f for f in python_files if TEST_FILE_MARKER not in f]

    for f in source_files:
        source_methods += parse_source(f)

    test_files = [f for f in python_files if TEST_FILE_MARKER in f]

    for f in test_files:
        parse_test(f, source_methods)

    # Dedupe source methods
    source_method_keys = set()
    source_methods_deduped = []
    for m in source_methods:
        key = ','.join(m.drift['region_tags'])
        if key not in source_method_keys:
            source_methods_deduped.append(m)
            source_method_keys.add(key)

    source_methods = source_methods_deduped

    source_parser.add_children_drift_data(source_methods)

    yaml_utils.add_yaml_data_to_source_methods(source_methods, root_dir)

    grep_tags = file_utils.get_region_tags(root_dir)
    source_tags = []
    for m in source_methods:
        source_tags += [x for x in m.drift['region_tags']]

    source_tags = list(set(source_tags))

    ignored_tags = []
    ignored_tags += [x for x in grep_tags if x in IGNORED_REGION_TAGS]

    # Remove ignored (by *source*) region tags from region tag lists
    grep_tags = [x for x in grep_tags if x not in ignored_tags]
    source_tags = [x for x in source_tags if x not in ignored_tags]

    # Get ignored (by *test*) region tags from YAML files
    ignored_tags += yaml_utils.get_untested_region_tags(root_dir)

    return (grep_tags, source_tags, ignored_tags, source_methods)
