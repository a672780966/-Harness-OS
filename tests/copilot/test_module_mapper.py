"""Tests for Module Mapper."""

from harness.copilot.module_mapper import (
    find_module_for_file,
    find_module_by_name,
    get_module_for_path,
    get_module_files,
    module_dependency_chain,
    module_summary_card,
)
from harness.copilot.schemas import (
    ProjectSemanticMap, ModuleCard, FileEntry, DependencyEdge, RiskLevel,
)


def _make_test_map() -> ProjectSemanticMap:
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
                dependencies=["tests"],
                dependents=[],
                risk_score=0.0,
            ),
            ModuleCard(
                name="tests",
                path="/tmp/test/tests",
                files=[
                    FileEntry(path="tests/test_main.py", language="Python", size_bytes=150, last_modified="now"),
                ],
                dependencies=[],
                dependents=["src"],
                risk_score=0.0,
            ),
            ModuleCard(
                name="config",
                path="/tmp/test/config",
                files=[
                    FileEntry(
                        path="config/.env",
                        language="Environment",
                        size_bytes=50,
                        last_modified="now",
                        risk_score=0.7,
                        risk_reasons=["Contains '.env' in path"],
                    ),
                ],
                dependencies=[],
                dependents=[],
                risk_score=0.7,
                risk_level=RiskLevel.HIGH,
            ),
        ],
        dependency_graph=[
            DependencyEdge(source_module="src", target_module="tests", dep_type="import"),
        ],
    )


class TestFindModuleForFile:
    def test_find_exact_match(self):
        sm = _make_test_map()
        mod = find_module_for_file(sm, "/tmp/test/src/main.py")
        assert mod is not None
        assert mod.name == "src"

    def test_find_nonexistent_file(self):
        sm = _make_test_map()
        mod = find_module_for_file(sm, "/tmp/test/unknown.py")
        assert mod is None


class TestFindModuleByName:
    def test_find_src(self):
        sm = _make_test_map()
        mod = find_module_by_name(sm, "src")
        assert mod is not None
        assert mod.name == "src"

    def test_find_nonexistent(self):
        sm = _make_test_map()
        mod = find_module_by_name(sm, "nonexistent")
        assert mod is None


class TestGetModuleForPath:
    def test_relative_path(self):
        sm = _make_test_map()
        mod = get_module_for_path(sm, "main.py")
        assert mod is not None
        assert mod.name == "src"

    def test_subpath(self):
        sm = _make_test_map()
        mod = get_module_for_path(sm, "utils.py")
        assert mod is not None


class TestGetModuleFiles:
    def test_get_src_files(self):
        sm = _make_test_map()
        files = get_module_files(sm, "src")
        assert len(files) == 2

    def test_empty_module(self):
        sm = _make_test_map()
        files = get_module_files(sm, "nonexistent")
        assert files == []


class TestModuleDependencyChain:
    def test_src_deps(self):
        sm = _make_test_map()
        chain = module_dependency_chain(sm, "src")
        assert "upstream" in chain
        assert "tests" in chain["upstream"] or chain["upstream"] == []

    def test_unknown_module(self):
        sm = _make_test_map()
        chain = module_dependency_chain(sm, "nope")
        assert chain["upstream"] == []
        assert chain["downstream"] == []


class TestModuleSummaryCard:
    def test_summary_exists(self):
        sm = _make_test_map()
        s = module_summary_card(sm, "src")
        assert s["name"] == "src"
        assert s["file_count"] == 2

    def test_summary_nonexistent(self):
        sm = _make_test_map()
        s = module_summary_card(sm, "nope")
        assert "error" in s
