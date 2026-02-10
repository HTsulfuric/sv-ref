from __future__ import annotations

from pathlib import Path

from sv_ref import __version__
from sv_ref.core.analyzer import analyze
from sv_ref.core.models import Refbook, TypeKind

SAMPLES_DIR = Path(__file__).parent / "samples"


def test_analyze_enum(basic_types_refbook: Refbook):
    state_e = next(t for t in basic_types_refbook.types if t.name == "state_e")
    assert state_e.kind == TypeKind.ENUM
    assert state_e.total_width == 2
    assert state_e.members is not None
    assert len(state_e.members) == 3
    assert state_e.members[0].name == "IDLE"
    assert state_e.members[0].value == 0
    assert state_e.members[1].name == "BUSY"
    assert state_e.members[1].value == 1
    assert state_e.members[2].name == "ERR"
    assert state_e.members[2].value == 2


def test_analyze_simple_struct(basic_types_refbook: Refbook):
    packet_t = next(t for t in basic_types_refbook.types if t.name == "packet_t")
    assert packet_t.kind == TypeKind.STRUCT
    assert packet_t.total_width == 16
    assert packet_t.fields is not None
    assert len(packet_t.fields) == 3

    header = packet_t.fields[0]
    assert header.name == "header"
    assert header.width == 8
    assert header.offset == 8

    status = packet_t.fields[1]
    assert status.name == "status"
    assert status.width == 2
    assert status.offset == 6

    payload = packet_t.fields[2]
    assert payload.name == "payload"
    assert payload.width == 6
    assert payload.offset == 0


def test_analyze_enum_field_inline(basic_types_refbook: Refbook):
    packet_t = next(t for t in basic_types_refbook.types if t.name == "packet_t")
    status = next(f for f in packet_t.fields if f.name == "status")
    assert status.field_type.name == "state_e"
    assert status.field_type.kind == TypeKind.ENUM
    assert status.enum_members is not None
    assert len(status.enum_members) == 3
    assert status.enum_members[0].name == "IDLE"


def test_analyze_nested_struct(nested_refbook: Refbook):
    outer_t = next(t for t in nested_refbook.types if t.name == "outer_t")
    assert outer_t.total_width == 32

    data_field = next(f for f in outer_t.fields if f.name == "data")
    assert data_field.field_type.name == "inner_t"
    assert data_field.field_type.kind == TypeKind.STRUCT
    assert data_field.inner_fields is not None
    assert len(data_field.inner_fields) == 2
    assert data_field.inner_fields[0].name == "a"
    assert data_field.inner_fields[0].width == 8
    assert data_field.inner_fields[1].name == "b"
    assert data_field.inner_fields[1].width == 8


def test_analyze_signed_field(signed_refbook: Refbook):
    mixed_t = next(t for t in signed_refbook.types if t.name == "mixed_t")
    signed_val = next(f for f in mixed_t.fields if f.name == "signed_val")
    unsigned_val = next(f for f in mixed_t.fields if f.name == "unsigned_val")
    assert signed_val.field_type.signed is True
    assert unsigned_val.field_type.signed is False


def test_analyze_package_name(basic_types_refbook: Refbook):
    for t in basic_types_refbook.types:
        assert t.package == "test_pkg"


def test_analyze_multiple_files():
    refbook = analyze([
        SAMPLES_DIR / "basic_types.sv",
        SAMPLES_DIR / "nested.sv",
    ])
    names = {t.name for t in refbook.types}
    assert "state_e" in names
    assert "packet_t" in names
    assert "inner_t" in names
    assert "outer_t" in names


def test_analyze_empty_package():
    empty_sv = SAMPLES_DIR / "empty.sv"
    empty_sv.write_text("package empty_pkg;\nendpackage\n")
    try:
        refbook = analyze([empty_sv])
        assert len(refbook.types) == 0
    finally:
        empty_sv.unlink()


def test_refbook_meta(basic_types_refbook: Refbook):
    assert basic_types_refbook.meta.version == __version__
    assert len(basic_types_refbook.meta.source_files) == 1
    assert "basic_types.sv" in basic_types_refbook.meta.source_files[0]
    assert basic_types_refbook.meta.generated_at != ""
