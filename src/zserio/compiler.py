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

def run_compiler(cmd_args: typing.List[str], *, capture_output = True,
                 check_exit_code = False) -> subprocess.CompletedProcess:
    """
    Runs zserio compiler using jar file stored in the zserio pip package.

    :param cmd_args: List of strings which represents zserio command line arguments.
    :param capture_output: True to capture stdout and stderr.
    :param check_exit_code: True to raise a subprocess.CalledProcessError exception if zserio compiler fails.
    :returns: subprocess.CompletedProcess instance returned from subprocess.run() method.
    :raises JavaNotFoundException: If Java is not found.
    """

    java_executable = _find_java_executable()
    zserio_command = [java_executable, "-cp", ZSERIO_JAR_FILE, "zserio.tools.ZserioToolPython"]
    zserio_command[len(zserio_command):] = cmd_args

    return subprocess.run(zserio_command, capture_output = capture_output, check = check_exit_code, text = True)

def generate(main_zs_file: str, *, is_default_package: bool = False, zs_dir: str = None, gen_dir: str = None,
             top_level_package: str = None, extra_args: typing.List[str] = None) -> typing.Any:
    """
    Generates Python sources by running zserio compiler.

    The generated Python package API will be automatically imported and returned as a result.

    The generated Python package will be as well automatically added to the pythonpath.

    If a directory where to generate Python sources is not specified, Python sources will be generated into
    the default directory `.zserio_python_package`. This default directory is created either in specified zserio
    source file directory or in directory where main zserio source file is located.

    Example using implicit imported API:
        ```
        appl_api = generate("test/structure.zs", zs_dir = "zs", gen_dir = "gen", top_level_package = "appl")
        test_structure = appl_api.test.structure.TestStructure()
        ```

    Example using explicit import:
        ```
        generate("test/structure.zs", zs_dir = "zs", gen_dir = "gen", top_level_package = "appl")
        structure_module = importlib.import_module("appl.test.structure.TestStructure")
        test_structure = structure_module.TestStructure()
        ```

    :param main_zs_file: Main zserio source file to compile.
    :param is_default_package: True if Zserio source file is default package.
    :param zs_dir: Zserio source file directory ('-src' command line option).
    :param gen_dir: Directory where to generate Python sources ('-python <dir>' command line option).
    :param top_level_package: Top level package for compilation ('-setTopLevelPackage <pkg>' cmd line option).
    :param extra_args: List of extra command line options.
    :returns: Imported api module of generated Python sources.
    :raises: JavaNotFoundException: If Java is not found.
    :raises: subprocess.CalledProcessError: If calling zserio compiler process failed.
    """

    cmd_args = [main_zs_file]
    if zs_dir is not None:
        cmd_args += ["-src", zs_dir]

    if gen_dir is not None:
        python_dir = gen_dir
    elif zs_dir is not None:
        python_dir = os.path.join(zs_dir, ZSERIO_DEFAULT_GEN_DIR_NAME)
    else:
        python_dir = os.path.join(os.path.dirname(os.path.abspath(main_zs_file)), ZSERIO_DEFAULT_GEN_DIR_NAME)
    cmd_args += ["-python", python_dir]

    if top_level_package is not None:
        cmd_args += ["-setTopLevelPackage", top_level_package]
    if extra_args is not None:
        cmd_args += extra_args

    run_compiler(cmd_args, check_exit_code = True)

    return _import_api_module(main_zs_file, is_default_package, python_dir, top_level_package)

def _find_java_executable() -> str:
    java_home = os.getenv("JAVA_HOME", None)
    if java_home:
        java_path = os.path.join(java_home, "bin")
        java_executable = shutil.which("java", path=java_path)
        if not java_executable:
            raise JavaNotFoundException("compiler: Java not found (wrong ${JAVA_HOME})")
    else:
        java_executable = shutil.which("java")
        if not java_executable:
            raise JavaNotFoundException("compiler: Java not found (checked ${JAVA_HOME} and ${PATH})")

    return java_executable

def _import_api_module(main_zs_file: str, is_default_package: bool, python_dir: str,
                       top_level_package: str = None) -> typing.Any:
    abs_python_dir = os.path.abspath(python_dir)
    sys.path.append(abs_python_dir)

    api_module_path = "api"
    if not is_default_package:
        # we need to find out the first left most part of path
        if top_level_package is not None:
            api_module_path_prefix = top_level_package.split(".")[0]
        else:
            main_zs_without_ext = os.path.splitext(main_zs_file)[0]
            api_module_path_prefix = main_zs_without_ext.split(os.sep)[0]

        api_module_path = api_module_path_prefix + "." + api_module_path

    return importlib.import_module(api_module_path)

ZSERIO_JAR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compiler", "zserio.jar")
ZSERIO_DEFAULT_GEN_DIR_NAME = ".zserio_python_package"
