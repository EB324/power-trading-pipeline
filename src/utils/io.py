"""文件读写工具，兼容 OneDrive 文件锁"""
import time
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def read_file(path: Path) -> pd.DataFrame:
    """读取 CSV 或 Excel，自动重试应对 OneDrive 锁"""
    path = Path(path)
    for attempt in range(3):
        try:
            if path.suffix.lower() in (".xlsx", ".xls"):
                return pd.read_excel(path, engine="openpyxl")
            else:
                for enc in ("utf-8-sig", "utf-8", "gbk"):
                    try:
                        return pd.read_csv(path, encoding=enc)
                    except UnicodeDecodeError:
                        continue
                return pd.read_csv(path, encoding="latin1")
        except PermissionError:
            logger.warning(f"文件被锁，{3*(attempt+1)}秒后重试: {path.name}")
            time.sleep(3 * (attempt + 1))
    raise PermissionError(f"无法打开文件（请关闭 Excel）: {path}")


def write_excel(df: pd.DataFrame, path: Path, metadata: dict = None):
    """写 Excel，可选附加元信息 sheet"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="数据", index=False)
        if metadata:
            meta_df = pd.DataFrame(
                list(metadata.items()), columns=["属性", "值"]
            )
            meta_df.to_excel(w, sheet_name="元信息", index=False)
    logger.info(f"已输出: {path.name}")
