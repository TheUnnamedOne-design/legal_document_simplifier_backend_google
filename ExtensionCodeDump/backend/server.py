from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import shlex

app = Flask(__name__)
# Allow all origins for simplicity while developing
CORS(app, resources={r"/factcheck": {"origins": "*"}})

# Ensure every response includes proper CORS headers + allow OPTIONS
@app.after_request
def add_cors_headers(resp):
  resp.headers["Access-Control-Allow-Origin"] = "*"
  resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
  resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
  return resp

@app.route("/factcheck", methods=["POST", "OPTIONS"])
def factcheck():
  if request.method == "OPTIONS":
    # Preflight success
    return ("", 204)

  data = request.get_json(silent=True) or {}
  sentence = (data.get("sentence") or "").strip()
  if not sentence:
    return jsonify({"reply": "No sentence provided."}), 200

  # Call Ollama (Mistral). Keep it simple; adjust prompt as you like.
  prompt = (
    "You are a strict fact-checker. "
    "Given the statement below, reply briefly with True/False/Unclear and a one-line justification. "
    "Statement:\n" + sentence
  )

  try:
    # If you prefer streaming or the HTTP API, adapt here.
    # This uses the CLI for portability.
    cmd = ["ollama", "run", "mistral", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
      reply = f"Ollama error: {result.stderr.strip() or 'non-zero exit'}"
    else:
      reply = result.stdout.strip()
  except Exception as e:
    reply = f"Exception running Ollama: {e}"

  return jsonify({"reply": reply}), 200

if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=True)
