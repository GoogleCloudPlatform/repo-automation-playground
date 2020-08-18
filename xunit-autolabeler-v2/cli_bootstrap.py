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
import sys

from ast_parser.core import cli

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command')
    parser.add_argument(
        'repo_json', help='Language-agnostic JSON parser output')
    parser.add_argument(
        'root_dir', help='Root directory')
    parser.add_argument(
        '--output_file',
        help='File to write output to. Omit to use stdout.',
        required=False)

    lrt_parser = subparsers.add_parser(
        'list-region-tags', help=cli.list_region_tags.__doc__)

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
        'list-source-files', help=cli.list_source_files.__doc__)
    lsf_parser.add_argument(
        '--tested_files', '-t',
        type=str,
        default='*',
        choices=['all', 'some', 'none', '*'],
        help='Display files where ({all, some, no}) methods are tested)')

    isj_parser = subparsers.add_parser(
        'inject-snippet-mapping', help=cli.inject_snippet_mapping.__doc__)

    vy_parser = subparsers.add_parser(
        'validate-yaml', help=cli.validate_yaml.__doc__)

    args = parser.parse_args()

    if args.command == 'list-region-tags':
        cli.list_region_tags(
            args.repo_json,
            args.root_dir,
            args.detected,
            args.undetected,
            args.show_test_counts,
            args.show_filenames, args.output_file)
    elif args.command == 'list-source-files':
        cli.list_source_files(args.repo_json, args.root_dir, args.tested_files, args.output_file)
    elif args.command == 'inject-snippet-mapping':
        cli.inject_snippet_mapping(args.repo_json, args.root_dir, sys.stdin.readlines(), args.output_file)
    elif args.command == 'validate-yaml':
        cli.validate_yaml(args.repo_json, args.root_dir)
