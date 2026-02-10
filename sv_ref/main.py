from __future__ import annotations

import glob as globmod
import json
from pathlib import Path
from typing import Annotated

import typer

from sv_ref import __version__
from sv_ref.core.analyzer import analyze
from sv_ref.core.filelist import parse_filelist
from sv_ref.decoder import decode_hex, find_type, load_refbook
from sv_ref.generator.html import generate_html

app = typer.Typer(help="sv-ref: SystemVerilog packed type refbook generator.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sv-ref {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True,
                     help="Show version and exit."),
    ] = None,
) -> None:
    pass


@app.command()
def generate(
    files: Annotated[
        list[Path] | None,
        typer.Argument(help="SystemVerilog source files"),
    ] = None,
    include_dir: Annotated[
        list[Path] | None,
        typer.Option("-I", "--include-dir", help="Include directories"),
    ] = None,
    output_dir: Annotated[
        Path, typer.Option("-o", "--output-dir", help="Output directory")
    ] = Path("."),
    json_only: Annotated[
        bool,
        typer.Option("--json-only", help="Only generate JSON output"),
    ] = False,
    html_only: Annotated[
        bool,
        typer.Option("--html-only", help="Only generate HTML output"),
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option("-r", "--recursive",
                     help="Recursively scan include directories"),
    ] = False,
    filelist: Annotated[
        list[Path] | None,
        typer.Option("-f", "--filelist",
                     help="Filelist (.f) files to parse"),
    ] = None,
) -> None:
    """Parse SystemVerilog files and generate a refbook."""
    if json_only and html_only:
        typer.echo("Error: --json-only and --html-only are mutually exclusive",
                   err=True)
        raise typer.Exit(code=1)

    all_files: list[Path] = []
    all_incdirs: list[Path] = list(include_dir or [])

    if filelist:
        for flist in filelist:
            if not flist.exists():
                typer.echo(f"Error: filelist not found: {flist}", err=True)
                raise typer.Exit(code=1)
            fl_sources, fl_incdirs = parse_filelist(flist)
            all_files.extend(fl_sources)
            all_incdirs.extend(fl_incdirs)

    if files:
        for f in files:
            if "*" in str(f):
                expanded = sorted(Path(p) for p in globmod.glob(str(f)))
                all_files.extend(expanded)
            else:
                if not f.exists():
                    typer.echo(f"Error: file not found: {f}", err=True)
                    raise typer.Exit(code=1)
                all_files.append(f)

    if not files and not filelist:
        typer.echo("Error: provide source files or --filelist", err=True)
        raise typer.Exit(code=1)

    for d in all_incdirs:
        if not d.is_dir():
            typer.echo(f"Error: include directory not found: {d}", err=True)
            raise typer.Exit(code=1)

    for d in all_incdirs:
        pattern = "**/*.sv" if recursive else "*.sv"
        all_files.extend(sorted(d.glob(pattern)))

    if not all_files:
        typer.echo("Error: no SystemVerilog files to process", err=True)
        raise typer.Exit(code=1)

    refbook = analyze(all_files)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = []

    if not html_only:
        json_path = output_dir / "refbook.json"
        json_path.write_text(
            json.dumps(refbook.model_dump(), indent=2) + "\n"
        )
        outputs.append(str(json_path))

    if not json_only:
        html_path = output_dir / "index.html"
        html_path.write_text(generate_html(refbook))
        outputs.append(str(html_path))

    typer.echo(
        f"Generated {' and '.join(outputs)} ({len(refbook.types)} types)"
    )


@app.command()
def decode(
    refbook_path: Annotated[
        Path, typer.Argument(help="Path to refbook.json"),
    ],
    type_name: Annotated[
        str, typer.Argument(help="Type name to decode (e.g. packet_t)"),
    ],
    hex_value: Annotated[
        str, typer.Argument(help="Hex value to decode (e.g. ABCD)"),
    ],
) -> None:
    """Decode a hex value using a previously generated refbook."""
    if not refbook_path.exists():
        typer.echo(f"Error: refbook not found: {refbook_path}", err=True)
        raise typer.Exit(code=1)

    refbook = load_refbook(refbook_path)
    sv_type = find_type(refbook, type_name)

    if sv_type is None:
        available = [t.name for t in refbook.types]
        typer.echo(f"Error: type '{type_name}' not found", err=True)
        typer.echo(f"Available types: {', '.join(available)}", err=True)
        raise typer.Exit(code=1)

    rows = decode_hex(sv_type, hex_value)

    hex_str = hex_value.lstrip("0x").lstrip("0X") or "0"
    typer.echo(f"{sv_type.name} [{sv_type.total_width} bits] = 0x{hex_str.upper()}")
    typer.echo("-" * 60)
    typer.echo(f"{'Name':<20} {'Bits':<12} {'Hex':<12} {'Decoded'}")
    typer.echo("-" * 60)

    for row in rows:
        indent = "  " * row["depth"]
        name = f"{indent}{row['name']}"
        typer.echo(f"{name:<20} {row['bits']:<12} {row['hex']:<12} {row['decoded']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
