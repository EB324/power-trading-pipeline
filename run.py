#!/usr/bin/env python3
"""
电力价格驱动因子数据管道 — 一键运行
用法: python run.py
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# 确保项目根目录在 sys.path 中
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.config import RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, LOG_DIR, load_config, ensure_dirs
from src.utils.io import write_excel
from src.utils.lineage import LineageTracker
from src.utils.demo_data import create_demo_data
from src.ingest.ingest import ingest
from src.clean.clean import clean
from src.merge.merge import merge
from src.analyze.summary import SummaryStats
from src.analyze.correlation import CorrelationAnalysis
from src.analyze.trend import TrendAnalysis

# ─── 日志配置 ───
ensure_dirs()  # 确保 logs/ 目录存在再创建 FileHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            LOG_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

# ─── 可插拔分析模块注册表 ───
# 新增分析只需: 1) 写一个继承 BaseAnalysis 的类  2) 加到这个列表
ANALYSES = [
    ("summary_stats", SummaryStats()),
    ("correlation",   CorrelationAnalysis()),
    ("trend",         TrendAnalysis()),
]


def main():
    cfg = load_config()
    tracker = LineageTracker(LOG_DIR)

    print("=" * 50)
    print("  电力价格驱动因子 — 数据管道")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    # ─── 检查是否有数据，没有则生成示例 ───
    has_data = any(
        list((RAW_DIR / src["folder"]).glob("*.*"))
        for src in cfg["sources"].values()
        if (RAW_DIR / src["folder"]).exists()
    )
    if not has_data:
        logger.info("未发现原始数据，生成示例数据...")
        demo_files = create_demo_data(RAW_DIR)
        logger.info(f"已生成 {len(demo_files)} 个示例文件\n")

    # ─── 步骤 1: 数据录入 ───
    print("\n▶ 步骤 1/4: 扫描原始数据")
    source_files = ingest()
    all_raw_files = [f for files in source_files.values() for f in files]

    # ─── 步骤 2: 数据清洗 ───
    print("\n▶ 步骤 2/4: 清洗数据")
    cleaned = clean(source_files)
    tracker.record(
        step="clean",
        inputs=all_raw_files,
        outputs=[PROCESSED_DIR / f"{n}_clean.csv" for n in cleaned],
        notes=f"清洗 {len(cleaned)} 个数据源",
    )

    # ─── 步骤 3: 合并对齐 ───
    print("\n▶ 步骤 3/4: 合并对齐")
    merged = merge(cleaned)
    if merged is not None:
        tracker.record(
            step="merge",
            inputs=[PROCESSED_DIR / f"{n}_clean.csv" for n in cleaned],
            outputs=[PROCESSED_DIR / "merged.csv"],
            params=cfg.get("merge", {}),
            notes=f"合并后 {len(merged)} 行",
        )

    # ─── 步骤 4: 运行分析 ───
    print("\n▶ 步骤 4/4: 运行分析")
    analysis_cfg = cfg.get("analysis", {})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    for analysis_name, analyzer in ANALYSES:
        params = analysis_cfg.get(analysis_name, {})
        logger.info(f"运行: {analysis_name}")

        # 优先用 merged，没有就用第一个 cleaned
        data = merged if merged is not None else next(iter(cleaned.values()), None)
        if data is None:
            logger.warning("无数据可分析")
            continue

        result = analyzer.run(data, params)
        if result.empty:
            continue

        # 输出 Excel（带元信息 sheet）
        out_path = OUTPUT_DIR / f"{analysis_name}_{timestamp}.xlsx"
        write_excel(result, out_path, metadata={
            "分析类型": analysis_name,
            "运行时间": datetime.now().isoformat(),
            "数据源": ", ".join(cleaned.keys()),
            "数据行数": str(len(data)),
        })

        tracker.record(
            step=f"analyze_{analysis_name}",
            inputs=[PROCESSED_DIR / "merged.csv"],
            outputs=[out_path],
            params=params,
        )

    # ─── 完成 ───
    print("\n" + "=" * 50)
    print("✅ 管道运行完成！")
    print(f"   清洗结果: data/processed/")
    print(f"   分析输出: outputs/")
    print(f"   血缘日志: logs/lineage.jsonl")
    print(f"\n💡 运行可视化: streamlit run dashboard.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
