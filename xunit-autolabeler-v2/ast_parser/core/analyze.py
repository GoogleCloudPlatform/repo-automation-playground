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
from os import path
from typing import List, Set, Tuple

from . import polyglot_drift_data as pdd, polyglot_parser, yaml_utils


def analyze_json(
    repo_json: str,
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
        repo_json: A path to a polyglot_snippet_data.json file
                   generated for the specified root_dir
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
    tuple_methods = []
    with open(repo_json, 'r') as file:
        json_content = '\n'.join(file.readlines())
        json_methods = json.loads(json_content)

        # Normalize source_path values
        parent_path = path.dirname(repo_json)
        for method in json_methods:
            method['source_path'] = (
                path.join(parent_path, method['source_path']))
            method['test_methods'] = (
                [tuple(test) for test in method['test_methods']])

            tuple_methods.append(
                pdd.PolyglotDriftData(**method))

    source_filepaths = set(method.source_path for method in tuple_methods)

    grep_tags: Set[str] = set()
    ignored_tags: Set[str] = set()

    for source_file in source_filepaths:
        if not path.isfile(source_file):
            raise ValueError(
                f'Path {source_file} in file {repo_json} not found! '
                'Did you move polyglot_snippet_data.json'
                ' from its generated location?'
            )

        region_tags, ignored_tag_names = (
            polyglot_parser.get_region_tag_regions(source_file))

        grep_tags = (
            grep_tags.union(set(region[0] for region in region_tags)))
        ignored_tags = ignored_tags.union(set(ignored_tag_names))

        for idx, method in enumerate(tuple_methods):
            if method.source_path != source_file:
                continue

            new_method = (
                polyglot_parser.add_region_tags_to_method(method, region_tags))
            tuple_methods[idx] = new_method

    source_methods = [method for method in tuple_methods if method.region_tags]

    # Dedupe source methods
    source_method_keys = set()
    source_methods_deduped = []
    for method in source_methods:
        key = ','.join(method.region_tags)
        if key not in source_method_keys:
            source_methods_deduped.append(method)
            source_method_keys.add(key)

    source_methods = source_methods_deduped

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
