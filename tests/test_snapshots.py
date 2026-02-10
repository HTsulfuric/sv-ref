from __future__ import annotations

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from sv_ref.core.analyzer import analyze

SAMPLES_DIR = Path(__file__).parent / "samples"

FIXED_TIMESTAMP = "2026-01-01T00:00:00+00:00"


def _snapshot_dict(refbook):
    d = refbook.model_dump()
    d["meta"]["generated_at"] = FIXED_TIMESTAMP
    d["meta"]["source_files"] = [Path(f).name for f in d["meta"]["source_files"]]
    return d


def test_basic_types_snapshot(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "basic_types.sv"])
    assert _snapshot_dict(refbook) == snapshot


def test_nested_snapshot(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "nested.sv"])
    assert _snapshot_dict(refbook) == snapshot


def test_edge_cases_snapshot(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "edge_cases.sv"])
    assert _snapshot_dict(refbook) == snapshot


def test_non_sequential_enum(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "edge_cases.sv"])
    sparse_e = next(t for t in refbook.types if t.name == "sparse_e")
    assert sparse_e.model_dump() == snapshot


def test_parameterized_struct(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "edge_cases.sv"])
    param_t = next(t for t in refbook.types if t.name == "param_t")
    assert param_t.model_dump() == snapshot


def test_large_struct(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "edge_cases.sv"])
    wide_t = next(t for t in refbook.types if t.name == "wide_t")
    assert wide_t.model_dump() == snapshot


def test_multiple_packages_in_one_file():
    refbook = analyze([SAMPLES_DIR / "edge_cases.sv"])
    packages = {t.package for t in refbook.types}
    assert "edge_pkg_a" in packages
    assert "edge_pkg_b" in packages


def test_module_types_snapshot(snapshot: SnapshotAssertion):
    refbook = analyze([SAMPLES_DIR / "module_types.sv"])
    assert _snapshot_dict(refbook) == snapshot
