from __future__ import annotations

import re

from sv_ref.core.models import Refbook
from sv_ref.generator.html import generate_html


def test_html_generation(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html
    assert "<title>" in html


def test_html_contains_json(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert 'type="application/json"' in html
    assert "packet_t" in html
    assert "state_e" in html


def test_html_self_contained(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    # No external CSS/JS dependencies
    assert "href=" not in html or 'href="http' not in html
    assert '<link rel="stylesheet"' not in html
    assert '<script src=' not in html


def test_html_bigint_helpers(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert "binToBigInt" in html
    assert "bigIntToHex" in html


def test_html_no_raw_parseint_binary(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    # No parseInt with binary radix (2) -- these should all be BigInt now
    # Allowed: parseInt(hex[i], 16) for single hex chars in hexToBin
    # Allowed: parseInt(items[i].dataset.index) for sidebar selection
    matches = re.findall(r"parseInt\([^)]*,\s*2\)", html)
    assert matches == [], f"Found raw parseInt with binary radix: {matches}"


def test_html_wide_type(wide_types_refbook: Refbook) -> None:
    html = generate_html(wide_types_refbook)
    assert "wide128_t" in html
    assert "wide_pkg" in html


def test_html_search_input(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert 'placeholder="Search types' in html
    assert "search-input" in html


def test_html_theme_toggle(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert "data-theme" in html
    assert "toggleTheme" in html
    assert "theme-toggle" in html


def test_html_keyboard_nav(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert "keydown" in html
    assert "ArrowDown" in html
    assert "kbd-highlight" in html


def test_html_url_hash(basic_types_refbook: Refbook) -> None:
    html = generate_html(basic_types_refbook)
    assert "loadFromHash" in html
    assert "updateHash" in html
    assert "replaceState" in html
