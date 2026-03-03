"""scripts/run_demo.py

Run a single canned query against the Mistral Large 3 cloud model via Ollama
and write the result to docs/latest_run.json for the GitHub Pages demo page.

Required environment variable:
  OLLAMA_HOST — URL of the remote Ollama server
                Falls back to http://localhost:11434 if not set.
"""

import json
import os
from datetime import datetime, timezone

import ollama

MODEL = "mistral-large-3:675b-cloud"
DEMO_QUERY = (
    "Describe Project Janus: what it archives, how the Harvester collects data, "
    "how the MCP Server exposes it as tools, and how Mistral Large 3 reasons "
    "over the results to produce neutral, unfiltered answers."
)
SYSTEM_PROMPT = (
    "You are a neutral technical assistant for Project Janus, a sovereign archival "
    "system. Describe the architecture clearly and concisely."
)


def main():
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    print(f"[demo] Connecting to Ollama at : {host}")
    print(f"[demo] Model                   : {MODEL}")
    print(f"[demo] Query                   : {DEMO_QUERY}\n")

    output = {
        "model": MODEL,
        "ollama_host": host,
        "query": DEMO_QUERY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response": "",
        "error": None,
    }

    try:
        client = ollama.Client(host=host)
        response = client.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": DEMO_QUERY},
            ],
        )
        output["response"] = response["message"]["content"]
        print(f"[demo] Response received ({len(output['response'])} chars)")
    except Exception as exc:
        output["error"] = str(exc)
        print(f"[demo] Error: {exc}")

    os.makedirs("docs", exist_ok=True)
    out_path = os.path.join("docs", "latest_run.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
    print(f"[demo] Written to {out_path}")


if __name__ == "__main__":
    main()
