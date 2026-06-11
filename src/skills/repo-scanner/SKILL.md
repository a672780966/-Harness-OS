# Repo Scanner Skill

## Description
Scan repository structure, detect tech stack, build repository maps.

## Category
repo-scanner

## Default
Enabled

## Tools

### scan_files
- **Risk**: low
- **Approval**: not required
- **Timeout**: 30s
- Scan files in repository matching a pattern.

### build_repository_map
- **Risk**: low
- **Approval**: not required
- **Timeout**: 30s
- Build a map of repository structure (source dirs, config files, commands).

### detect_commands
- **Risk**: low
- **Approval**: not required
- **Timeout**: 10s
- Detect package manager and available commands from project files.

## Notes
- Uses package manifest and lockfile detection.
- Falls back to ripgrep for symbol scanning when tree-sitter is unavailable.
- Built results feed into Context Pack's Repository Map section.
