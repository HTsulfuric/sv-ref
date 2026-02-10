from __future__ import annotations

from pathlib import Path

from sv_ref.core.filelist import parse_filelist


def test_parse_filelist_basic(tmp_path: Path):
    sv_file = tmp_path / "foo.sv"
    sv_file.write_text("// empty")
    flist = tmp_path / "files.f"
    flist.write_text("foo.sv\n")

    sources, incdirs = parse_filelist(flist)

    assert len(sources) == 1
    assert sources[0] == tmp_path / "foo.sv"
    assert incdirs == []


def test_parse_filelist_comments(tmp_path: Path):
    flist = tmp_path / "files.f"
    flist.write_text(
        "# comment line\n"
        "// another comment\n"
        "\n"
        "foo.sv\n"
    )

    sources, incdirs = parse_filelist(flist)

    assert len(sources) == 1
    assert sources[0].name == "foo.sv"


def test_parse_filelist_incdir(tmp_path: Path):
    inc = tmp_path / "inc"
    inc.mkdir()
    flist = tmp_path / "files.f"
    flist.write_text("+incdir+inc\n")

    sources, incdirs = parse_filelist(flist)

    assert sources == []
    assert len(incdirs) == 1
    assert incdirs[0] == tmp_path / "inc"


def test_parse_filelist_relative_paths(tmp_path: Path):
    sub = tmp_path / "sub"
    sub.mkdir()
    flist = sub / "files.f"
    flist.write_text("../top.sv\nlocal.sv\n")

    sources, _ = parse_filelist(flist)

    assert len(sources) == 2
    assert sources[0] == sub.resolve() / ".." / "top.sv"
    assert sources[1] == sub.resolve() / "local.sv"


def test_parse_filelist_unknown_directives(tmp_path: Path):
    flist = tmp_path / "files.f"
    flist.write_text(
        "+define+FOO=1\n"
        "-sv\n"
        "+incdir+.\n"
        "real.sv\n"
    )

    sources, incdirs = parse_filelist(flist)

    assert len(sources) == 1
    assert sources[0].name == "real.sv"
    assert len(incdirs) == 1
