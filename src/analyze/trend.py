"""趋势统计分析 — 各因子的移动平均"""
import logging
import pandas as pd
from src.analyze.base import BaseAnalysis

logger = logging.getLogger(__name__)


class TrendAnalysis(BaseAnalysis):
    name = "trend"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        windows = params.get("windows", [7, 30])

        # 找时间列
        time_cols = [c for c in df.columns if "datetime" in c.lower() or "time" in c.lower()]
        if not time_cols:
            logger.warning("未找到时间列，跳过趋势分析")
            return pd.DataFrame()

        t_c = time_cols[0]
        numeric_cols = df.select_dtypes("number").columns.tolist()
        if not numeric_cols:
            return pd.DataFrame()

        result = df[[t_c] + numeric_cols].copy()
        result = result.sort_values(t_c).reset_index(drop=True)

        # 对每个数值列计算滚动均值
        for col in numeric_cols:
            for w in windows:
                result[f"{col}_MA{w}d"] = (
                    result[col]
                    .rolling(window=w * 24, min_periods=1)  # 小时数据, 窗口*24
                    .mean()
                    .round(4)
                )

        logger.info(f"📊 趋势分析: {len(numeric_cols)} 个因子, 窗口={windows}")
        return result
