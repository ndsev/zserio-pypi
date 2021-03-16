import setuptools
import json
import urllib.request
import zipfile
import io
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUILD_DIR = os.path.join(ROOT_DIR, "build")
BUILD_DIR = os.getenv("PYPI_BUILD_DIR", DEFAULT_BUILD_DIR)
DOWNLOAD_DIR = os.path.join(BUILD_DIR, "download")

def _download_latest_zserio_release() -> str:
    """
    Downloads the latest Zserio release from GitHub.

    The method extracts downloaded zip files to the DOWNLOAD_DIR as well.

    :returns: The latest Zserio release version in string format.
    """
    print("downloading the latest zserio release JSON file", end = "")
    zserio_release_url = urllib.request.urlopen("https://api.github.com/repos/ndsev/zserio/releases")
    zserio_release_json = json.loads(zserio_release_url.read().decode('utf-8'))
    zserio_latest_release_json = zserio_release_json[0]
    zserio_version = zserio_latest_release_json["tag_name"][1:]
    zserio_bin_zip_url = zserio_latest_release_json["assets"][0]["browser_download_url"]
    zserio_runtime_libs_zip_url = zserio_latest_release_json["assets"][1]["browser_download_url"]
    print(" (found zserio version " + zserio_version + ")")

    print("downloading the latest zserio binaries")
    zserio_bin_zip = urllib.request.urlopen(zserio_bin_zip_url)
    print("extracting the latest zserio binaries")
    zserio_bin_zip_file = zipfile.ZipFile(io.BytesIO(zserio_bin_zip.read()), 'r')
    zserio_bin_zip_file.extractall(DOWNLOAD_DIR)
 
    print("downloading the latest zserio runtime")
    zserio_runtime_libs_zip = urllib.request.urlopen(zserio_runtime_libs_zip_url)
    print("extracting the latest zserio runtime")
    zserio_runtime_libs_zip_file = zipfile.ZipFile(io.BytesIO(zserio_runtime_libs_zip.read()), 'r')
    zserio_runtime_libs_zip_file.extractall(DOWNLOAD_DIR)

    return zserio_version

def _create_zserio_pypi_package():
    """
    Creates Zserio PyPi package.

    Zserio PyPi package is a merge of Zserio Python runtime library and PyPi source directory.

    :returns: The directory where Zserio PyPi package has been created.
    """
    print("copying zserio python runtime and compiler")
    downloaded_runtime_dir = os.path.join(DOWNLOAD_DIR, "runtime_libs", "python", "zserio")
    zserio_package_dir = os.path.join(BUILD_DIR, "zserio")
    shutil.copytree(downloaded_runtime_dir, zserio_package_dir, dirs_exist_ok = True)
    runtime_compiler_dir = os.path.join(zserio_package_dir, "compiler")
    if not os.path.exists(runtime_compiler_dir):
        os.makedirs(runtime_compiler_dir)
    shutil.copyfile(os.path.join(DOWNLOAD_DIR, "zserio.jar"), os.path.join(runtime_compiler_dir, "zserio.jar"))

    pypi_src_dir = os.path.join(ROOT_DIR, "src", "zserio")
    shutil.copytree(pypi_src_dir, zserio_package_dir, dirs_exist_ok = True,
                    ignore = shutil.ignore_patterns("__init__.py"))

    print("extending zserio runtime __init__.py")
    runtime_init_py_file_name = os.path.join(zserio_package_dir, "__init__.py")
    with open(runtime_init_py_file_name, "a+", encoding="utf-8") as runtime_init_py_file:
        pypi_init_py_file_name = os.path.join(pypi_src_dir, "__init__.py")
        with open(pypi_init_py_file_name, "r", encoding="utf-8") as pypi_init_py_file:
            runtime_init_py_file.write("\n")
            runtime_init_py_file.write(pypi_init_py_file.read())

    return BUILD_DIR

def _create_pypi_long_description() -> str:
    """
    Creates long description for PyPi package from project's README.md file.

    :returns: The PyPi long description.
    """
    read_me_file_name = os.path.join(ROOT_DIR, "README.md")
    with open(read_me_file_name, "r", encoding="utf-8") as file:
        read_me = file.read()
    start_index = read_me.find("Zserio PyPi package contains")
    if start_index == -1:
        start_index = 0
    end_index = read_me.find("\n## Building")
    if end_index == -1:
        end_index = len(read_me)
    long_description = read_me[start_index:end_index]

    return long_description

setuptools.setup(
    name="zserio",
    version=_download_latest_zserio_release(),
    url="https://github.com/ndsev/zserio-pypi",
    author="Navigation Data Standard e.V.",
    author_email="support@nds-association.org",

    description="Zserio runtime with compiler.",
    long_description=_create_pypi_long_description(),
    long_description_content_type="text/markdown",

    package_dir={
        '': _create_zserio_pypi_package()
    },
    packages=['zserio'],
    package_data={
        'zserio': ['compiler/zserio.jar', 'py.typed']
    },

    entry_points={
        'console_scripts': ['zserio=zserio.__main__:main']
    },

    python_requires='>=3.8',

    license = "BSD-3 Clause",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License"
     ],
)
