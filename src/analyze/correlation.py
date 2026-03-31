"""因子相关性分析"""
import logging
import pandas as pd
from src.analyze.base import BaseAnalysis

logger = logging.getLogger(__name__)


class CorrelationAnalysis(BaseAnalysis):
    name = "correlation"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        method = params.get("method", "pearson")

        # 只取数值列
        numeric = df.select_dtypes("number")
        if numeric.shape[1] < 2:
            logger.warning("数值列不足 2 列，跳过相关性分析")
            return pd.DataFrame()

        corr = numeric.corr(method=method)
        logger.info(f"📊 相关性矩阵: {corr.shape[0]} 个因子, 方法={method}")
        return corr
