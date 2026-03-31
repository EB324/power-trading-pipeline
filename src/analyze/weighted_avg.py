"""加权平均分析"""
import logging
import pandas as pd
from src.analyze.base import BaseAnalysis

logger = logging.getLogger(__name__)


class WeightedAverage(BaseAnalysis):
    name = "weighted_average"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        val_col = params.get("value_column", "price")
        wt_col = params.get("weight_column", "volume")

        # 找到匹配的列（可能有来源前缀）
        val_candidates = [c for c in df.columns if val_col in c.lower()]
        wt_candidates = [c for c in df.columns if wt_col in c.lower()]

        if not val_candidates:
            logger.warning(f"未找到价格列 (含 '{val_col}')，跳过加权平均")
            return pd.DataFrame()

        val_c = val_candidates[0]

        if wt_candidates:
            wt_c = wt_candidates[0]
            valid = df[[val_c, wt_c]].dropna()
            if valid[wt_c].sum() == 0:
                weighted_avg = valid[val_c].mean()
            else:
                weighted_avg = (valid[val_c] * valid[wt_c]).sum() / valid[wt_c].sum()
            result = pd.DataFrame({
                "指标": ["加权平均", "简单平均", "最大值", "最小值", "数据点数"],
                "值": [
                    round(weighted_avg, 4),
                    round(valid[val_c].mean(), 4),
                    round(valid[val_c].max(), 4),
                    round(valid[val_c].min(), 4),
                    len(valid),
                ],
            })
        else:
            valid = df[[val_c]].dropna()
            result = pd.DataFrame({
                "指标": ["简单平均", "最大值", "最小值", "标准差", "数据点数"],
                "值": [
                    round(valid[val_c].mean(), 4),
                    round(valid[val_c].max(), 4),
                    round(valid[val_c].min(), 4),
                    round(valid[val_c].std(), 4),
                    len(valid),
                ],
            })

        logger.info(f"📊 加权平均分析完成 (列: {val_c})")
        return result
