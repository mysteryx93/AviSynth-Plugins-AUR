#!/usr/bin/env python3
"""Read catalog.yaml and emit matrices / package records for GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    sys.stderr.write("PyYAML is required: pip install pyyaml\n")
    raise SystemExit(1) from exc

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog.yaml"

DISTRO_RUNNERS = {
    "arch": {
        "runs_on": "ubuntu-latest",
        "container": "archlinux:base-devel",
    },
    "ubuntu22.04": {
        "runs_on": "ubuntu-22.04",
        "container": "",
    },
    "any": {
        "runs_on": "ubuntu-22.04",
        "container": "",
    },
}


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "packages" not in data:
        raise SystemExit(f"Invalid catalog: {CATALOG_PATH}")
    validate_catalog(data)
    return data


def validate_catalog(data: dict[str, Any]) -> None:
    """kind=bin needs a kind=source sibling. Source is required for compiled plugins."""
    packages = data["packages"]
    if not isinstance(packages, list):
        raise SystemExit("catalog packages must be a list")
    by_id = {}
    names = set()
    for pkg in packages:
        if not isinstance(pkg, dict):
            raise SystemExit("Each package must be a mapping")
        for field in ("id", "aur"):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(pkg.get(field, ""))):
                raise SystemExit(f"Invalid package {field}: {pkg.get(field)}")
        if pkg["id"] in by_id or pkg["aur"] in names:
            raise SystemExit(f"Duplicate package id or aur: {pkg['id']}")
        by_id[pkg["id"]] = pkg
        names.add(pkg["aur"])
        if pkg.get("host") not in ("avisynth", "vapoursynth"):
            raise SystemExit(f"{pkg['id']}: invalid host")
        for distro in distros_for(pkg, data.get("defaults") or {}):
            if distro not in DISTRO_RUNNERS or (pkg.get("kind") == "source" and distro == "any"):
                raise SystemExit(f"{pkg['id']}: invalid distro {distro}")
    for pkg in packages:
        kind = pkg.get("kind")
        if kind not in ("source", "bin", "script"):
            raise SystemExit(f"{pkg.get('id')}: unknown kind={kind}")
        if kind != "bin":
            continue
        src_id = pkg.get("binary_of")
        if not src_id:
            raise SystemExit(f"{pkg['id']}: kind=bin requires binary_of pointing at a source package")
        src = by_id.get(src_id)
        if not src:
            raise SystemExit(f"{pkg['id']}: binary_of={src_id} not in catalog")
        if src.get("kind") != "source":
            raise SystemExit(f"{pkg['id']}: binary_of must be kind=source (got {src.get('kind')})")
        if pkg["aur"] != src["aur"] + "-bin" or pkg["host"] != src["host"]:
            raise SystemExit(f"{pkg['id']}: binary name and host must match its source sibling")
        if "arch" not in distros_for(src, data.get("defaults") or {}):
            raise SystemExit(f"{pkg['id']}: binary source must build for Arch")


def parse_ids(raw: str, packages: list[dict[str, Any]]) -> list[str]:
    raw = (raw or "all").strip()
    known = [p["id"] for p in packages]
    if raw in ("", "all"):
        return known
    wanted = [part.strip() for part in raw.split(",") if part.strip()]
    unknown = [w for w in wanted if w not in known]
    if unknown:
        raise SystemExit(f"Unknown package id(s): {', '.join(unknown)}\nKnown: {', '.join(known)}")
    return wanted


def selected(catalog: dict[str, Any], raw_ids: str) -> list[dict[str, Any]]:
    packages = catalog["packages"]
    ids = set(parse_ids(raw_ids, packages))
    return [p for p in packages if p["id"] in ids]


def github_slug(repo_url: str) -> str:
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("github.com/")
    if len(parts) != 2:
        raise SystemExit(f"Not a GitHub repo URL: {repo_url}")
    return parts[1]


def http_json(url: str, token: str | None) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "AviSynth-Plugins-AUR"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except HTTPError as exc:
        raise SystemExit(f"API {url} failed: HTTP {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"API {url} failed: {exc.reason}") from exc


def strip_v(tag: str) -> str:
    tag = tag.strip()
    if tag.startswith("v") and len(tag) > 1 and tag[1].isdigit():
        return tag[1:]
    return tag


def checked_version(version: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._+]*", version):
        raise SystemExit(f"Unsupported pkgver: {version!r}; use an explicit upstream mapping")
    return version


def tag_sort_key(name: str) -> tuple[tuple[int, int | str], ...] | None:
    """Numeric pkgver only. Drops pinterf's old r2.7.5.22-style tags (GitHub lists those first)."""
    version = strip_v(name)
    if not re.fullmatch(r"[0-9][a-zA-Z0-9._+]*", version):
        return None
    parts: list[tuple[int, int | str]] = []
    for piece in re.split(r"[._+]", version):
        parts.append((0, int(piece)) if piece.isdigit() else (1, piece))
    return tuple(parts)


def latest_numeric_tag(tags: list[dict[str, Any]]) -> str | None:
    ranked: list[tuple[tuple[tuple[int, int | str], ...], str]] = []
    for tag in tags:
        key = tag_sort_key(tag.get("name") or "")
        if key is not None:
            ranked.append((key, strip_v(tag["name"])))
    if not ranked:
        return None
    ranked.sort()
    return ranked[-1][1]


def resolve_upstream_version(pkg: dict[str, Any], token: str | None) -> str:
    source = pkg.get("version_from", "release")
    if source == "manual":
        version = str(pkg.get("version", "")).strip()
        if not version:
            raise SystemExit(f"{pkg['id']}: version_from=manual requires version")
        return version
    slug = github_slug(pkg["repo"])
    if source == "release":
        data = http_json(f"https://api.github.com/repos/{slug}/releases/latest", token)
        tag = data.get("tag_name") or ""
        if not tag:
            raise SystemExit(f"{pkg['id']}: latest release has no tag_name")
        return strip_v(tag)
    if source == "tag":
        data = http_json(f"https://api.github.com/repos/{slug}/tags?per_page=100", token)
        if not data:
            raise SystemExit(f"{pkg['id']}: no tags on {slug}")
        version = latest_numeric_tag(data)
        if not version:
            raise SystemExit(f"{pkg['id']}: no numeric tags on {slug}")
        return version
    raise SystemExit(f"{pkg['id']}: unknown version_from={source}")


def pkgbuild_pkgver(aur: str) -> str | None:
    path = ROOT / "packages" / aur / "PKGBUILD"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("pkgver="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return None


def aur_pkgver(aur: str) -> str | None:
    """Published AUR pkgver (no epoch/pkgrel). Cron uses this; this git tree may be stale."""
    data = http_json(f"https://aur.archlinux.org/rpc/v5/info?arg[]={aur}", None)
    if data.get("type") == "error":
        raise SystemExit(f"AUR lookup failed: {data.get('error')}")
    results = data.get("results", [])
    return results[0]["Version"].split(":")[-1].rsplit("-", 1)[0] if results else None


def distros_for(pkg: dict[str, Any], defaults: dict[str, Any]) -> list[str]:
    if pkg.get("kind") == "bin":
        return []  # compile the source sibling instead
    if pkg.get("kind") == "script":
        return ["any"]
    return list(pkg.get("distros") or defaults.get("distros") or ["arch", "ubuntu22.04"])


def compile_pkg(pkg: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """CI compiles source once; -bin is AUR-only."""
    if pkg.get("kind") == "bin":
        src_id = pkg.get("binary_of")
        if not src_id:
            return None
        src = by_id.get(src_id)
        if not src:
            raise SystemExit(f"{pkg['id']}: binary_of={src_id} not in catalog")
        return src
    return pkg


def artifact_id(pkg: dict[str, Any]) -> str:
    return pkg.get("binary_of") or pkg["id"]


def build_row(pkg: dict[str, Any], distro: str, version: str) -> dict[str, str]:
    checked_version(version)
    runner = DISTRO_RUNNERS[distro]
    return {
        "id": pkg["id"],
        "aur": pkg["aur"],
        "kind": pkg["kind"],
        "host": pkg["host"],
        "author": pkg["author"],
        "repo": pkg["repo"],
        "version": version,
        "distro": distro,
        "runs_on": runner["runs_on"],
        "container": runner["container"],
        "tarball": tarball_name(pkg, version, distro),
    }


def tarball_label(distro: str) -> str:
    if distro.startswith("ubuntu"):
        return "ubuntu"
    return distro


def tarball_name(pkg: dict[str, Any], version: str, distro: str) -> str:
    base = pkg["aur"]
    if base.endswith("-bin"):
        base = base[: -len("-bin")]
    return f"{base}-{version}-linux-x86_64-{tarball_label(distro)}.tar.zst"


def release_tag(pkg: dict[str, Any] | str, version: str) -> str:
    pkg_id = pkg if isinstance(pkg, str) else artifact_id(pkg)
    return f"{pkg_id}-v{version}"


def cmd_resolve(catalog: dict[str, Any], args: argparse.Namespace) -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    defaults = catalog.get("defaults") or {}
    packages_out: list[dict[str, Any]] = []
    build_include: list[dict[str, str]] = []
    aur_include: list[dict[str, str]] = []
    release_include: list[dict[str, str]] = []
    skipped: list[str] = []
    built_ids: set[str] = set()
    by_id = {p["id"]: p for p in catalog["packages"]}
    versions = {}
    for pkg in selected(catalog, args.packages):
        src = compile_pkg(pkg, by_id)
        if src["id"] not in versions:
            versions[src["id"]] = checked_version(resolve_upstream_version(src, token))
        version = versions[src["id"]]
        # Cron: AUR. Manual/PR: local PKGBUILD (Publish does not commit pkgver).
        current = aur_pkgver(pkg["aur"]) if args.skip_unchanged else pkgbuild_pkgver(pkg["aur"])
        changed = current != version
        if args.skip_unchanged and not args.force and not changed:
            skipped.append(f"{pkg['id']} already {version}")
            continue
        row = {
            "id": pkg["id"],
            "aur": pkg["aur"],
            "kind": pkg["kind"],
            "version": version,
            "previous": current,
            "changed": changed,
            "release_tag": release_tag(pkg, version),
            "artifact_id": artifact_id(pkg),
            "arch_tarball": tarball_name(
                pkg, version, "any" if pkg["kind"] == "script" else "arch"
            ),
        }
        packages_out.append(row)
        aur_include.append(row)
        src = compile_pkg(pkg, by_id)
        if src and src["id"] not in built_ids:
            built_ids.add(src["id"])
            for distro in distros_for(src, defaults):
                build_include.append(build_row(src, distro, version))
            if src.get("kind") != "bin":
                release_include.append(
                    {
                        "id": src["id"],
                        "aur": src["aur"],
                        "kind": src["kind"],
                        "version": version,
                        "release_tag": release_tag(src, version),
                    }
                )
    build_matrix = {"include": build_include} if build_include else {"include": []}
    aur_matrix = {"include": aur_include} if aur_include else {"include": []}
    release_matrix = {"include": release_include} if release_include else {"include": []}
    if args.github_output:
        write_output(
            has_packages=str(bool(aur_include)).lower(),
            has_builds=str(bool(build_include)).lower(),
            build_matrix=json.dumps(build_matrix),
            release_matrix=json.dumps(release_matrix),
            aur_matrix=json.dumps(aur_matrix),
            skipped="; ".join(skipped),
        )
    json.dump(
        {
            "packages": packages_out,
            "skipped": skipped,
            "build_matrix": build_matrix,
            "release_matrix": release_matrix,
            "aur_matrix": aur_matrix,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")


def cmd_list(catalog: dict[str, Any], args: argparse.Namespace) -> None:
    for pkg in selected(catalog, args.packages):
        print(f"{pkg['id']}\t{pkg['aur']}\t{pkg['kind']}\t{pkg['host']}\t{pkg['repo']}")


def cmd_get(catalog: dict[str, Any], args: argparse.Namespace) -> None:
    matches = [p for p in catalog["packages"] if p["id"] == args.id]
    if not matches:
        raise SystemExit(f"Unknown package id: {args.id}")
    pkg = dict(matches[0])
    defaults = catalog.get("defaults") or {}
    gcc = pkg.get("gcc", defaults.get("gcc"))
    if gcc is not None and gcc != "":
        pkg["gcc"] = str(gcc)
    json.dump(pkg, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_matrix(catalog: dict[str, Any], args: argparse.Namespace) -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    force = args.force
    include: list[dict[str, str]] = []
    skipped: list[str] = []
    for pkg in selected(catalog, args.packages):
        by_id = {p["id"]: p for p in catalog["packages"]}
        version = checked_version(resolve_upstream_version(compile_pkg(pkg, by_id), token))
        current = aur_pkgver(pkg["aur"]) if args.skip_unchanged else pkgbuild_pkgver(pkg["aur"])
        if not force and current == version and args.skip_unchanged:
            skipped.append(f"{pkg['id']} already {version}")
            continue
        include.append(
            {
                "id": pkg["id"],
                "aur": pkg["aur"],
                "kind": pkg["kind"],
                "version": version,
                "release_tag": release_tag(pkg, version),
                "arch_tarball": tarball_name(pkg, version, "arch" if pkg["kind"] != "script" else "any"),
            }
        )
    payload = {"include": include} if include else {"include": []}
    if args.github_output:
        write_output(
            has_packages=str(bool(include)).lower(),
            matrix=json.dumps(payload),
            skipped="; ".join(skipped),
        )
    json.dump({"matrix": payload, "skipped": skipped}, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_matrix_build(catalog: dict[str, Any], args: argparse.Namespace) -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    defaults = catalog.get("defaults") or {}
    include: list[dict[str, str]] = []
    seen: set[str] = set()
    by_id = {p["id"]: p for p in catalog["packages"]}
    pinned = json.loads(args.versions) if args.versions else {}
    for pkg in selected(catalog, args.packages):
        src = compile_pkg(pkg, by_id)
        if src is None:
            continue
        if src["id"] in seen:
            continue
        seen.add(src["id"])
        # Explicit --version / --versions skip GitHub. Otherwise PKGBUILD, then upstream.
        version = pinned.get(src["id"], pinned.get(pkg["id"], args.version))
        if version:
            pass
        elif args.from_pkgbuild:
            version = pkgbuild_pkgver(src["aur"]) or resolve_upstream_version(src, token)
        else:
            version = args.version or resolve_upstream_version(src, token)
        for distro in distros_for(src, defaults):
            if args.distro and distro not in (args.distro, "any"):
                continue
            include.append(build_row(src, distro, version))
    payload = {"include": include} if include else {"include": []}
    if args.github_output:
        write_output(has_packages=str(bool(include)).lower(), matrix=json.dumps(payload))
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def write_output(**kwargs: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        for key, value in kwargs.items():
            if "\n" in value:
                fh.write(f"{key}<<EOF\n{value}\nEOF\n")
            else:
                fh.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", default="all", help="all or comma-separated ids")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Print id, aur, kind, host, repo")

    get_p = sub.add_parser("get", help="Print one package as JSON")
    get_p.add_argument("id")

    rs = sub.add_parser("resolve", help="Resolve versions and emit build + AUR matrices")
    rs.add_argument("--force", action="store_true")
    rs.add_argument("--skip-unchanged", action="store_true")
    rs.add_argument("--github-output", action="store_true")

    mx = sub.add_parser("matrix", help="AUR publish matrix (one row per package)")
    mx.add_argument("--force", action="store_true")
    mx.add_argument("--skip-unchanged", action="store_true")
    mx.add_argument("--github-output", action="store_true")

    mb = sub.add_parser("matrix-build", help="Build matrix (package × distro)")
    mb.add_argument("--version", default="")
    mb.add_argument("--versions", default="", help="JSON object of id→version")
    mb.add_argument("--distro", default="")
    mb.add_argument("--from-pkgbuild", action="store_true")
    mb.add_argument("--github-output", action="store_true")

    args = parser.parse_args()
    catalog = load_catalog()
    if args.cmd == "list":
        cmd_list(catalog, args)
    elif args.cmd == "get":
        cmd_get(catalog, args)
    elif args.cmd == "resolve":
        cmd_resolve(catalog, args)
    elif args.cmd == "matrix":
        cmd_matrix(catalog, args)
    elif args.cmd == "matrix-build":
        cmd_matrix_build(catalog, args)
    else:
        raise SystemExit(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
