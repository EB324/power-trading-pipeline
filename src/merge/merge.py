"""步骤3: 合并对齐 — 将多源数据按时间轴合并"""
import logging
from pathlib import Path
import pandas as pd
from src.utils.config import PROCESSED_DIR, load_config

logger = logging.getLogger(__name__)


def merge(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    """将多个已清洗数据源按时间列合并"""
    cfg = load_config()
    merge_cfg = cfg.get("merge", {})
    freq = merge_cfg.get("time_resolution", "1h")
    how = merge_cfg.get("join_method", "outer")

    if len(cleaned) < 2:
        logger.info("🔗 不足两个数据源，跳过合并")
        if cleaned:
            name, df = next(iter(cleaned.items()))
            out = PROCESSED_DIR / "merged.csv"
            df.to_csv(out, index=False, encoding="utf-8-sig")
            return df
        return None

    # 分别 resample 每个源到统一频率，然后 join
    resampled = {}
    for name, df in cleaned.items():
        src_cfg = cfg["sources"][name]
        time_col = src_cfg.get("time_column", "datetime").lower().replace(" ", "_")
        if time_col not in df.columns:
            logger.warning(f"  {name}: 缺少时间列 '{time_col}'，跳过")
            continue

        # 选择数值列 resample
        numeric_cols = df.select_dtypes("number").columns.tolist()
        if not numeric_cols:
            continue

        ts = df.set_index(time_col)[numeric_cols]
        ts = ts.resample(freq).mean()           # 按频率聚合
        ts = ts.add_prefix(f"{name}_")           # 加前缀区分来源
        resampled[name] = ts
        logger.info(f"  {name}: resample 到 {freq}, {len(ts)} 个时间点")

    # 逐步 join
    names = list(resampled.keys())
    merged = resampled[names[0]]
    for n in names[1:]:
        merged = merged.join(resampled[n], how=how)

    merged = merged.reset_index()
    out_path = PROCESSED_DIR / "merged.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"🔗 合并完成: {len(merged)} 行 × {len(merged.columns)} 列 → {out_path.name}")
    return merged
