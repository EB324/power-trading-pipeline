"""步骤1: 数据录入 — 扫描 raw 文件，基本检查"""
import logging
from pathlib import Path
from src.utils.config import RAW_DIR, load_config
from src.utils.io import read_file

logger = logging.getLogger(__name__)


def ingest() -> dict[str, list[Path]]:
    """扫描所有数据源文件夹，返回 {source_name: [file_paths]}"""
    cfg = load_config()
    result = {}

    for name, src in cfg["sources"].items():
        folder = RAW_DIR / src["folder"]
        files = sorted(
            p for p in folder.iterdir()
            if p.suffix.lower() in (".csv", ".xlsx", ".xls")
        ) if folder.exists() else []

        result[name] = files
        if files:
            logger.info(f"📥 {src['description']}: 发现 {len(files)} 个文件")
            for f in files:
                df = read_file(f)
                logger.info(f"   {f.name}  ({len(df)} 行, {len(df.columns)} 列)")
        else:
            logger.info(f"📥 {src['description']}: 无文件")

    return result
