# Git Skill

## Description
Git operations: status, diff, commit, branch management, and push.

## Category
git

## Default
Enabled

## Tools

### git_status
- **Risk**: low
- **Approval**: not required
- **Timeout**: 10s
- Show working tree status (branch, changed files, untracked files).

### git_diff
- **Risk**: low
- **Approval**: not required
- **Timeout**: 10s
- Show changes in working tree or between commits.

### git_commit
- **Risk**: medium
- **Approval**: not required
- **Timeout**: 10s
- Create a commit with a message.

### git_push
- **Risk**: high
- **Approval**: required
- **Timeout**: 30s
- Push commits to remote. Always requires approval.

## Security
- git status/diff/log are always allowed.
- Must check git status before any code modification.
- Must not overwrite user uncommitted changes.
- push main and force push require governance approval.
- git reset --hard and git clean -fd require approval.
