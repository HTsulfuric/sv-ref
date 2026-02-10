from __future__ import annotations

import json
from pathlib import Path

from sv_ref.core.models import Refbook, StructField, SVType


def load_refbook(path: Path) -> Refbook:
    data = json.loads(path.read_text())
    return Refbook.model_validate(data)


def find_type(refbook: Refbook, type_name: str) -> SVType | None:
    for t in refbook.types:
        if t.name == type_name:
            return t
    for t in refbook.types:
        qualified = f"{t.package}::{t.name}" if t.package else t.name
        if qualified == type_name:
            return t
    return None


def decode_hex(sv_type: SVType, hex_value: str) -> list[dict]:
    hex_str = hex_value.lstrip("0x").lstrip("0X") or "0"
    full_value = int(hex_str, 16)

    if sv_type.fields is None:
        return []

    rows: list[dict] = []
    _decode_fields(sv_type.fields, full_value, 0, rows)
    return rows


def _decode_fields(
    fields: list[StructField],
    value: int,
    depth: int,
    rows: list[dict],
) -> None:
    for field in fields:
        mask = (1 << field.width) - 1
        raw_val = (value >> field.offset) & mask

        high_bit = field.offset + field.width - 1
        bits_str = f"[{high_bit}:{field.offset}]"

        hex_len = (field.width + 3) // 4
        hex_str = f"0x{raw_val:0{hex_len}X}"

        decoded = _decode_value(field, raw_val)

        rows.append({
            "name": field.name,
            "bits": bits_str,
            "hex": hex_str,
            "decoded": decoded,
            "depth": depth,
        })

        if field.inner_fields:
            _decode_fields(field.inner_fields, raw_val, depth + 1, rows)


def _decode_value(field: StructField, raw_val: int) -> str:
    if field.enum_members:
        for m in field.enum_members:
            if m.value == raw_val:
                return m.name

    if field.field_type.signed and raw_val >= (1 << (field.width - 1)):
        signed_val = raw_val - (1 << field.width)
        return str(signed_val)

    return str(raw_val)
