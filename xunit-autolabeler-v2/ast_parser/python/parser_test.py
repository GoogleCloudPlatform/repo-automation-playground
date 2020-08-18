from ast_parser.python.constants import FLASK_DEFAULT_METHODS
from ast_parser.python import source_parser, test_parser

from os import path
import pytest
import unittest


TEST_DATA_ROOT = path.join(path.dirname(__file__), 'test_data')


class ParserSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init(self):
        self.parser_path = path.join(TEST_DATA_ROOT, 'parser')

    def test_direct_invocation_parser(self):
        source_path = path.join(self.parser_path, 'http/http_main.py')

        source_methods = source_parser.get_top_level_methods(source_path)
        source_methods = [x for x in source_methods if
                          x.drift['parser'] == 'direct_invocation']

        assert len(source_methods) == 9
        method = source_methods[0]
        assert hasattr(method, 'drift')
        assert method.drift['name'] == 'hello_get'

    def test_webapp2_parser(self):
        source_path = path.join(self.parser_path, 'webapp2/webapp2_main.py')

        source_methods = source_parser.get_top_level_methods(source_path)
        source_methods = [x for x in source_methods if
                          x.drift['parser'] == 'webapp2_router']

        assert len(source_methods) == 3

        method = source_methods[-1]
        assert hasattr(method, 'drift')
        assert method.drift['url'] == '/sign'

        assert method.drift['http_method'] == 'post'

    def test_flask_router_parser(self):
        source_path = path.join(self.parser_path, 'flask/flask_main.py')

        source_methods = source_parser.get_top_level_methods(source_path)
        source_methods = [x for x in source_methods if
                          x.drift['parser'] == 'flask_router']

        # direct_invocation parser should ignore Flask methods
        assert len(source_methods) == 1

        method = source_methods[0]
        assert hasattr(method, 'drift')
        assert method.drift['url'] == '/'

        # Flask has a default HTTP method set for routes that don't specify any
        assert method.drift['http_methods'] == FLASK_DEFAULT_METHODS


class ParserEdgeCaseTests(unittest.TestCase):
    def test_prohibits_identically_named_tests(self):
        test_path = path.join(
            TEST_DATA_ROOT, 'duplicate_test_names/class_wrapped_test.py')

        with self.assertRaises(ValueError) as err:
            test_parser.get_test_methods(test_path)

        assert 'must be unique' in str(err.exception)

    def test_flask_router_parser(self):
        source_path = path.join(TEST_DATA_ROOT, 'parser/flask/flask_main.py')

        source_methods = source_parser.get_top_level_methods(source_path)
        source_methods = [x for x in source_methods if
                          x.drift['parser'] == 'flask_router']

        # direct_invocation parser should ignore Flask methods
        assert len(source_methods) == 1

        method = source_methods[0]
        assert hasattr(method, 'drift')
        assert method.drift['url'] == '/'

        # Flask uses default HTTP methods for routes that don't specify any
        assert method.drift['http_methods'] == FLASK_DEFAULT_METHODS
