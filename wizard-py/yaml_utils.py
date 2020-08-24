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


import constants
import file_utils
import os
import yaml


def __handle_overrides(source_methods, root_dir):
    yaml_paths = file_utils.get_yaml_files(root_dir)

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

    for m in source_methods:
        if set(m.drift['region_tags']).intersection(overwritten_tags):
            m.drift['test_methods'] = []


def __handle_additions_clause(source_methods, root_dir):
    yaml_paths = file_utils.get_yaml_files(root_dir)

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            additions_tags = [k for k in parsed_yaml.keys() if
                              k not in constants.RESERVED_YAML_KEYS]

            for tag in additions_tags:
                yaml_entry = parsed_yaml[tag]
                if 'additions' in yaml_entry and \
                   isinstance(yaml_entry['additions'], list):
                    added_tags = set(yaml_entry['additions'])

                    for m in source_methods:
                        method_tags = set(m.drift['region_tags'])
                        if tag not in m.drift['region_tags'] and \
                           added_tags.intersection(method_tags):
                            m.drift['region_tags'].append(tag)


def __handle_manually_specified_tests(source_methods, root_dir):
    yaml_paths = file_utils.get_yaml_files(root_dir)

    test_tag_map = {}

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_dir = os.path.dirname(path)
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            # Filter out all keys in RESERVED_YAML_KEYS *except* overwrite
            # (overwrite can be in a manually-specified test's YAML entry)
            filtered_keys = set(constants.RESERVED_YAML_KEYS)
            filtered_keys.remove('overwrite')

            manual_tags = [t for t in parsed_yaml.keys() if not set(
                           parsed_yaml[t].keys()).intersection(filtered_keys)]

            for tag in manual_tags:
                yaml_entry = parsed_yaml[tag]
                test_tag_map[tag] = []

                for test_rel_path in yaml_entry.keys():
                    test_path = os.path.join(yaml_dir, test_rel_path)
                    if test_path and os.path.exists(test_path):
                        for test_name in yaml_entry[test_rel_path]:
                            test_tag_map[tag].append((test_path, test_name))

    for m in source_methods:
        for tag in m.drift['region_tags']:
            if tag in test_tag_map and test_tag_map[tag]:
                m.drift['test_methods'].append(test_tag_map[tag])


def get_untested_region_tags(root_dir):
    yaml_paths = file_utils.get_yaml_files(root_dir)
    all_untested_tags = []

    for path in yaml_paths:
        with open(path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            local_untested_tags = [k for k in parsed_yaml.keys()
                                   if parsed_yaml[k].get('tested') is False]
            all_untested_tags += local_untested_tags

    return list(set(all_untested_tags))


def validate_yaml_syntax(root_dir, grep_tags, source_tags):
    yaml_paths = file_utils.get_yaml_files(root_dir)
    is_valid = True

    seen_region_tags = set()

    # Validate region tags
    for yaml_path in yaml_paths:
        with open(yaml_path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]
                tag_should_be_in_source = not (
                    'tested' in yaml_entry and yaml_entry['tested'] is False)

                # Verify mentioned region tags are used in the
                # source code (via parsing and/or grep results)
                # TODO add to node script
                if tag not in grep_tags:
                    print(
                        f'Yaml file {yaml_path} contains region '
                        f'tag not used in source files: {tag}')
                    is_valid = False
                elif tag_should_be_in_source and tag not in source_tags:
                    print(
                        f'Yaml file {yaml_path} contains '
                        f'unparsed region tag: {tag}')
                    print('  Remove it, or label it with "tested: false".')
                    is_valid = False
                elif not tag_should_be_in_source and tag in source_tags:
                    print(f'Parsed tag {tag} in file'
                          f'{yaml_path} marked untested!')
                    is_valid = False

                # Verify region tags are present at most once
                if tag in seen_region_tags:
                    print(f'Region tag {tag} is used multiple '
                          'times in .drift-data.yml files!')
                    is_valid = False
                else:
                    seen_region_tags.add(tag)

    # Validate individual attributes
    for yaml_path in yaml_paths:
        with open(yaml_path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]

                attr = [x for x in yaml_entry if
                        x in constants.RESERVED_YAML_KEYS]
                if attr:
                    attr = attr[0]
                attr_is_valid = True

                if attr and attr in constants.REQUIRED_KEY_VALUES:
                    actual = yaml_entry[attr]
                    expected = constants.REQUIRED_KEY_VALUES[attr]
                    if actual != expected:
                        attr_is_valid = False
                        is_valid = False
                        print(f'Invalid {attr} value in file {yaml_path} '
                              f'for tag {tag}: {actual}, expected {expected} '
                              ' (or omission)')

                # Validate additions field
                if attr == 'additions':
                    if not isinstance(yaml_entry[attr], list):
                        # additions field must be an array
                        print(f'Additions key for {tag} in '
                              f'{yaml_path} is not a list!')
                        attr_is_valid = False
                        is_valid = False
                    elif any(t not in grep_tags for t in yaml_entry[attr]):
                        # added tags must be correctly parsed from the codebase
                        print(f'Yaml file {yaml_path} contains region '
                              f'tag not used in source files: {tag}')
                        attr_is_valid = False
                        is_valid = False

                # Validate manually-specified tests
                yaml_dirname = os.path.dirname(yaml_path)
                test_paths_exist = True
                for test_path in yaml_entry.keys():
                    if test_path in constants.RESERVED_YAML_KEYS:
                        continue  # Skip non-filepaths

                    if not os.path.isabs(test_path):
                        test_path = os.path.join(yaml_dirname, test_path)
                    if not os.path.exists(test_path):
                        print(f'Test file {test_path} used '
                              f'in {yaml_path} not found!')
                        is_valid = False
                        test_paths_exist = False
                if test_paths_exist:
                    continue

                # Bad YAML format (unknown error)
                if is_valid:
                    print(f'Region tag {tag} in file {yaml_path} '
                          'is formatted incorrectly!')
                    is_valid = False

                # Messaging for invalid attrs
                if not attr_is_valid:
                    print(f'Invalid {attr} key in file {yaml_path}')

    return is_valid


def add_yaml_data_to_source_methods(source_methods, root_dir):
    __handle_overrides(source_methods, root_dir)
    __handle_manually_specified_tests(source_methods, root_dir)
    __handle_additions_clause(source_methods, root_dir)
