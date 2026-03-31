# 电力价格驱动因子数据管道

收集、清洗、对齐影响电力价格的外部因子数据，并提供可视化仪表板。

## 数据流程

```mermaid
flowchart LR
    SRC["Official Data Sources"] -->|collect| RAW["Raw Data (data/raw/)"]
    RAW -->|clean & align| PROC["Processed Data (data/processed/)"]
    PROC -->|analyse| OUT["Excel + Dashboard"]

    style SRC fill:#1e3a5f,stroke:#85b7eb,color:#fff
    style RAW fill:#0f6e56,stroke:#5dcaa5,color:#fff
    style PROC fill:#0f6e56,stroke:#5dcaa5,color:#fff
    style OUT fill:#854f0b,stroke:#fac775,color:#fff
```

> ℹ️ 上图为 Mermaid 流程图。GitHub / GitLab 可直接渲染；VS Code 需安装 [Mermaid Preview](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) 扩展；也可粘贴到 [mermaid.live](https://mermaid.live) 在线查看。

## 快速开始

**最简单 — 双击运行（Windows）：**

```
run_pipeline.bat
```

**或者用命令行：**

```powershell
irm https://astral.sh/uv/install.ps1 | iex   # 首次：安装 uv
uv sync                                       # 首次：安装项目依赖
uv run python run.py                          # 运行管道
uv run streamlit run dashboard.py             # 启动仪表板
```

<details>
<summary>没有 uv？用 pip 也行</summary>

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows 激活虚拟环境
pip install -e .
python run.py
streamlit run dashboard.py
```

</details>

> 首次运行会自动生成示例数据，跑完清洗→合并→分析全流程。结果在 `outputs/` 和浏览器仪表板中查看。

## 项目文件结构

```text
power-trading-pipeline/
|
|-- data/
|   |-- raw/                    <-- 原始数据放这里
|   |   |-- weather/                天气数据
|   |   |-- fuel_price/             燃料价格
|   |   |-- load_actual/            电力负荷
|   |   |-- renewable_output/       新能源出力
|   |   +-- carbon_price/           碳排放价格
|   +-- processed/              <-- 清洗后的数据（自动生成）
|
|-- src/                        <-- 所有处理逻辑代码
|   |-- ingest/                     数据读取
|   |-- clean/                      数据清洗
|   |-- merge/                      数据合并对齐
|   |-- analyze/                    分析模块（统计/趋势/相关性等）
|   +-- utils/                      配置、IO、血缘等工具
|
|-- outputs/                    <-- 分析结果 Excel（自动生成）
|-- logs/                       <-- 运行日志和血缘记录（自动生成）
|-- docs/                       <-- 项目文档
|-- notebooks/                  <-- Jupyter 笔记本
|-- tests/                      <-- 测试代码
|-- configs/pipeline.yaml       <-- 管道参数配置
|-- run.py                      <-- 数据管道入口
|-- run_pipeline.bat            <-- Windows 一键运行脚本
|-- dashboard.py                <-- Streamlit 可视化仪表板
+-- pyproject.toml              <-- Python 依赖声明
```

## 数据因子

| 因子 | 文件夹 | 说明 | 现实数据来源 |
| --- | --- | --- | --- |
| 气象 | `data/raw/weather/` | 温度/湿度/风速/日照/降水 | 气象台 API / Open-Meteo |
| 燃料价格 | `data/raw/fuel_price/` | LNG/煤炭/原油 | Wind/Bloomberg 导出 |
| 电力负荷 | `data/raw/load_actual/` | 实际负荷 + 日前预测 | 电力交易中心 |
| 新能源 | `data/raw/renewable_output/` | 风电/光伏出力 | 电网调度数据 |
| 碳价 | `data/raw/carbon_price/` | 全国碳市场 + EU ETS | 交易所公告 |

## 用自己的数据

1. **准备文件** — Excel (`.xlsx`) 或 CSV，必须包含 `datetime` 列
2. **放入文件夹** — 放到对应的 `data/raw/<因子>/` 目录下
3. **运行管道** — `python run.py`
4. **查看结果** — `streamlit run dashboard.py` 或打开 `outputs/`

## 仪表板功能

- **因子概览**: KPI 卡片 + 数据质量表
- **时序趋势**: 多因子叠加折线图，支持日/周粒度切换
- **相关性矩阵**: 热力图 + 高相关因子对筛选
- **数据导出**: 按时间/列筛选后一键下载 Excel/CSV

## OneDrive / SharePoint 注意

- 确保文件同步完成后再运行
- 不要多人同时运行 `run.py`
- `data/raw/` 里的文件一旦放入不要修改，有新版本请放新文件

## 更多文档

- [如何添加新分析模块](docs/add_new_analysis.md) — 插件式扩展，不用改已有代码
- [OneDrive / SharePoint 使用指南](docs/onedrive_guide.md) — 团队协作和文件同步注意事项
