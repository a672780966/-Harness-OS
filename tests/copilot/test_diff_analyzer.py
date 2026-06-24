"""Tests for Diff Analyzer."""

from harness.copilot.diff_analyzer import (
    parse_diff,
    group_diff_by_module,
    diff_file_list,
    simple_diff_stats,
)
from harness.copilot.schemas import DiffEntry, ProjectSemanticMap, ModuleCard, FileEntry


SAMPLE_DIFF = """diff --git a/src/main.py b/src/main.py
index abc..def 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,7 @@
 def main():
-    print("hello")
+    print("hello world")
+    print("new line")
+
 def existing():
     pass
diff --git a/src/utils.py b/src/utils.py
index 123..456 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,4 @@
 def helper():
-    return 0
+    return 1
+    # comment
"""

SAMPLE_DIFF_SINGLE = """diff --git a/README.md b/README.md
index a..b 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
-# Project
+# Project Title
+## Description
"""


class TestParseDiff:
    def test_parse_two_files(self):
        entries = parse_diff(SAMPLE_DIFF)
        assert len(entries) == 2
        assert entries[0].file_path == "src/main.py"
        assert entries[1].file_path == "src/utils.py"

    def test_parse_line_counts(self):
        entries = parse_diff(SAMPLE_DIFF)
        main_entry = entries[0]
        # +"hello world", +"new line", +"" (trailing newline)
        assert main_entry.lines_added == 3
        assert main_entry.lines_removed == 1  # -"hello"
        assert main_entry.hunks == 1

    def test_parse_single_file(self):
        entries = parse_diff(SAMPLE_DIFF_SINGLE)
        assert len(entries) == 1
        assert entries[0].file_path == "README.md"
        assert entries[0].lines_added == 2

    def test_parse_empty_diff(self):
        entries = parse_diff("")
        assert entries == []

    def test_new_file_detection(self):
        diff = """diff --git a/new.py b/new.py
new file mode 100644
index 000..123
--- /dev/null
+++ b/new.py
@@ -0,0 +1,3 @@
+def new_func():
+    pass
+"""
        entries = parse_diff(diff)
        assert len(entries) == 1
        assert entries[0].change_type == "added" or entries[0].lines_added > 0

    def test_change_type_classification(self):
        entries = parse_diff(SAMPLE_DIFF)
        # Both files have adds and removes = modified
        for entry in entries:
            assert entry.change_type == "modified"


class TestDiffFileList:
    def test_list_files(self):
        files = diff_file_list(SAMPLE_DIFF)
        assert len(files) == 2
        assert "src/main.py" in files
        assert "src/utils.py" in files

    def test_empty_diff(self):
        files = diff_file_list("")
        assert files == []


class TestSimpleDiffStats:
    def test_stats(self):
        stats = simple_diff_stats(SAMPLE_DIFF)
        assert stats["files_changed"] == 2
        assert stats["lines_added"] >= 2
        assert stats["lines_removed"] >= 1

    def test_empty_stats(self):
        stats = simple_diff_stats("")
        assert stats["files_changed"] == 0

    def test_file_list_in_stats(self):
        stats = simple_diff_stats(SAMPLE_DIFF)
        assert len(stats["file_list"]) == 2


class TestGroupDiffByModule:
    def _make_map(self) -> ProjectSemanticMap:
        return ProjectSemanticMap(
            project_name="test",
            project_root="/tmp/test",
            modules=[
                ModuleCard(
                    name="src",
                    path="/tmp/test/src",
                    files=[
                        FileEntry(path="src/main.py", language="Python", size_bytes=100, last_modified="now"),
                        FileEntry(path="src/utils.py", language="Python", size_bytes=200, last_modified="now"),
                    ],
                ),
            ],
        )

    def test_group_by_module(self):
        entries = parse_diff(SAMPLE_DIFF)
        sm = self._make_map()
        summaries = group_diff_by_module(entries, sm)
        assert len(summaries) >= 1
        # Should find src module
        src_summaries = [s for s in summaries if s.module_name == "src"]
        assert len(src_summaries) > 0

    def test_group_with_fallback(self):
        """Files not in map should get fallback grouping."""
        entries = parse_diff(SAMPLE_DIFF)
        empty_map = ProjectSemanticMap(project_name="empty", project_root="/tmp")
        summaries = group_diff_by_module(entries, empty_map)
        # Should fallback to first directory component
        assert len(summaries) >= 1
