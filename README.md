# sv-ref

SystemVerilog packed struct/enum type definitions to JSON/HTML refbook generator.

Parses SystemVerilog source using [pyslang](https://github.com/MikePopoloski/slang)
and outputs bit-level field information for waveform debugging. The generated HTML
viewer lets you paste hex values and instantly decode them into named struct fields
and enum values.

## Installation

Requires Python 3.11+.

```bash
# Clone and install
git clone https://github.com/HTsulfuric/sv-ref.git
cd sv-ref
uv sync
```

## Usage

### Generate

```bash
sv-ref generate <files...> [options]
```

| Option | Description |
|---|---|
| `files` | One or more SystemVerilog source files (supports glob patterns) |
| `-I`, `--include-dir` | Include directories (auto-discovers `*.sv` files) |
| `-o`, `--output-dir` | Output directory (default: `.`) |
| `-f`, `--filelist` | Filelist (`.f`) files to parse (repeatable) |
| `-r`, `--recursive` | Recursively scan include directories |
| `--json-only` | Only generate JSON output (skip HTML) |
| `--html-only` | Only generate HTML output (skip JSON) |
| `--version` | Show version and exit |

### Decode

Decode a hex value in the terminal without opening a browser:

```bash
sv-ref decode <refbook.json> <type_name> <hex_value>
```

Example:

```bash
$ sv-ref decode refbook.json packet_t ABCD
packet_t [16 bits] = 0xABCD
------------------------------------------------------------
Name                 Bits         Hex          Decoded
------------------------------------------------------------
header               [15:8]       0xAB         171
status               [7:6]        0x02         ERR
payload              [5:0]        0x0D         13
```

### Filelist Support

Use `.f` files to specify source files and include directories:

```
# sources.f
rtl/types.sv
rtl/pkg.sv

# Include directories
+incdir+rtl/includes
+incdir+lib/common
```

```bash
sv-ref generate -f sources.f -o out/
```

### Example

Given a SystemVerilog file `types.sv`:

```systemverilog
package test_pkg;
    typedef enum logic [1:0] { IDLE=0, BUSY=1, ERR=2 } state_e;
    typedef struct packed {
        logic [7:0] header;
        state_e status;
        logic [5:0] payload;
    } packet_t;
endpackage
```

Run:

```bash
sv-ref generate types.sv -o out/
```

This produces two files in `out/`:

- **refbook.json** -- machine-readable type data with bit widths and offsets
- **index.html** -- self-contained HTML viewer with hex decoder

### JSON Output

The generated `refbook.json` contains all parsed types with field-level detail:

```json
{
  "meta": {
    "version": "0.3.0b1",
    "generated_at": "2026-02-07T00:00:00+00:00",
    "source_files": ["types.sv"]
  },
  "types": [
    {
      "name": "packet_t",
      "kind": "struct",
      "total_width": 16,
      "package": "test_pkg",
      "fields": [
        {
          "name": "header",
          "width": 8,
          "offset": 8,
          "field_type": { "name": "logic[7:0]", "kind": null, "signed": false }
        },
        {
          "name": "status",
          "width": 2,
          "offset": 6,
          "field_type": { "name": "state_e", "kind": "enum", "signed": false },
          "enum_members": [
            { "name": "IDLE", "value": 0 },
            { "name": "BUSY", "value": 1 },
            { "name": "ERR", "value": 2 }
          ]
        },
        {
          "name": "payload",
          "width": 6,
          "offset": 0,
          "field_type": { "name": "logic[5:0]", "kind": null, "signed": false }
        }
      ]
    }
  ]
}
```

### HTML Viewer

The generated `index.html` is a self-contained single-page app (no external dependencies).
Open it in any browser to:

- Browse all parsed types in a sidebar with package grouping
- Search types by name or package (`/` to focus)
- Paste a hex value to decode it into individual struct fields
- See enum member names resolved automatically
- View nested struct fields recursively
- Click any hex or decoded value to copy to clipboard
- Share decoded state via URL hash (`#type=packet_t&hex=ABCD`)
- Toggle light/dark theme (persisted to localStorage)

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `/` | Focus search input |
| `Escape` | Clear search, blur input |
| Arrow Up/Down | Navigate type list |
| `Enter` | Focus hex input for selected type |

## Supported Types

- Packed structs (`typedef struct packed`)
- Enums (`typedef enum`)
- Nested packed structs
- Signed/unsigned fields
- Parameterized types (resolved at elaboration)
- Multiple packages per file
- Wide types (>53 bits) via BigInt

Types must be defined inside a `package` block.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check sv_ref/ tests/

# Format
uv run ruff format sv_ref/ tests/

# Generate demo output
make demo
```

## License

MIT
