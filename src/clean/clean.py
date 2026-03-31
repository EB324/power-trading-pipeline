"""步骤2: 数据清洗 — 统一时间格式、去重、标记来源"""
import logging
from pathlib import Path
import pandas as pd
from src.utils.config import PROCESSED_DIR, load_config
from src.utils.io import read_file

logger = logging.getLogger(__name__)


def clean(source_files: dict[str, list[Path]]) -> dict[str, pd.DataFrame]:
    """对每个数据源执行基础清洗，返回 {source_name: cleaned_df}"""
    cfg = load_config()
    cleaned = {}

    for name, files in source_files.items():
        if not files:
            continue

        src_cfg = cfg["sources"][name]
        time_col = src_cfg.get("time_column", "datetime")

        # 读取并合并同一来源的所有文件
        dfs = []
        for f in files:
            df = read_file(f)
            df["_source_file"] = f.name       # 行级血缘：记录来源文件
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)
        rows_before = len(df)

        # 标准化列名（去空格、小写）
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        time_col = time_col.lower().replace(" ", "_")

        # 统一时间列
        if time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df = df.dropna(subset=[time_col])
            df = df.sort_values(time_col).reset_index(drop=True)

        # 去重
        df = df.drop_duplicates().reset_index(drop=True)
        rows_after = len(df)

        # 保存
        out_path = PROCESSED_DIR / f"{name}_clean.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        cleaned[name] = df

        logger.info(
            f"🧹 {src_cfg['description']}: {rows_before}→{rows_after} 行, "
            f"保存到 {out_path.name}"
        )

    return cleaned
