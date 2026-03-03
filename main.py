"""
main.py — Project Janus entry point.

1. Runs the Harvester against a list of target URLs to populate data/vault.db.
2. Runs the SiteCloner to produce a navigable Markdown mirror of a full domain.
3. Launches the interactive Mistral/Ollama agent loop.
"""

import os
from src.harvester.engine import Harvester

# ---------------------------------------------------------------------------
# Target URLs to harvest (per-thread; adds posts to vault.db)
# ---------------------------------------------------------------------------
TARGET_URLS = [
    # Add forum thread URLs here, e.g.:
    # "https://stolenhistory.net/threads/some-thread.1234/",
]

# ---------------------------------------------------------------------------
# Full-site Markdown clone (set to seed URL to mirror an entire domain)
# ---------------------------------------------------------------------------
TARGET_SITE = None          # e.g. "https://stolenhistory.net/"
CLONE_MAX_PAGES = 500       # safety cap on number of pages crawled

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "vault.db")
MIRROR_DIR = os.path.join(os.path.dirname(__file__), "data", "site_mirror")


def run_harvester():
    if not TARGET_URLS:
        print("[main] No TARGET_URLS configured — skipping thread harvest phase.")
        return

    print(f"[main] Starting harvest of {len(TARGET_URLS)} URL(s)...")
    harvester = Harvester(DB_PATH)
    for url in TARGET_URLS:
        harvester.ingest_thread(url)
    print("[main] Harvest complete.")


def run_site_cloner():
    if not TARGET_SITE:
        print("[main] No TARGET_SITE configured — skipping site clone phase.")
        return

    from src.harvester.site_cloner import SiteCloner
    print(f"[main] Starting full-site clone of {TARGET_SITE} (max {CLONE_MAX_PAGES} pages)...")
    cloner = SiteCloner(output_dir=MIRROR_DIR, max_pages=CLONE_MAX_PAGES)
    mirror_root = cloner.clone(TARGET_SITE)
    print(f"[main] Site mirror written to: {mirror_root}")


def run_agent():
    from run_agent import main as agent_main
    agent_main()


if __name__ == "__main__":
    run_harvester()
    run_site_cloner()
    run_agent()

