SystemVerilog Refbook Generator (sv-ref) - Specification

Version: 0.3.0
Date: 2026-02-10
Author: User & AI
Revision History:
  0.1.0 (2026-02-06) - Initial draft
  0.2.0 (2026-02-07) - Updated with pyslang API verification results
  0.3.0 (2026-02-10) - Added filelist, decode command, CLI enhancements, HTML UI overhaul


1. Project Overview

1.1. Background (Problem)

SystemVerilog development environments lack the tooling maturity of software
ecosystems (Rust/Python). During waveform debugging, engineers must mentally
map binary/hex values to source-level type definitions (struct/enum fields).
This imposes significant cognitive load. Existing tools are either limited to
static structure display or require expensive EDA licenses.

1.2. Objective (Solution)

Develop sv-ref, a CLI tool that parses and elaborates SystemVerilog source code
to generate a "Refbook" -- a semantic dictionary for interpreting waveform data
by humans and AI. The Refbook provides parameter-resolved bit widths and offsets,
enabling instant hex-to-struct decoding.

1.3. Core Values

  - Semantic Decoding: Convert binary data into meaningful field breakdowns.
  - Machine Readable: Output JSON schema that LLMs can understand for
    AI-assisted debugging.
  - Portable: No EDA licenses or heavy GUIs required. Runs in browser.


2. Scope Definition (MVP)

2.1. In-Scope

  - Target language: SystemVerilog (IEEE 1800-2017)
  - Analysis targets:
    - typedef struct packed (including nested packed structs)
    - typedef enum
    - Parameters that affect type widths
  - Analysis depth: Full elaboration via pyslang (parameter propagation/resolution)
  - Include path support: -I / --include-dir CLI option
  - Output artifacts:
    - refbook.json: Type info, bit widths, offsets, enum members
    - index.html: Single-page hex decoder application (JSON embedded)

2.2. Out-of-Scope

  - Complex include path auto-resolution (user specifies via -I flag)
  - interface / module port analysis (focus on data types)
  - Unpacked struct / union
  - Packed union (reserved for future iteration)
  - Class / Coverage / Assertion analysis
  - Encrypted IP analysis
  - Waveform file (VCD/FSDB) direct loading


3. System Architecture

3.1. Processing Flow

  1. CLI Input: User specifies .sv file(s) and optional -I paths
  2. Elaboration: pyslang builds AST, performs type checking and parameter
     resolution
  3. Extraction: Traverse compilation symbols, filter TypeAlias entries,
     extract struct fields and enum members into Pydantic models
  4. Generation:
     - refbook.json (data output)
     - index.html (viewer with embedded JSON)
  5. Serving: Open locally in browser or serve via local HTTP server

3.2. Technical Stack

  Category          Tool              Rationale
  -----------------------------------------------------------------------
  Package Manager   uv                Fast dependency resolution, reproducible
  Language          Python 3.11+      pyslang compatibility, type hints
  Parser Engine     pyslang 10.0.0+   Only Python library with full SV elaboration
  CLI Framework     Typer             Type-hint based argument definitions
  Data Schema       Pydantic          Validation and schema definition
  Templating        Jinja2            HTML generation
  Testing           pytest + syrupy   TDD and snapshot testing for JSON output
  Linter            Ruff              Code quality

3.3. pyslang API Access Pattern (Verified 2026-02-07)

  The pyslang Python API uses a 3-level model to access type information:

  Level 1: TypeAlias Symbol
    - Obtained by iterating Package members (filter SymbolKind.TypeAlias)
    - Provides: name, bitWidth, isStruct, isEnum
    - Note: Package members also include TransparentMember symbols (enum values
      promoted to package scope). These must be filtered out.

  Level 2: DeclaredType
    - Access via alias_sym.targetType
    - Intermediate wrapper managing type references

  Level 3: Actual Type (PackedStructType / EnumType)
    - Access via alias_sym.targetType.type
    - Iterable: yields FieldSymbol (struct) or EnumValueSymbol (enum)
    - Required for field decomposition

  For nested struct resolution:
    field.type.canonicalType -> resolves TypeAliasType to PackedStructType

  See docs/architecture.md Section 3 for complete API reference.


4. Data Structure Design (Revised Schema)

sv-ref outputs refbook.json conforming to the following Pydantic-based schema.

4.1. Schema Overview

  Refbook
    meta: RefbookMeta
    types: list[SVType]

  RefbookMeta
    version: str            -- sv-ref version
    generated_at: str       -- ISO 8601 timestamp
    source_files: list[str] -- input file paths

  SVType
    name: str               -- type name ("packet_t")
    kind: TypeKind          -- "struct" | "enum"
    total_width: int        -- total bit width
    package: str | None     -- package name ("my_pkg")
    fields: list[StructField] | None     -- struct fields (struct only)
    members: list[EnumMember] | None     -- enum members (enum only)

  StructField
    name: str               -- field name ("header")
    width: int              -- field bit width
    offset: int             -- bit offset from LSB (see 4.2)
    field_type: FieldType   -- type metadata
    inner_fields: list[StructField] | None  -- nested struct expansion
    enum_members: list[EnumMember] | None   -- inline enum members

  FieldType
    name: str               -- type name ("logic", "state_e")
    kind: TypeKind | None   -- None for primitives like logic
    signed: bool            -- True for signed types

  EnumMember
    name: str               -- member name ("IDLE")
    value: int              -- integer value (0)

4.2. Offset Semantics

  All offset values represent bit position from LSB (bit 0).
  This matches SystemVerilog packed struct semantics where the first declared
  field occupies the MSB and the last declared field starts at bit 0.

  Example:
    typedef struct packed {
        logic [7:0] header;   // offset=8, width=8 -> bits [15:8]
        logic [1:0] status;   // offset=6, width=2 -> bits [7:6]
        logic [5:0] payload;  // offset=0, width=6 -> bits [5:0]
    } packet_t;               // total_width=16

4.3. Denormalization

  StructField contains optional inner_fields and enum_members to make the
  HTML decoder self-contained without requiring cross-references:
  - inner_fields: recursively expanded when field type is a struct
  - enum_members: inlined when field type is an enum

  The top-level types list independently contains all struct and enum types
  for programmatic access.

4.4. ConstantValue (Enum Value) Parsing

  pyslang returns enum values as ConstantValue objects with SV literal
  string representation. Parsing rules:

    Format: <width>'<base><digits>
    Examples:
      "2'b0"   -> 0  (binary)
      "2'b10"  -> 2  (binary)
      "8'd255" -> 255 (decimal)
      "8'hff"  -> 255 (hexadecimal)
      "3'o7"   -> 7  (octal)

    Values containing X or Z bits are stored as -1 with a warning.

4.5. Example Output

{
  "meta": {
    "version": "0.1.0",
    "generated_at": "2026-02-07T12:00:00Z",
    "source_files": ["types.sv"]
  },
  "types": [
    {
      "name": "state_e",
      "kind": "enum",
      "total_width": 2,
      "package": "my_pkg",
      "fields": null,
      "members": [
        { "name": "IDLE", "value": 0 },
        { "name": "BUSY", "value": 1 },
        { "name": "ERR",  "value": 2 }
      ]
    },
    {
      "name": "packet_t",
      "kind": "struct",
      "total_width": 16,
      "package": "my_pkg",
      "fields": [
        {
          "name": "header",
          "width": 8,
          "offset": 8,
          "field_type": { "name": "logic", "kind": null, "signed": false },
          "inner_fields": null,
          "enum_members": null
        },
        {
          "name": "status",
          "width": 2,
          "offset": 6,
          "field_type": { "name": "state_e", "kind": "enum", "signed": false },
          "inner_fields": null,
          "enum_members": [
            { "name": "IDLE", "value": 0 },
            { "name": "BUSY", "value": 1 },
            { "name": "ERR",  "value": 2 }
          ]
        },
        {
          "name": "payload",
          "width": 6,
          "offset": 0,
          "field_type": { "name": "logic", "kind": null, "signed": false },
          "inner_fields": null,
          "enum_members": null
        }
      ],
      "members": null
    }
  ]
}


5. Development Roadmap (Revised)

  Day 1 (Done): Environment setup, pyslang API verification PoC
  Day 2 (Done): API verification complete, GO decision, design docs
  Day 3: Pydantic models (models.py) + unit tests
  Day 4: Analyzer core (analyzer.py) + integration tests
  Day 5: CLI (Typer) + JSON generation + end-to-end tests
  Day 6: HTML/JS Viewer (Hex Decoder UI)
  Day 7: Documentation, packaging, demo


6. Directory Structure

sv-ref/
  CLAUDE.md                     # Project instructions for AI sessions
  pyproject.toml                # uv configuration + scripts entry
  README.md
  docs/
    specification.md            # <- THIS FILE
    architecture.md             # Technical architecture + pyslang API ref
    tasks.md                    # Task breakdown for implementation
  sv_ref/                       # Source code
    __init__.py
    main.py                     # CLI entrypoint (Typer)
    decoder.py                  # Terminal hex decode logic
    core/
      __init__.py
      analyzer.py               # pyslang bridge
      filelist.py               # .f filelist parser
      models.py                 # Pydantic schemas
    generator/
      __init__.py
      html.py                   # Jinja2 rendering
    templates/
      index.html.j2             # HTML viewer template
  tests/
    __init__.py
    conftest.py                 # Shared fixtures
    test_models.py
    test_analyzer.py
    test_cli.py
    test_decode.py
    test_filelist.py
    test_html_generator.py
    test_snapshots.py
    samples/                    # Test SV files
      basic_types.sv
      nested.sv
      signed_types.sv
      edge_cases.sv
      wide_types.sv


7. Configuration

7.1. pyproject.toml Scripts Entry

  [project.scripts]
  sv-ref = "sv_ref.main:app"

7.2. CLI Interface

  sv-ref generate <files...> [options]
    - files: one or more .sv files (supports glob patterns, optional if -f used)
    - --include-dir / -I: additional include search paths (repeatable)
    - --output-dir / -o: output directory (default: ./)
    - --filelist / -f: filelist (.f) files to parse (repeatable)
    - --recursive / -r: recursively scan include directories
    - --json-only: only generate JSON output (skip HTML)
    - --html-only: only generate HTML output (skip JSON)
    - --version: show version and exit

  sv-ref decode <refbook.json> <type_name> <hex_value>
    - refbook.json: path to a previously generated refbook.json
    - type_name: type name to decode (e.g. packet_t)
    - hex_value: hex value to decode (e.g. ABCD)

7.3. Filelist Format (.f files)

  One path per line. Supports:
    - # and // comments
    - +incdir+<path> directives for include directories
    - Relative paths resolved from filelist parent directory
    - Unknown directives (+define+, -sv, etc.) silently skipped
