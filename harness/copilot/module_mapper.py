"""Module Mapper — resolve file paths to ModuleCards in a project map."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List

from .schemas import ProjectSemanticMap, ModuleCard, FileEntry


def find_module_for_file(
    sem_map: ProjectSemanticMap,
    file_path: str,
) -> Optional[ModuleCard]:
    """Find which module a file belongs to."""
    abs_file = str(Path(file_path).resolve())
    project_root = str(Path(sem_map.project_root).resolve())

    for mod in sem_map.modules:
        for fe in mod.files:
            fe_abs = str(Path(project_root, fe.path).resolve())
            if fe_abs == abs_file:
                return mod
    return None


def find_module_by_name(
    sem_map: ProjectSemanticMap,
    module_name: str,
) -> Optional[ModuleCard]:
    """Find a module by name."""
    for mod in sem_map.modules:
        if mod.name == module_name:
            return mod
    return None


def get_module_for_path(
    sem_map: ProjectSemanticMap,
    file_path: str,
) -> Optional[ModuleCard]:
    """Get module by relative path (looser matching)."""
    rel_path = Path(file_path).as_posix()
    for mod in sem_map.modules:
        for fe in mod.files:
            if fe.path == rel_path or fe.path.endswith("/" + rel_path):
                return mod
    return None


def get_module_files(
    sem_map: ProjectSemanticMap,
    module_name: str,
) -> List[FileEntry]:
    """Get all files in a module."""
    mod = find_module_by_name(sem_map, module_name)
    if mod:
        return list(mod.files)
    return []


def module_dependency_chain(
    sem_map: ProjectSemanticMap,
    module_name: str,
    max_depth: int = 3,
) -> Dict[str, List[str]]:
    """Build a dependency chain for a module (upstream + downstream)."""
    result: Dict[str, List[str]] = {
        "upstream": [],
        "downstream": [],
    }
    mod = find_module_by_name(sem_map, module_name)
    if mod is None:
        return result

    result["upstream"] = list(mod.dependencies) if mod.dependencies else []
    result["downstream"] = list(mod.dependents) if mod.dependents else []
    return result


def module_summary_card(sem_map: ProjectSemanticMap, module_name: str) -> Dict:
    """Produce a summary dict for a module card."""
    mod = find_module_by_name(sem_map, module_name)
    if mod is None:
        return {"error": f"Module '{module_name}' not found"}

    return {
        "name": mod.name,
        "path": mod.path,
        "file_count": len(mod.files),
        "risk_score": mod.risk_score,
        "risk_level": mod.risk_level.value,
        "dependencies": mod.dependencies,
        "dependents": mod.dependents,
        "languages": list({f.language for f in mod.files}),
        "high_risk_files": [
            {"path": f.path, "risk_score": f.risk_score, "reasons": f.risk_reasons}
            for f in mod.files if f.risk_score >= 0.5
        ],
    }
