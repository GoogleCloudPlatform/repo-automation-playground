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


import argparse
import analyze
import os
import sys
import yaml_utils
import xml.etree.ElementTree as etree


# Lists region tags in a file or directory.
def list_region_tags(root_dir,
                     show_detected,
                     show_undetected,
                     show_test_counts,
                     show_filenames):

    if show_undetected and show_test_counts:
        print('WARN Undetected/ignored region tags do not have test counts')

    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_dir(root_dir)

    def __get_test_count_str(region_tag):
        if not show_test_counts:
            return ''

        test_data_matches = [x for x in source_methods if
                             region_tag in x.drift['region_tags']]

        total_tests = 0
        for t in test_data_matches:
            total_tests += len(t.drift['test_methods'])

        return f' ({total_tests} test(s))'

    if show_detected:
        print('Detected region tags:')
        for tag in source_tags:
            print('  ' + tag + __get_test_count_str(tag))
            if show_filenames:
                source_file = [x.drift['source_path'] for x in source_methods
                               if tag in x.drift['region_tags']][0]
                print('    Source file: ' + source_file)

    if show_undetected:
        print('Undetected region tags:')
        undetected_tags = [t for t in grep_tags if t not in source_tags]
        undetected_tags = [t for t in undetected_tags if t not in ignored_tags]
        for tag in undetected_tags:
            print('  ' + tag)

    if ignored_tags:
        print('Ignored region tags')
        for tag in ignored_tags:
            print('  ' + tag)


# Lists snippet source file paths in a file or directory.
def list_source_files(root_dir, show_tested_files):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_dir(root_dir)
    # Ignore methods without region tags
    source_methods = [x for x in source_methods if x.drift['region_tags']]

    tested_files = set(x.drift['source_path'] for x in source_methods
                       if x.drift['test_methods'])
    untested_files = set(x.drift['source_path'] for x in source_methods
                         if not x.drift['test_methods'])

    files = set(x.drift['source_path'] for x in source_methods)

    if show_tested_files == 'all':
        files = [x for x in tested_files if x not in untested_files]

    if show_tested_files == 'some':
        files = tested_files

    if show_tested_files == 'none':
        files = [x for x in untested_files if x not in tested_files]

    for f in files:
        print(f)


# Adds snippet mapping to XUnit output
def inject_snippet_mapping(root_dir, stdin_lines, output_file=None):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_dir(root_dir)

    xunit_tree = etree.fromstring("".join(stdin_lines))

    for x in xunit_tree.findall('.//testcase'):
        class_parts = [p for p in x.attrib['classname'].split('.')
                       if not p.startswith('Test')]
        test_key = (class_parts[-1], x.attrib['name'])
        for m in source_methods:
            m_test_keys = [(os.path.splitext(os.path.basename(t[0]))[0], t[1])
                           for t in m.drift['test_methods']]

            if test_key in m_test_keys:
                # Inject region tags into customProperty XML attribute
                existing_tag_str = x.attrib.get('customProperty')
                existing_tag_list = existing_tag_str.split(',') \
                    if existing_tag_str else []

                deduped_tag_list = \
                    list(set(existing_tag_list + m.drift['region_tags']))

                x.set('region_tags', ','.join(deduped_tag_list))

    output = etree.tostring(xunit_tree).decode()
    if output_file:
        with open(output_file, 'w+') as f:
            f.write(output)
    else:
        print(output)


# Validates .drift-data.yml files in a directory
def validate_yaml(root_dir):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_dir(root_dir)

    is_valid = yaml_utils.validate_yaml_syntax(
        root_dir, grep_tags, source_tags)
    if is_valid:
        print('All files are valid.')
    else:
        print('Invalid file(s) found!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command')
    parser.add_argument(
        'root_dir', help='Root directory')

    lrt_parser = subparsers.add_parser(
        'list-region-tags', help=list_region_tags.__doc__)

    detected = lrt_parser.add_mutually_exclusive_group(required=False)
    detected.add_argument(
        '--show-detected', '-d1',
        dest='detected', action='store_true')
    detected.add_argument(
        '--hide-detected', '-d0',
        dest='detected', action='store_false')
    lrt_parser.set_defaults(detected=True)

    undetected = lrt_parser.add_mutually_exclusive_group(required=False)
    undetected.add_argument(
        '--show-undetected', '-u1',
        dest='undetected', action='store_true')
    undetected.add_argument(
        '--hide-undetected', '-u0',
        dest='undetected', action='store_false')
    lrt_parser.set_defaults(undetected=True)

    show_test_counts = lrt_parser.add_mutually_exclusive_group(required=False)
    show_test_counts.add_argument(
        '--show-test-counts', '-c1',
        dest='show_test_counts', action='store_true')
    show_test_counts.add_argument(
        '--hide-test-counts', '-c0',
        dest='show_test_counts', action='store_false')
    lrt_parser.set_defaults(show_test_counts=True)

    show_filenames = lrt_parser.add_mutually_exclusive_group(required=False)
    show_filenames.add_argument(
        '--show-filenames', '-f1',
        dest='show_filenames', action='store_true')
    show_filenames.add_argument(
        '--hide-filenames', '-f0',
        dest='show_filenames', action='store_false')
    lrt_parser.set_defaults(show_filenames=True)

    lsf_parser = subparsers.add_parser(
        'list-source-files', help=list_source_files.__doc__)
    lsf_parser.add_argument(
        '--tested_files', '-t',
        type=str,
        default='*',
        choices=['all', 'some', 'none', '*'],
        help='Display files where ({all, some, no}) methods are tested)')

    isj_parser = subparsers.add_parser(
        'inject-snippet-mapping', help=inject_snippet_mapping.__doc__)

    # Hotfix requested by tmatsuo@ (vs. writing to stdout)
    # TODO(anassri@): upcoming version ("polyglot parser") will support
    #                 file output for *all* commands, not just this one
    isj_parser.add_argument(
        '--output_file',
        type=str,
        default=None,
        help='File to write output to. (Omit for stdout)')

    vy_parser = subparsers.add_parser(
        'validate-yaml', help=validate_yaml.__doc__)

    args = parser.parse_args()

    if args.command == 'list-region-tags':
        list_region_tags(
            args.root_dir,
            args.detected,
            args.undetected,
            args.show_test_counts,
            args.show_filenames)
    elif args.command == 'list-source-files':
        list_source_files(args.root_dir, args.tested_files)
    elif args.command == 'inject-snippet-mapping':
        inject_snippet_mapping(
            args.root_dir, sys.stdin.readlines(), args.output_file)
    elif args.command == 'validate-yaml':
        validate_yaml(args.root_dir)
