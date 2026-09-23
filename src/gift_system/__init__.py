"""Gift System package."""

from .core.matching import partition_and_match as generate_assignments
from .services.santa_service import (
    build_and_save_assignments as build_assignments,
    load_employees_from_file as load_employees,
    resolve_worker_name as resolve_assignment,
)

from .cli import run_build

__all__ = [
    "build_assignments",
    "generate_assignments",
    "load_employees",
    "resolve_assignment",
    "run_build",
]
