# Changelog

## Unreleased

### Added
- **MVP install path**: `pyproject.toml` added — `pip install -e .` now works
- **Product docs**: Quickstart guide, architecture overview, and first-user 30-minute path
- **Contributing guide**: `CONTRIBUTING.md` with setup, branch, review, and governance rules
- **Python CI**: GitHub Actions now validates Python CLI and pytest in addition to Node

### Changed
- **README.md**: Rewritten with product story, dual CLI explanation, MVP path, and evidence model
- **README.zh.md**: Aligned with English MVP documentation

### Fixed
- `pip install -e .` is now functional (was broken due to missing pyproject.toml)
