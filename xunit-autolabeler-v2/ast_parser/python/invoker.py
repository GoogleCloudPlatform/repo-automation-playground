import json
import os

from lib import file_utils
from python import source_parser, test_parser
from python.constants import TEST_FILE_MARKER


def __parse_source(source_path):
    source_methods = source_parser.get_top_level_methods(source_path)
    return [x for x in source_methods]


def __parse_test(test_path, source_methods):
    test_methods = test_parser.get_test_methods(test_path)
    test_method_map = test_parser.get_test_to_method_map(test_methods)

    test_parser.add_method_names_to_tests(source_methods, test_method_map)


def get_json_for_dir(root_dir):
    python_files = file_utils.get_python_files(root_dir)

    source_methods = []
    source_files = [f for f in python_files if TEST_FILE_MARKER not in f]

    for f in source_files:
        source_methods += __parse_source(f)

    test_files = [f for f in python_files if TEST_FILE_MARKER in f]

    for f in test_files:
        __parse_test(f, source_methods)

    for m in source_methods:
        m.drift['source_path'] = os.path.relpath(
            m.drift['source_path'], root_dir)

    return json.dumps([m.drift for m in source_methods])
