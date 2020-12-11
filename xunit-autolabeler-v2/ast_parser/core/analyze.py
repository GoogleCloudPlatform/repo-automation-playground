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

import json
import os
from os import path
from typing import Dict, List, Set, Tuple

from ast_parser.lib import constants as lib_constants

from . import constants
from . import polyglot_drift_data as pdd
from . import polyglot_parser, yaml_utils


def _get_data(
    snippet_data_json: str
) -> Tuple[List[pdd.PolyglotDriftData], Dict[str, List[str]]]:
    """Retrieves a list of snippet methods from a JSON repo file
       (usually named polyglot_snippet_data.json)

    Args:
        snippet_data_json: The path to a polyglot_snippet_data.json file

    Returns:
        A 2-tuple containing the following information retrieved from the
        specified JSON file:
         - A list of snippet methods
         - A mapping between test data and snippet-method-based keys
    """
    tuple_methods = []
    with open(snippet_data_json, 'r') as file:
        json_content = json.loads('\n'.join(file.readlines()))
        json_test_map = json_content['test_method_map']
        json_snippets = json_content['snippets']

        # Normalize source_path values
        parent_path = path.dirname(snippet_data_json)
        for snippet in json_snippets:
            snippet['source_path'] = (
                path.join(parent_path, snippet['source_path']))

            tuple_methods.append(
                pdd.PolyglotDriftData(**snippet))

        # Convert test_method_map values to tuples
        # (Required because tuples aren't JSON-encodable)
        for test_key, test_list in json_test_map.items():
            json_test_map[test_key] = [
                tuple(test) for test in test_list]

    return tuple_methods, json_test_map


def _process_file_region_tags(
    source_file: str,
    snippet_data_json: str,
    tuple_methods: List[pdd.PolyglotDriftData]
) -> Tuple[Set[str], Set[str]]:
    """Process a snippet source file's region tags

    This method extracts region tags from a snippet source file,
    classifies them, and adds them to any matching snippet method
    objects. It then returns the classified groups of region tags
    it extracted.

    Arguments:
        source_file: path to the target snippet source file
        snippet_data_json: The path to a polyglot_snippet_data.json file
        tuple_methods: path to the target foobar

    Modifies:
        Adds region tags to their respective methods in tuple_methods

    Returns:
        A tuple containing the following:
         - A list of *every* tag found in the snippet source file
         - A list of 'ignored' tags found in the snippet source file
    """
    if not path.isfile(source_file):
        raise ValueError(
            f'Path {source_file} in file {snippet_data_json}'
            ' not found! '
            'Try regenerating polyglot_snippet_data.json?'
        )

    region_tags, ignored_tag_names = (
        polyglot_parser.get_region_tag_regions(source_file))

    grep_tag_names = set(region[0] for region in region_tags)
    ignored_tag_names = set(ignored_tag_names)

    for method in tuple_methods:
        if method.source_path != source_file:
            continue

        polyglot_parser.add_region_tags_to_method(method, region_tags)

    return grep_tag_names, ignored_tag_names


def _dedupe_source_methods(
    source_methods: List[pdd.PolyglotDriftData]
) -> List[pdd.PolyglotDriftData]:
    """Remove methods with duplicate region tag-sets in a method list

    This method is a helper function for analyze_json()
    that de-dupes methods based on their region tag-set.
    (Order-invariant region tag sets are unique IDs for
     source methods.)

    Arguments:
        source_methods: the list of methods to be de-duped

    Returns:
        A de-duped list of (snippet) source methods
    """
    source_method_keys = set()
    deduped_methods = []

    for method in source_methods:
        if method.name in constants.SNIPPET_INVOCATION_METHODS:
            key = f'{method.source_path},{method.name}'
        else:
            key = ','.join(sorted(method.region_tags))

        if key in source_method_keys:
            continue

        source_method_keys.add(key)
        deduped_methods.append(method)

    return list(deduped_methods)


def _store_tests_on_methods(
    source_methods: List[pdd.PolyglotDriftData],
    test_to_method_key_map: Dict[Tuple[str, str], Tuple[str, str]]
) -> None:
    """Adds test data to snippet method objects

    This method uses test keys and the mapping generated by per-language
    parsers to match snippet methods with their tests. That test data
    (file paths and method names) is then added to the methods themselves
    by updating their "test_methods" property.

    Args:
        source_methods: a list of top-level methods in snippet source files
        test_to_method_key_map: a map from test keys to test data
                                (filepaths and names) generated by the
                                language-specific parsers
    """
    for method in source_methods:
        source_root = os.path.dirname(method.source_path)

        keys = []
        if method.parser == 'direct_invocation':
            keys = [
                method.class_name +
                lib_constants.KEY_SEPARATOR +
                method.method_name
            ]
        elif method.parser == 'webapp2_router':
            keys = [
                method.http_methods[0] +
                lib_constants.KEY_SEPARATOR +
                method.url
            ]
        elif method.parser == 'flask_router':
            keys = [http_method + lib_constants.KEY_SEPARATOR + method.url
                    for http_method in method.http_methods]

        new_test_methods = list(method.test_methods)  # deep copy
        for key in keys:
            if key not in test_to_method_key_map:
                # Nonexistent key
                continue

            map_entry = test_to_method_key_map[key]
            if not map_entry:
                # No tests specified (empty array)
                continue

            matching_tests = [
                (file, path) for (file, path) in map_entry
                if source_root in file
            ]

            new_test_methods.extend(matching_tests)

        method.test_methods = new_test_methods


def analyze_json(
    snippet_data_json: str,
    root_dir: str
) -> Tuple[Set[str], Set[str], Set[str], List[pdd.PolyglotDriftData]]:
    """Perform language-agnostic AST analysis on a directory

    This function processes a given directory's language-specific
    analysis (stored in a polyglot_snippet_data.json file) into a
    list of automatically detected snippets. It then augments the
    automatic detection results with useful manual data (specified
    in .drift-data.yml files). Finally, it repackages all this data
    into a tuple containing 4 useful lists of data as shown in the
    'returns' section.

    Arguments:
        snippet_data_json: A path to a polyglot_snippet_data.json
                           file generated for the specified root_dir
        root_dir: The root directory to perform AST analysis on

    Returns:
        A tuple containing the following:
         - A list of tags found (via grep/text search)
           within the given directory and its subdirectories
         - A list of tags detected (by the AST parser)
           within the given directory and its subdirectories
         - A list of tags that the AST parser detected,
           but chose to ignore (due to constants or user
           specification in .drift-data.yml files)
         - A list of snippet objects (as typed NamedTuples)
           detected by the AST parser in the given directory
           and its subdirectories
    """
    tuple_methods, test_method_map = _get_data(snippet_data_json)

    source_filepaths = set(method.source_path for method in tuple_methods)

    grep_tags: Set[str] = set()
    ignored_tags: Set[str] = set()

    for source_file in source_filepaths:
        grep_tag_names, ignored_tag_names = (
            _process_file_region_tags(
                source_file, snippet_data_json, tuple_methods))

        grep_tags = grep_tags.union(grep_tag_names)
        ignored_tags = ignored_tags.union(ignored_tag_names)

    source_methods = [method for method in tuple_methods
                      if method.region_tags or
                      method.name in constants.SNIPPET_INVOCATION_METHODS]

    source_methods = _dedupe_source_methods(source_methods)

    _store_tests_on_methods(source_methods, test_method_map)

    polyglot_parser.add_children_drift_data(source_methods)
    yaml_utils.add_yaml_data_to_source_methods(source_methods, root_dir)

    source_tags: Set[str] = set()
    for method in source_methods:
        source_tags = source_tags.union(set(method.region_tags))

    # Remove automatically ignored region tags from region tag lists
    grep_tags = set(tag for tag in grep_tags
                    if tag not in ignored_tags)
    source_tags = set(tag for tag in source_tags
                      if tag not in ignored_tags)

    # Add manually ignored (via yaml) tags to ignored tags list
    #   These should *not* overlap w/ source_tags, but we
    #   check that in validate_yaml_syntax  - *not here!*
    ignored_tags = ignored_tags.union(
        yaml_utils.get_untested_region_tags(root_dir))

    return grep_tags, source_tags, ignored_tags, source_methods
