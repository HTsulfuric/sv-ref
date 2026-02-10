from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class TypeKind(str, Enum):
    STRUCT = "struct"
    ENUM = "enum"


class EnumMember(BaseModel):
    name: str
    value: int


class FieldType(BaseModel):
    name: str
    kind: TypeKind | None = None
    signed: bool = False


class StructField(BaseModel):
    name: str
    width: int
    offset: int
    field_type: FieldType
    inner_fields: list[StructField] | None = None
    enum_members: list[EnumMember] | None = None


class SVType(BaseModel):
    name: str
    kind: TypeKind
    total_width: int
    package: str | None = None
    fields: list[StructField] | None = None
    members: list[EnumMember] | None = None


class RefbookMeta(BaseModel):
    version: str
    generated_at: str
    source_files: list[str]


class Refbook(BaseModel):
    meta: RefbookMeta
    types: list[SVType]
