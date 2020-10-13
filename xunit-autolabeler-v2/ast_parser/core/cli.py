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


from typing import List

from ast_parser.core import analyze, cli_yaml


def _write_output(output: List[str], output_file: str) -> None:
    """Helper function that writes output to stdout or a file

    This function outputs data from AST parser CLI commands to a given
    filepath (if one is provided) or stdout (if no filepath is provided).

    Args:
        output: A list of strings to write to the chosen output
        output_file: One of {None, a filepath}
    """
    if output_file:
        with open(output_file, 'w+') as file:
            file.write('\n'.join(output))
    else:
        for line in output:
            print(line)


def validate_yaml(
    data_json: str,
    root_dir: str,
    output_file: str = None
) -> None:
    """ Validates .drift-data.yml files in a directory

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
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(data_json, root_dir)

    (is_valid, output) = cli_yaml.validate_yaml_syntax(
        root_dir, grep_tags, source_tags)

    if is_valid:
        output.append('All files are valid.')
    else:
        output.append('Invalid file(s) found!')

    _write_output(output, output_file)
