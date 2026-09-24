from pathlib import Path

from trame_slicer import __version__

BASE_URL = f"trame_slicer_{__version__}"
serve = {BASE_URL: str(Path(__file__).with_name("serve").resolve())}
scripts = [f"{BASE_URL}/chunk_loader.js"]
styles = []
