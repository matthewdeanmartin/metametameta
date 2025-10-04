# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2024-10-02

### Fixed

- Mypy complaints when lists are empty. Added more null safety checks.

### Added

- `metametameta sync-check` run on CI server to see if your about file is out of sync
- `metametameta auto` make best guess what your metadata source is. Give up if there are two possibilities.


## [0.1.4] - 2024-10-02

### Fixed

- Mypy complaints when lists are empty. Added more null safety checks.

### Added

- Experimental setup.py support.

## [0.1.3] - 2024-06-28

### Fixed

- Fix bug in pep621 command where `-` in name but src folder is `_` 

## [0.1.2] - 2024-06-14

### Fixed

- Fix bug in pep621 command.

## [0.1.1] - 2024-08-03

### Added

- `--verbose` option

### Fixed

- Less noisy by default, most prints moved to logging invocations

### Changed

- Makes best efforts to find src folder even if different from package name.


## [0.1.0] - 2024-01-20

### Added

- Application created.

