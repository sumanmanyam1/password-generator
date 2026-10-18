# PassGen — Command-Line Tool (CLI)

A command-line tool to generate, store, and retrieve secure passwords locally.
It uses the same Python engine (`backend/core/`) that powers the web app, and
all passwords are saved in a plain text file on your machine.

> For the web app (React frontend + Flask API), see the root `README.md`.

---

## Features

- Generates cryptographically secure passwords using Python's `secrets` module
- Every password is guaranteed to contain: 1 uppercase, 1 digit, 1 special char
- Stores passwords in a local plain text file (`backend/data/passwords.txt`)
- Retrieve any stored password by label
- Password strength analysis with detailed scoring
- Bulk password generation and export (CSV / JSON / TXT)
- Fully offline — no internet required

---

## Requirements

- Python 3.8+
- pip

---

## Setup

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

All CLI commands below are run from the `backend/` directory.

---

## Commands

### Generate a password (auto-saved to storage)
```bash
python cli/passgen.py generate --label github
python cli/passgen.py generate --label gmail --length 24
python cli/passgen.py generate --label netflix --length 20 --no-symbols
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--label` | required | Label for the password (e.g. github, gmail) |
| `--length` | 16 | Length of the password |
| `--no-symbols` | off | Exclude symbols `[]{}...` |
| `--no-digits` | off | Exclude digits `0-9` |
| `--no-upper` | off | Exclude uppercase letters |

---

### Retrieve a stored password
```bash
python cli/passgen.py get github
```

**Output:**
```
✓ Password for 'github': X7#kLmP2@qRvN!wZ
Show password strength analysis? [y/N]:
```

---

### List all stored labels
```bash
python cli/passgen.py list
```

**Output:**
```
📋 Stored passwords (3):

  Label                Length   Created At           Age
  -------------------- -------- -------------------- ----------
  github               16       2026-09-16 11:35:00  Today
  gmail                24       2026-09-16 11:36:00  Today
  netflix              20       2026-09-16 11:37:00  Today
```

---

### Delete a stored entry
```bash
python cli/passgen.py delete github
```

**Output:**
```
⚠️  You are about to delete the password for 'github'.
   This action cannot be undone.
Delete password for 'github'? [y/N]: y
✓ Successfully deleted 'github' from storage.
```

---

### Analyze password strength
```bash
python cli/passgen.py analyze --password mypassword
python cli/passgen.py analyze --label github
```

**Output:**
```
==================================================
PASSWORD STRENGTH ANALYSIS
==================================================

Password      : ***********
Length        : 11 characters
Score         : 44/100
Strength      : Weak
Estimated crack time: 2.1 years

DETAILED ANALYSIS:
--------------------
  ⚠ Adequate length — 12+ recommended
  ✗ Contains sequential numbers
  ✗ This is a very commonly used weak password
```

---

### Generate multiple passwords
```bash
python cli/passgen.py bulk --count 5 --save
python cli/passgen.py bulk --count 3 --length 20
```

---

### Export the vault
```bash
python cli/passgen.py export --format csv
python cli/passgen.py export --format json --include-passwords
```

---

## Storage File

Passwords are stored in `backend/data/passwords.txt`.

**Format:**
```
Password Storage File
==================================================
Format: Label | Password | Length | Created At
==================================================

github | X7#kLmP2@qRvN!wZ | 16 | 2026-09-16 11:35:00
gmail | Zy9$mNx3@wQ8rT2v | 24 | 2026-09-16 11:36:00
```

It is a plain text file you can open with any text editor.

---

## Project Structure

```
backend/
├── core/
│   ├── generator.py          # Password generation logic
│   ├── strength_analyzer.py  # Password strength analysis
│   └── storage.py            # Text file read/write operations
├── cli/
│   └── passgen.py            # CLI entry point
├── api/
│   └── app.py                # Flask API (used by the web frontend)
├── data/
│   └── passwords.txt         # Stored passwords
└── requirements.txt          # Dependencies
```

---

## Security Notes

- Passwords generated using Python's `secrets` module (cryptographically secure)
- Storage file is plain text for easy access
- File permissions set to `600` (owner read/write only)
- No encryption — passwords are readable in the text file

---

## Backup

To back up your passwords, copy `backend/data/passwords.txt` to a safe location.
The file is human-readable and can be opened with any text editor.

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| click | 8.1.7 | CLI interface |
