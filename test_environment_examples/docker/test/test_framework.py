import json
import logging
import os
import re
import sys
from importlib import import_module
from typing import List, Dict

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULT_TAG = os.getenv("RESULT_TAG", "<RESULT_TAG>")
ERROR_TAG = os.getenv("ERROR_TAG", "<ERROR_TAG>")


def print_result(result):
    print()  # make sure start with a new line
    print(RESULT_TAG + json.dumps(result))


def print_error_message(msg: str):
    print()  # make sure start with a new line
    print(ERROR_TAG + msg, file=sys.stderr)


def dict_set_path(d: dict, path: str, value):
    obj = d
    segments = path.split('.')
    for segment in segments[:-1]:
        sub_obj = obj.get(segment)
        if sub_obj is None:
            obj[segment] = sub_obj = {}
        obj = sub_obj
    obj[segments[-1]] = value


class TestConfigError(Exception):
    pass


class TestUnit:
    METHOD_PATH_FORMAT = re.compile(r'^(\w+\.)?\w+$')
    RESULT_PATH_FORMAT = re.compile(r'^(\w+\.)*\w+$')

    def __init__(self, name: str, endpoint, require_methods: List[str] = None, result_path: str = None,
                 add_to_total: bool = True):
        self.name = name
        self.endpoint = endpoint
        self.require_methods = require_methods or []
        self.result_path = result_path if result_path is not None else name  # replace it with name if it is None
        self.add_to_total = add_to_total

        if not self.name:
            raise TestConfigError('Test unit name must not be empty')
        if endpoint is None:
            raise TestConfigError('Test unit endpoint must not be empty')
        for method_path in self.require_methods:
            if not method_path:
                raise TestConfigError('Required method path must not be empty')
            if not self.METHOD_PATH_FORMAT.match(method_path):
                raise TestConfigError('Invalid format in required method path')

    def run(self, modules: dict):
        return self.endpoint(**modules)


class TestSuite:
    MODULE_ALIAS_FORMAT = re.compile(r'^\w+$')
    MODULE_PATH_FORMAT = re.compile(r'^(\w+\.)*\w+$')

    def __init__(self, require_modules: Dict[str, str] = None, total_path: str = 'Total'):
        """
        A TestSuite contains a list of TestUnits.
        :param require_modules: Required modules that will be loaded for testing. It must be a dict where each key is an
        alias name for a module and each value is the corresponding module name.
        :param total_path: The path in which the total result will be saved in the result object. A path can  be a
        dot-separated string, e.g. 'Marks.Total'. By default, it is 'Total'. If specify it as None or empty string, the
        total result will not appear in the result object.
        """
        self._units = []
        self._require_modules = require_modules or {}
        self._total_path = total_path

        self._loaded_modules = {}

        for alias, module_path in self._require_modules.items():
            if not alias:
                raise TestConfigError('Required module alias must not be empty')
            if not module_path:
                raise TestConfigError('Required module path must not be empty')
            if not self.MODULE_ALIAS_FORMAT.match(alias):
                raise TestConfigError('Invalid format in required module alias: %s' % alias)
            if not self.MODULE_PATH_FORMAT.match(module_path):
                raise TestConfigError('Invalid format in required module path: %s' % module_path)
        if total_path and not TestUnit.RESULT_PATH_FORMAT.match(total_path):
            raise TestConfigError('Invalid format in total_path: %s' % total_path)

    def add_unit(self, unit: TestUnit):
        for _unit in self._units:
            if _unit.name == unit.name:
                raise TestConfigError('Duplicate name: "%s"' % unit.name)
            if _unit.endpoint == unit.endpoint:
                raise TestConfigError('Duplicate endpoint: "%s"' % unit.endpoint.__name__)
            if _unit.endpoint.__name__ == unit.endpoint.__name__:
                raise TestConfigError('Duplicate test endpoint name: "%s"' % unit.endpoint.__name__)
            if _unit.result_path == unit.result_path:
                raise TestConfigError('Duplicate result path: "%s"' % unit.result_path)
        self._units.append(unit)

    def test(self, name: str, require_methods: List[str] = None, result_path: str = None, add_to_total: bool = True):
        """
        Create a TestUnit with the wrapped function as the endpoint and register it in this TestSuite.
        :param name: Name of the new test unit.
        :param require_methods: A list of paths of required methods. If there are exactly one required module in this
        test suite, each path can be just the method names. Otherwise, each path must start with the alias name of a
        required module, followed by a dot character, then with the method name, e.g. 'submission.my_func'.
        :param result_path: The path in which the result of this unit should be saved in the result object. A path can
        be a dot-separated string, e.g. 'ProblemA.Question3'. If it is None, which is also the default value, it will be
        replaced with the name of this test unit. If it is an empty string, then the result of this unit will not appear
        in the result object.
        :param add_to_total: If this is true, the result will be added to the total, no matter if this result appear in
        the result object or not, as long as this result is an integer or float number.
        :return: A decorator function
        """

        def decorator(f):
            self.add_unit(TestUnit(name, f, require_methods=require_methods, result_path=result_path,
                                   add_to_total=add_to_total))

        return decorator

    def run(self):
        """
        Run the TestUnits one by one in the order of the registration. If any of the required modules is not loaded, an
        exception will be raised and no TestUnit will be started. For a TestUnit, if any of the required methods is not
        found, this TestUnit will be skipped and the following TestUnits would be started. If any of the TestUnit throws
        an exception, the following TestUnits would still be started.
        """
        # load required modules
        for alias, module_path in self._require_modules.items():
            try:
                self._loaded_modules[alias] = import_module(module_path)
                # it is safe to report some error messages of some known types here as we have not provided any data to
                # the imported modules.
                # The details of the exception are printed to the stderr but not reported (only appear in stderr.txt
                # output file).
                # The test units should not run if exception occurred here.
            except ImportError as e:
                print_error_message('ImportError: %s' % e.name)
                raise
            except SyntaxError as e:
                print_error_message('SyntaxError: line %d offset %d' % (e.lineno, e.offset))
                raise
            except Exception:
                print_error_message('Failed to load module')
                raise

        # run tests
        total = 0
        results = {}
        for unit in self._units:
            methods_not_found = []
            modules = {}
            for method_path in unit.require_methods:
                segments = method_path.split('.', 1)
                if len(segments) > 1:
                    alias, method_name = segments
                else:  # only method name provided
                    # this is valid only if only one module required by the test suite
                    method_name = segments[0]
                    if len(self._require_modules) != 1:
                        msg = 'Missing module alias for required method: %s' % method_name
                        print_error_message(msg)
                        raise NameError(msg)
                    alias = list(self._loaded_modules.keys())[0]

                module = self._loaded_modules.get(alias)
                if module is None:
                    msg = 'Module not found for alias: %s' % alias
                    print_error_message(msg)
                    raise NameError(msg)

                if not hasattr(module, method_name):
                    methods_not_found.append(method_name)
                modules[alias] = module

            if methods_not_found:
                # skip running this test unit if any of the required methods do not exist
                result = 'Not Implemented'
                logger.info('Skipping test unit %s as methods not implemented: %s', unit.name,
                            ', '.join(methods_not_found))
            else:
                logger.info('Running test unit %s', unit.name)
                # noinspection PyBroadException
                try:
                    result = unit.run(modules)
                    logger.info('Test unit %s finished: %s', unit.name, result)
                    # DO NOT provide ANY error messages here as we have provided the testing data to the target methods
                    # and the students can deliberately throw an Exception with confidential data.
                except Exception:
                    result = 'Exception Occurred'
                    # The details of the exception are printed to the stderr but not reported (only appear in stderr.txt
                    # output file).
                    logger.exception('Exception occurred in test unit %s', unit.name)
                    # Continue running the following test units

            if unit.result_path:
                dict_set_path(results, unit.result_path, result)
            if unit.add_to_total and type(result) in {int, float}:
                total += result
        if self._total_path:
            dict_set_path(results, self._total_path, total)

        print_result(results)
