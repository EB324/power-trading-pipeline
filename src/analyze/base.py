"""分析基类 — 所有分析模块继承此类"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseAnalysis(ABC):
    """添加新分析只需：
    1. 新建文件 src/analyze/my_analysis.py
    2. 继承 BaseAnalysis，实现 run()
    3. 在 run.py 的 ANALYSES 列表里加一行
    """

    name: str = "base"

    @abstractmethod
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """执行分析，返回结果 DataFrame"""
        ...
