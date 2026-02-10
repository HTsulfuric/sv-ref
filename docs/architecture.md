sv-ref Architecture Document

Version: 0.2.0
Date: 2026-02-07
Status: Verified via PoC (check_pyslang.py v1-v5)


1. System Overview

sv-ref parses SystemVerilog source files, extracts packed struct/enum type
definitions with resolved bit widths and offsets, and outputs a machine-readable
JSON (Refbook) plus an HTML decoder UI.

    SV Files --> [pyslang] --> [Analyzer] --> [Pydantic Models] --> JSON / HTML


2. Module Responsibilities

2.1 sv_ref/core/models.py
    - Pydantic models defining the Refbook JSON schema
    - Pure data structures, no I/O or pyslang dependency
    - Public API: Refbook, SVType, StructField, EnumMember, FieldType, RefbookMeta

2.2 sv_ref/core/analyzer.py
    - Bridge between pyslang and Pydantic models
    - Creates pyslang Compilation, traverses AST, extracts types
    - Public API: analyze(source_files: list[Path]) -> Refbook

2.3 sv_ref/main.py
    - Typer CLI entrypoint
    - Argument parsing, file path resolution, output writing
    - Calls analyzer.analyze() and serializes result

2.4 sv_ref/generator/html.py
    - Jinja2-based HTML generation
    - Embeds JSON into single-page HTML viewer
    - Public API: generate_html(refbook: Refbook) -> str


3. pyslang API Reference (Verified)

All patterns below were verified against pyslang 10.0.0 on 2026-02-07.

3.1 Compilation Setup

    import pyslang

    tree = pyslang.SyntaxTree.fromText(sv_code)     # from string
    tree = pyslang.SyntaxTree.fromFile(str(path))    # from file

    comp = pyslang.Compilation()
    comp.addSyntaxTree(tree)

    diags = comp.getAllDiagnostics()    # check for errors
    root = comp.getRoot()              # RootSymbol

3.2 AST Traversal

    Symbols are iterable. Use `for child in symbol:` to walk children.

    root (RootSymbol)
      -> CompilationUnit
           -> Package (SymbolKind.Package)
                -> TransparentMember (enum values promoted to scope -- SKIP)
                -> TypeAlias (SymbolKind.TypeAlias -- TARGET)

    Filter: `member.kind == pyslang.SymbolKind.TypeAlias`

3.3 Type Resolution (3-Level Model)

    Level 1: TypeAlias Symbol
        - member.name             -> "packet_t"
        - member.bitWidth         -> 16
        - member.isStruct         -> True / False
        - member.isEnum           -> True / False

    Level 2: DeclaredType
        - member.targetType       -> DeclaredType object

    Level 3: Actual Type
        - member.targetType.type  -> PackedStructType or EnumType
        - This is the object you iterate for fields/members

    For bit width only: Level 1 is sufficient.
    For field decomposition: Level 3 is required.

3.4 PackedStructType (Struct Fields)

    actual_type = alias_sym.targetType.type   # PackedStructType
    for field in actual_type:                 # FieldSymbol
        field.name           # "header"
        field.kind           # SymbolKind.Field
        field.bitOffset      # 8 (bit position from LSB)
        field.fieldIndex     # 0 (declaration order)
        field.type           # TypeAliasType or PackedArrayType
        field.type.bitWidth  # 8
        field.type.isStruct  # False
        field.type.isEnum    # True / False
        field.type.isAlias   # True (user-defined) / False (primitive)
        field.type.name      # "state_e" (alias name, empty for primitives)
        field.type.isSigned  # True / False
        field.type.canonicalType  # resolves alias -> actual type

3.5 EnumType (Enum Members)

    actual_type = alias_sym.targetType.type   # EnumType
    actual_type.baseType                      # "logic[1:0]"
    for ev in actual_type:                    # EnumValueSymbol
        ev.name              # "IDLE"
        ev.kind              # SymbolKind.EnumValue
        ev.value             # ConstantValue (see 3.6)

3.6 ConstantValue Parsing

    str(ev.value) returns SV literal notation:
        "2'b0"    -> binary
        "2'b10"   -> binary
        "8'd255"  -> decimal
        "8'hff"   -> hexadecimal
        "3'o7"    -> octal

    Parsing algorithm:
        s = str(constant_value)
        if "'b" in s: int(s.split("'b")[1], 2)
        if "'d" in s: int(s.split("'d")[1])
        if "'h" in s: int(s.split("'h")[1], 16)
        if "'o" in s: int(s.split("'o")[1], 8)

    Edge case: values with X/Z bits (e.g., "4'bxx01") cannot be parsed to int.
    Strategy: store as -1 or None and log a warning.

3.7 Nested Struct Resolution

    When a struct field's type is another struct:
        field.type.isAlias == True
        field.type.canonicalType.isStruct == True
        field.type.canonicalType is iterable (yields inner FieldSymbols)

    Resolution path:
        field.type -> TypeAliasType
        field.type.canonicalType -> PackedStructType (iterable)

    This enables recursive field extraction.

3.8 Field Type Name Resolution

    For user-defined types (isAlias == True):
        field.type.name -> "state_e" (the typedef name)

    For primitive types (isAlias == False):
        str(field.type) -> "logic[5:0]" (full type string)
        field.type.name -> "" (empty)


4. Data Model Design

4.1 Type Hierarchy

    Refbook
      meta: RefbookMeta
      types: list[SVType]

    SVType
      name: str                     # "packet_t"
      kind: TypeKind                # "struct" | "enum"
      total_width: int              # 16
      package: str | None           # "my_pkg"
      fields: list[StructField]     # (struct only)
      members: list[EnumMember]     # (enum only)

    StructField
      name: str                     # "header"
      width: int                    # 8
      offset: int                   # bit offset from LSB
      field_type: FieldType         # type metadata
      inner_fields: list[StructField] | None   # recursive (nested struct)
      enum_members: list[EnumMember] | None    # inline (enum-typed field)

    FieldType
      name: str                     # "logic", "state_e"
      kind: TypeKind | None         # None for primitives
      signed: bool                  # False

    EnumMember
      name: str                     # "IDLE"
      value: int                    # 0

    RefbookMeta
      version: str                  # "0.1.0"
      generated_at: str             # ISO 8601
      source_files: list[str]       # input file paths

4.2 Offset Semantics

    All offsets are bit positions from LSB (bit 0).
    This matches pyslang's FieldSymbol.bitOffset behavior.

    Example: typedef struct packed {
        logic [7:0] header;   // offset=8, width=8 (bits 15:8)
        logic [1:0] status;   // offset=6, width=2 (bits 7:6)
        logic [5:0] payload;  // offset=0, width=6 (bits 5:0)
    } packet_t;               // total_width=16

4.3 Denormalization Strategy

    StructField.inner_fields: when a field's type is a struct, the inner fields
    are expanded inline. This duplicates data but makes the HTML decoder
    self-contained (no cross-reference needed at render time).

    StructField.enum_members: when a field's type is an enum, the members are
    inlined so the decoder can show symbolic names for values.

    The top-level SVType list still contains all types (structs and enums
    independently) for programmatic access.


5. Error Handling Strategy

5.1 pyslang Diagnostics
    - After compilation, check comp.getAllDiagnostics()
    - Fatal errors (parse failure): raise AnalysisError with diagnostic messages
    - Warnings: collect and include in Refbook.meta (future)

5.2 Type Extraction Failures
    - If a specific type cannot be extracted (unexpected structure): skip with
      warning, do not abort the entire run
    - Log skipped types to stderr

5.3 Input Validation
    - File existence: check before passing to pyslang
    - Empty output: if no types found, produce valid JSON with empty types list


6. Recursive Type Resolution Algorithm

    def extract_field(field_sym) -> StructField:
        ft = field_sym.type
        ct = ft.canonicalType

        field_type = FieldType(
            name = ft.name if ft.isAlias else str(ft),
            kind = determine_kind(ct),
            signed = ct.isSigned
        )

        inner_fields = None
        enum_members = None

        if ct.isStruct:
            inner_fields = [extract_field(f) for f in ct]
        elif ct.isEnum:
            enum_members = [extract_enum_member(ev) for ev in ct]

        return StructField(
            name = field_sym.name,
            width = ft.bitWidth,
            offset = field_sym.bitOffset,
            field_type = field_type,
            inner_fields = inner_fields,
            enum_members = enum_members,
        )

    Note: Packed structs cannot be self-referential, so infinite recursion
    is not possible. No depth limit needed.
