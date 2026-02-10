from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sv_ref import __version__
from sv_ref.main import app

runner = CliRunner()

SAMPLES_DIR = Path(__file__).parent / "samples"


def test_generate_json_output(tmp_path: Path):
    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "-o", str(tmp_path),
    ])
    assert result.exit_code == 0

    out_file = tmp_path / "refbook.json"
    assert out_file.exists()
    assert (tmp_path / "index.html").exists()

    data = json.loads(out_file.read_text())
    assert "meta" in data
    assert "types" in data
    assert len(data["types"]) == 2
    names = {t["name"] for t in data["types"]}
    assert "state_e" in names
    assert "packet_t" in names


def test_generate_with_include_dir(tmp_path: Path):
    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "-I", str(SAMPLES_DIR),
        "-o", str(tmp_path),
    ])
    assert result.exit_code == 0

    data = json.loads((tmp_path / "refbook.json").read_text())
    names = {t["name"] for t in data["types"]}
    assert "state_e" in names
    assert "packet_t" in names


def test_generate_missing_file():
    result = runner.invoke(app, [
        "generate",
        "nonexistent.sv",
    ])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()


def test_generate_output_dir_creation(tmp_path: Path):
    out_dir = tmp_path / "sub" / "dir"
    assert not out_dir.exists()

    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "-o", str(out_dir),
    ])
    assert result.exit_code == 0
    assert out_dir.exists()
    assert (out_dir / "refbook.json").exists()
    assert (out_dir / "index.html").exists()


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"sv-ref {__version__}" in result.output


def test_generate_json_only(tmp_path: Path):
    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "--json-only",
        "-o", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "refbook.json").exists()
    assert not (tmp_path / "index.html").exists()


def test_generate_html_only(tmp_path: Path):
    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "--html-only",
        "-o", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert not (tmp_path / "refbook.json").exists()
    assert (tmp_path / "index.html").exists()


def test_generate_mutually_exclusive_flags(tmp_path: Path):
    result = runner.invoke(app, [
        "generate",
        str(SAMPLES_DIR / "basic_types.sv"),
        "--json-only",
        "--html-only",
        "-o", str(tmp_path),
    ])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_generate_include_dir_resolves_includes(tmp_path: Path):
    inc = tmp_path / "inc"
    inc.mkdir()

    header_sv = """\
typedef enum logic [1:0] {
    ST_IDLE = 2'b00,
    ST_RUN  = 2'b01
} common_state_e;
"""
    (inc / "common_defs.svh").write_text(header_sv)

    main_sv = """\
`include "common_defs.svh"
package inc_pkg;
    typedef struct packed {
        common_state_e state;
        logic [5:0]    data;
    } inc_frame_t;
endpackage
"""
    main_file = tmp_path / "main.sv"
    main_file.write_text(main_sv)

    out = tmp_path / "out"
    result = runner.invoke(app, [
        "generate",
        str(main_file),
        "-I", str(inc),
        "--json-only",
        "-o", str(out),
    ])
    assert result.exit_code == 0
    data = json.loads((out / "refbook.json").read_text())
    names = {t["name"] for t in data["types"]}
    assert "inc_frame_t" in names


def test_filelist_cli_integration(tmp_path: Path):
    flist = tmp_path / "sources.f"
    flist.write_text(f"{SAMPLES_DIR / 'basic_types.sv'}\n")

    out = tmp_path / "out"
    result = runner.invoke(app, [
        "generate",
        "-f", str(flist),
        "--json-only",
        "-o", str(out),
    ])
    assert result.exit_code == 0

    data = json.loads((out / "refbook.json").read_text())
    names = {t["name"] for t in data["types"]}
    assert "state_e" in names
    assert "packet_t" in names


def test_generate_no_files_no_filelist():
    result = runner.invoke(app, ["generate"])
    assert result.exit_code != 0
    assert "provide" in result.output.lower() or "error" in result.output.lower()
