# PassGen — Simple Password Generator CLI

A command-line tool to generate, store, and retrieve secure passwords locally.
All passwords are saved in a **plain text file** on your machine for easy access.

---

## Features

- Generates cryptographically secure passwords using Python's `secrets` module
- Every password guaranteed to contain: 1 uppercase, 1 digit, 1 special character, 1 symbol
- Stores passwords in a local plain text file (`passwords.txt`)
- Retrieve any stored password by label
- Password strength analysis with detailed scoring
- Bulk password generation
- Fully offline — no internet required

---

## Requirements

- Python 3.8+
- pip

---

## Installation

1. Navigate to the project folder:
   ```bash
   cd "demo project 1/passgen"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Commands

### Generate a password (auto-saved to storage)
```bash
python passgen.py generate --label github
python passgen.py generate --label gmail --length 24
python passgen.py generate --label netflix --length 20 --no-symbols
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
python passgen.py get github
```

**Output:**
```
✓ Password for 'github': X7#kLmP2@qRvN!wZ
Show password strength analysis? [y/N]:
```

---

### List all stored labels
```bash
python passgen.py list
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
python passgen.py delete github
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
python passgen.py analyze --password mypassword
python passgen.py analyze --label github
```

**Output:**
```
==================================================
PASSWORD STRENGTH ANALYSIS
==================================================

Password: ***********
Length: 11 characters
Score: 44/100
Strength: Weak
Estimated crack time: 2.1 years

DETAILED ANALYSIS:
--------------------
  ⚠ Adequate length (8+ characters)
  ⚠ Uses only 2 character types
  ✓ High character uniqueness
  ✗ Contains sequential numbers
  ✗ This is a commonly used weak password
```

---

### Generate multiple passwords
```bash
python passgen.py bulk --count 5 --save
python passgen.py bulk --count 3 --length 20
```

---

## Storage File

Passwords are stored in `passwords.txt` in the project folder.

**Format:**
```
Password Storage File
==================================================
Format: Label | Password | Length | Created At
==================================================

github | X7#kLmP2@qRvN!wZ | 16 | 2026-09-16 11:35:00
gmail | Zy9$mNx3@wQ8rT2v | 24 | 2026-09-16 11:36:00
```

The file is a plain text file that you can open with any text editor like Notepad.

---

## Project Structure

```
passgen/
├── passgen.py              # CLI entry point
├── generator.py            # Password generation logic
├── simple_storage.py       # Text file read/write operations
├── strength_analyzer.py    # Password strength analysis
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## Security Notes

- Passwords generated using Python's `secrets` module (cryptographically secure)
- Storage file is plain text for easy access
- File permissions set to `600` (owner read/write only)
- No encryption - passwords are readable in the text file

---

## Backup

To back up your passwords, simply copy `passwords.txt` to a safe location.
The file is human-readable and can be opened with any text editor.

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| click | 8.1.7 | CLI interface |