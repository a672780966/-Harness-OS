# Filesystem Skill

## Description
Read, write, and manage project files within the workspace boundary.

## Category
filesystem

## Default
Enabled

## Tools

### read_file
- **Risk**: low
- **Approval**: not required
- **Timeout**: 10s
- Read file contents with optional line range support.

### write_file
- **Risk**: medium
- **Approval**: not required
- **Timeout**: 10s
- Write content to a file. Creates file if missing.

### list_dir
- **Risk**: low
- **Approval**: not required
- **Timeout**: 5s
- List directory contents.

### search_text
- **Risk**: low
- **Approval**: not required
- **Timeout**: 30s
- Search for text patterns in files using glob or regex.

### delete_file
- **Risk**: high
- **Approval**: required
- **Timeout**: 5s
- Delete a file. Always requires explicit approval.

## Security
- All paths are restricted to the project workspace.
- Path traversal and symlink escape are blocked.
- Write operations record diff summaries.
- AGENTS.md and accepted ADR modification require governance approval.
