# Repository review

The catalog plus hand-written PKGBUILDs is a reasonable structure for this
repository. Keep the two workflows and three package kinds; a larger framework
would add maintenance without removing the need to review individual recipes.

## Corrections made

- Bootstrap Python/PyYAML before reading the catalog in fresh build environments.
- Install catalog-specific build dependencies; stop hiding Arch dependency errors.
- Use sudo for Ubuntu's system-wide AviSynth header installation.
- Pin manual script builds to the same commit as their PKGBUILD.
- Create unique work directories instead of deleting a path derived from input.
- Validate package identifiers, distro choices, binary siblings, and versions.
- Resolve a source/binary pair's upstream version once; honor explicit version
  overrides without first contacting upstream.
- Compare scheduled updates against AUR state instead of stale local PKGBUILDs.
- Pass dispatch package selection through environment variables; remove duplicate
  version resolution and redundant chmod calls.
- Give the release job an explicit repository and tag the workflow's commit.
- Include RIFE's license in release archives and its binary package; require the
  expected shared libraries rather than silently accepting an empty find result.
- Ignore IDE metadata, virtual environments, Python bytecode, and makepkg output.
  Keep `.SRCINFO` visible so it can be tracked if the maintenance process needs it.
- Add offline regression tests to both workflows.

## Remaining considerations

1. **Test PKGBUILDs before release upload.** Build currently validates catalog
   commands. Publish's AUR action uses `test: true`, but runs after GitHub Release
   creation. Recipe drift can therefore pass Build and leave a release even when
   AUR publication fails. A separate Arch makepkg validation stage would close
   this gap, at the cost of another expensive source build for RIFE.
2. **Avoid replacing published binaries under the same version.** Release upload
   still uses `--clobber`. If AUR publication subsequently fails, existing AUR
   checksums may refer to the old archive. Immutable releases or an explicit
   rebuild revision would improve retry behavior. This needs a deliberate version
   policy across release tags, tarball names, and binary PKGBUILDs.
3. **Keep local recipe versions current.** Publication changes a disposable
   checkout, not this repository. The cron fix avoids repeated publication, but
   PR builds continue to use local versions. Manual script updates must change
   `_commit`, `pkgver`, and the catalog's manual version together.
4. **Complete reproducibility requires more pins.** AviSynth headers are fetched
   from the default branch on Ubuntu; containers, system packages, and minimum
   CMake versions float. Release/tag discovery also assumes simple numeric tags
   with an optional `v`. Add explicit tag mapping if an upstream changes conventions.
5. **Checksums and submodule sources need packaging review.** Recipes retain
   `SKIP`; Publish runs `updpkgsums`, but local archive recipes do not verify a
   stored digest. RIFE initializes submodules in `prepare()` rather than declaring
   each as a makepkg source, so offline source-package builds need more work.
6. **Runtime compatibility is not yet tested.** No test loads the built plugins
   in AviSynth or VapourSynth. Ubuntu 22.04 compilation alone does not guarantee
   compatibility on every newer distro. The current catalog has no VapourSynth
   package exercising that path yet.

## Validation scope

Seven offline regression tests pass. Shell syntax checks cover scripts, package
recipes, and templates; both workflow YAML files parse; Git whitespace checks
and representative ignore-rule checks pass. No full plugin compilation, runtime
loading, GitHub Actions run, release upload, or AUR publication was performed.
