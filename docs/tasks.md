sv-ref Implementation Tasks

Version: 1.0.0
Date: 2026-02-07

Each task is designed to be completable in a single Claude Code session.
Tasks are ordered by dependency. Each task has clear input, output, and
acceptance criteria.


Legend:
  [x] Done
  [ ] Not started
  Status: DONE | READY | BLOCKED (by T-XX)


T-00: Design Documentation [x]
============================================================
  Description: Create architecture.md, update specification.md, create
               tasks.md, create CLAUDE.md
  Input:       pyslang API verification results (check_pyslang.py)
  Output:      docs/architecture.md, docs/specification.md (v0.2.0),
               docs/tasks.md, CLAUDE.md
  Acceptance:  All 4 documents exist and are internally consistent
  Dependencies: None
  Status: DONE


T-01: Package Structure + Pydantic Models [x]
============================================================
  Description: Create the sv_ref package directory structure and implement
               all Pydantic models in sv_ref/core/models.py.
               Write unit tests for model creation and JSON serialization.

  Input:       Schema definition from docs/specification.md Section 4
  Output:
    - sv_ref/__init__.py
    - sv_ref/core/__init__.py
    - sv_ref/core/models.py
    - tests/__init__.py
    - tests/test_models.py

  Implementation Details:
    Models to implement (see docs/architecture.md Section 4.1):
      TypeKind(str, Enum): "struct" | "enum"
      EnumMember(BaseModel): name (str), value (int)
      FieldType(BaseModel): name (str), kind (TypeKind | None), signed (bool)
      StructField(BaseModel): name, width, offset, field_type, inner_fields, enum_members
      SVType(BaseModel): name, kind, total_width, package, fields, members
      RefbookMeta(BaseModel): version, generated_at, source_files
      Refbook(BaseModel): meta, types

  Tests (tests/test_models.py):
    - test_enum_member_creation
    - test_field_type_creation_primitive
    - test_field_type_creation_user_type
    - test_struct_field_simple
    - test_struct_field_with_inner_fields (nested struct)
    - test_struct_field_with_enum_members
    - test_svtype_struct
    - test_svtype_enum
    - test_refbook_json_serialization
    - test_refbook_json_round_trip

  Acceptance: uv run pytest tests/test_models.py -v -> all pass
  Dependencies: T-00
  Status: DONE


T-02: Test Fixtures + Analyzer Core [x]
============================================================
  Description: Create SystemVerilog test fixtures and implement the core
               analyzer that bridges pyslang and Pydantic models.

  Input:       pyslang API patterns from docs/architecture.md Section 3
  Output:
    - tests/samples/basic_types.sv
    - tests/samples/nested.sv
    - tests/samples/signed_types.sv
    - sv_ref/core/analyzer.py
    - tests/test_analyzer.py
    - tests/conftest.py

  Test Fixtures:

    tests/samples/basic_types.sv:
      package test_pkg;
          typedef enum logic [1:0] { IDLE=0, BUSY=1, ERR=2 } state_e;
          typedef struct packed {
              logic [7:0] header;
              state_e status;
              logic [5:0] payload;
          } packet_t;
      endpackage

    tests/samples/nested.sv:
      package test_pkg;
          typedef struct packed { logic [7:0] a; logic [7:0] b; } inner_t;
          typedef struct packed { inner_t data; logic [15:0] extra; } outer_t;
      endpackage

    tests/samples/signed_types.sv:
      package test_pkg;
          typedef struct packed {
              logic signed [7:0] signed_val;
              logic [7:0] unsigned_val;
          } mixed_t;
      endpackage

  Implementation (sv_ref/core/analyzer.py):
    Public API:
      analyze(source_files: list[Path]) -> Refbook

    Internal functions:
      _extract_package_types(pkg_sym, pkg_name: str) -> list[SVType]
      _extract_struct(alias_sym, actual_type, pkg_name: str) -> SVType
      _extract_enum(alias_sym, actual_type, pkg_name: str) -> SVType
      _extract_field(field_sym) -> StructField
      _extract_enum_member(ev_sym) -> EnumMember
      _parse_sv_literal(s: str) -> int
      _get_field_type(field_sym) -> FieldType
      _determine_type_kind(type_obj) -> TypeKind | None

    Key patterns (from docs/architecture.md):
      - Filter SymbolKind.TypeAlias (skip TransparentMember)
      - Level 3 access: alias_sym.targetType.type
      - Nested struct: field.type.canonicalType -> iterate if isStruct
      - Enum values: str(ev.value) -> _parse_sv_literal()
      - Field type name: ft.name if ft.isAlias else str(ft)

  Tests (tests/test_analyzer.py):
    - test_analyze_enum (state_e: 3 members, width=2)
    - test_analyze_simple_struct (packet_t: 3 fields, width=16, correct offsets)
    - test_analyze_enum_field_inline (packet_t.status has enum_members)
    - test_analyze_nested_struct (outer_t.data has inner_fields)
    - test_analyze_signed_field (mixed_t.signed_val.field_type.signed == True)
    - test_analyze_package_name (all types have package="test_pkg")
    - test_analyze_multiple_files
    - test_analyze_empty_package (no types -> empty list)
    - test_refbook_meta (version, source_files populated)

  Acceptance: uv run pytest tests/test_analyzer.py -v -> all pass
  Dependencies: T-01
  Status: DONE


T-03: CLI (Typer) + JSON Output [x]
============================================================
  Description: Implement Typer CLI entrypoint that accepts .sv files,
               calls the analyzer, and writes refbook.json.

  Input:       analyzer.analyze() API from T-02
  Output:
    - sv_ref/main.py (replace existing placeholder)
    - tests/test_cli.py
    - pyproject.toml update ([project.scripts])

  Implementation (sv_ref/main.py):
    Typer app with `generate` command:
      sv-ref generate <files...> [-I <include_dir>] [-o <output_dir>]

    Logic:
      1. Validate input files exist
      2. Call analyze(files)
      3. Write refbook.json to output dir
      4. Print summary to stdout

  Tests (tests/test_cli.py):
    - test_generate_json_output (file written, valid JSON)
    - test_generate_with_include_dir
    - test_generate_missing_file (error message)
    - test_generate_output_dir_creation

  Acceptance: uv run pytest tests/test_cli.py -v -> all pass
              uv run sv-ref generate tests/samples/basic_types.sv -> produces valid JSON
  Dependencies: T-02
  Status: DONE


T-04: HTML Viewer [x]
============================================================
  Description: Implement Jinja2-based HTML generator and the single-page
               Hex Decoder UI.

  Input:       Refbook model, refbook.json
  Output:
    - sv_ref/generator/__init__.py
    - sv_ref/generator/html.py
    - sv_ref/templates/index.html.j2
    - tests/test_html_generator.py
    - Update sv_ref/main.py to also output index.html

  Implementation:
    - Vanilla JS + CSS (no framework)
    - Type list sidebar + hex decoder main area
    - JSON embedded as <script type="application/json">
    - Recursive bit field visualization for nested structs
    - Enum value name display in decoded output

  Tests (tests/test_html_generator.py):
    - test_html_generation (valid HTML output)
    - test_html_contains_json (embedded JSON present)
    - test_html_self_contained (no external dependencies)

  Acceptance: uv run pytest tests/test_html_generator.py -v -> all pass
              Generated HTML opens in browser and decodes hex values
  Dependencies: T-03
  Status: DONE


T-05: Snapshot Tests + Edge Cases [x]
============================================================
  Description: Add syrupy snapshot tests for JSON output stability.
               Add edge case test fixtures and handle them.

  Input:       Working analyzer + CLI from T-02, T-03
  Output:
    - tests/test_snapshots.py
    - tests/samples/edge_cases.sv (parameterized types, wide enums, etc.)
    - Snapshot files under tests/__snapshots__/

  Test Cases:
    - Snapshot of basic_types.sv output
    - Snapshot of nested.sv output
    - Parameterized struct (parameter WIDTH = 8; logic [WIDTH-1:0] data)
    - Enum with non-sequential values
    - Large struct (many fields)
    - Multiple packages in one file

  Acceptance: uv run pytest tests/test_snapshots.py -v -> all pass
  Dependencies: T-03
  Status: DONE


T-06: Documentation + Packaging [x]
============================================================
  Description: Write README.md, finalize pyproject.toml metadata,
               ensure uv run sv-ref --help works, create demo.

  Input:       Complete working tool from T-01 through T-05
  Output:
    - README.md (usage, installation, examples)
    - pyproject.toml (complete metadata)
    - Demo script or Makefile for generating sample output

  Acceptance: uv run sv-ref --help shows correct usage
              README.md has installation + usage sections
  Dependencies: T-04, T-05
  Status: DONE


T-07: Project Hygiene + Version Sync [x]
============================================================
  Description: Fix all project infrastructure issues. Create LICENSE file,
               .gitignore, remove dev artifacts, fix version sync via
               importlib.metadata, fix code style violations.

  Input:       Existing v0.1.0 codebase
  Output:
    - LICENSE (new, MIT)
    - .gitignore (new, Python standard)
    - check_pyslang.py (delete)
    - sv_ref/__init__.py (expose __version__)
    - sv_ref/core/analyzer.py (remove hardcoded VERSION)
    - sv_ref/main.py (fix Optional[] -> X | None)
    - pyproject.toml (version -> 0.3.0b1)
    - tests/test_analyzer.py (fix version assertion)
    - tests/__snapshots__/ (regenerate)

  Implementation Details:
    LICENSE:
      Standard MIT text, Copyright 2026 HTsulfuric

    .gitignore:
      __pycache__/, *.pyc, *.egg-info/, dist/, build/, .venv/,
      .pytest_cache/, .ruff_cache/, demo_output/

    sv_ref/__init__.py:
      from importlib.metadata import version
      __version__ = version("sv-ref")

    sv_ref/core/analyzer.py:
      Remove VERSION = "0.1.0"
      Import __version__ from sv_ref
      Use __version__ in RefbookMeta

    sv_ref/main.py:
      Remove `from typing import Optional`
      Change Optional[list[Path]] -> list[Path] | None

    tests/test_analyzer.py:
      Fix test_refbook_meta to assert version == __version__ (dynamic)

  Acceptance:
    - uv run pytest tests/ -v -> all pass
    - LICENSE file exists
    - .gitignore file exists
    - check_pyslang.py is deleted
    - uv run python -c "from sv_ref import __version__; print(__version__)" -> 0.3.0b1
  Dependencies: T-06
  Status: DONE


T-08: CLI Enhancements (filelist, recursive, output flags) [x]
============================================================
  Description: Add real-world CLI capabilities: filelist (.f) support,
               recursive directory scanning, --json-only/--html-only flags,
               --version flag. Make positional files argument optional when
               filelist is provided.

  Input:       Clean codebase from T-07
  Output:
    - sv_ref/core/filelist.py (new)
    - sv_ref/main.py (updated)
    - tests/test_filelist.py (new)
    - tests/test_cli.py (updated)

  Implementation Details:
    sv_ref/core/filelist.py:
      parse_filelist(path: Path) -> tuple[list[Path], list[Path]]
      - Returns (source_files, include_dirs)
      - One path per line
      - # and // comments
      - +incdir+<path> directives
      - Relative paths resolved from filelist parent dir
      - Unknown directives (+define+, -sv, etc.) silently skipped

    sv_ref/main.py changes:
      1. --version flag (eager callback, prints "sv-ref <version>")
      2. --json-only flag (skip HTML generation)
      3. --html-only flag (skip JSON generation)
      4. Error if both --json-only and --html-only
      5. -r / --recursive flag (use rglob instead of glob for -I dirs)
      6. -f / --filelist option (parse .f files, add sources + incdirs)
      7. Make files argument optional (list[Path] | None = None)
      8. Glob pattern expansion in files argument (if "*" in path)

    Tests (tests/test_filelist.py):
      - test_parse_filelist_basic
      - test_parse_filelist_comments
      - test_parse_filelist_incdir
      - test_parse_filelist_relative_paths
      - test_parse_filelist_unknown_directives

    Tests (tests/test_cli.py additions):
      - test_version_flag
      - test_generate_json_only
      - test_generate_html_only
      - test_generate_mutually_exclusive_flags
      - test_generate_recursive_include
      - test_filelist_cli_integration

  Acceptance:
    - uv run pytest tests/test_filelist.py tests/test_cli.py -v -> all pass
    - uv run sv-ref --version -> prints version
    - uv run sv-ref generate --json-only tests/samples/basic_types.sv -o /tmp/t -> no index.html
    - uv run sv-ref generate -f <filelist> -o /tmp/t -> works
  Dependencies: T-07
  Status: DONE


T-09: Terminal Decode Command [x]
============================================================
  Description: Add `sv-ref decode` subcommand for terminal-based hex decoding.
               No browser needed. Reads a previously-generated refbook.json
               and prints a field breakdown table to stdout.

  Input:       CLI from T-08
  Output:
    - sv_ref/decoder.py (new)
    - sv_ref/main.py (add decode command)
    - tests/test_decode.py (new)

  Implementation Details:
    sv_ref/decoder.py:
      Public API:
        load_refbook(path: Path) -> Refbook
        find_type(refbook: Refbook, type_name: str) -> SVType | None
        decode_hex(sv_type: SVType, hex_value: str) -> list[dict]

      find_type: match by name, also try pkg::name
      decode_hex:
        - Parse hex string, extract field values via bit masking
        - For each field: compute (value >> offset) & mask
        - Resolve enum members by value match
        - Handle signed fields (two's complement)
        - Return list of row dicts: name, bits, hex, decoded, depth
        - Python int handles arbitrary precision (no BigInt issue)

    sv_ref/main.py:
      @app.command()
      def decode(refbook_path, type_name, hex_value):
        Load refbook, find type, decode, print table
        Print format:
          packet_t [16 bits] = 0xABCD
          ------------------------------------------------------------
          Name                 Bits         Hex          Decoded
          ------------------------------------------------------------
          header               [15:8]       0xAB         171
          status               [7:6]        0x02         ERR
          payload              [5:0]        0x0D         13

    Tests (tests/test_decode.py):
      - test_decode_struct (fields in output)
      - test_decode_enum (member name matched)
      - test_decode_type_not_found (error + available types listed)
      - test_decode_nested_struct (inner fields indented)
      - test_decode_signed_field (negative value decoded)

  Acceptance:
    - uv run pytest tests/test_decode.py -v -> all pass
    - uv run sv-ref decode refbook.json packet_t ABCD -> readable table
  Dependencies: T-08
  Status: DONE


T-10: BigInt Fix in HTML Viewer [x]
============================================================
  Description: Fix the critical bug where parseInt() silently corrupts
               values for types wider than 53 bits. Replace all binary/hex
               string-to-number conversions with BigInt equivalents.

  Input:       HTML template from T-04
  Output:
    - sv_ref/templates/index.html.j2 (updated)
    - tests/samples/wide_types.sv (new)
    - tests/test_html_generator.py (updated)

  Implementation Details:
    New BigInt helper functions (add near top of <script>):
      binToBigInt(b) -> BigInt("0b" + b)
      bigIntToHex(val, hexLen) -> "0x" + padded hex string

    Call sites to fix (13 total):
      1. updateHexStatus: Math.pow(2,N)-1 -> (1n << BigInt(N)) - 1n
      2. updateHexStatus: parseInt(hexStr,16) -> BigInt("0x" + hexStr)
      3. decode overflow: same pattern as #1 and #2
      4. bitsToHex: parseInt(b,2) -> binToBigInt(b)
      5. findEnumName: parseInt(bits,2) -> binToBigInt(bits)
      6. findEnumName: members[i].value === val -> BigInt(m.value) === val
      7. renderStructFields signed: parseInt(fieldBits,2) -> binToBigInt
      8. renderStructFields signed: (1 << f.width) -> (1n << BigInt(f.width))
      9. renderEnumMembers: parseInt(bits,2) -> binToBigInt
     10. renderEnumMembers: m.value.toString(16) -> BigInt(m.value).toString(16)
     11. renderEnumMembers: m.value === currentVal -> BigInt(m.value) === currentVal
     12. renderEnumMembers display: parseInt(bits,2) -> binToBigInt
     13. renderEnumMembers no-match: parseInt(bits,2) -> binToBigInt

    SAFE (no change needed):
      - hexToBin: parses single hex chars (0-15), safe
      - selectType: parseInt(dataset.index), small integer, safe

    Test fixture (tests/samples/wide_types.sv):
      package wide_pkg;
          typedef struct packed {
              logic [63:0] upper;
              logic [63:0] lower;
          } wide128_t;
      endpackage

    Tests (tests/test_html_generator.py additions):
      - test_html_bigint_helpers (binToBigInt in output)
      - test_html_no_raw_parseint_binary (no parseInt(b,2) or parseInt(bits,2))

  Acceptance:
    - uv run pytest tests/test_html_generator.py -v -> all pass
    - Open generated HTML with 128-bit type, decode all Fs
      -> upper=0xFFFFFFFFFFFFFFFF, lower=0xFFFFFFFFFFFFFFFF (not corrupted)
  Dependencies: T-07
  Status: DONE


T-11: HTML UI Overhaul [x]
============================================================
  Description: Make the HTML viewer usable for large projects (200+ types).
               Add search, package grouping, keyboard navigation, URL hash
               routing, copy-to-clipboard, and light/dark theme toggle.

  Input:       BigInt-fixed template from T-10
  Output:
    - sv_ref/templates/index.html.j2 (updated)
    - tests/test_html_generator.py (updated)

  Implementation Details:
    1. Theme toggle (light/dark):
       - Add :root[data-theme="light"] CSS variables (Catppuccin Latte)
       - JS: initTheme() reads localStorage, toggleTheme() switches
       - Toggle button in sidebar header (sun/moon icon via CSS)
       - Persist to localStorage("sv-ref-theme")

    2. Sidebar search:
       - <input> above type list, placeholder "Search types... (/)"
       - Filters .type-item elements by name substring match
       - Also searches against package name

    3. Package grouping:
       - Group types by t.package in collapsible sections
       - .pkg-header element, click to toggle .collapsed class
       - Types hidden when parent group is collapsed
       - Search overrides collapsed state (show matching items)

    4. Keyboard navigation:
       - / -> focus search input
       - Escape -> clear search, blur input
       - ArrowDown/ArrowUp -> navigate visible type items
       - Enter -> focus hex input for selected type
       - Active item scrolled into view

    5. URL hash routing:
       - Format: #type=<name>&hex=<value>
       - loadFromHash() on page load -> auto-select type and decode
       - updateHash() called on selectType() and decode()
       - Uses history.replaceState (not pushState, to avoid back-button spam)

    6. Copy to clipboard:
       - Event delegation on #content div
       - .copyable class on hex values and decoded values
       - data-copy attribute holds the text to copy
       - Brief visual feedback (tooltip or highlight)
       - navigator.clipboard.writeText()

  Tests (tests/test_html_generator.py additions):
    - test_html_search_input (search input element present)
    - test_html_theme_toggle (data-theme, toggleTheme in output)
    - test_html_keyboard_nav (keydown listener present)
    - test_html_url_hash (loadFromHash function present)

  Acceptance:
    - uv run pytest tests/test_html_generator.py -v -> all pass
    - Manual browser test: all 6 features work
    - 200+ type sidebar scrolls and filters correctly
  Dependencies: T-10
  Status: DONE


T-12: Documentation + Final Polish [x]
============================================================
  Description: Update all documentation for v0.3.0-beta. Update README
               with new features, update CLAUDE.md directory structure,
               update specification.md version.

  Input:       Complete v0.3.0-beta from T-07 through T-11
  Output:
    - README.md (updated)
    - CLAUDE.md (updated)
    - docs/specification.md (updated)
    - docs/tasks.md (all tasks marked done)

  Implementation Details:
    README.md:
      - Update arguments table with new flags
      - Add Decode Command section with example
      - Add Filelist section with .f format example
      - Update HTML Viewer section with new features
      - Add Keyboard Shortcuts section

    CLAUDE.md:
      - Add decoder.py and filelist.py to directory structure
      - Add decode command to Commands section

    docs/specification.md:
      - Bump version to 0.3.0
      - Add filelist to Section 7.2 CLI Interface
      - Add decode subcommand

  Acceptance:
    - uv run pytest tests/ -v -> all pass (50+ tests)
    - uv run sv-ref --help -> shows generate and decode commands
    - uv run sv-ref --version -> 0.3.0b1
    - README has installation + usage + decode + filelist sections
  Dependencies: T-07, T-08, T-09, T-10, T-11
  Status: DONE


Task Dependency Graph
============================================================

  T-00..T-06 (v0.1.0)          [ALL DONE]
    |
    v
  T-07 (Project Hygiene)        [x]
    |
    +------+------+
    |             |
    v             v
  T-08 (CLI)   T-10 (BigInt)
    [x]           [x]
    |             |
    v             v
  T-09 (Decode) T-11 (UI)
    [x]           [x]
    |             |
    +------+------+
           |
           v
         T-12 (Docs)
           [x]


Session Workflow
============================================================

When starting a new session for task T-XX:

  1. Read CLAUDE.md (loaded automatically)
  2. Read this file (docs/tasks.md) to find the task
  3. Read docs/architecture.md for technical reference
  4. Read docs/specification.md Section 4 for schema reference
  5. Implement the task following the description
  6. Run acceptance criteria tests
  7. Mark task as done in this file
