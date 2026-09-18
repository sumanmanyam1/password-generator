"""
app.py — Interactive menu-driven interface for PassGen.

Run this file directly in VS Code (press ▶ or F5) — no command-line
arguments needed.  Everything is driven by numbered menus.
"""

import os
import sys
import csv
import json
from datetime import datetime

# Make sure imports from the same folder work when run from VS Code
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator import generate_password
from simple_storage import (
    storage_exists,
    create_storage,
    add_entry,
    overwrite_entry,
    get_entry,
    list_entries,
    delete_entry,
    label_exists,
    get_all_entries_with_passwords,
    get_storage_file_path,
)
from strength_analyzer import analyze_password_strength, format_strength_analysis


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def ask(prompt, default=""):
    """Simple input with an optional default value."""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()


def ask_int(prompt, default=None, min_val=None, max_val=None):
    """Ask for an integer, re-prompting on invalid input."""
    while True:
        raw = ask(prompt, str(default) if default is not None else "")
        try:
            value = int(raw)
            if min_val is not None and value < min_val:
                print(f"  ❌ Must be at least {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"  ❌ Must be at most {max_val}.")
                continue
            return value
        except ValueError:
            print("  ❌ Please enter a valid number.")


def ask_yes_no(prompt, default=False):
    """Ask a yes/no question."""
    hint = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {hint}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def ensure_storage():
    if not storage_exists():
        print("✓ Creating new password storage file...")
        create_storage()
        print(f"✓ Storage created at: {get_storage_file_path()}\n")


# ─────────────────────────────────────────────────────────────
# MENU ACTIONS
# ─────────────────────────────────────────────────────────────

def action_generate():
    print("\n─── Generate / Save Password ────────────────\n")
    print("  1. Auto-generate a password")
    print("  2. Enter my own password")
    mode = input("Choose [1/2]: ").strip()

    if mode not in ("1", "2"):
        print("❌ Invalid choice.")
        return

    # ── Label ─────────────────────────────────────────────────
    label = ask("\nLabel (e.g. github, gmail)")
    if not label:
        print("❌ Label cannot be empty.")
        return
    if len(label) > 50:
        print("❌ Label cannot exceed 50 characters.")
        return
    invalid_chars = set(label) & set('\\/:*?"<>|')
    if invalid_chars:
        print(f"❌ Label contains invalid characters: {', '.join(invalid_chars)}")
        return

    # ── Get the password ───────────────────────────────────────
    if mode == "1":
        # Auto-generate
        length     = ask_int("Password length", default=16, min_val=1)
        no_symbols = ask_yes_no("Exclude symbols  ([]{}|;:,.<>?)", default=False)
        no_digits  = ask_yes_no("Exclude digits   (0-9)",           default=False)
        no_upper   = ask_yes_no("Exclude uppercase (A-Z)",          default=False)

        try:
            password = generate_password(
                length=length,
                no_symbols=no_symbols,
                no_digits=no_digits,
                no_upper=no_upper,
            )
        except ValueError as e:
            print(f"❌ {e}")
            return

        print(f"\n✓ Generated password : {password}")

    else:
        # Manual entry
        password = input("Enter your password: ")
        if not password:
            print("❌ Password cannot be empty.")
            return
        print(f"\n✓ Password accepted.")

    # ── Strength analysis (always shown) ──────────────────────
    analysis = analyze_password_strength(password)
    print(f"\n  Strength  : {analysis['strength_level']}  (Score: {analysis['score']}/100)")
    print(f"  Length    : {len(password)} characters")
    print(f"  Crack time: {analysis['crack_time']}")

    # Requirements check
    print()
    for line in analysis['feedback']:
        if line.startswith("✓") or line.startswith("✗") or line.startswith("⚠"):
            print(f"  {line}")

    if not analysis['meets_requirements']:
        print("\n  ⚠️  Password does not meet requirements:")
        print("     • At least 1 uppercase letter")
        print("     • At least 1 digit")
        print("     • At least 1 special character")
        if not ask_yes_no("\n  Save anyway?", default=False):
            print("❌ Password not saved.")
            return

    # ── Save ──────────────────────────────────────────────────
    print()
    if label_exists(label):
        print(f"⚠️  Label '{label}' already exists.")
        if not ask_yes_no(f"Overwrite existing password for '{label}'?", default=False):
            print("❌ Aborted. Password not saved.")
            return
        overwrite_entry(label, password)
        print(f"✓ Updated password for '{label}'.")
    else:
        add_entry(label, password)
        print(f"✓ Saved password for '{label}'.")

    print(f"📄 Storage: {get_storage_file_path()}")


def action_get():
    print("\n─── Retrieve Password ───────────────────────\n")

    label = ask("Label to retrieve")
    if not label:
        print("❌ Label cannot be empty.")
        return

    password = get_entry(label)
    if password is None:
        print(f"❌ No password found for '{label}'.")
        print("   Tip: choose option 4 (List) to see all labels.")
        return

    print(f"\n✓ Password for '{label}': {password}")

    if ask_yes_no("Show strength analysis?", default=False):
        analysis = analyze_password_strength(password)
        print(f"\n  Strength : {analysis['strength_level']}  (Score: {analysis['score']}/100)")
        print(f"  Length   : {analysis['length']} characters")
        print(f"  Crack time: {analysis['crack_time']}")


def action_list():
    print("\n─── Stored Passwords ────────────────────────\n")

    entries = list_entries()
    if not entries:
        print("📭 No passwords stored yet.")
        print("   Use option 1 (Generate) to add your first password.")
        return

    print(f"  {'Label':<20} {'Length':<8} {'Created At':<20} {'Age'}")
    print(f"  {'-'*20} {'-'*8} {'-'*20} {'-'*10}")

    now = datetime.now()
    for lbl, length, created_at in entries:
        try:
            created_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            age_days = (now - created_time).days
            if age_days == 0:
                age_str = "Today"
            elif age_days == 1:
                age_str = "1 day"
            elif age_days < 30:
                age_str = f"{age_days} days"
            elif age_days < 365:
                age_str = f"{age_days // 30} months"
            else:
                age_str = f"{age_days // 365} years"
        except Exception:
            age_str = "Unknown"
        print(f"  {lbl:<20} {str(length):<8} {created_at:<20} {age_str}")

    print(f"\n  Total: {len(entries)} password(s)")
    print(f"  Storage: {get_storage_file_path()}")


def action_delete():
    print("\n─── Delete Password ─────────────────────────\n")

    label = ask("Label to delete")
    if not label:
        print("❌ Label cannot be empty.")
        return

    if not label_exists(label):
        print(f"❌ No password found for '{label}'.")
        print("   Tip: choose option 4 (List) to see all labels.")
        return

    print(f"⚠️  You are about to delete the password for '{label}'.")
    print("   This action cannot be undone.")
    if not ask_yes_no(f"Delete '{label}'?", default=False):
        print("❌ Deletion cancelled.")
        return

    if delete_entry(label):
        print(f"✓ Successfully deleted '{label}'.")
    else:
        print(f"❌ Could not delete '{label}'.")


def action_analyze():
    print("\n─── Analyze Password Strength ───────────────\n")
    print("  1. Analyze a stored password (by label)")
    print("  2. Analyze a password you type in")
    choice = ask("Choose").strip()

    if choice == "1":
        label = ask("Label")
        if not label:
            print("❌ Label cannot be empty.")
            return
        password = get_entry(label)
        if password is None:
            print(f"❌ No password found for '{label}'.")
            return
        print(f"\nAnalyzing stored password for '{label}'...\n")
    elif choice == "2":
        password = ask("Enter password to analyze")
        if not password:
            print("❌ Password cannot be empty.")
            return
    else:
        print("❌ Invalid choice.")
        return

    analysis = analyze_password_strength(password)
    print(format_strength_analysis(analysis))


def action_bulk():
    print("\n─── Bulk Generate ───────────────────────────\n")

    count  = ask_int("How many passwords?", default=5,  min_val=1,  max_val=100)
    length = ask_int("Length of each",      default=16, min_val=1)
    no_symbols = ask_yes_no("Exclude symbols?",   default=False)
    no_digits  = ask_yes_no("Exclude digits?",    default=False)
    no_upper   = ask_yes_no("Exclude uppercase?", default=False)
    save       = ask_yes_no("Save to storage?",   default=False)

    print(f"\nGenerating {count} passwords...\n")

    passwords = []
    for i in range(count):
        try:
            password = generate_password(
                length=length,
                no_symbols=no_symbols,
                no_digits=no_digits,
                no_upper=no_upper,
            )
            passwords.append(password)
            print(f"  {i+1:2d}. {password}")

            if save:
                lbl = f"bulk_{i+1:03d}"
                if label_exists(lbl):
                    overwrite_entry(lbl, password)
                else:
                    add_entry(lbl, password)
        except ValueError as e:
            print(f"  ❌ Password {i+1}: {e}")

    print(f"\nGenerated {len(passwords)} password(s).")
    if save:
        print(f"Saved with labels: bulk_001 … bulk_{count:03d}")

    if passwords:
        print("\nSTRENGTH SUMMARY:")
        print("-" * 30)
        total = 0
        for i, pwd in enumerate(passwords):
            a = analyze_password_strength(pwd)
            total += a["score"]
            print(f"  {i+1:2d}. Score: {a['score']:3d}/100  ({a['strength_level']})")
        print(f"\n  Average score: {total / len(passwords):.1f}/100")


def action_export():
    print("\n─── Export Passwords ────────────────────────\n")
    print("  Format:  1=CSV  2=JSON  3=TXT")
    fmt_choice = ask("Format", default="1").strip()
    fmt_map = {"1": "csv", "2": "json", "3": "txt"}
    export_format = fmt_map.get(fmt_choice, "csv")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"passwords_export_{timestamp}",
    )
    output = ask("Output file path (without extension)", default=default_out)
    if not output.lower().endswith(f".{export_format}"):
        output += f".{export_format}"

    if os.path.exists(output):
        if not ask_yes_no(f"File '{output}' exists. Overwrite?", default=False):
            print("❌ Export cancelled.")
            return

    include_pw = ask_yes_no(
        "Include actual passwords? (creates unencrypted file — handle carefully)",
        default=False,
    )

    entries = list_entries()
    if not entries:
        print("📭 No passwords stored yet.")
        return

    try:
        if include_pw:
            all_entries = get_all_entries_with_passwords()
            if export_format == "csv":
                _export_with_passwords_csv(all_entries, output)
            elif export_format == "json":
                _export_with_passwords_json(all_entries, output)
            else:
                print("⚠️  TXT format does not support password export for security reasons.")
                print("   Use CSV or JSON for password exports.")
                return
            os.chmod(output, 0o600)
            print(f"\n✓ Export done — file permissions set to 600 (owner only).")
        else:
            if export_format == "csv":
                _export_to_csv(entries, output)
            elif export_format == "json":
                _export_to_json(entries, output)
            else:
                _export_to_txt(entries, output)
            print("\n✓ Export completed.")

        print(f"  File   : {output}")
        print(f"  Format : {export_format.upper()}")
        print(f"  Entries: {len(entries)}")

    except Exception as e:
        print(f"❌ Export failed: {e}")


# ─────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────

def _export_to_csv(entries, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "Length", "Created At"])
        for label, length, created_at in entries:
            writer.writerow([label, length, created_at])


def _export_to_json(entries, path):
    data = [
        {"label": label, "length": length, "created_at": created_at}
        for label, length, created_at in entries
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _export_to_txt(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"PassGen Export — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"{'Label':<20} {'Length':<8} {'Created At'}\n")
        f.write(f"{'-'*20} {'-'*8} {'-'*20}\n")
        for label, length, created_at in entries:
            f.write(f"{label:<20} {str(length):<8} {created_at}\n")


def _export_with_passwords_csv(all_entries, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "Password", "Length", "Created At"])
        for e in all_entries:
            writer.writerow([e["label"], e["password"], e["length"], e["created_at"]])


def _export_with_passwords_json(all_entries, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)


# ─────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════╗
║          PassGen — Password Manager      ║
╠══════════════════════════════════════════╣
║  1. Generate password                    ║
║  2. Get / retrieve a password            ║
║  3. Delete a password                    ║
║  4. List all passwords                   ║
║  5. Analyze password strength            ║
║  6. Bulk generate passwords              ║
║  7. Export passwords                     ║
║  0. Exit                                 ║
╚══════════════════════════════════════════╝
"""

ACTIONS = {
    "1": action_generate,
    "2": action_get,
    "3": action_delete,
    "4": action_list,
    "5": action_analyze,
    "6": action_bulk,
    "7": action_export,
}


def main():
    ensure_storage()
    while True:
        try:
            clear()
            print(MENU)
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋\n")
            break

        if choice == "0":
            print("\nGoodbye! 👋\n")
            break

        action = ACTIONS.get(choice)
        if action:
            try:
                action()
            except (EOFError, KeyboardInterrupt):
                print("\n\n↩ Returning to menu...")
        else:
            print("❌ Invalid choice. Please enter a number from 0 to 7.")

        try:
            pause()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋\n")
            break


if __name__ == "__main__":
    main()
