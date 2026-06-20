# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.13] - 2026-05-24

### Fixed

- Generated `__about__.py` files now sort `__all__` entries so the output passes Ruff linting without any post-generation edits

### Changed

- Quality-gate coverage now generates `__about__.py` files through the CLI in subprocess-based tests and verifies they pass Ruff format/lint, pylint, isort, black, and mypy unchanged

## [0.1.12] - 2026-05-04

### Fixed

- Suppress false sync-check mismatch when source has an empty dependency list and `__about__.py` omits the field

## [0.1.11] - 2026-05-03

### Fixed

- Generate valid `__about__.py` with empty `__dependencies__` list for zero-dependency projects

## [0.1.10] - 2026-05-02

### Fixed

- Zero-dependency projects now generate a valid `__about__.py` with a typed `__dependencies__: list[str] = []` entry instead of dropping dependency metadata, covering PEP 621, Poetry, setup.cfg, setup.py, requirements.txt, and conda metadata inputs
- Package directory resolution improved for cases where project name differs from module name

### Changed

- Raises `PackageDirectoryNotFoundError` with a helpful message when the package directory cannot be located, listing the locations searched and telling the user how to point at the correct module via `--output path/to/module/__about__.py`

## [0.1.9] - 2026-04-27

### Fixed

- Support full paths in `sync-check --output`
- Support type-annotated assignments (e.g., `__version__: str = "..."`) in `sync-check`
- Fixed `python -m metametameta` ignoring command-line arguments

## [0.1.8] - 2026-03-29

### Added

- GUI command (`mmm gui` or `metametameta gui`) for feature discoverability

## [0.1.7] - 2026-03-27

### Added

- Support for additional build system formats
- Improved testing and documentation flow

## [0.1.5] - 2025-10-04

### Fixed

- Added null safety checks to address mypy complaints when lists are empty

### Added

- `metametameta sync-check` command for running on CI servers to check if `__about__.py` is out of sync with the metadata source
- `metametameta auto` command for automatic metadata source detection, giving up if there are two possibilities
- Quality of life commands

### Changed

- Switched to uv for package management

## [0.1.4] - 2025-10-03

### Fixed

- Improved null safety for empty lists to address mypy complaints

### Added

- Experimental setup.py support

## [0.1.3] - 2025-06-28

### Fixed

- Fixed PEP 621 bug where `-` in project name but src folder uses `_` caused a mismatch

## [0.1.2] - 2025-06-14

### Fixed

- Fixed PEP 621 parsing bug
- Fixed logging verbosity

### Changed

- Removed unnecessary dependencies

## [0.1.1] - 2024-08-03

### Added

- `--verbose` option

### Fixed

- Reduced default noise by moving most print calls to logging invocations

### Changed

- Improved package discovery for src folder layouts where folder name differs from package name

## [0.1.0] - 2024-01-20

### Added

- Initial release with basic metadata generation

[0.1.13]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.12...v0.1.13
[0.1.12]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.11...v0.1.12
[0.1.11]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.10...v0.1.11
[0.1.10]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.5...v0.1.7
[0.1.5]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/matthewdeanmartin/metametameta/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/matthewdeanmartin/metametameta/releases/tag/v0.1.0
