import argparse
from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", action="store_true", required=True)
    parser.add_argument("--setup-only", action="store_true")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.exit(1, "Cần Python 3.12\n")
    import hashlib
    key = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:12]
    env = (Path(os.environ["LOCALAPPDATA"]) / "SqlImportLab" / key
           if sys.platform == "win32" else ROOT / ".venv")
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        venv.EnvBuilder(with_pip=True).create(env)
    marker = env / "requirements.sha256"
    requirements = ROOT / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    if not marker.is_file() or marker.read_text().strip() != digest:
        subprocess.run([python, "-m", "pip", "install", "-r", requirements], check=True)
        marker.write_text(digest)
    if not args.setup_only:
        subprocess.run([python, "-m", "notebook", "--notebook-dir", ROOT,
                        ROOT / "notebooks/02_import.ipynb"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
