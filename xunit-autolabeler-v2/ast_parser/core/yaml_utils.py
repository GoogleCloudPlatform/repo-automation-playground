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

import os
from typing import Dict, List, Tuple

from ast_parser.core import constants, polyglot_drift_data
from ast_parser.lib import file_utils

import yaml


def _handle_overwrites(
    source_methods_json: List[polyglot_drift_data.PolyglotDriftData],
    root_dir: str
) -> None:
    """Handle overwrites in .drift-data.yml files

    The "overwrite" clause is used to denote when a .drift-data.yml
    entry should overwrite any automatically-detected test methods.
    If an overwrite entry is present for a given region tag, this
    method clears all previously-detected tests for snippet methods
    containing that region tag.

    Args:
        source_methods_json: A list of language-agnostic snippet methods
        root_dir: A path to the directory source_methods_json was created from
    """
    yaml_paths = file_utils.get_drift_yaml_files(root_dir)

    overwritten_tags = set()

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]
                if 'overwrite' in yaml_entry:
                    if yaml_entry.get('overwrite', False) is True:
                        overwritten_tags.add(tag)

    for idx, method in enumerate(source_methods_json):
        if set(method.region_tags).intersection(overwritten_tags):
            # _replace() creates a *copy*
            # (named-tuples themselves are immutable)
            # so we must update the underlying array
            source_methods_json[idx] = \
                method._replace(test_methods=[])


def _handle_additions_clause(
    source_methods_json: List[polyglot_drift_data.PolyglotDriftData],
    root_dir: str
) -> None:
    """Handle additions clause in .drift-data.yml files

    The "additions" clause is used to specify lists of region tags
    that correspond to the same set of tests. If a given snippet
    method contains one of these region tags, it will be deemed to
    contain *all* of them!

    This is useful for multi-region-tag samples like the following:
     - my_sample_setup
     - my_sample_do_thing_1
     - my_sample_do_thing_2
     - my_sample_teardown

    Args:
        source_methods_json: A list of language-agnostic snippet methods
        root_dir: A path to the directory source_methods_json was created from
    """
    yaml_paths = file_utils.get_drift_yaml_files(root_dir)

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            additions_tags = [key for key in parsed_yaml.keys() if
                              key not in constants.RESERVED_YAML_KEYS]

            for tag in additions_tags:
                yaml_entry = parsed_yaml[tag]
                if 'additions' in yaml_entry and \
                   isinstance(yaml_entry['additions'], list):

                    added_tags = set(yaml_entry['additions'])
                    added_tags.add(tag)

                    for idx, method in enumerate(source_methods_json):
                        method_tags = set(method.region_tags)

                        if added_tags.intersection(method_tags):
                            new_method_tags = list(
                                set(method.region_tags)
                                .union(added_tags)
                            )
                            # _replace() creates a *copy*
                            # (named-tuples themselves are immutable)
                            # so we must update the underlying array
                            source_methods_json[idx] = \
                                method._replace(
                                    region_tags=new_method_tags)


def _handle_manually_specified_tests(
    source_methods_json: List[polyglot_drift_data.PolyglotDriftData],
    root_dir: str
) -> None:
    """Handle manually specified tests in .drift-data.yml files

    This method allows users to manually specify which tests (file
    paths and method names) correspond to a given region tag. This
    is useful in two cases:
     - automatic detection doesn't detect a snippet <-> test mapping
     - automatic detection detects an incorrect mapping

    In the latter case, use the 'overwrite' attribute to ignore
    auto-detected mappings in favor of manually specified ones.

    Args:
        source_methods_json: A list of language-agnostic snippet methods
        root_dir: A path to the directory source_methods_json was created from
    """

    def _no_banned_subkeys(yaml_entry: Dict, banned_keys: set):
        """Determine whether a given yaml entry has "banned" keys

        (Banned keys cannot exist in a manually-specified test entry.)
        """
        return not set(yaml_entry.keys()).intersection(banned_keys)

    yaml_paths = file_utils.get_drift_yaml_files(root_dir)

    test_tag_map: Dict[str, List[Tuple[str, str]]] = {}

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_dir = os.path.dirname(path)
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            # Manually specified tests cannot contain any keys in
            # RESERVED_YAML_KEYS (except for "overwrite"), so filter
            # out any yaml entries that *do* have these keys
            banned_keys = set(constants.RESERVED_YAML_KEYS)
            banned_keys.remove('overwrite')

            manual_tags = [tag for tag in parsed_yaml.keys() if
                           _no_banned_subkeys(parsed_yaml[tag], banned_keys)]

            for tag in manual_tags:
                yaml_entry = parsed_yaml[tag]
                test_tag_map[tag] = []

                for test_rel_path in yaml_entry.keys():
                    test_path = os.path.join(yaml_dir, test_rel_path)
                    if test_path and os.path.exists(test_path):
                        for test_name in yaml_entry[test_rel_path]:
                            test_tag_map[tag].append((test_path, test_name))

    for method in source_methods_json:
        for tag in method.region_tags:
            if tag in test_tag_map and test_tag_map[tag]:
                method.test_methods.append(test_tag_map[tag])


def add_yaml_data_to_source_methods(
    source_methods_json: List[Dict],
    root_dir: str
) -> None:
    """Coordination method that handles major .drift-data.yml clauses

    Args:
        source_methods_json: A list of language-agnostic snippet methods
        root_dir: A path to the directory source_methods_json was created from
    """
    _handle_overwrites(source_methods_json, root_dir)
    _handle_manually_specified_tests(source_methods_json, root_dir)
    _handle_additions_clause(source_methods_json, root_dir)


def get_untested_region_tags(root_dir: str) -> List[str]:
    """Get the 'untested' region tags for a given directory

    In this method, 'untested' region tags are those *explicitly marked*
    as untested in .drift-data.yml. (In other words, these are *not* region
    tags for which a test exists, but could not be found by automatically.)

    Args:
        root_dir: A directory containing snippets and .drift-data.yml files
    """
    yaml_paths = file_utils.get_drift_yaml_files(root_dir)
    all_untested_tags = []

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            local_untested_tags = [key for key in parsed_yaml.keys()
                                   if parsed_yaml[key].get('tested') is False]
            all_untested_tags += local_untested_tags

    return list(set(all_untested_tags))
