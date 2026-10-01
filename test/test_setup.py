import unittest
import os
import importlib.util

def _load_setup_module():
    setup_file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "setup.py")
    spec = importlib.util.spec_from_file_location("zserio_pypi_setup", setup_file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

SETUP = _load_setup_module()

def _create_release(tag_name, prerelease=False, draft=False, asset_names=None):
    version = tag_name[1:]
    if asset_names is None:
        asset_names = ["zserio-" + version + "-bin.zip", "zserio-" + version + "-runtime-libs.zip"]

    return {
        "tag_name": tag_name,
        "prerelease": prerelease,
        "draft": draft,
        "assets": [{"name": name, "browser_download_url": "https://download/" + tag_name + "/" + name}
                   for name in asset_names]
    }

class SetupTest(unittest.TestCase):

    def test_select_latest_stable_release(self):
        releases = [_create_release("v2.18.2"), _create_release("v2.19.0"), _create_release("v2.9.9")]
        self.assertEqual("v2.19.0", SETUP._select_latest_stable_release(releases)["tag_name"])

    def test_select_latest_stable_release_skips_prerelease(self):
        releases = [
            _create_release("v2.20.0-rc1", prerelease=True),
            _create_release("v2.20.0", prerelease=True),
            _create_release("v2.21.0", draft=True),
            _create_release("v2.19.0")
        ]
        selected_release = SETUP._select_latest_stable_release(releases)
        self.assertEqual("v2.19.0", selected_release["tag_name"])
        self.assertEqual(("https://download/v2.19.0/zserio-2.19.0-bin.zip",
                          "https://download/v2.19.0/zserio-2.19.0-runtime-libs.zip"),
                         SETUP._select_asset_urls(selected_release))

    def test_select_latest_stable_release_not_found(self):
        with self.assertRaises(RuntimeError):
            SETUP._select_latest_stable_release([_create_release("v2.20.0-rc1", prerelease=True)])

    def test_get_release_version(self):
        self.assertEqual("2.19.0", SETUP._get_release_version(_create_release("v2.19.0")))

    def test_select_asset_urls(self):
        release = _create_release("v2.19.0")
        self.assertEqual(("https://download/v2.19.0/zserio-2.19.0-bin.zip",
                          "https://download/v2.19.0/zserio-2.19.0-runtime-libs.zip"),
                         SETUP._select_asset_urls(release))

    def test_select_asset_urls_reordered(self):
        release = _create_release("v2.19.0", asset_names=[
            "zserio-2.19.0-runtime-libs.zip",
            "zserio-2.19.0-sources.zip",
            "zserio-2.19.0-bin.zip"
        ])
        self.assertEqual(("https://download/v2.19.0/zserio-2.19.0-bin.zip",
                          "https://download/v2.19.0/zserio-2.19.0-runtime-libs.zip"),
                         SETUP._select_asset_urls(release))

    def test_select_asset_urls_missing(self):
        release = _create_release("v2.19.0", asset_names=["zserio-2.19.0-bin.zip"])
        with self.assertRaises(RuntimeError):
            SETUP._select_asset_urls(release)
