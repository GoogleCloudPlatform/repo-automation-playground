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

from . import analyze, yaml_utils


def __write_output(output, output_file):
    if output_file:
        with open(output_file, 'w+') as f:
            f.write("\n".join(output))
    else:
        for o in output:
            print(o)


# Lists region tags in a file or directory.
def list_region_tags(repo_json,
                     root_dir,
                     show_detected,
                     show_undetected,
                     show_test_counts,
                     show_filenames,
                     output_file=None):

    output = []

    if show_undetected and show_test_counts:
        output.append(
            'WARN Undetected/ignored region tags do not have test counts')

    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(repo_json, root_dir)

    def __get_test_count_str(region_tag):
        if not show_test_counts:
            return ''

        test_data_matches = [x for x in source_methods if
                             region_tag in x['region_tags']]

        total_tests = 0
        for t in test_data_matches:
            total_tests += len(t['test_methods'])

        return f'({total_tests} test(s))'

    if show_detected:
        output.append('Detected region tags:')
        for tag in source_tags:
            output.append(f'  {tag} {__get_test_count_str(tag)}')
            if show_filenames:
                source_file = [x['source_path'] for x in source_methods
                               if tag in x['region_tags']][0]
                output.append(f'    Source file: {source_file}')

    if show_undetected:
        output.append('Undetected region tags:')
        undetected_tags = [t for t in grep_tags if t not in source_tags]
        undetected_tags = [t for t in undetected_tags if t not in ignored_tags]
        for tag in undetected_tags:
            output.append(f'  {tag}')

    if ignored_tags:
        output.append('Ignored region tags')
        for tag in ignored_tags:
            output.append(f'  {tag}')

    __write_output(output, output_file)


# Lists snippet source file paths in a file or directory.
def list_source_files(repo_json,
                      root_dir,
                      show_tested_files,
                      output_file=None):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(repo_json, root_dir)
    # Ignore methods without region tags
    source_methods = [x for x in source_methods if x['region_tags']]

    tested_files = set(x['source_path'] for x in source_methods
                       if x['test_methods'])
    untested_files = set(x['source_path'] for x in source_methods
                         if not x['test_methods'])

    files = set(x['source_path'] for x in source_methods)

    if show_tested_files == 'all':
        files = [x for x in tested_files if x not in untested_files]

    if show_tested_files == 'some':
        files = tested_files

    if show_tested_files == 'none':
        files = [x for x in untested_files if x not in tested_files]

    __write_output(files, output_file)


# Adds snippet mapping to XUnit output
def inject_snippet_mapping(repo_json,
                           root_dir,
                           stdin_lines,
                           output_file=None):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(repo_json, root_dir)

    xunit_tree = etree.fromstring("".join(stdin_lines))

    for x in xunit_tree.findall('.//testcase'):
        class_parts = [p for p in x.attrib['classname'].split('.')
                       if not p.startswith('Test')]
        test_key = (class_parts[-1], x.attrib['name'])
        for m in source_methods:
            m_test_keys = [(os.path.splitext(os.path.basename(t[0]))[0], t[1])
                           for t in m['test_methods']]

            if test_key in m_test_keys:
                # Inject region tags into region_tags XML attribute
                existing_tag_str = x.attrib.get('region_tags')
                existing_tag_list = \
                    existing_tag_str.split(',') if existing_tag_str else []

                deduped_tag_list = \
                    list(set(existing_tag_list + m['region_tags']))

                x.set('region_tags', ','.join(deduped_tag_list))

    __write_output(
        [etree.tostring(xunit_tree).decode()],
        output_file)


# Validates .drift-data.yml files in a directory
def validate_yaml(repo_json, root_dir, output_file=None):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(repo_json, root_dir)

    (is_valid, output) = yaml_utils.validate_yaml_syntax(
        root_dir, grep_tags, source_tags)

    if is_valid:
        output.append('All files are valid.')
    else:
        output.append('Invalid file(s) found!')

    __write_output(output, output_file)
