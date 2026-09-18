"""
simple_storage.py — Simple text file storage for passwords.

Stores passwords in a readable text file format without encryption.
Format: Label | Password | Length | Created At
"""

import os
from datetime import datetime

STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "passwords.txt")
SEPARATOR = " | "


def storage_exists():
    """Check if the storage file already exists."""
    return os.path.exists(STORAGE_FILE)


def create_storage():
    """Create a new storage file with headers."""
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        f.write("Password Storage File\n")
        f.write("=" * 50 + "\n")
        f.write("Format: Label | Password | Length | Created At\n")
        f.write("=" * 50 + "\n\n")
    
    # Set file permissions to owner read/write only for some security
    os.chmod(STORAGE_FILE, 0o600)


def add_entry(label, password):
    """Add a new password entry to the storage."""
    if not storage_exists():
        create_storage()
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{label}{SEPARATOR}{password}{SEPARATOR}{len(password)}{SEPARATOR}{created_at}\n"
    
    with open(STORAGE_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


def overwrite_entry(label, password):
    """Update an existing password entry."""
    if not storage_exists():
        create_storage()
        add_entry(label, password)
        return
    
    entries = []
    found = False
    
    # Read all entries
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process entries, skipping header lines
    for line in lines:
        if SEPARATOR in line:
            parts = line.strip().split(SEPARATOR)
            if len(parts) >= 4 and parts[0].lower() == label.lower():
                # Update this entry
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_entry = f"{label}{SEPARATOR}{password}{SEPARATOR}{len(password)}{SEPARATOR}{created_at}\n"
                entries.append(new_entry)
                found = True
            else:
                entries.append(line)
        else:
            entries.append(line)
    
    if not found:
        # Add new entry if not found
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = f"{label}{SEPARATOR}{password}{SEPARATOR}{len(password)}{SEPARATOR}{created_at}\n"
        entries.append(new_entry)
    
    # Write back to file
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        f.writelines(entries)


def get_entry(label):
    """Retrieve a password by label."""
    if not storage_exists():
        return None
    
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if SEPARATOR in line and not line.startswith('Format:') and '===' not in line:
                parts = line.split(SEPARATOR)
                if len(parts) >= 4 and parts[0].lower() == label.lower():
                    return parts[1]  # Return password
    return None


def list_entries():
    """List all stored labels with metadata."""
    if not storage_exists():
        return []
    
    entries = []
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if SEPARATOR in line and not line.startswith('Format:') and '===' not in line:
                parts = line.split(SEPARATOR)
                if len(parts) >= 4:
                    label, password, length, created_at = parts[0], parts[1], parts[2], parts[3]
                    # Skip if it looks like a header or format line
                    if label.lower() not in ['label', 'format']:
                        entries.append((label, int(length) if length.isdigit() else 0, created_at))
    return entries


def delete_entry(label):
    """Delete a password entry by label."""
    if not storage_exists():
        return False
    
    entries = []
    found = False
    
    # Read all entries
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Filter out the entry to delete
    for line in lines:
        if SEPARATOR in line:
            parts = line.strip().split(SEPARATOR)
            if len(parts) >= 4 and parts[0].lower() == label.lower():
                found = True
                continue  # Skip this entry
        entries.append(line)
    
    if found:
        # Write back to file
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            f.writelines(entries)
    
    return found


def label_exists(label):
    """Check if a label already exists."""
    if not storage_exists():
        return False
    
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if SEPARATOR in line:
                parts = line.strip().split(SEPARATOR)
                if len(parts) >= 4 and parts[0].lower() == label.lower():
                    return True
    return False


def get_all_entries_with_passwords():
    """Get all entries including passwords for export purposes."""
    if not storage_exists():
        return []
    
    entries = []
    with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if SEPARATOR in line:
                parts = line.strip().split(SEPARATOR)
                if len(parts) >= 4:
                    label, password, length, created_at = parts[0], parts[1], parts[2], parts[3]
                    entries.append({
                        "label": label,
                        "password": password,
                        "length": int(length) if length.isdigit() else 0,
                        "created_at": created_at
                    })
    return entries


def get_storage_file_path():
    """Get the path to the storage file."""
    return STORAGE_FILE