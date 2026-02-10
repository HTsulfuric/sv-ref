from __future__ import annotations

from pathlib import Path


def parse_filelist(path: Path) -> tuple[list[Path], list[Path]]:
    """Parse a .f filelist file and return (source_files, include_dirs)."""
    source_files: list[Path] = []
    include_dirs: list[Path] = []
    base_dir = path.parent.resolve()

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line.startswith("+incdir+"):
            inc_path = line[len("+incdir+"):]
            resolved = _resolve_path(inc_path, base_dir)
            include_dirs.append(resolved)
            continue

        if line.startswith("+") or line.startswith("-"):
            continue

        resolved = _resolve_path(line, base_dir)
        source_files.append(resolved)

    return source_files, include_dirs


def _resolve_path(raw: str, base_dir: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return base_dir / p
