# 如何添加新分析模块

分析框架采用插件式设计，添加新分析不需要改动已有代码。

## 步骤 1：创建分析文件

在 `src/analyze/` 下新建一个 Python 文件，继承 `BaseAnalysis`：

```python
"""我的新分析模块"""

import pandas as pd
from src.analyze.base import BaseAnalysis


class MyNewAnalysis(BaseAnalysis):
    name = "my_new_analysis"
    description = "分析描述"

    def run(self, df: pd.DataFrame) -> dict:
        # 你的分析逻辑
        value_col = self.params.get("value_column", "price")

        result = df.groupby("date")[value_col].agg(["mean", "std"]).reset_index()

        return {
            "result_df": result,
            "summary": f"分析完成，共 {len(result)} 行结果",
            "metadata": {"value_column": value_col},
        }
```

## 步骤 2：注册分析类

打开 `src/analyze/run_analyses.py`，在 `ANALYSIS_REGISTRY` 中添加：

```python
ANALYSIS_REGISTRY = {
    "src.analyze.weighted_avg": "WeightedAverageAnalysis",
    "src.analyze.trend": "TrendAnalysis",
    "src.analyze.my_new": "MyNewAnalysis",        # 新增
}
```

## 步骤 3：在配置中启用

打开 `configs/pipeline.yaml`，在 `analyses:` 下添加：

```yaml
analyses:
  my_new_analysis:
    enabled: true
    description: "我的新分析"
    module: "src.analyze.my_new"
    params:
      value_column: "price"
      # 其他自定义参数
```

## 步骤 4：测试

```bash
make analyze
```

结果会自动输出到 `outputs/analysis_my_new_analysis_时间戳.xlsx`

## 分析模块的 run() 方法约定

**输入**：`df` 是合并后的完整数据集，包含所有来源的列。

**输出**：必须返回一个 dict，包含三个键：
- `result_df`：分析结果 DataFrame（会被导出为文件）
- `summary`：人类可读的文字摘要
- `metadata`：dict，记录参数和关键统计值
