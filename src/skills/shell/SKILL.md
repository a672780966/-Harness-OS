# Shell Skill

## Description
Execute controlled shell commands within the workspace boundary. All commands have timeout control and output capture.

## Category
shell

## Default
Enabled

## Tools

### run_command
- **Risk**: medium
- **Approval**: not required by default
- **Timeout**: 300s (5 min)
- Execute a shell command with configurable working directory and timeout.

### run_test
- **Risk**: low
- **Approval**: not required
- **Timeout**: 300s (5 min)
- Run a test command and capture results.

### run_build
- **Risk**: low
- **Approval**: not required
- **Timeout**: 600s (10 min)
- Run a build command.

## Security
- Dangerous commands (rm -rf, sudo, chmod -R, git reset --hard) require approval.
- Default cwd is workspace root.
- All commands record stdout/stderr summary and exit code.
- sudo, curl|sh, wget|sh are prohibited by default.
