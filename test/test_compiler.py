import unittest
import os
import distutils.dir_util
import importlib
import subprocess

from zserio.compiler import JavaNotFoundException, runCompiler, generatePython, generate

class CompilerTest(unittest.TestCase):

    def testRunCompiler(self):
        completedProcess = runCompiler(["--help"])
        self.assertEqual(0, completedProcess.returncode)

        completedProcess = runCompiler([])
        self.assertEqual(1, completedProcess.returncode)

    def testJavaHomeNotFound(self):
        javaHomeExists = "JAVA_HOME" in os.environ
        if javaHomeExists:
            javaHome = os.environ["JAVA_HOME"]
        os.environ["JAVA_HOME"] = "wrong_path"
        with self.assertRaises(JavaNotFoundException):
            runCompiler(["--help"])
        if javaHomeExists:
            os.environ["JAVA_HOME"] = javaHome
        else:
            del os.environ["JAVA_HOME"]

    def testJavaOnPathNotFound(self):
        javaHomeExists = "JAVA_HOME" in os.environ
        if javaHomeExists:
            javaHome = os.environ["JAVA_HOME"]
            del os.environ["JAVA_HOME"]
        path = os.environ["PATH"]
        os.environ["PATH"] = ""
        with self.assertRaises(JavaNotFoundException):
            runCompiler(["--help"])
        os.environ["PATH"] = path
        if javaHomeExists:
            os.environ["JAVA_HOME"] = javaHome

    def testGenerateCompilationFailure(self):
        with self.assertRaises(subprocess.CalledProcessError):
            generatePython("invalid_source.zs")

    def testGeneratePythonDefaultPackage(self):
        zsDir = os.path.join(self._getTestZsDir(), "default_package")
        buildDir = os.path.join(self._getBuildTestDir(), "generate_python_default_package")
        testZsDir = os.path.join(buildDir, "zs")
        distutils.dir_util.copy_tree(zsDir, testZsDir)
        genDir = os.path.join(buildDir, "gen")
        mainZsFile = "structure_default.zs"
        currentDir = os.getcwd()
        os.chdir(testZsDir)
        api = generatePython(mainZsFile, isDefaultPackage = True, genDir = genDir)
        os.chdir(currentDir)

        testStructure = api.TestStructure()
        self.assertEqual(0, testStructure.getValue())

        testStructureModule = importlib.import_module("TestStructure")
        importedTestStructure = testStructureModule.TestStructure()
        self.assertEqual(0, importedTestStructure.getValue())

    def testGeneratePythonMainZsWithPath(self):
        zsDir = os.path.join(self._getTestZsDir(), "main_zs_with_path")
        buildDir = os.path.join(self._getBuildTestDir(), "generate_python_main_zs_with_path")
        genDir = os.path.join(buildDir, "gen")
        mainZsFile = os.path.join("company", "main", "structure_with_path.zs")
        companyApi = generatePython(mainZsFile, zsDir = zsDir, genDir = genDir)

        testStructure = companyApi.main.structure_with_path.TestStructure()
        self.assertEqual(0, testStructure.getValue())

        testStructureModule = importlib.import_module("company.main.structure_with_path.TestStructure")
        importedTestStructure = testStructureModule.TestStructure()
        self.assertEqual(0, importedTestStructure.getValue())

    def testGeneratePythonMainZsWithoutPath(self):
        zsDir = os.path.join(self._getTestZsDir(), "main_zs_without_path")
        buildDir = os.path.join(self._getBuildTestDir(), "generate_python_main_zs_without_path")
        genDir = os.path.join(buildDir, "gen")
        mainZsFile = "structure_without_path.zs"
        api = generatePython(mainZsFile, zsDir = zsDir, genDir = genDir)

        testStructure = api.TestStructure()
        self.assertEqual(0, testStructure.getValue())

        structureModule = importlib.import_module("structure_without_path.TestStructure")
        importedTestStructure = structureModule.TestStructure()
        self.assertEqual(0, importedTestStructure.getValue())

    def testGeneratePythonTopLevelPackage(self):
        zsDir = os.path.join(self._getTestZsDir(), "main_zs_without_path")
        buildDir = os.path.join(self._getBuildTestDir(), "generate_python_top_level_package")
        genDir = os.path.join(buildDir, "gen")
        mainZsFile = "structure_without_path.zs"
        # "top_level_package.main" must be unique not to mix paths in python system path
        topLevelPackageApi = generatePython(mainZsFile, zsDir = zsDir, genDir = genDir,
                                            topLevelPackage = "top_level_package.main",
                                            extraArgs = ["-withoutPubsubCode", "-withoutServiceCode"])

        testStructure = topLevelPackageApi.main.structure_without_path.TestStructure()
        self.assertEqual(0, testStructure.getValue())

        structureModule = importlib.import_module("top_level_package.main.structure_without_path.TestStructure")
        importedTestStructure = structureModule.TestStructure()
        self.assertEqual(0, importedTestStructure.getValue())

    def testGeneratePythonWithoutGenDir(self):
        zsDir = os.path.join(self._getTestZsDir(), "main_zs_without_path")
        buildDir = os.path.join(self._getBuildTestDir(), "generate_python_without_gen_dir")
        testZsDir = os.path.join(buildDir, "zs")
        distutils.dir_util.copy_tree(zsDir, testZsDir)
        mainZsFile = "structure_without_path.zs"
        currentDir = os.getcwd()
        os.chdir(testZsDir)
        # "without_gen_dir.main" must be unique not to mix paths in python system path
        withoutGenDirApi = generatePython(mainZsFile, topLevelPackage = "without_gen_dir.main")
        os.chdir(currentDir)

        testStructure = withoutGenDirApi.main.structure_without_path.TestStructure()
        self.assertEqual(0, testStructure.getValue())

        testStructureModule = importlib.import_module(
            "without_gen_dir.main.structure_without_path.TestStructure")
        importedTestStructure = testStructureModule.TestStructure()
        self.assertEqual(0, importedTestStructure.getValue())

    def testGenerate(self):
        zsDir = os.path.join(self._getTestZsDir(), "main_zs_without_path")
        buildDir = os.path.join(self._getBuildTestDir(), "generate")
        testZsDir = os.path.join(buildDir, "zs")
        distutils.dir_util.copy_tree(zsDir, testZsDir)
        zsFile = os.path.join(testZsDir, "structure_without_path.zs")
        generate(zsFile, "generate")

        testStructureModule = importlib.import_module("generate.structure_without_path.TestStructure")
        testStructure = testStructureModule.TestStructure()
        self.assertEqual(0, testStructure.getValue())

    @staticmethod
    def _getBuildTestDir():
        testDir = os.path.dirname(os.path.abspath(__file__))
        testZsDir = os.path.join(testDir, "..", "build", "test")

        return testZsDir

    @staticmethod
    def _getTestZsDir():
        testDir = os.path.dirname(os.path.abspath(__file__))
        zsDir = os.path.join(testDir, "zs")

        return zsDir
