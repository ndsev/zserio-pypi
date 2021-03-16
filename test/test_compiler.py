import unittest
import os
import distutils.dir_util
import importlib
import subprocess

from zserio.compiler import JavaNotFoundException, run_compiler, generate

class CompilerTest(unittest.TestCase):

    def test_run_compiler(self):
        completed_process = run_compiler(["--help"])
        self.assertEqual(0, completed_process.returncode)

        completed_process = run_compiler([])
        self.assertEqual(1, completed_process.returncode)

    def test_java_home_notfound(self):
        java_home_exists = "JAVA_HOME" in os.environ
        if java_home_exists:
            java_home = os.environ["JAVA_HOME"]
        os.environ["JAVA_HOME"] = "wrong_path"
        with self.assertRaises(JavaNotFoundException):
            run_compiler(["--help"])
        if java_home_exists:
            os.environ["JAVA_HOME"] = java_home
        else:
            del os.environ["JAVA_HOME"]

    def test_java_on_path_notfound(self):
        java_home_exists = "JAVA_HOME" in os.environ
        if java_home_exists:
            java_home = os.environ["JAVA_HOME"]
            del os.environ["JAVA_HOME"]
        path = os.environ["PATH"]
        os.environ["PATH"] = ""
        with self.assertRaises(JavaNotFoundException):
            run_compiler(["--help"])
        os.environ["PATH"] = path
        if java_home_exists:
            os.environ["JAVA_HOME"] = java_home

    def test_generate_compilation_failure(self):
        with self.assertRaises(subprocess.CalledProcessError):
            generate("invalid_source.zs")

    def test_generate_default_package(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "default_package")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_default_package")
        test_zs_dir = os.path.join(build_dir, "zs")
        distutils.dir_util.copy_tree(zs_dir, test_zs_dir)
        gen_dir = os.path.join(build_dir, "gen")
        main_zs_file = "structure_default.zs"
        current_dir = os.getcwd()
        os.chdir(test_zs_dir)
        api = generate(main_zs_file, is_default_package = True, gen_dir = gen_dir)
        os.chdir(current_dir)

        test_structure = api.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    def test_generate_main_zs_with_path(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "main_zs_with_path")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_main_zs_with_path")
        gen_dir = os.path.join(build_dir, "gen")
        main_zs_file = os.path.join("company", "main", "structure_with_path.zs")
        company_api = generate(main_zs_file, zs_dir = zs_dir, gen_dir = gen_dir)

        test_structure = company_api.main.structure_with_path.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("company.main.structure_with_path.test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    def test_generate_main_zs_without_path(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "main_zs_without_path")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_main_zs_without_path")
        gen_dir = os.path.join(build_dir, "gen")
        main_zs_file = "structure_without_path.zs"
        api = generate(main_zs_file, zs_dir = zs_dir, gen_dir = gen_dir)

        test_structure = api.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("structure_without_path.test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    def test_generate_top_level_package(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "main_zs_without_path")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_top_level_package")
        gen_dir = os.path.join(build_dir, "gen")
        main_zs_file = "structure_without_path.zs"
        # "top_level_package.main" must be unique not to mix paths in python system path
        top_level_package_api = generate(main_zs_file, zs_dir = zs_dir, gen_dir = gen_dir,
                                         top_level_package = "top_level_package.main",
                                         extra_args = ["-withoutPubsubCode", "-withoutServiceCode"])

        test_structure = top_level_package_api.main.structure_without_path.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("top_level_package.main.structure_without_path.test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    def test_generate_without_gen_dir(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "main_zs_without_path")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_without_gen_dir")
        test_zs_dir = os.path.join(build_dir, "zs")
        distutils.dir_util.copy_tree(zs_dir, test_zs_dir)
        main_zs_file = "structure_without_path.zs"
        current_dir = os.getcwd()
        os.chdir(test_zs_dir)
        # "without_gen_dir.main" must be unique not to mix paths in python system path
        without_gen_dir_api = generate(main_zs_file, top_level_package = "without_gen_dir.main")
        os.chdir(current_dir)

        test_structure = without_gen_dir_api.main.structure_without_path.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("without_gen_dir.main.structure_without_path.test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    def test_generate_without_gen_dir_with_zs_dir(self):
        zs_dir = os.path.join(self._get_test_zs_dir(), "main_zs_without_path")
        build_dir = os.path.join(self._get_build_test_dir(), "generate_without_gen_dir_with_zs_dir")
        test_zs_dir = os.path.join(build_dir, "zs")
        distutils.dir_util.copy_tree(zs_dir, test_zs_dir)
        main_zs_file = "structure_without_path.zs"
        api = generate(main_zs_file, zs_dir=test_zs_dir)

        test_structure = api.TestStructure()
        self.assertEqual(0, test_structure.value)

        test_module = importlib.import_module("structure_without_path.test_structure")
        imported_test_structure = test_module.TestStructure()
        self.assertEqual(0, imported_test_structure.value)

    @staticmethod
    def _get_build_test_dir():
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_zs_dir = os.path.join(test_dir, "..", "build", "test")

        return test_zs_dir

    @staticmethod
    def _get_test_zs_dir():
        test_dir = os.path.dirname(os.path.abspath(__file__))
        zs_dir = os.path.join(test_dir, "zs")

        return zs_dir
