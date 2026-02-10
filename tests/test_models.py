from __future__ import annotations

import json

from sv_ref.core.models import (
    EnumMember,
    FieldType,
    Refbook,
    RefbookMeta,
    StructField,
    SVType,
    TypeKind,
)


def test_enum_member_creation():
    em = EnumMember(name="IDLE", value=0)
    assert em.name == "IDLE"
    assert em.value == 0


def test_field_type_creation_primitive():
    ft = FieldType(name="logic", kind=None, signed=False)
    assert ft.name == "logic"
    assert ft.kind is None
    assert ft.signed is False


def test_field_type_creation_user_type():
    ft = FieldType(name="state_e", kind=TypeKind.ENUM, signed=False)
    assert ft.name == "state_e"
    assert ft.kind == TypeKind.ENUM


def test_struct_field_simple():
    sf = StructField(
        name="header",
        width=8,
        offset=8,
        field_type=FieldType(name="logic", kind=None, signed=False),
    )
    assert sf.name == "header"
    assert sf.width == 8
    assert sf.offset == 8
    assert sf.inner_fields is None
    assert sf.enum_members is None


def test_struct_field_with_inner_fields():
    inner_a = StructField(
        name="a",
        width=8,
        offset=8,
        field_type=FieldType(name="logic", signed=False),
    )
    inner_b = StructField(
        name="b",
        width=8,
        offset=0,
        field_type=FieldType(name="logic", signed=False),
    )
    outer = StructField(
        name="data",
        width=16,
        offset=16,
        field_type=FieldType(name="inner_t", kind=TypeKind.STRUCT, signed=False),
        inner_fields=[inner_a, inner_b],
    )
    assert outer.inner_fields is not None
    assert len(outer.inner_fields) == 2
    assert outer.inner_fields[0].name == "a"
    assert outer.inner_fields[1].name == "b"


def test_struct_field_with_enum_members():
    members = [
        EnumMember(name="IDLE", value=0),
        EnumMember(name="BUSY", value=1),
        EnumMember(name="ERR", value=2),
    ]
    sf = StructField(
        name="status",
        width=2,
        offset=6,
        field_type=FieldType(name="state_e", kind=TypeKind.ENUM, signed=False),
        enum_members=members,
    )
    assert sf.enum_members is not None
    assert len(sf.enum_members) == 3
    assert sf.enum_members[2].name == "ERR"
    assert sf.enum_members[2].value == 2


def test_svtype_struct():
    fields = [
        StructField(
            name="header",
            width=8,
            offset=8,
            field_type=FieldType(name="logic", signed=False),
        ),
        StructField(
            name="payload",
            width=8,
            offset=0,
            field_type=FieldType(name="logic", signed=False),
        ),
    ]
    svt = SVType(
        name="packet_t",
        kind=TypeKind.STRUCT,
        total_width=16,
        package="my_pkg",
        fields=fields,
    )
    assert svt.name == "packet_t"
    assert svt.kind == TypeKind.STRUCT
    assert svt.total_width == 16
    assert svt.package == "my_pkg"
    assert svt.fields is not None
    assert len(svt.fields) == 2
    assert svt.members is None


def test_svtype_enum():
    members = [
        EnumMember(name="IDLE", value=0),
        EnumMember(name="BUSY", value=1),
    ]
    svt = SVType(
        name="state_e",
        kind=TypeKind.ENUM,
        total_width=2,
        package="my_pkg",
        members=members,
    )
    assert svt.kind == TypeKind.ENUM
    assert svt.members is not None
    assert len(svt.members) == 2
    assert svt.fields is None


def test_refbook_json_serialization():
    refbook = Refbook(
        meta=RefbookMeta(
            version="0.1.0",
            generated_at="2026-02-07T12:00:00Z",
            source_files=["types.sv"],
        ),
        types=[
            SVType(
                name="state_e",
                kind=TypeKind.ENUM,
                total_width=2,
                package="my_pkg",
                members=[
                    EnumMember(name="IDLE", value=0),
                    EnumMember(name="BUSY", value=1),
                ],
            ),
        ],
    )
    data = json.loads(refbook.model_dump_json())
    assert data["meta"]["version"] == "0.1.0"
    assert data["meta"]["source_files"] == ["types.sv"]
    assert len(data["types"]) == 1
    assert data["types"][0]["kind"] == "enum"
    assert data["types"][0]["members"][0]["name"] == "IDLE"


def test_refbook_json_round_trip():
    refbook = Refbook(
        meta=RefbookMeta(
            version="0.1.0",
            generated_at="2026-02-07T12:00:00Z",
            source_files=["test.sv"],
        ),
        types=[
            SVType(
                name="packet_t",
                kind=TypeKind.STRUCT,
                total_width=16,
                package="test_pkg",
                fields=[
                    StructField(
                        name="header",
                        width=8,
                        offset=8,
                        field_type=FieldType(name="logic", signed=False),
                    ),
                    StructField(
                        name="status",
                        width=2,
                        offset=6,
                        field_type=FieldType(
                            name="state_e", kind=TypeKind.ENUM, signed=False
                        ),
                        enum_members=[
                            EnumMember(name="IDLE", value=0),
                            EnumMember(name="BUSY", value=1),
                        ],
                    ),
                    StructField(
                        name="payload",
                        width=6,
                        offset=0,
                        field_type=FieldType(name="logic", signed=False),
                    ),
                ],
            ),
        ],
    )
    json_str = refbook.model_dump_json()
    restored = Refbook.model_validate_json(json_str)
    assert restored == refbook
    assert restored.types[0].fields[1].enum_members[0].name == "IDLE"
