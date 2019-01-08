from pykwalify.errors import SchemaError
from yaml import YAMLError

from ..configurator import load_config
from ..ui import UIError, escape_braces

from .rebench_test_case import ReBenchTestCase


class UITest(ReBenchTestCase):

    def test_escape_braces(self):
        str_with_braces = "{ddd"
        e_str = escape_braces(str_with_braces)
        self.assertEqual(str_with_braces, e_str.format())

        str_with_braces = "{ddd}"
        e_str = escape_braces(str_with_braces)
        self.assertEqual(str_with_braces, e_str.format())

        str_with_braces = "{{ddd}} {{eee }} }} aaa {}"
        e_str = escape_braces(str_with_braces)
        self.assertEqual(str_with_braces, e_str.format())

    def test_missing_file(self):
        with self.assertRaises(UIError) as err:
            load_config("--file-that-does-not-exist")
        self.assertIsInstance(err.exception.source_exception, IOError)

    def test_config_not_validating(self):
        with self.assertRaises(UIError) as err:
            load_config(self._path + '/broken-schema.conf')
        self.assertIsInstance(err.exception.source_exception, SchemaError)

    def test_config_not_proper_yaml(self):
        with self.assertRaises(UIError) as err:
            load_config(self._path + '/broken-yaml.conf')
        self.assertIsInstance(err.exception.source_exception, YAMLError)
