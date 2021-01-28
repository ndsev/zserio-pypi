"""
The module runs zserio compiler and provides convenient method to generate Python sources.
"""

import os
import subprocess
import sys
import shutil
import importlib
import typing

class JavaNotFoundException(Exception):
    """
    Exception thrown if Java executable has been not found.
    """

def runCompiler(cmdArgs: typing.List[str], *, captureOutput = True,
                checkExitCode = False) -> subprocess.CompletedProcess:
    """
    Runs zserio compiler using jar file stored in the zserio pip package.

    :param cmdArgs: List of strings which represents zserio command line arguments.
    :param captureOutput: True to capture stdout and stderr.
    :param checkExitCode: True to raise a subprocess.CalledProcessError exception if the zserio compiler fails.
    :returns: subprocess.CompletedProcess instance returned from subprocess.run() method.
    :raises JavaNotFoundException: If Java is not found.
    """

    javaExectuable = _findJavaExecutable()
    zserioCommand = [javaExectuable, "-jar", ZSERIO_JAR_FILE]
    zserioCommand[len(zserioCommand):] = cmdArgs

    return subprocess.run(zserioCommand, capture_output = captureOutput, check = checkExitCode, text = True)

def generatePython(mainZsFile: str, *, isDefaultPackage: bool = False, zsDir: str = None, genDir: str = None,
                   topLevelPackage: str = None, extraArgs: typing.List[str] = None) -> typing.Any:
    """
    Generates Python sources by running zserio compiler.

    The generated Python package API will be automatically imported and returned as a result.

    The generated Python package will be as well automatically added to the pythonpath.

    If a directory where to generate Python sources is not specified, Python sources will be generated into
    the default directory `.zserio_python_package`. This default directory is created either in specified zserio
    source file directory or in directory where main zserio source file is located.

    Example using implicit imported API:
        ```
        applApi = generatePython("test/structure.zs", zsDir = "zs", genDir = "gen", topLevelPackage = "appl")
        testStructure = applApi.test.structure.TestStructure()
        ```

    Example using explicit import:
        ```
        generatePython("test/structure.zs", zsDir = "zs", genDir = "gen", topLevelPackage = "appl")
        structureModule = importlib.import_module("appl.test.structure.TestStructure")
        testStructure = structureModule.TestStructure()
        ```

    :param mainZsFile: Main zserio source file to compile.
    :param isDefaultPackage: True if Zserio source file is default package.
    :param zsDir: Zserio source file directory ('-src' command line option).
    :param genDir: Directory where to generate Python sources ('-python <dir>' command line option).
    :param topLevelPackage: Top level package for compilation ('-setTopLevelPackage <pkg>' command line option).
    :param extraArgs: List of extra command line options.
    :returns: Imported api module of generated Python sources.
    :raises: JavaNotFoundException: If Java is not found.
    :raises: subprocess.CalledProcessError: If calling zserio compiler process failed.
    """

    cmdArgs = [mainZsFile]
    if zsDir is not None:
        cmdArgs += ["-src", zsDir]

    if genDir is not None:
        pythonDir = genDir
    elif zsDir is not None:
        pythonDir = os.path.join(zsDir, ZSERIO_DEFAULT_GEN_DIR_NAME)
    else:
        pythonDir = os.path.join(os.path.dirname(os.path.abspath(mainZsFile)), ZSERIO_DEFAULT_GEN_DIR_NAME)
    cmdArgs += ["-python", pythonDir]

    if topLevelPackage is not None:
        cmdArgs += ["-setTopLevelPackage", topLevelPackage]
    if extraArgs is not None:
        cmdArgs += extraArgs

    runCompiler(cmdArgs, checkExitCode = True)

    return _importApiModule(mainZsFile, isDefaultPackage, pythonDir, topLevelPackage)

def generate(srcFile: str = "", moduleName: str = "") -> None:
    """
    Generates Python sources by running zserio compiler given main zserio source with full path.

    The generated Python package will be added automatically to the pythonpath.

    This method is DEPRECATED and will be removed in the next release! Please note, that this method
    works correctly only if main zserio source package contains only one package id (see example below)!

    Example of main zserio file `structure.zs` which does not compile by this method:
        ```
        package test.structure;

        struct TestStructure
        {
            int32 value;
        };
        ```

    The `moduleName` argument allows to set a top-level python module name,
    under which the generated sources will be placed.

    Examples:

        With top-level package:
            ```
            import zserio
            zserio.generate("myfile.zs", "mypackage")
            from mypackage.myfile import *
            ```

        Without top-level package:
            ```
            import zserio
            zserio.generate("myfile.zs")
            from myfile import *
            ```

    :param srcFile: Source zserio file.
    :param moduleName: (Optional) Top-level package directory name.
    """

    mainZsFile = os.path.basename(srcFile)
    zsDir = os.path.dirname(os.path.abspath(srcFile))

    generatePython(mainZsFile, zsDir = zsDir, topLevelPackage = moduleName)

def _findJavaExecutable() -> str:
    javaHome = os.getenv("JAVA_HOME", None)
    if javaHome:
        javaPath = os.path.join(javaHome, "bin")
        javaExecutable = shutil.which("java", path=javaPath)
        if not javaExecutable:
            raise JavaNotFoundException("compiler: Java not found (wrong ${JAVA_HOME})")
    else:
        javaExecutable = shutil.which("java")
        if not javaExecutable:
            raise JavaNotFoundException("compiler: Java not found (checked ${JAVA_HOME} and ${PATH})")

    return javaExecutable

def _importApiModule(mainZsFile: str, isDefaultPackage: bool, pythonDir: str,
                     topLevelPackage: str = None) -> typing.Any:
    absPythonDir = os.path.abspath(pythonDir)
    sys.path.append(absPythonDir)

    apiModulePath = "api"
    if not isDefaultPackage:
        # we need to find out the first left most part of path
        if topLevelPackage is not None:
            apiModulePathPrefix = topLevelPackage.split(".")[0]
        else:
            mainZsWithoutExt = os.path.splitext(mainZsFile)[0]
            apiModulePathPrefix = mainZsWithoutExt.split(os.sep)[0]

        apiModulePath = apiModulePathPrefix + "." + apiModulePath

    return importlib.import_module(apiModulePath)

ZSERIO_JAR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compiler", "zserio.jar")
ZSERIO_DEFAULT_GEN_DIR_NAME = ".zserio_python_package"
