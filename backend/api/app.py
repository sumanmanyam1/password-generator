"""
app.py — Flask API that exposes the PassGen core logic to the frontend.

Runs locally at http://localhost:5000 and reuses the same Python code
(core.generator, core.strength_analyzer, core.storage) that powers the CLI.

Endpoints:
    GET  /api/health                 -> service check
    POST /api/generate               -> generate a password (optionally save)
    POST /api/bulk                   -> generate multiple passwords
    POST /api/analyze                -> analyze a password's strength
    GET  /api/passwords              -> list stored labels (no passwords)
    GET  /api/passwords/<label>      -> reveal a stored password
    DELETE /api/passwords/<label>    -> delete a stored entry
"""

import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

# Make the backend/ directory importable so `core` resolves regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generator import generate_password
from core.strength_analyzer import analyze_password_strength
from core import storage

app = Flask(__name__)
# Allow the Vite dev server (and other local origins) to call the API.
CORS(app)

INVALID_LABEL_CHARS = set('\\/:*?"<>|')


def _clean_label(label):
    """Validate a label the same way the CLI does. Returns (label, error)."""
    if label is None:
        return None, "Label is required."
    label = str(label).strip()
    if not label:
        return None, "Label cannot be empty."
    if len(label) > 50:
        return None, "Label cannot exceed 50 characters."
    bad = set(label) & INVALID_LABEL_CHARS
    if bad:
        return None, f"Label contains invalid characters: {', '.join(sorted(bad))}"
    return label, None


def _gen_options(data):
    """Extract generation options from a request body."""
    return {
        "length": int(data.get("length", 16)),
        "no_symbols": bool(data.get("no_symbols", False)),
        "no_digits": bool(data.get("no_digits", False)),
        "no_upper": bool(data.get("no_upper", False)),
    }


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "passgen-api"})


@app.post("/api/generate")
def api_generate():
    data = request.get_json(silent=True) or {}
    opts = _gen_options(data)
    save = bool(data.get("save", False))
    label_raw = data.get("label")

    try:
        password = generate_password(**opts)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    analysis = analyze_password_strength(password)
    result = {
        "password": password,
        "length": len(password),
        "strength": {
            "score": analysis["score"],
            "level": analysis["strength_level"],
            "color": analysis["strength_color"],
            "meets_requirements": analysis["meets_requirements"],
            "crack_time": analysis["crack_time"],
            "feedback": analysis["feedback"],
        },
        "saved": False,
    }

    if save:
        label, err = _clean_label(label_raw)
        if err:
            return jsonify({"error": err}), 400
        existing = storage.label_exists(label)
        if existing:
            storage.overwrite_entry(label, password)
        else:
            storage.add_entry(label, password)
        result["saved"] = True
        result["label"] = label
        result["overwritten"] = existing

    return jsonify(result)


@app.post("/api/bulk")
def api_bulk():
    data = request.get_json(silent=True) or {}
    count = int(data.get("count", 5))
    if count < 1 or count > 100:
        return jsonify({"error": "Count must be between 1 and 100."}), 400
    opts = _gen_options(data)

    items = []
    try:
        for _ in range(count):
            pwd = generate_password(**opts)
            a = analyze_password_strength(pwd)
            items.append({
                "password": pwd,
                "length": len(pwd),
                "score": a["score"],
                "level": a["strength_level"],
                "color": a["strength_color"],
            })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    avg = round(sum(i["score"] for i in items) / len(items), 1) if items else 0
    return jsonify({"count": len(items), "average_score": avg, "passwords": items})


@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True) or {}
    password = data.get("password")
    label = data.get("label")

    if label and password:
        return jsonify({"error": "Provide either password or label, not both."}), 400

    if label:
        password = storage.get_entry(str(label).strip())
        if password is None:
            return jsonify({"error": f"No password found for '{label}'."}), 404
    if not password:
        return jsonify({"error": "A password (or label) is required."}), 400

    a = analyze_password_strength(password)
    return jsonify({
        "length": a["length"],
        "score": a["score"],
        "max_score": a["max_score"],
        "level": a["strength_level"],
        "color": a["strength_color"],
        "meets_requirements": a["meets_requirements"],
        "crack_time": a["crack_time"],
        "feedback": a["feedback"],
        "criteria": a["criteria"],
    })


@app.get("/api/passwords")
def api_list():
    entries = storage.list_entries()
    return jsonify({
        "count": len(entries),
        "entries": [
            {"label": lbl, "length": length, "created_at": created}
            for (lbl, length, created) in entries
        ],
    })


@app.get("/api/passwords/<label>")
def api_get(label):
    password = storage.get_entry(label.strip())
    if password is None:
        return jsonify({"error": f"No password found for '{label}'."}), 404
    return jsonify({"label": label, "password": password})


@app.delete("/api/passwords/<label>")
def api_delete(label):
    label = label.strip()
    if not storage.label_exists(label):
        return jsonify({"error": f"No password found for '{label}'."}), 404
    ok = storage.delete_entry(label)
    if not ok:
        return jsonify({"error": "Could not delete entry."}), 500
    return jsonify({"deleted": True, "label": label})


if __name__ == "__main__":
    # Ensure storage exists on first run.
    if not storage.storage_exists():
        storage.create_storage()
    app.run(host="127.0.0.1", port=5000, debug=True)
