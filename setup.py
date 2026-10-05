import setuptools
import json
import re
import urllib.parse
import urllib.request
import zipfile
import io
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUILD_DIR = os.path.join(ROOT_DIR, "build")
BUILD_DIR = os.getenv("PYPI_BUILD_DIR", DEFAULT_BUILD_DIR)
DOWNLOAD_DIR = os.path.join(BUILD_DIR, "download")

ZSERIO_RELEASES_URL = "https://api.github.com/repos/ndsev/zserio/releases"
ZSERIO_RELEASE_TAG = os.getenv("ZSERIO_RELEASE_TAG", "")
STABLE_TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

def _select_latest_stable_release(releases: list) -> dict:
    """
    Selects the stable release with the highest version tag.

    Drafts, pre-releases and releases whose tag is not in the form 'vX.Y.Z' are skipped,
    so the order of the given releases does not matter.

    :param releases: Release JSON objects as returned by GitHub API.
    :returns: The selected release JSON object.
    """
    stable_releases = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        match = STABLE_TAG_PATTERN.match(release.get("tag_name", ""))
        if match:
            stable_releases.append((tuple(int(part) for part in match.groups()), release))
    if not stable_releases:
        raise RuntimeError("no stable zserio release found")

    return max(stable_releases, key=lambda version_release: version_release[0])[1]

def _get_release_version(release: dict) -> str:
    """
    Gets the Zserio version from the release tag.

    :param release: Release JSON object as returned by GitHub API.
    :returns: The release tag without the leading 'v'.
    """
    tag_name = release["tag_name"]

    return tag_name[1:] if tag_name.startswith("v") else tag_name

def _select_asset_url(release: dict, asset_name: str) -> str:
    """
    Selects the download URL of the release asset with the given name.

    :param release: Release JSON object as returned by GitHub API.
    :param asset_name: Name of the asset to select.
    :returns: The download URL of the asset.
    """
    for asset in release["assets"]:
        if asset["name"] == asset_name:
            return asset["browser_download_url"]

    raise RuntimeError("asset '" + asset_name + "' not found in zserio release " + release["tag_name"])

def _select_asset_urls(release: dict) -> tuple:
    """
    Selects the download URLs of the Zserio binaries and the Zserio runtime libraries.

    :param release: Release JSON object as returned by GitHub API.
    :returns: Tuple of the binaries zip URL and the runtime libraries zip URL.
    """
    zserio_version = _get_release_version(release)

    return (_select_asset_url(release, "zserio-" + zserio_version + "-bin.zip"),
            _select_asset_url(release, "zserio-" + zserio_version + "-runtime-libs.zip"))

def _download_json(url: str):
    """
    Downloads and decodes JSON from the given URL.

    :param url: URL to download.
    :returns: The decoded JSON.
    """
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode('utf-8'))

def _download_zserio_release() -> str:
    """
    Downloads the Zserio release from GitHub.

    The release is given by the tag in the ZSERIO_RELEASE_TAG environment variable. If it is not set,
    the stable release with the highest version is used.

    The method extracts downloaded zip files to the DOWNLOAD_DIR as well.

    :returns: The downloaded Zserio release version in string format.
    """
    if ZSERIO_RELEASE_TAG:
        print("downloading the zserio release JSON file for tag " + ZSERIO_RELEASE_TAG, end = "")
        zserio_release_json = _download_json(ZSERIO_RELEASES_URL + "/tags/" +
                                             urllib.parse.quote(ZSERIO_RELEASE_TAG))
    else:
        print("downloading the latest zserio release JSON file", end = "")
        zserio_release_json = _select_latest_stable_release(
            _download_json(ZSERIO_RELEASES_URL + "?per_page=100"))
    zserio_version = _get_release_version(zserio_release_json)
    zserio_bin_zip_url, zserio_runtime_libs_zip_url = _select_asset_urls(zserio_release_json)
    print(" (found zserio version " + zserio_version + ")")

    print("downloading the zserio binaries")
    zserio_bin_zip = urllib.request.urlopen(zserio_bin_zip_url)
    print("extracting the zserio binaries")
    zserio_bin_zip_file = zipfile.ZipFile(io.BytesIO(zserio_bin_zip.read()), 'r')
    zserio_bin_zip_file.extractall(DOWNLOAD_DIR)

    print("downloading the zserio runtime")
    zserio_runtime_libs_zip = urllib.request.urlopen(zserio_runtime_libs_zip_url)
    print("extracting the zserio runtime")
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

if __name__ == "__main__":
    setuptools.setup(
        name="zserio",
        version=_download_zserio_release(),
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
