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

    if not show_detected and show_test_counts:
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
def inject_snippet_mapping(root_dir, stdin_lines):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_dir(root_dir)

    xunit_tree = etree.fromstring("".join(stdin_lines))

    for x in xunit_tree.findall('.//testcase'):
        test_key = (x.attrib['classname'].split('.')[-1], x.attrib['name'])
        for m in source_methods:
            m_test_keys = [(os.path.splitext(os.path.basename(t[0]))[0], t[1])
                           for t in m.drift['test_methods']]

            if test_key in m_test_keys:
                # Inject region tags into customProperty XML attribute
                existing_tag_str = x.attrib.get('customProperty')
                existing_tag_list = existing_tag_str.split(',') if existing_tag_str else []

                deduped_tag_list = list(set(existing_tag_list + m.drift['region_tags']))

                x.set('customProperty', ','.join(deduped_tag_list))

    print(etree.tostring(xunit_tree).decode())


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
    lrt_parser.add_argument(
        '--detected', '-d',
        type=bool,
        default=True,
        help='Display region tags detected by the AST parser')

    lrt_parser.add_argument(
        '--undetected', '-u',
        type=bool,
        default=True,
        help='Display region tags NOT detected by the AST parser')

    lrt_parser.add_argument(
        '--show_test_counts', '-c',
        type=bool,
        default=True,
        help='Display region tags NOT detected by the AST parser')

    lrt_parser.add_argument(
        '--show_filenames', '-f',
        type=bool,
        default=True,
        help='Display region tags NOT detected by the AST parser')

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
        inject_snippet_mapping(args.root_dir, sys.stdin.readlines())
    elif args.command == 'validate-yaml':
        validate_yaml(args.root_dir)
