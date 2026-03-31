"""路径常量和配置加载"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT / "configs"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"
LOG_DIR = ROOT / "logs"


def load_config() -> dict:
    with open(CONFIG_DIR / "pipeline.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs():
    for d in [RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    for src in cfg["sources"].values():
        (RAW_DIR / src["folder"]).mkdir(parents=True, exist_ok=True)
