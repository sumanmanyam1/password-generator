"""
passgen.py — CLI entry point for the Password Generator tool.

Commands:
    generate    Generate and store a password
    get         Retrieve a stored password
    list        List all stored labels
    delete      Delete a stored entry
"""

import getpass
import sys
import os
from datetime import datetime

import csv
import json
import click
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


# ──────────────────────────────────────────────
# EXPORT HELPERS
# ──────────────────────────────────────────────

def validate_export_path(output, export_format):
    """Validate and normalise the export file path.

    Returns the final path with the correct extension.
    Raises FileExistsError if the file already exists.
    Raises ValueError for invalid paths.
    """
    if not output:
        raise ValueError("Output path cannot be empty.")

    if not output.lower().endswith(f".{export_format}"):
        output = f"{output}.{export_format}"

    # Check that the parent directory exists
    parent = os.path.dirname(os.path.abspath(output))
    if not os.path.isdir(parent):
        raise ValueError(f"Directory does not exist: {parent}")

    if os.path.exists(output):
        raise FileExistsError(f"File already exists: {output}")

    return output


def export_to_csv(entries, output_path):
    """Export label/length/created_at entries to a CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "Length", "Created At"])
        for label, length, created_at in entries:
            writer.writerow([label, length, created_at])


def export_to_json(entries, output_path):
    """Export label/length/created_at entries to a JSON file."""
    data = [
        {"label": label, "length": length, "created_at": created_at}
        for label, length, created_at in entries
    ]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def export_to_txt(entries, output_path):
    """Export label/length/created_at entries to a plain-text file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Password Vault Export — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"{'Label':<20} {'Length':<8} {'Created At'}\n")
        f.write(f"{'-'*20} {'-'*8} {'-'*20}\n")
        for label, length, created_at in entries:
            f.write(f"{label:<20} {str(length):<8} {created_at}\n")


def export_with_passwords_csv(all_entries, output_path):
    """Export full entries including passwords to a CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "Password", "Length", "Created At"])
        for entry in all_entries:
            writer.writerow([entry['label'], entry['password'], entry['length'], entry['created_at']])
    # Restrict permissions to owner read/write only
    os.chmod(output_path, 0o600)


def export_with_passwords_json(all_entries, output_path):
    """Export full entries including passwords to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, indent=2)
    # Restrict permissions to owner read/write only
    os.chmod(output_path, 0o600)


def _prompt_password(prompt_text):
    """Prompt for a password securely using getpass."""
    try:
        password = getpass.getpass(prompt=prompt_text + ": ")
        if not password.strip():
            raise ValueError("Password cannot be empty")
        return password
    except (getpass.GetPassWarning, EOFError, Exception):
        # Fallback for non-TTY environments
        sys.stdout.write(prompt_text + ": ")
        sys.stdout.flush()
        password = input()
        if not password.strip():
            raise ValueError("Password cannot be empty")
        return password


@click.group()
def cli():
    """PassGen — Simple Password Generator & Manager."""
    if not storage_exists():
        click.echo("✓ Creating new password storage file...")
        create_storage()
        click.echo(f"✓ Storage created at: {get_storage_file_path()}")
        click.echo("")
    pass


# ──────────────────────────────────────────────
# GENERATE
# ──────────────────────────────────────────────
@cli.command()
@click.option("--label", required=True, help="Label to store the password under (e.g. github, gmail)")
@click.option("--length", default=16, show_default=True, help="Length of the password")
@click.option("--no-symbols", is_flag=True, default=False, help="Exclude symbols []{}|;:,.<>?")
@click.option("--no-digits",  is_flag=True, default=False, help="Exclude digits 0-9")
@click.option("--no-upper",   is_flag=True, default=False, help="Exclude uppercase letters A-Z")
def generate(label, length, no_symbols, no_digits, no_upper):
    """Generate a password and save it to storage."""
    
    # Validate inputs
    # Clean and validate label
    label = label.strip()
    if not label:
        click.echo("❌ Error: Label cannot be empty.")
        return
    
    if len(label) > 50:
        click.echo("❌ Error: Label cannot exceed 50 characters.")
        return

    # Check for invalid characters in label
    invalid_chars = set(label) & set('\\/:*?"<>|')
    if invalid_chars:
        click.echo(f"❌ Error: Label contains invalid characters: {', '.join(invalid_chars)}")
        click.echo("   Labels cannot contain: \\ / : * ? \" < > |")
        return

    # Generate password
    try:
        password = generate_password(
            length=length,
            no_symbols=no_symbols,
            no_digits=no_digits,
            no_upper=no_upper,
        )
        click.echo(f"\n✓ Generated password: {password}")
        
        # Show strength analysis
        analysis = analyze_password_strength(password)
        click.echo(f"  Strength: {analysis['strength_level']} (Score: {analysis['score']}/100)")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
        return

    # Save to storage
    try:
        if label_exists(label):
            click.echo(f"⚠️  Label '{label}' already exists.")
            if not click.confirm(f"Overwrite existing password for '{label}'?", default=False):
                click.echo("❌ Aborted. Password not saved.")
                return
            overwrite_entry(label, password)
            click.echo(f"✓ Updated password for '{label}' in storage.")
        else:
            add_entry(label, password)
            click.echo(f"✓ Saved password for '{label}' to storage.")
            
        click.echo(f"📄 Storage file: {get_storage_file_path()}")
        
    except Exception as e:
        click.echo(f"❌ Error saving password: {e}")


# ──────────────────────────────────────────────
# GET
# ──────────────────────────────────────────────
@cli.command()
@click.argument("label")
def get(label):
    """Retrieve the password for a label."""
    
    # Validate and clean label
    label = label.strip()
    if not label:
        click.echo("❌ Error: Label cannot be empty.")
        return
    
    try:
        password = get_entry(label)
        if password is None:
            click.echo(f"❌ Error: No password found for '{label}'.")
            click.echo("   Use 'python passgen.py list' to see all stored labels.")
        else:
            click.echo(f"\n✓ Password for '{label}': {password}")
            
            # Optionally show strength analysis
            if click.confirm("Show password strength analysis?", default=False):
                analysis = analyze_password_strength(password)
                click.echo(f"\nQuick Analysis:")
                click.echo(f"  Strength: {analysis['strength_level']} (Score: {analysis['score']}/100)")
                click.echo(f"  Length: {analysis['length']} characters")
                
    except Exception as e:
        click.echo(f"❌ Error retrieving password: {e}")


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────
@cli.command("list")
def list_cmd():
    """List all stored labels."""
    
    try:
        entries = list_entries()
        if not entries:
            click.echo("📭 No passwords stored yet.")
            click.echo("   Use 'python passgen.py generate --label <name>' to add your first password.")
        else:
            click.echo(f"\n📋 Stored passwords ({len(entries)}):\n")
            click.echo(f"  {'Label':<20} {'Length':<8} {'Created At':<20} {'Age'}")
            click.echo(f"  {'-'*20} {'-'*8} {'-'*20} {'-'*10}")
            
            now = datetime.now()
            
            for lbl, length, created_at in entries:
                # Calculate age
                try:
                    created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    age_days = (now - created_time).days
                    if age_days == 0:
                        age_str = "Today"
                    elif age_days == 1:
                        age_str = "1 day"
                    elif age_days < 30:
                        age_str = f"{age_days} days"
                    elif age_days < 365:
                        age_str = f"{age_days//30} months"
                    else:
                        age_str = f"{age_days//365} years"
                except:
                    age_str = "Unknown"
                
                click.echo(f"  {lbl:<20} {str(length):<8} {created_at:<20} {age_str}")
            
            click.echo(f"\n💡 Tips:")
            click.echo(f"   • Use 'python passgen.py get <label>' to retrieve a password")
            click.echo(f"   • Use 'python passgen.py analyze --label <label>' to check password strength")
            click.echo(f"   • Your passwords are stored in: {get_storage_file_path()}")
            
    except Exception as e:
        click.echo(f"❌ Error listing passwords: {e}")


# ──────────────────────────────────────────────
# DELETE
# ──────────────────────────────────────────────
@cli.command()
@click.argument("label")
def delete(label):
    """Delete a stored password entry."""
    
    # Validate and clean label
    label = label.strip()
    if not label:
        click.echo("❌ Error: Label cannot be empty.")
        return
    
    try:
        if not label_exists(label):
            click.echo(f"❌ Error: No password found for '{label}'.")
            click.echo("   Use 'python passgen.py list' to see all stored labels.")
            return

        # Show details before deletion
        click.echo(f"⚠️  You are about to delete the password for '{label}'.")
        click.echo("   This action cannot be undone.")
        
        if not click.confirm(f"Delete password for '{label}'?", default=False):
            click.echo("❌ Deletion cancelled.")
            return

        success = delete_entry(label)
        if success:
            click.echo(f"✓ Successfully deleted '{label}' from storage.")
        else:
            click.echo(f"❌ Error: Could not delete '{label}'. It may have been removed already.")
            
    except Exception as e:
        click.echo(f"❌ Error deleting password: {e}")


# ──────────────────────────────────────────────
# ANALYZE
# ──────────────────────────────────────────────
@cli.command()
@click.option("--password", help="Password to analyze (will prompt if not provided)")
@click.option("--label", help="Analyze a stored password by label")
def analyze(password, label):
    """Analyze password strength and security."""
    
    if label and password:
        click.echo("❌ Error: Cannot specify both --password and --label options.")
        return
    
    if label:
        # Analyze a stored password
        try:
            stored_password = get_entry(label)
            if stored_password is None:
                click.echo(f"❌ Error: No password found for '{label}'.")
                return
            password_to_analyze = stored_password
            click.echo(f"Analyzing stored password for '{label}'...\n")
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            return
    elif password:
        # Analyze provided password
        password_to_analyze = password
    else:
        # Prompt for password to analyze
        try:
            password_to_analyze = _prompt_password("Enter password to analyze")
        except ValueError as e:
            click.echo(f"❌ Error: {e}")
            return
    
    # Perform analysis
    analysis = analyze_password_strength(password_to_analyze)
    formatted_analysis = format_strength_analysis(analysis)
    
    click.echo(formatted_analysis)


# ──────────────────────────────────────────────
# BULK GENERATE
# ──────────────────────────────────────────────
@cli.command()
@click.option("--count", default=5, show_default=True, help="Number of passwords to generate")
@click.option("--length", default=16, show_default=True, help="Length of each password")
@click.option("--no-symbols", is_flag=True, default=False, help="Exclude symbols []{}|;:,.<>?")
@click.option("--no-digits",  is_flag=True, default=False, help="Exclude digits 0-9")
@click.option("--no-upper",   is_flag=True, default=False, help="Exclude uppercase letters A-Z")
@click.option("--save", is_flag=True, default=False, help="Save passwords to storage with auto-generated labels")
def bulk(count, length, no_symbols, no_digits, no_upper, save):
    """Generate multiple passwords at once."""
    if count < 1 or count > 100:
        click.echo("❌ Error: Count must be between 1 and 100.")
        return

    click.echo(f"Generating {count} passwords...\n")
    
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
            
            # Display password
            click.echo(f"{i+1:2d}. {password}")
            
            # Save to storage if requested
            if save:
                label = f"bulk_{i+1:03d}"
                try:
                    if label_exists(label):
                        overwrite_entry(label, password)
                    else:
                        add_entry(label, password)
                except Exception as e:
                    click.echo(f"    Warning: Could not save to storage - {e}")
            
        except ValueError as e:
            click.echo(f"❌ Error generating password {i+1}: {e}")
    
    click.echo(f"\nGenerated {len(passwords)} passwords successfully.")
    
    if save:
        click.echo(f"Passwords saved to storage with labels: bulk_001 to bulk_{count:03d}")
    
    # Show strength analysis summary
    if passwords:
        click.echo("\nSTRENGTH ANALYSIS SUMMARY:")
        click.echo("-" * 30)
        total_score = 0
        for i, pwd in enumerate(passwords):
            analysis = analyze_password_strength(pwd)
            total_score += analysis['score']
            click.echo(f"{i+1:2d}. Score: {analysis['score']:2d}/100 ({analysis['strength_level']})")
        
        avg_score = total_score / len(passwords)
        click.echo(f"\nAverage strength score: {avg_score:.1f}/100")


# ──────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────
@cli.command()
@click.option("--format", "export_format", type=click.Choice(['csv', 'json', 'txt']), 
              default='csv', show_default=True, help="Export format")
@click.option("--output", help="Output file path (extension will be added if missing)")
@click.option("--include-passwords", is_flag=True, default=False, 
              help="Include actual passwords (WARNING: creates unencrypted file)")
def export(export_format, output, include_passwords):
    """Export vault data to various formats."""
    
    try:
        # Get entries from storage
        if include_passwords:
            all_entries = get_all_entries_with_passwords()
            if not all_entries:
                click.echo("No passwords stored yet.")
                return
            entries_for_basic_export = [(e['label'], e['length'], e['created_at']) for e in all_entries]
        else:
            entries_for_basic_export = list_entries()
            if not entries_for_basic_export:
                click.echo("No passwords stored yet.")
                return
        
        # Determine output path
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"passwords_export_{timestamp}"
        
        try:
            output_path = validate_export_path(output, export_format)
        except FileExistsError as e:
            if not click.confirm(f"{e}\nOverwrite existing file?", default=False):
                click.echo("Export cancelled.")
                return
            output_path = output  # Use original path even if file exists
            if not output_path.lower().endswith(f".{export_format}"):
                output_path += f".{export_format}"
        except ValueError as e:
            click.echo(f"Error: {e}")
            return
        
        # Security warning for password export
        if include_passwords:
            click.echo("⚠️  WARNING: You are about to export passwords in plain text!")
            click.echo("   This creates an unencrypted file that contains your actual passwords.")
            click.echo("   Make sure to:")
            click.echo("   • Store the file in a secure location")
            click.echo("   • Delete the file when no longer needed")
            click.echo("   • Never share or transmit the file over insecure channels")
            
            if not click.confirm("\nDo you want to continue with password export?", default=False):
                click.echo("Export cancelled.")
                return
        
        # Perform export
        if include_passwords:
            if export_format == 'csv':
                export_with_passwords_csv(all_entries, output_path)
            elif export_format == 'json':
                export_with_passwords_json(all_entries, output_path)
            else:  # txt format with passwords not implemented for security
                click.echo("Text format with passwords is not supported for security reasons.")
                click.echo("Use CSV or JSON format for password exports.")
                return
        else:
            if export_format == 'csv':
                export_to_csv(entries_for_basic_export, output_path)
            elif export_format == 'json':
                export_to_json(entries_for_basic_export, output_path)
            else:  # txt
                export_to_txt(entries_for_basic_export, output_path)
        
        click.echo(f"\n✓ Export completed successfully!")
        click.echo(f"  File: {output_path}")
        click.echo(f"  Format: {export_format.upper()}")
        click.echo(f"  Entries: {len(entries_for_basic_export)}")
        
        if include_passwords:
            click.echo(f"  File permissions: 600 (owner read/write only)")
        
    except ValueError as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    cli()
