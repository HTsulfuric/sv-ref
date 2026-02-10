from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sv_ref.core.models import Refbook
from sv_ref.decoder import decode_hex, find_type, load_refbook
from sv_ref.main import app

runner = CliRunner()

SAMPLES_DIR = Path(__file__).parent / "samples"


@pytest.fixture
def basic_refbook_path(basic_types_refbook: Refbook, tmp_path: Path) -> Path:
    path = tmp_path / "refbook.json"
    path.write_text(json.dumps(basic_types_refbook.model_dump(), indent=2))
    return path


@pytest.fixture
def nested_refbook_path(nested_refbook: Refbook, tmp_path: Path) -> Path:
    path = tmp_path / "refbook.json"
    path.write_text(json.dumps(nested_refbook.model_dump(), indent=2))
    return path


@pytest.fixture
def signed_refbook_path(signed_refbook: Refbook, tmp_path: Path) -> Path:
    path = tmp_path / "refbook.json"
    path.write_text(json.dumps(signed_refbook.model_dump(), indent=2))
    return path


def test_load_refbook(basic_refbook_path: Path):
    rb = load_refbook(basic_refbook_path)
    assert isinstance(rb, Refbook)
    assert len(rb.types) == 2


def test_find_type_by_name(basic_types_refbook: Refbook):
    t = find_type(basic_types_refbook, "packet_t")
    assert t is not None
    assert t.name == "packet_t"


def test_find_type_by_qualified_name(basic_types_refbook: Refbook):
    t = find_type(basic_types_refbook, "test_pkg::packet_t")
    assert t is not None
    assert t.name == "packet_t"


def test_find_type_not_found(basic_types_refbook: Refbook):
    t = find_type(basic_types_refbook, "nonexistent_t")
    assert t is None


def test_decode_struct(basic_types_refbook: Refbook):
    # packet_t [16 bits]: header[15:8], status[7:6], payload[5:0]
    # 0xAB8D = 0b1010_1011_1000_1101
    # header = 0xAB = 171, status = 0b10 = 2 (ERR), payload = 0b001101 = 13
    sv_type = find_type(basic_types_refbook, "packet_t")
    assert sv_type is not None

    rows = decode_hex(sv_type, "AB8D")
    assert len(rows) == 3

    header = rows[0]
    assert header["name"] == "header"
    assert header["bits"] == "[15:8]"
    assert header["hex"] == "0xAB"
    assert header["decoded"] == "171"

    payload = rows[2]
    assert payload["name"] == "payload"
    assert payload["bits"] == "[5:0]"
    assert payload["hex"] == "0x0D"
    assert payload["decoded"] == "13"


def test_decode_enum(basic_types_refbook: Refbook):
    # packet_t status field: offset=6, width=2
    # 0xAB8D -> bits[7:6] = 0b10 = 2 -> ERR
    sv_type = find_type(basic_types_refbook, "packet_t")
    assert sv_type is not None

    rows = decode_hex(sv_type, "AB8D")
    status = rows[1]
    assert status["name"] == "status"
    assert status["decoded"] == "ERR"


def test_decode_type_not_found(basic_refbook_path: Path):
    result = runner.invoke(app, [
        "decode",
        str(basic_refbook_path),
        "nonexistent_t",
        "ABCD",
    ])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()
    assert "packet_t" in result.output or "packet_t" in (result.stderr or "")


def test_decode_nested_struct(nested_refbook: Refbook):
    # outer_t [32 bits]: data[31:16] (inner_t), extra[15:0]
    # inner_t: a[15:8], b[7:0]
    # 0x12345678 -> data=0x1234, extra=0x5678
    # data.a=0x12, data.b=0x34
    sv_type = find_type(nested_refbook, "outer_t")
    assert sv_type is not None

    rows = decode_hex(sv_type, "12345678")

    # data (depth 0), data.a (depth 1), data.b (depth 1), extra (depth 0)
    assert rows[0]["name"] == "data"
    assert rows[0]["depth"] == 0
    assert rows[0]["hex"] == "0x1234"

    assert rows[1]["name"] == "a"
    assert rows[1]["depth"] == 1
    assert rows[1]["hex"] == "0x12"

    assert rows[2]["name"] == "b"
    assert rows[2]["depth"] == 1
    assert rows[2]["hex"] == "0x34"

    assert rows[3]["name"] == "extra"
    assert rows[3]["depth"] == 0
    assert rows[3]["hex"] == "0x5678"


def test_decode_signed_field(signed_refbook: Refbook):
    # mixed_t [16 bits]: signed_val[15:8] (signed), unsigned_val[7:0]
    # 0xFF00 -> signed_val=0xFF=-1 (signed), unsigned_val=0x00=0
    sv_type = find_type(signed_refbook, "mixed_t")
    assert sv_type is not None

    rows = decode_hex(sv_type, "FF00")
    signed_row = rows[0]
    assert signed_row["name"] == "signed_val"
    assert signed_row["decoded"] == "-1"

    unsigned_row = rows[1]
    assert unsigned_row["name"] == "unsigned_val"
    assert unsigned_row["decoded"] == "0"


def test_decode_cli_output(basic_refbook_path: Path):
    result = runner.invoke(app, [
        "decode",
        str(basic_refbook_path),
        "packet_t",
        "AB8D",
    ])
    assert result.exit_code == 0
    assert "packet_t" in result.output
    assert "16 bits" in result.output
    assert "header" in result.output
    assert "ERR" in result.output
