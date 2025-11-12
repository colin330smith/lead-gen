"""Expose modules from backend/src as part of the backend package."""

from pathlib import Path

_src_path = Path(__file__).resolve().parent / "src"
if _src_path.exists():
    __path__.append(str(_src_path))  # type: ignore[name-defined]
