"""
generator.py — Password generation logic.

Every generated password is guaranteed to contain at least:
- 1 uppercase letter   (unless no_upper=True)
- 1 digit              (unless no_digits=True)
- 1 special character  (!@#$%^&*()-_=+[]{}|;:,.<>?)

There is no minimum length requirement — the length is whatever
the user requests (minimum is automatically the number of mandatory
characters that must be included, which is at most 3).
"""

import secrets
import string

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS    = string.digits
SPECIAL   = "!@#$%^&*()-_=+[]{}|;:,.<>?"


def generate_password(length=16, no_symbols=False, no_digits=False, no_upper=False):
    """
    Generate a cryptographically secure password.

    Args:
        length (int): Total length of the password.
                      Must be >= the number of mandatory characters
                      (between 1 and 3 depending on flags).
        no_symbols (bool): Exclude special characters if True.
        no_digits  (bool): Exclude digits if True.
        no_upper   (bool): Exclude uppercase letters if True.

    Returns:
        str: The generated password.

    Raises:
        ValueError: If all character types are disabled, or length is
                    too short to fit the required mandatory characters.
    """
    # Build mandatory characters based on requirements
    mandatory = []

    if not no_upper:
        mandatory.append(secrets.choice(UPPERCASE))   # at least 1 uppercase

    if not no_digits:
        mandatory.append(secrets.choice(DIGITS))      # at least 1 digit

    if not no_symbols:
        mandatory.append(secrets.choice(SPECIAL))     # at least 1 special char

    # Build the character pool for remaining positions
    pool = LOWERCASE
    if not no_upper:
        pool += UPPERCASE
    if not no_digits:
        pool += DIGITS
    if not no_symbols:
        pool += SPECIAL

    if not pool:
        raise ValueError("At least one character type must be enabled.")

    # The minimum valid length equals the number of mandatory characters
    min_length = len(mandatory) if mandatory else 1
    if length < min_length:
        raise ValueError(
            f"Length must be at least {min_length} to fit the required character types."
        )

    # Fill remaining positions from the pool
    remaining = length - len(mandatory)
    password_chars = mandatory + [secrets.choice(pool) for _ in range(remaining)]

    # Shuffle so mandatory characters aren't always at the front
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
