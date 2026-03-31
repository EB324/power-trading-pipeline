#!/usr/bin/env python3
"""
电力价格驱动因子 — 可视化仪表板
用法: streamlit run dashboard.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

# ═══════════════════════════════════════════════════════
# 页面配置
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="电力因子数据看板",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════
# 数据加载（缓存）
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=300)  # 5 分钟缓存
def load_merged() -> pd.DataFrame | None:
    """加载合并后数据"""
    path = PROCESSED_DIR / "merged.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["datetime"])
    return df


@st.cache_data(ttl=300)
def load_cleaned_sources() -> dict[str, pd.DataFrame]:
    """加载各个 cleaned 数据源"""
    result = {}
    for f in sorted(PROCESSED_DIR.glob("*_clean.csv")):
        name = f.stem.replace("_clean", "")
        df = pd.read_csv(f)
        for col in df.columns:
            if "datetime" in col.lower() or "time" in col.lower():
                df[col] = pd.to_datetime(df[col], errors="coerce")
        result[name] = df
    return result


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame → Excel bytes（用于下载）"""
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════════════
st.sidebar.title("⚡ 电力因子看板")
page = st.sidebar.radio(
    "导航",
    ["📋 因子概览", "📈 时序趋势", "🔥 相关性矩阵", "📤 数据导出"],
    label_visibility="collapsed",
)

# 加载数据
merged = load_merged()
sources = load_cleaned_sources()

if merged is None and not sources:
    st.error("未找到数据！请先运行 `python run.py` 生成数据。")
    st.stop()

# 时间范围筛选（全局）
if merged is not None and "datetime" in merged.columns:
    date_min = merged["datetime"].min().date()
    date_max = merged["datetime"].max().date()
    st.sidebar.markdown("---")
    st.sidebar.subheader("时间范围")
    date_range = st.sidebar.date_input(
        "选择日期",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )
    if len(date_range) == 2:
        mask = (merged["datetime"].dt.date >= date_range[0]) & (
            merged["datetime"].dt.date <= date_range[1]
        )
        merged_filtered = merged[mask].copy()
    else:
        merged_filtered = merged.copy()
else:
    merged_filtered = merged


# ═══════════════════════════════════════════════════════
# 页面 1: 因子概览
# ═══════════════════════════════════════════════════════
if page == "📋 因子概览":
    st.title("因子概览")

    if merged_filtered is not None:
        numeric_cols = merged_filtered.select_dtypes("number").columns.tolist()

        # KPI 卡片
        cols_per_row = 4
        for i in range(0, len(numeric_cols), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col_name in enumerate(numeric_cols[i : i + cols_per_row]):
                with cols[j]:
                    latest = merged_filtered[col_name].dropna()
                    if len(latest) > 0:
                        current = latest.iloc[-1]
                        mean_val = latest.mean()
                        delta = ((current - mean_val) / mean_val * 100) if mean_val != 0 else 0
                        st.metric(
                            label=col_name,
                            value=f"{current:,.1f}",
                            delta=f"{delta:+.1f}% vs 均值",
                        )

        st.markdown("---")

        # 数据质量表
        st.subheader("数据质量")
        quality = pd.DataFrame({
            "因子": numeric_cols,
            "有效数据量": [merged_filtered[c].notna().sum() for c in numeric_cols],
            "缺失率 %": [
                round(merged_filtered[c].isna().sum() / len(merged_filtered) * 100, 2)
                for c in numeric_cols
            ],
            "均值": [round(merged_filtered[c].mean(), 2) for c in numeric_cols],
            "标准差": [round(merged_filtered[c].std(), 2) for c in numeric_cols],
            "最小值": [round(merged_filtered[c].min(), 2) for c in numeric_cols],
            "最大值": [round(merged_filtered[c].max(), 2) for c in numeric_cols],
        })
        st.dataframe(quality, use_container_width=True, hide_index=True)

    # 各数据源状态
    st.subheader("数据源状态")
    for name, df in sources.items():
        with st.expander(f"📁 {name}  ({len(df)} 行, {len(df.columns)} 列)"):
            st.dataframe(df.head(10), use_container_width=True)


# ═══════════════════════════════════════════════════════
# 页面 2: 时序趋势
# ═══════════════════════════════════════════════════════
elif page == "📈 时序趋势":
    st.title("时序趋势")

    if merged_filtered is not None and "datetime" in merged_filtered.columns:
        numeric_cols = merged_filtered.select_dtypes("number").columns.tolist()

        # 因子选择
        selected = st.multiselect(
            "选择因子（可多选）",
            numeric_cols,
            default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols,
        )

        if selected:
            # 采样粒度
            resample_freq = st.radio(
                "时间粒度",
                ["原始 (1h)", "日均", "周均"],
                horizontal=True,
            )

            plot_df = merged_filtered.set_index("datetime")[selected].copy()

            if resample_freq == "日均":
                plot_df = plot_df.resample("1D").mean()
            elif resample_freq == "周均":
                plot_df = plot_df.resample("1W").mean()

            st.line_chart(plot_df, use_container_width=True)

            # 各因子单独看
            if st.checkbox("展开单因子视图"):
                for col in selected:
                    st.subheader(col)
                    single = merged_filtered.set_index("datetime")[[col]].copy()
                    if resample_freq == "日均":
                        single = single.resample("1D").mean()
                    elif resample_freq == "周均":
                        single = single.resample("1W").mean()
                    st.area_chart(single, use_container_width=True)
    else:
        st.warning("无合并数据，请先运行管道。")


# ═══════════════════════════════════════════════════════
# 页面 3: 相关性矩阵
# ═══════════════════════════════════════════════════════
elif page == "🔥 相关性矩阵":
    st.title("因子相关性矩阵")

    if merged_filtered is not None:
        numeric_cols = merged_filtered.select_dtypes("number").columns.tolist()

        method = st.radio("相关性方法", ["pearson", "spearman"], horizontal=True)

        corr = merged_filtered[numeric_cols].corr(method=method)

        # 用 Streamlit 内置热力图（基于 dataframe 着色）
        st.dataframe(
            corr.style.background_gradient(cmap="RdYlBu_r", vmin=-1, vmax=1).format("{:.3f}"),
            use_container_width=True,
        )

        # 高相关性对
        st.subheader("高相关性因子对 (|r| > 0.5)")
        pairs = []
        for i in range(len(corr)):
            for j in range(i + 1, len(corr)):
                r = corr.iloc[i, j]
                if abs(r) > 0.5:
                    pairs.append({
                        "因子 A": corr.index[i],
                        "因子 B": corr.columns[j],
                        "相关系数": round(r, 4),
                    })
        if pairs:
            pairs_df = pd.DataFrame(pairs).sort_values("相关系数", key=abs, ascending=False)
            st.dataframe(pairs_df, use_container_width=True, hide_index=True)
        else:
            st.info("无 |r| > 0.5 的因子对")
    else:
        st.warning("无合并数据。")


# ═══════════════════════════════════════════════════════
# 页面 4: 数据导出
# ═══════════════════════════════════════════════════════
elif page == "📤 数据导出":
    st.title("数据导出")

    tab1, tab2 = st.tabs(["合并数据导出", "单源数据导出"])

    with tab1:
        if merged_filtered is not None:
            st.write(f"当前筛选: {len(merged_filtered)} 行 × {len(merged_filtered.columns)} 列")

            # 列选择
            all_cols = merged_filtered.columns.tolist()
            export_cols = st.multiselect("选择导出列", all_cols, default=all_cols)

            if export_cols:
                export_df = merged_filtered[export_cols]
                st.dataframe(export_df.head(20), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "⬇️ 下载 Excel",
                        data=to_excel_bytes(export_df),
                        file_name=f"factors_export_{datetime.now():%Y%m%d_%H%M}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                with col2:
                    st.download_button(
                        "⬇️ 下载 CSV",
                        data=export_df.to_csv(index=False, encoding="utf-8-sig"),
                        file_name=f"factors_export_{datetime.now():%Y%m%d_%H%M}.csv",
                        mime="text/csv",
                    )
        else:
            st.warning("无合并数据。")

    with tab2:
        if sources:
            source_name = st.selectbox("选择数据源", list(sources.keys()))
            src_df = sources[source_name]
            st.write(f"{len(src_df)} 行 × {len(src_df.columns)} 列")
            st.dataframe(src_df.head(20), use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "⬇️ 下载 Excel",
                    data=to_excel_bytes(src_df),
                    file_name=f"{source_name}_{datetime.now():%Y%m%d_%H%M}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_excel_{source_name}",
                )
            with col2:
                st.download_button(
                    "⬇️ 下载 CSV",
                    data=src_df.to_csv(index=False, encoding="utf-8-sig"),
                    file_name=f"{source_name}_{datetime.now():%Y%m%d_%H%M}.csv",
                    mime="text/csv",
                    key=f"dl_csv_{source_name}",
                )
        else:
            st.warning("无数据源文件。")

    # 分析结果文件
    st.markdown("---")
    st.subheader("历史分析结果")
    analysis_files = sorted(OUTPUT_DIR.glob("*.xlsx"), reverse=True) if OUTPUT_DIR.exists() else []
    if analysis_files:
        for f in analysis_files[:10]:
            size_kb = f.stat().st_size / 1024
            st.download_button(
                f"📊 {f.name}  ({size_kb:.0f} KB)",
                data=f.read_bytes(),
                file_name=f.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{f.name}",
            )
    else:
        st.info("暂无分析输出文件，请先运行 python run.py")
