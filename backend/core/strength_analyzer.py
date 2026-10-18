"""
strength_analyzer.py — Password strength analysis and scoring.

Strength is determined primarily by whether the password meets the
three core requirements:
    • At least 1 uppercase letter
    • At least 1 digit
    • At least 1 special character

Meeting all three requirements = "Strong".
Additional criteria (length, patterns, common passwords) raise or
lower the score further to "Very Strong" or below.

Score breakdown (max 100):
    Requirements met  — up to 60 pts  (20 pts each)
    Length bonus      — up to 20 pts
    Pattern penalty   — up to -20 pts
    Common password   — up to -20 pts
"""

import re
from typing import Dict, List, Tuple


COMMON_WEAK_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345", "1234567",
    "1234567890", "qwerty", "abc123", "password123", "admin", "letmein",
    "welcome", "monkey", "dragon", "master", "sunshine", "princess",
    "football", "batman", "trustno1", "hello", "charlie", "hottie",
}

KEYBOARD_PATTERNS = [
    "qwerty", "asdf", "zxcv", "1234", "abcd", "qwertyuiop",
    "asdfghjkl", "zxcvbnm", "123456789", "987654321",
]

REPEATED_PATTERNS = [
    r"(.)\1{2,}",   # 3+ same characters in a row
    r"(..+)\1+",    # repeated sequences  (abcabc, 123123)
]


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def analyze_password_strength(password: str) -> Dict:
    """
    Analyze password strength and return detailed results.

    Returns a dict with:
        score          int   0–100
        strength_level str   "Very Weak" … "Very Strong"
        meets_requirements bool
        feedback       list[str]
        crack_time     str
    """
    analysis = {
        "password": password,
        "length": len(password),
        "score": 0,
        "max_score": 100,
        "strength_level": "Very Weak",
        "strength_color": "red",
        "meets_requirements": False,
        "feedback": [],
        "criteria": {},
    }

    # ── Core requirements (max 60 pts) ────────────────────────
    req_score, req_feedback, meets = _analyze_requirements(password)
    analysis["score"] += req_score
    analysis["criteria"]["requirements"] = req_score
    analysis["feedback"].extend(req_feedback)
    analysis["meets_requirements"] = meets

    # ── Length bonus (max 20 pts) ─────────────────────────────
    len_score, len_feedback = _analyze_length(len(password))
    analysis["score"] += len_score
    analysis["criteria"]["length"] = len_score
    analysis["feedback"].extend(len_feedback)

    # ── Pattern penalty (max -20 pts) ─────────────────────────
    pat_score, pat_feedback = _analyze_patterns(password)
    analysis["score"] += pat_score          # pat_score is 0 or negative
    analysis["criteria"]["patterns"] = pat_score
    analysis["feedback"].extend(pat_feedback)

    # ── Common password penalty (max -20 pts) ─────────────────
    common_score, common_feedback = _analyze_common(password)
    analysis["score"] += common_score       # common_score is 0 or negative
    analysis["criteria"]["common"] = common_score
    analysis["feedback"].extend(common_feedback)

    # Clamp to 0–100
    analysis["score"] = max(0, min(100, analysis["score"]))

    analysis["strength_level"], analysis["strength_color"] = _get_strength_level(
        analysis["score"], meets
    )
    analysis["crack_time"] = _estimate_crack_time(password)

    return analysis


def format_strength_analysis(analysis: Dict) -> str:
    """Format the strength analysis for display."""
    lines = []
    lines.append("=" * 50)
    lines.append("PASSWORD STRENGTH ANALYSIS")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Password      : {'*' * len(analysis['password'])}")
    lines.append(f"Length        : {analysis['length']} characters")
    lines.append(f"Score         : {analysis['score']}/{analysis['max_score']}")
    lines.append(f"Strength      : {analysis['strength_level']}")
    lines.append(f"Requirements  : {'✓ Met' if analysis['meets_requirements'] else '✗ Not fully met'}")
    lines.append(f"Crack time    : {analysis['crack_time']}")
    lines.append("")

    lines.append("REQUIREMENTS (must have):")
    lines.append("-" * 30)
    pwd = analysis["password"]
    lines.append(f"  {'✓' if re.search(r'[A-Z]', pwd) else '✗'} At least 1 uppercase letter")
    lines.append(f"  {'✓' if re.search(r'[0-9]', pwd) else '✗'} At least 1 digit")
    lines.append(f"  {'✓' if re.search(r'[!@#$%^&*()\-_=+\\[\\]{{}}|;:,.<>?]', pwd) else '✗'} At least 1 special character")
    lines.append("")

    lines.append("DETAILED ANALYSIS:")
    lines.append("-" * 30)
    for fb in analysis["feedback"]:
        lines.append(f"  {fb}")
    lines.append("")

    lines.append("RECOMMENDATIONS:")
    lines.append("-" * 20)
    if not analysis["meets_requirements"]:
        lines.append("  • Add at least 1 uppercase letter (A-Z)")
        lines.append("  • Add at least 1 digit (0-9)")
        lines.append("  • Add at least 1 special character (!@#$%^&* etc.)")
    elif analysis["score"] < 60:
        lines.append("  • Requirements are met but the password is still weak")
        lines.append("  • Increase the length and avoid common words/patterns")
    elif analysis["score"] < 80:
        lines.append("  • Good password — consider making it longer for extra security")
    else:
        lines.append("  • Excellent password! Keep using unique passwords per account.")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _analyze_requirements(password: str) -> Tuple[int, List[str], bool]:
    """
    Check the three core requirements.
    Each requirement is worth 20 points (total max 60).
    Returns (score, feedback_list, all_met).
    """
    score = 0
    feedback = []

    has_upper   = bool(re.search(r'[A-Z]', password))
    has_digit   = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]', password))

    if has_upper:
        score += 20
        feedback.append("✓ Contains uppercase letter")
    else:
        feedback.append("✗ Missing uppercase letter  (required)")

    if has_digit:
        score += 20
        feedback.append("✓ Contains digit")
    else:
        feedback.append("✗ Missing digit  (required)")

    if has_special:
        score += 20
        feedback.append("✓ Contains special character")
    else:
        feedback.append("✗ Missing special character  (required)")

    all_met = has_upper and has_digit and has_special
    return score, feedback, all_met


def _analyze_length(length: int) -> Tuple[int, List[str]]:
    """
    Length bonus — max 20 extra points.
    No deductions for being short; length is not a hard requirement.
    """
    feedback = []

    if length >= 16:
        score = 20
        feedback.append("✓ Excellent length (16+ characters)")
    elif length >= 12:
        score = 15
        feedback.append("✓ Good length (12+ characters)")
    elif length >= 8:
        score = 10
        feedback.append("⚠ Adequate length — 12+ recommended")
    elif length >= 5:
        score = 5
        feedback.append("⚠ Short password — consider using more characters")
    else:
        score = 0
        feedback.append("⚠ Very short — consider using more characters")

    return score, feedback


def _analyze_patterns(password: str) -> Tuple[int, List[str]]:
    """
    Pattern penalty — returns 0 or a negative number (max deduction -20).
    """
    deductions = 0
    feedback = []
    password_lower = password.lower()

    for pattern in KEYBOARD_PATTERNS:
        if pattern in password_lower or pattern[::-1] in password_lower:
            deductions += 8
            feedback.append(f"✗ Contains keyboard pattern: {pattern}")
            break

    for pattern in REPEATED_PATTERNS:
        if re.search(pattern, password):
            deductions += 6
            feedback.append("✗ Contains repeated character sequences")
            break

    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
        deductions += 5
        feedback.append("✗ Contains sequential numbers")

    if re.search(
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',
        password_lower,
    ):
        deductions += 5
        feedback.append("✗ Contains sequential letters")

    if re.search(r'(19|20)\d{2}', password):
        deductions += 4
        feedback.append("✗ Contains year pattern")

    if deductions == 0:
        feedback.append("✓ No predictable patterns detected")

    return -min(deductions, 20), feedback


def _analyze_common(password: str) -> Tuple[int, List[str]]:
    """
    Common password penalty — returns 0 or negative (max deduction -20).
    """
    feedback = []
    password_lower = password.lower()

    if password_lower in COMMON_WEAK_PASSWORDS:
        feedback.append("✗ This is a very commonly used weak password")
        return -20, feedback

    base = re.sub(r'[0-9!@#$%^&*()\-_=+\[\]{}|;:,.<>?]', '', password_lower)
    if base in COMMON_WEAK_PASSWORDS and len(base) > 3:
        feedback.append("✗ Based on a common weak password with simple modifications")
        return -15, feedback

    substituted = (
        password_lower
        .replace('@', 'a').replace('3', 'e')
        .replace('1', 'i').replace('0', 'o').replace('5', 's')
    )
    if substituted in COMMON_WEAK_PASSWORDS:
        feedback.append("⚠ Uses common character substitutions on a weak password")
        return -10, feedback

    feedback.append("✓ Not found in common password lists")
    return 0, feedback


def _get_strength_level(score: int, meets_requirements: bool) -> Tuple[str, str]:
    """
    Map score to a human-readable strength label.
    If requirements are not met, cap at 'Weak' regardless of score.
    """
    if not meets_requirements:
        if score >= 40:
            return "Weak", "orange"
        return "Very Weak", "red"

    if score >= 90:
        return "Very Strong", "green"
    elif score >= 75:
        return "Strong", "lightgreen"
    elif score >= 60:
        return "Good", "yellow"
    elif score >= 40:
        return "Weak", "orange"
    else:
        return "Very Weak", "red"


def _estimate_crack_time(password: str) -> str:
    """Estimate brute-force crack time."""
    char_space = 0
    if re.search(r'[a-z]', password):
        char_space += 26
    if re.search(r'[A-Z]', password):
        char_space += 26
    if re.search(r'[0-9]', password):
        char_space += 10
    if re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]', password):
        char_space += 32

    if char_space == 0 or len(password) == 0:
        return "Unknown"

    combinations = char_space ** len(password)
    seconds = combinations / (2 * 1_000_000_000)   # 1 billion guesses/sec

    if seconds < 1:
        return "Instantly"
    elif seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    elif seconds < 31_536_000:
        return f"{seconds/86400:.1f} days"
    elif seconds < 31_536_000_000:
        return f"{seconds/31_536_000:.1f} years"
    else:
        return f"{seconds/31_536_000:.0e} years"
