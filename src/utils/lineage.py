"""数据血缘追踪 — 记录每步的输入/输出/参数"""
import json
import hashlib
from datetime import datetime
from pathlib import Path


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


class LineageTracker:
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "lineage.jsonl"

    def record(self, step: str, inputs: list, outputs: list,
               params: dict = None, notes: str = None):
        entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "inputs": [
                {"path": str(p), "hash": file_hash(p)}
                for p in inputs if Path(p).exists()
            ],
            "outputs": [str(p) for p in outputs],
            "params": params or {},
            "notes": notes,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
