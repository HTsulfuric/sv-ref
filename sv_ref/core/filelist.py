from __future__ import annotations

from pathlib import Path


def parse_filelist(path: Path) -> tuple[list[Path], list[Path]]:
    """Parse a .f filelist file and return (source_files, include_dirs).

    Relative paths are resolved against CWD (standard EDA convention).
    """
    source_files: list[Path] = []
    include_dirs: list[Path] = []

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line.startswith("+incdir+"):
            inc_path = line[len("+incdir+"):]
            include_dirs.append(Path(inc_path).resolve())
            continue

        if line.startswith("+") or line.startswith("-"):
            continue

        source_files.append(Path(raw_line.strip()).resolve())

    return source_files, include_dirs
