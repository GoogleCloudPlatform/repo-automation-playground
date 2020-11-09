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
from typing import Any, Dict, List, Optional, Tuple

from ast_parser.core import constants
from ast_parser.lib import file_utils

import yaml


def __attr_validate_required_values(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    tag: str,
    attr: str
) -> Optional[str]:
    """Ensure required-value YAML keys have the correct values

    Some .drift-data.yml keys only allow a predefined set of values.

    Arguments:
        yaml_path: A path to a .drift-data.yml file
        yaml_entry: The YAML entry to validate
        tag: The region tag corresponding to the specified YAML entry
        attr: The attribute of the YAML entry to validate

    Returns:
        An error message if an attribute is invalid; None otherwise
    """
    if not attr or attr not in constants.REQUIRED_KEY_VALUES:
        return None

    actual = yaml_entry[attr]
    expected = constants.REQUIRED_KEY_VALUES[attr]
    if actual != expected:
        return (
            f'Invalid {attr} value in file {yaml_path} '
            f'for tag {tag}: {actual}, expected {expected} '
            ' (or omission)')

    return None


def __attr_validate_additions(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    tag: str,
    attr: str,
    grep_tags: List[str]
) -> Optional[str]:
    """Ensure additions attributes have correct values

    This function ensures that additions attributes are lists, and that
    the child tags they refer to are detected in the codebase.

    Arguments:
        yaml_path: A path to a .drift-data.yml file
        yaml_entry: The YAML entry to validate
        tag: The region tag corresponding to the specified YAML entry
        attr: The attribute of the YAML entry to validate
        grep_tags: A list of tags existing (not necessarily parsed out of)
                   the source code

    Returns:
        An error message if the additions attribute is invalid; None otherwise
    """
    if attr != 'additions':
        return None

    # Additions field must be an array
    if not isinstance(yaml_entry[attr], list):
        return (f'Additions key for {tag} in '
                f'{yaml_path} is not a list!')

    # Added tags must be correctly parsed from the codebase
    if any(t not in grep_tags for t in yaml_entry[attr]):
        return (f'Yaml file {yaml_path} contains region '
                f'tag not used in source files: {tag}')

    return None


def __attr_validate_manually_specified_tests(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    tag: str,
    attr: str,
    grep_tags: List[str]
) -> List[str]:
    """Ensure manually-specified tests are correct

    This function ensures that manually-specified
    tests refer to files that actually exist.

    Arguments:
        yaml_path: A path to a .drift-data.yml file
        yaml_entry: The YAML entry to validate
        tag: The region tag corresponding to the specified YAML entry
        attr: The attribute of the YAML entry to validate
        grep_tags: A list of tags existing (not necessarily parsed out of)
                   the source code

    Returns:
        An error message if the manually-specified tests are invalid; None
        otherwise
    """
    errors = []
    yaml_dirname = os.path.dirname(yaml_path)

    for test_path in yaml_entry.keys():
        if test_path in constants.RESERVED_YAML_KEYS:
            continue  # Skip non-filepaths

        if not os.path.isabs(test_path):
            test_path = os.path.join(yaml_dirname, test_path)

        if not os.path.exists(test_path):
            errors.append(f'Test file {test_path} used '
                          f'in {yaml_path} not found!')

    return errors


def _validate_attrs(
    yaml_paths: List[str],
    grep_tags: List[str]
) -> Tuple[bool, List[str]]:
    """Validate attributes in a list of .drift-data.yml files

    This method verifies that attributes within
    a .drift-data.yml file are used appropriately.

    Args:
        yaml_paths: A list of .drift-data.yml filepaths to validate
        grep_tags: A list of region tags (parsed *and* unparsed) that exist
                   in the target directory

    Returns:
        A 2-tuple containing the following:
         - A boolean including file validity (True if all files passed
           attribute validation, False otherwise)
         - A list of validation error messages (if any) that were raised
    """

    errors = []

    for yaml_path in yaml_paths:
        with open(yaml_path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]
                yaml_keys = list(yaml_entry.keys())

                if not yaml_keys:
                    continue

                yaml_attr = yaml_keys[0]

                # Validate keys that require specific values
                required_value_error = __attr_validate_required_values(
                    yaml_path,
                    yaml_entry,
                    tag,
                    yaml_attr
                )
                if required_value_error:
                    errors.append(required_value_error)

                # Validate additions field
                additions_error = __attr_validate_additions(
                    yaml_path,
                    yaml_entry,
                    tag,
                    yaml_attr,
                    grep_tags
                )
                if additions_error:
                    errors.append(additions_error)

                # Validate manually-specified tests
                manual_errors = __attr_validate_manually_specified_tests(
                    yaml_path,
                    yaml_entry,
                    tag,
                    yaml_attr,
                    grep_tags
                )
                if manual_errors:
                    errors += manual_errors

    is_valid = not errors
    return (is_valid, errors)


def _validate_region_tags(
    yaml_paths: List[str],
    grep_tags: List[str],
    source_tags: List[str],
) -> Tuple[bool, List[str]]:
    """Validate region-tag keys in a list of .drift-data.yml files

    This method verifies that region tag keys within a .drift-data.yml
    file are used *exactly* once in the source code.

    Args:
        yaml_paths: A list of .drift-data.yml filepaths to validate
        grep_tags: A list of region tags (parsed *and* unparsed) that exist
                   in the target directory
        source_tags: A list of successfully-parsed region tags in the target
                     directory

    Returns:
        A 2-tuple containing the following:
         - A boolean including file validity (True if all files passed region
           tag validation, False otherwise)
         - A list of validation error messages (if any) that were raised
    """

    seen_region_tags = set()
    output = []
    is_valid = True

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
                if tag not in grep_tags:
                    output.append(
                        f'Yaml file {yaml_path} contains region '
                        f'tag not used in source files: {tag}')
                    is_valid = False
                elif tag_should_be_in_source and tag not in source_tags:
                    output.append(
                        f'Yaml file {yaml_path} contains '
                        f'unparsed region tag: {tag}')
                    output.append(
                        '  Remove it, or label it with "tested: false".')
                    is_valid = False
                elif not tag_should_be_in_source and tag in source_tags:
                    output.append(f'Parsed tag {tag} in file'
                                  f'{yaml_path} marked untested!')
                    is_valid = False

                # Verify region tags are present at most once
                if tag in seen_region_tags:
                    output.append(f'Region tag {tag} is used multiple '
                                  'times in .drift-data.yml files!')
                    is_valid = False
                else:
                    seen_region_tags.add(tag)

    return (is_valid, output)


def validate_yaml_syntax(
    root_dir: str,
    grep_tags: List[str],
    source_tags: List[str]
) -> Tuple[bool, List[str]]:
    """Validate a given directory's .drift-data.yml files

    This method validates that a given directory's .drift-data.yml files are
    semantically correct, and match up with the directory's source code.

    Args:
        yaml_paths: A list of .drift-data.yml filepaths to validate
        grep_tags: A list of region tags (parsed *and* unparsed) that exist
                   in the target directory
        source_tags: A list of successfully-parsed region tags in the target
                     directory

    Returns:
        A 2-tuple containing the following:
         - A boolean including file validity (True if all .drift-data.yml
           files passed validation, False otherwise)
         - A list of validation error messages (if any) that were raised
    """
    yaml_paths = file_utils.get_drift_yaml_files(root_dir)

    (tags_are_valid, tags_output) = (
        _validate_region_tags(yaml_paths, grep_tags, source_tags))
    (attrs_are_valid, attrs_output) = _validate_attrs(yaml_paths, grep_tags)

    output = tags_output + attrs_output
    is_valid = tags_are_valid and attrs_are_valid

    return (is_valid, output)
