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

from . import polyglot_parser, yaml_utils


def analyze_json(repo_json, root_dir):
    json_methods = []
    with open(repo_json, 'r') as file:
        json_content = '\n'.join(file.readlines())
        json_methods = json.loads(json_content)

        # Normalize source_path values
        parent_path = path.dirname(repo_json)
        for m in json_methods:
            m['source_path'] = path.join(parent_path, m['source_path'])

    source_filepaths = set([m['source_path'] for m in json_methods])

    grep_tags = set()
    ignored_tags = set()

    for source_file in source_filepaths:
        if not path.isfile(source_file):
            raise ValueError(
                f'Path {source_file} in file {repo_json} not found! '
                'Did you move repo.json from its generated location?'
            )

        (region_tags, ignored_tag_names) = \
            polyglot_parser.get_region_tag_regions(source_file)

        grep_tags = grep_tags.union(set([t[0] for t in region_tags]))
        ignored_tags = ignored_tags.union(set(ignored_tag_names))

        file_methods = [m for m in json_methods
                        if m['source_path'] == source_file]

        polyglot_parser.add_region_tags_to_methods(
            file_methods, region_tags)

    source_methods = [m for m in json_methods if m['region_tags']]

    # Dedupe source methods
    source_method_keys = set()
    source_methods_deduped = []
    for m in source_methods:
        key = ','.join(m['region_tags'])
        if key not in source_method_keys:
            source_methods_deduped.append(m)
            source_method_keys.add(key)

    source_methods = source_methods_deduped

    # Convert test_methods values to tuples
    for m in source_methods:
        m['test_methods'] = [tuple(x) for x in m['test_methods']]

    polyglot_parser.add_children_drift_data(source_methods)

    yaml_utils.add_yaml_data_to_source_methods(source_methods, root_dir)

    source_tags = set()
    for m in source_methods:
        source_tags = source_tags.union(set(m['region_tags']))

    # Remove automatically ignored region tags from region tag lists
    grep_tags = [x for x in grep_tags if x not in ignored_tags]
    source_tags = [x for x in source_tags if x not in ignored_tags]

    # Add manually ignored (via yaml) tags to ignored tags list
    #   These should *not* overlap w/ source_tags, but we
    #   check that in validate_yaml_syntax  - *not here!*
    ignored_tags = ignored_tags.union(
        yaml_utils.get_untested_region_tags(root_dir))

    return (grep_tags, source_tags, list(ignored_tags), source_methods)
