# sweepr

**sweepr** is a conservative multi-language static analysis CLI for finding and optionally removing safely identifiable unused code.

It is designed to be **backup-first**, **dry-run by default**, and easy to extend through language-specific analyzers.

## sweepr

- Scans entire folders recursively
- Supports Python, JavaScript/TypeScript, Go, and Java
- Detects unused imports, variables, functions, and classes where confidence is high
- Generates markdown reports for audits and pull requests
- Creates backups before modifying files
- Uses a modular parser architecture so contributors can add more languages

## Installation

### Install from GitHub

```bash
pipx install git+https://github.com/william-trann/sweepr.git
```

Or with pip:

```bash
pip install git+https://github.com/william-trann/sweepr.git
```

### Install from a local clone

```bash
git clone https://github.com/william-trann/sweepr.git
cd sweepr
pip install .
```

## Quick start

Dry run only:

```bash
sweepr . --dry-run
```

Apply safe fixes:

```bash
sweepr . --apply
```

Generate a markdown report:

```bash
sweepr . --report --report-file sweepr-report.md
```

Verbose output:

```bash
sweepr . --dry-run --verbose
```

## Safety model

sweepr is intentionally conservative.

### Auto-fix candidates
- Python unused imports
- Python obviously unused local variables in simple assignment patterns

### Report-only candidates
- Potentially unused private functions and classes
- JavaScript/TypeScript, Go, and Java findings that are not safe enough to rewrite blindly

### Backups
When `--apply` is used, original files are copied to `code_sifter_backup/` before any edits are written.

## Example output

```text
[DRY-RUN] src/demo.py
  - remove unused import: os
  - remove unused import: sys
  - remove unused variable: temp_value
```

## Project layout

```text
sweepr/
  pyproject.toml
  README.md
  LICENSE
  Makefile
  src/
    sweepr/
      cli.py
      scanner.py
      report.py
      backup.py
      logging_utils.py
      models.py
      parsers/
        python_parser.py
        javascript_parser.py
        go_parser.py
        java_parser.py
```

## Contributing

Each language analyzer lives in its own module under `src/sweepr/parsers/`.

To add a new language:
1. create a parser module
2. implement an analyzer with the same interface
3. register it in `scanner.py`

## Limitations

sweepr is not a compiler and does not perform whole program semantic analysis, reflection, runtime imports, decorators, and code generation may hide  usage from static analysis. That is why sweepr keeps many findings in report-only mode.

## License

MIT
