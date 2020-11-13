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
import xml.etree.ElementTree as etree
from typing import Any, Dict, Tuple, List, Optional

from ast_parser.core import analyze, cli_yaml
from ast_parser.core import cli_list_region_tags, cli_list_region_tags_datatypes


def _write_output(output: List[str], output_file: str) -> None:
    """Helper function that writes output to stdout or a file

    This function outputs data from AST parser CLI commands to a given
    filepath (if one is provided) or stdout (if no filepath is provided).

    Args:
        output: A list of strings to write to the chosen output.
        output_file: One of {None, a filepath}.
    """
    if output_file:
        with open(output_file, 'w+') as file:
            file.write('\n'.join(output))
    else:
        for line in output:
            print(line)


def list_region_tags(
    data_json: str,
    root_dir: str,
    show_detected: bool,
    show_undetected: bool,
    show_test_counts: bool,
    show_filenames: bool,
    output_file: Optional[str] = None
) -> None:
    """Lists region tags in a directory.

    This method lists the region tags for snippets parsed from a given
    directory, filtered based on whether each tag was detected by an AST
    parser (or not). It can also display test counts and/or source filenames
    for each region tag.

    Args:
        data_json: A path to a polyglot_drift_data.json file for the specified
                   root directory
        root_dir: A path to the target root directory.
        show_detected: Whether or not to show region tags that *were* detected
                       by the AST parser
        show_undetected: Whether or not to show region tags *not* detected by
                         the AST parser
        show_test_counts: Whether or not to show test counts for each
                          AST-parser-detected region tag
        show_filenames: Whether or not to show source filenames for each
                        AST-parser-detected region tag
        output_file: (Optional) A filepath to write the YAML validation
                     results to. Results will be written to stdout if this
                     argument is omitted.
    """
    invocation = cli_list_region_tags_datatypes.ListRegionTagsInvocation(
        data_json,
        root_dir,
        show_detected,
        show_undetected,
        show_test_counts,
        show_filenames
    )
    result = cli_list_region_tags.process_list_region_tags(invocation)
    output_lines = cli_list_region_tags.format_list_region_tags(invocation, result)

    _write_output(output_lines, output_file)


def list_source_files(
    data_json: str,
    root_dir: str,
    show_tested_files: bool,
    output_file: str = None
) -> None:
    """Lists snippet source file paths in a directory.

    This method lists the source files for snippets parsed from a given
    directory. It can also filter listed source files based on how many
    (all, some, or none) of their methods are tested using the
    show_tested_files parameter.

    Args:
        data_json: A path to a polyglot_drift_data.json file for the specified
                   root directory
        root_dir: A path to the target root directory.
        show_tested_files: If specified, this method will only list files that
                           have {all, some, none} of their methods tested.
        output_file: (Optional) A filepath to write the YAML validation
                     results to. Results will be written to stdout if this
                     argument is omitted.
    """
    grep_tags, source_tags, ignored_tags, source_methods = (
        analyze.analyze_json(data_json, root_dir))

    # Ignore methods without region tags
    source_methods = [method for method in source_methods
                      if method['region_tags']]

    tested_files = set(method['source_path'] for method in source_methods
                       if method['test_methods'])
    untested_files = set(method['source_path'] for method in source_methods
                         if not method['test_methods'])

    files = set(method['source_path'] for method in source_methods)

    if show_tested_files == 'all':
        files = [file for file in tested_files if file not in untested_files]

    if show_tested_files == 'some':
        files = tested_files

    if show_tested_files == 'none':
        files = [file for file in untested_files if file not in tested_files]

    _write_output(files, output_file)


def inject_snippet_mapping(
    data_json: str,
    root_dir: str,
    stdin_lines: List[str],
    output_file: bool = None
) -> None:
    """Adds snippet mapping to XUnit results

    This method injects test-snippet mappings into XUnit test results provided
    via stdin. It then saves the modified XUnit results to a file (if
    output_file is specified) or prints them to stdout (if output_file is *not*
    specified).

    Args:
        data_json: A path to a polyglot_drift_data.json file for the specified
                   root directory
        root_dir: A path to the target root directory.
        stdin_lines: The lines of an XUnit test result file.
        output_file: (Optional) A filepath to write the YAML validation
                     results to. Results will be written to stdout if this
                     argument is omitted.
    """

    grep_tags, source_tags, ignored_tags, source_methods = (
        analyze.analyze_json(data_json, root_dir))

    xunit_tree = etree.fromstring(''.join(stdin_lines))

    for elem in xunit_tree.findall('.//testcase'):
        class_parts = [part for part in elem.attrib['classname'].split('.')
                       if not part.startswith('Test')]
        test_key = (class_parts[-1], elem.attrib['name'])
        for method in source_methods:
            method_test_keys = [(
                os.path.splitext(os.path.basename(test[0]))[0],
                test[1]
            ) for test in method['test_methods']]

            if test_key in method_test_keys:
                # Inject region tags into region_tags XML attribute
                existing_tag_str = elem.attrib.get('region_tags')
                existing_tag_list = (
                    existing_tag_str.split(',') if existing_tag_str else [])

                deduped_tag_list = (
                    list(set(existing_tag_list + method['region_tags'])))

                elem.set('region_tags', ','.join(deduped_tag_list))

    _write_output(
        [etree.tostring(xunit_tree).decode()],
        output_file)


def validate_yaml(
    data_json: str,
    root_dir: str,
    output_file: str = None
) -> None:
    """Validates .drift-data.yml files in a directory

    This method coordinates the function calls necessary to validate
    .drift-data.yml files in a given directory. (The validation process
    requires data provided by analyze_json(), and this method is responsible
    for passing that in.)

    Args:
        data_json: A path to a polyglot_drift_data.json file for the specified
                   root directory
        root_dir: A path to the target root directory.
        output_file: (Optional) A filepath to write the YAML validation
                     results to. Results will be written to stdout if this
                     argument is omitted.
    """
    grep_tags, source_tags, ignored_tags, source_methods = (
        analyze.analyze_json(data_json, root_dir))

    (is_valid, output) = cli_yaml.validate_yaml_syntax(
        root_dir, grep_tags, source_tags)

    if is_valid:
        output.append('All files are valid.')
    else:
        output.append('Invalid file(s) found!')

    _write_output(output, output_file)
