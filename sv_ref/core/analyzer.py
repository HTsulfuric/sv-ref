from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pyslang

from sv_ref import __version__
from sv_ref.core.models import (
    EnumMember,
    FieldType,
    Refbook,
    RefbookMeta,
    StructField,
    SVType,
    TypeKind,
)

logger = logging.getLogger(__name__)


def analyze(
    source_files: list[Path],
    include_dirs: list[Path] | None = None,
) -> Refbook:
    inc_dirs = include_dirs or []
    bag = _make_options_bag(inc_dirs)
    sm = pyslang.SourceManager()
    comp = pyslang.Compilation(options=bag)
    for path in source_files:
        if inc_dirs:
            tree = pyslang.SyntaxTree.fromFile(str(path), sm, bag)
        else:
            tree = pyslang.SyntaxTree.fromFile(str(path))
        comp.addSyntaxTree(tree)

    root = comp.getRoot()
    types: list[SVType] = []
    seen: set[tuple[str, str]] = set()

    for cu in root:
        if cu.kind != pyslang.SymbolKind.CompilationUnit:
            continue
        for sym in cu:
            if sym.kind == pyslang.SymbolKind.Package:
                for sv_type in _extract_package_types(sym, sym.name):
                    key = (sv_type.package or "", sv_type.name)
                    if key not in seen:
                        seen.add(key)
                        types.append(sv_type)

    for sym in root:
        if sym.kind == pyslang.SymbolKind.Instance:
            _collect_instance_types(sym, types, seen)

    meta = RefbookMeta(
        version=__version__,
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_files=[str(f) for f in source_files],
    )
    return Refbook(meta=meta, types=types)


def _collect_instance_types(
    inst,
    types: list[SVType],
    seen: set[tuple[str, str]],
) -> None:
    body = inst.body
    module_name = body.name
    for sv_type in _extract_package_types(body, module_name):
        key = (sv_type.package or "", sv_type.name)
        if key not in seen:
            seen.add(key)
            types.append(sv_type)
    for child in body:
        if child.kind == pyslang.SymbolKind.Instance:
            _collect_instance_types(child, types, seen)


def _extract_package_types(pkg_sym, pkg_name: str) -> list[SVType]:
    types: list[SVType] = []
    for member in pkg_sym:
        if member.kind != pyslang.SymbolKind.TypeAlias:
            continue
        try:
            actual_type = member.targetType.type
            if member.isStruct:
                types.append(_extract_struct(member, actual_type, pkg_name))
            elif member.isEnum:
                types.append(_extract_enum(member, actual_type, pkg_name))
        except Exception:
            logger.warning("Failed to extract type '%s', skipping", member.name)
    return types


def _extract_struct(alias_sym, actual_type, pkg_name: str) -> SVType:
    fields = [_extract_field(f) for f in actual_type]
    return SVType(
        name=alias_sym.name,
        kind=TypeKind.STRUCT,
        total_width=alias_sym.bitWidth,
        package=pkg_name,
        fields=fields,
    )


def _extract_enum(alias_sym, actual_type, pkg_name: str) -> SVType:
    members = [_extract_enum_member(ev) for ev in actual_type]
    return SVType(
        name=alias_sym.name,
        kind=TypeKind.ENUM,
        total_width=alias_sym.bitWidth,
        package=pkg_name,
        members=members,
    )


def _extract_field(field_sym) -> StructField:
    ft = field_sym.type
    ct = ft.canonicalType

    field_type = _get_field_type(ft, ct)

    inner_fields = None
    enum_members = None

    if ct.isStruct:
        inner_fields = [_extract_field(f) for f in ct]
    elif ct.isEnum:
        enum_members = [_extract_enum_member(ev) for ev in ct]

    return StructField(
        name=field_sym.name,
        width=ft.bitWidth,
        offset=field_sym.bitOffset,
        field_type=field_type,
        inner_fields=inner_fields,
        enum_members=enum_members,
    )


def _extract_enum_member(ev_sym) -> EnumMember:
    return EnumMember(
        name=ev_sym.name,
        value=_parse_sv_literal(str(ev_sym.value)),
    )


def _parse_sv_literal(s: str) -> int:
    if "'b" in s:
        return int(s.split("'b")[1], 2)
    if "'d" in s:
        return int(s.split("'d")[1])
    if "'h" in s:
        return int(s.split("'h")[1], 16)
    if "'o" in s:
        return int(s.split("'o")[1], 8)
    return int(s)


def _get_field_type(ft, ct) -> FieldType:
    if ft.isAlias:
        name = ft.name
    else:
        name = str(ft)
    return FieldType(
        name=name,
        kind=_determine_type_kind(ct),
        signed=ct.isSigned,
    )


def _determine_type_kind(type_obj) -> TypeKind | None:
    if type_obj.isStruct:
        return TypeKind.STRUCT
    if type_obj.isEnum:
        return TypeKind.ENUM
    return None


def _make_options_bag(include_dirs: list[Path]) -> pyslang.Bag:
    prep_opts = pyslang.PreprocessorOptions()
    if include_dirs:
        prep_opts.additionalIncludePaths = include_dirs
    return pyslang.Bag([prep_opts])
