"""Catalog matrix/version logic. Does not compile plugins or run makepkg."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = catalog.load_catalog()

    def run_command(self, function, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            function(self.data, argparse.Namespace(**kwargs))
        return json.loads(output.getvalue())

    def test_default_matrix_builds_source_once(self):
        result = self.run_command(catalog.cmd_matrix_build, packages="all",
                                  from_pkgbuild=True, version="", versions="",
                                  distro="", github_output=False)
        rows = result["include"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(row["id"] == "rife-asdg" for row in rows), 2)
        self.assertFalse(any(row["kind"] == "bin" for row in rows))

    def test_pinned_binary_version_needs_no_network(self):
        with patch.object(catalog, "resolve_upstream_version", side_effect=AssertionError("network")):
            result = self.run_command(catalog.cmd_matrix_build, packages="rife-asdg-bin",
                                      from_pkgbuild=False, version="",
                                      versions='{"rife-asdg-bin": "1.2.3"}',
                                      distro="arch", github_output=False)
        self.assertEqual(result["include"][0]["version"], "1.2.3")

    def test_source_and_binary_share_version_lookup(self):
        with patch.object(catalog, "resolve_upstream_ref", return_value=("1.2.3", "abc")) as resolve:
            result = self.run_command(catalog.cmd_resolve, packages="rife-asdg,rife-asdg-bin",
                                      force=False, skip_unchanged=False, github_output=False)
        resolve.assert_called_once()
        self.assertEqual(len(result["build_matrix"]["include"]), 2)
        self.assertEqual(len(result["aur_matrix"]["include"]), 2)

    def test_cron_compares_published_version(self):
        with patch.object(catalog, "resolve_upstream_ref", return_value=("9.0", "abc")), \
             patch.object(catalog, "aur_pkgver", return_value="9.0"):
            result = self.run_command(catalog.cmd_resolve, packages="rife-asdg",
                                      force=False, skip_unchanged=True, github_output=False)
        self.assertEqual(result["aur_matrix"]["include"], [])

    def test_auto_prefers_release_then_tag_then_head(self):
        pkg = {
            "id": "xclean-avs",
            "repo": "https://github.com/mysteryx93/xClean",
            "version_from": "auto",
            "git_branch": "master",
        }
        with patch.object(
            catalog, "http_json",
            return_value={"tag_name": "0.11"},
        ), patch.object(catalog, "commit_sha", return_value="deadbeef" * 5):
            self.assertEqual(catalog.resolve_upstream_ref(pkg, None)[0], "0.11")
        with patch.object(catalog, "http_json", side_effect=[
            None,
            [{"name": "r1.0"}, {"name": "0.10", "commit": {"sha": "a" * 40}}],
        ]):
            self.assertEqual(catalog.resolve_upstream_ref(pkg, None), ("0.10", "a" * 40))
        with patch.object(catalog, "http_json", side_effect=[
            None,
            [],
            [{"sha": "c" * 40, "commit": {"committer": {"date": "2026-09-15T00:00:00Z"}}}],
        ]):
            self.assertEqual(
                catalog.resolve_upstream_ref(pkg, None),
                ("r20260915." + "c" * 7, "c" * 40),
            )

    def test_aur_version_removes_epoch_and_pkgrel(self):
        with patch.object(catalog, "http_json", return_value={"results": [{"Version": "2:1.4.1-3"}]}):
            self.assertEqual(catalog.aur_pkgver("example"), "1.4.1")

    def test_duplicate_and_unsafe_identifiers_rejected(self):
        for mutation in (lambda p: p.append(copy.deepcopy(p[0])),
                         lambda p: p[0].update(id="../../escape"),
                         lambda p: p[0].update(distros=["unknown"])):
            data = copy.deepcopy(self.data)
            mutation(data["packages"])
            with self.assertRaises(SystemExit):
                catalog.validate_catalog(data)

    def test_get_merges_default_gcc(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            catalog.cmd_get(self.data, argparse.Namespace(id="rife-asdg"))
        pkg = json.loads(output.getvalue())
        self.assertEqual(pkg["gcc"], str(self.data["defaults"]["gcc"]))

    def test_tag_source_skips_non_numeric_prefix(self):
        tags = [
            {"name": "r2.7.5.22", "commit": {"sha": "1" * 40}},
            {"name": "2.7.46", "commit": {"sha": "2" * 40}},
            {"name": "2.7.47", "commit": {"sha": "3" * 40}},
        ]
        self.assertEqual(catalog.latest_numeric_tag(tags), "2.7.47")
        with patch.object(catalog, "http_json", return_value=tags):
            version, git_ref = catalog.resolve_upstream_ref(
                {"id": "mvtools2-pinterf", "repo": "https://github.com/pinterf/mvtools",
                 "version_from": "tag"},
                None,
            )
        self.assertEqual((version, git_ref), ("2.7.47", "3" * 40))

    def test_ubuntu_tarball_name_has_no_version(self):
        pkg = {"aur": "avisynth-plugin-rife-asdg"}
        self.assertEqual(
            catalog.tarball_name(pkg, "1.4.1", "ubuntu22.04"),
            "avisynth-plugin-rife-asdg-1.4.1-linux-x86_64-ubuntu.tar.zst",
        )
        self.assertEqual(catalog.tarball_label("arch"), "arch")

    def test_unsafe_versions_rejected(self):
        for version in ("1.0'; echo bad", "../1", "1\n2", "1-2"):
            with self.assertRaises(SystemExit):
                catalog.checked_version(version)


if __name__ == "__main__":
    unittest.main()
