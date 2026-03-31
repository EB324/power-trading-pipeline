"""因子统计摘要 — 均值 / 标准差 / 缺失率 / 滚动统计"""
import logging
import pandas as pd
from src.analyze.base import BaseAnalysis

logger = logging.getLogger(__name__)


class SummaryStats(BaseAnalysis):
    name = "summary_stats"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        windows = params.get("windows", [7, 30])

        numeric = df.select_dtypes("number")
        if numeric.empty:
            logger.warning("无数值列，跳过统计摘要")
            return pd.DataFrame()

        # 基础统计
        stats = numeric.describe().T
        stats["missing_pct"] = ((numeric.isna().sum() / len(numeric)) * 100).round(2)
        stats["non_null_count"] = numeric.notna().sum()

        # 重命名使输出更友好
        stats = stats.rename(columns={
            "count": "有效数量",
            "mean": "均值",
            "std": "标准差",
            "min": "最小值",
            "25%": "P25",
            "50%": "中位数",
            "75%": "P75",
            "max": "最大值",
            "missing_pct": "缺失率%",
            "non_null_count": "非空数",
        })

        stats.index.name = "因子"
        stats = stats.reset_index()

        logger.info(f"📊 统计摘要: {len(stats)} 个因子")
        return stats
