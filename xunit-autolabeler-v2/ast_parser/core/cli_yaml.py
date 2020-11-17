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

from ast_parser.core import constants, cli_yaml_errors
from ast_parser.lib import file_utils

import yaml


def _attr_required_values_get_errors(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    tag: str,
    attr: str
) -> Optional[str]:
    """Report incorrect values for required-value YAML keys

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
        return cli_yaml_errors.InvalidAttributeViolation(
            attr, yaml_path, tag, actual, expected)

    return None


def _attr_additions_get_errors(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    region_tag: str,
    attr: str,
    grep_tags: List[str]
) -> Optional[str]:
    """Report any incorrect values for additions attributes

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
        return cli_yaml_errors.AdditionsKeyNotAListViolation(
            region_tag, yaml_path)

    # Added tags must be correctly parsed from the codebase
    if any(t not in grep_tags for t in yaml_entry[attr]):
        return cli_yaml_errors.UnusedRegionTagViolation(region_tag, yaml_path)

    return None


def _attr_manually_specified_tests_get_errors(
    yaml_path: str,
    yaml_entry: Dict[str, Any],
    tag: str,
    attr: str,
    grep_tags: List[str]
) -> List[str]:
    """Report incorrect manually-specified test attributes

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
            errors.append(
                cli_yaml_errors.MissingTestFileViolation(
                    test_path, yaml_path))

    return errors


def _get_attr_errors(
    yaml_paths: List[str],
    grep_tags: List[str]
) -> Tuple[bool, List[str]]:
    """Report attribute errors in a list of .drift-data.yml files

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
                required_value_error = _attr_required_values_get_errors(
                    yaml_path,
                    yaml_entry,
                    tag,
                    yaml_attr
                )
                if required_value_error:
                    errors.append(required_value_error)

                # Validate additions field
                additions_error = _attr_additions_get_errors(
                    yaml_path,
                    yaml_entry,
                    tag,
                    yaml_attr,
                    grep_tags
                )
                if additions_error:
                    errors.append(additions_error)

                # Validate manually-specified tests
                manual_errors = _attr_manually_specified_tests_get_errors(
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


def _get_region_tag_errors(
    yaml_paths: List[str],
    grep_tags: List[str],
    source_tags: List[str],
) -> Tuple[bool, List[str]]:
    """Report region-tag errors in a list of .drift-data.yml files

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
                        cli_yaml_errors.UnusedRegionTagViolation(
                            tag, yaml_path))
                    is_valid = False
                elif tag_should_be_in_source and tag not in source_tags:
                    output.append(cli_yaml_errors.UnparsedRegionTagViolation(
                        tag, yaml_path))
                    is_valid = False
                elif not tag_should_be_in_source and tag in source_tags:
                    output.append(
                        cli_yaml_errors.DetectedTagMarkedUndetectedViolation(
                            tag, yaml_path))
                    is_valid = False

                # Verify region tags are present at most once
                if tag in seen_region_tags:
                    output.append(cli_yaml_errors.RepeatedTagViolation(tag))
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

    (tags_are_valid, tags_violations) = (
        _get_region_tag_errors(yaml_paths, grep_tags, source_tags))
    (attrs_are_valid, attrs_violations) = _get_attr_errors(yaml_paths, grep_tags)

    violations = tags_violations + attrs_violations
    output = [str(violation) for violation in violations]

    is_valid = tags_are_valid and attrs_are_valid

    return (is_valid, output)
