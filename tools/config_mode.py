"""Switch only this project's Codex configuration; back up every replaced file."""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from orchestration.protocol import safe_path

def switch(root, mode):
    root=Path(root).resolve()
    if mode not in ("legacy","current"):
        raise ValueError("mode must be legacy or current")
    source=root/"compat"/mode/".codex"
    files=["config.toml","agents/researcher.toml","agents/solver.toml","agents/reviewer.toml"]
    for name in files:
        if not (source/name).is_file():
            raise ValueError("missing compatibility source")
    backup=root/"work/config-backups"/str(time.time_ns())
    backup.mkdir(parents=True)
    for name in files:
        dest=safe_path(root,".codex/"+name)
        if dest.exists():
            old=backup/name
            old.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dest,old)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source/name,dest)
    return {"mode":mode,"backup":backup.relative_to(root).as_posix(),
            "note":"restart Codex and verify project trust; no global configuration changed"}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["current","legacy"])
    print(json.dumps(switch(ROOT,p.parse_args().mode),ensure_ascii=False,indent=2))
