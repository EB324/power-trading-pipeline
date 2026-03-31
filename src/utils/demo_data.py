"""生成仿真因子数据 — 让 POC 开箱即用
数据模式参考真实场景:
  - 气象: 日内温度正弦波 + 季节趋势
  - 燃料: 随机游走 + 均值回归
  - 负荷: 日内双峰 (上午+傍晚) + 周末效应
  - 新能源: 光伏跟日照, 风电跟风速
  - 碳价: 缓慢上行趋势
"""
import numpy as np
import pandas as pd
from pathlib import Path


def create_demo_data(raw_dir: Path) -> list[Path]:
    """在 data/raw/ 下生成两个月的仿真因子数据"""
    np.random.seed(42)
    hours = pd.date_range("2026-01-01", "2026-02-28 23:00", freq="1h")
    n = len(hours)
    hour_of_day = np.array([t.hour for t in hours])
    day_of_week = np.array([t.dayofweek for t in hours])
    day_of_year = np.array([t.dayofyear for t in hours])

    created_files = []

    # ═══ 1. 气象数据 ═══
    # 温度: 冬季基线 5°C, 日内振幅 ±8°C
    temp_base = 5 + 3 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
    temp_daily = 8 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
    temperature = temp_base + temp_daily + np.random.normal(0, 2, n)

    # 湿度: 与温度负相关
    humidity = 70 - 0.5 * temperature + np.random.normal(0, 8, n)
    humidity = np.clip(humidity, 20, 100)

    # 风速: 对数正态
    wind_speed = np.random.lognormal(mean=1.5, sigma=0.6, size=n)
    wind_speed = np.clip(wind_speed, 0.2, 25)

    # 太阳辐照: 白天正弦, 夜间为 0
    solar_max = 600 + 200 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    solar_raw = solar_max * np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12))
    solar_raw[hour_of_day < 6] = 0
    solar_raw[hour_of_day > 18] = 0
    solar_rad = solar_raw + np.random.normal(0, 30, n)
    solar_rad = np.maximum(0, solar_rad)

    # 降水
    precip = np.random.exponential(0.3, n)
    precip[np.random.random(n) > 0.15] = 0  # 85% 时间无降水

    weather = pd.DataFrame({
        "datetime": hours,
        "temperature_c": temperature.round(1),
        "humidity_pct": humidity.round(1),
        "wind_speed_ms": wind_speed.round(1),
        "solar_rad_whm2": solar_rad.round(0),
        "precipitation_mm": precip.round(1),
    })
    for month in [1, 2]:
        out = raw_dir / "weather" / f"weather_2026{month:02d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        weather[weather["datetime"].dt.month == month].to_csv(
            out, index=False, encoding="utf-8-sig"
        )
        created_files.append(out)

    # ═══ 2. 燃料价格 ═══ (日频, 然后 forward fill 到小时)
    days = pd.date_range("2026-01-01", "2026-02-28", freq="1D")
    nd = len(days)

    # JKM LNG: 均值约 12 USD/MMBtu, 随机游走
    gas_walk = np.cumsum(np.random.normal(0, 0.15, nd))
    gas_price = 12 + gas_walk + 0.8 * np.sin(2 * np.pi * np.arange(nd) / 30)

    # 纽卡斯尔煤: 均值约 130 USD/ton
    coal_walk = np.cumsum(np.random.normal(0, 0.8, nd))
    coal_price = 130 + coal_walk

    # 布伦特原油
    oil_walk = np.cumsum(np.random.normal(0, 0.5, nd))
    oil_price = 78 + oil_walk

    fuel = pd.DataFrame({
        "datetime": days,
        "gas_jkm_usd_mmbtu": gas_price.round(2),
        "coal_newc_usd_ton": coal_price.round(2),
        "oil_brent_usd_bbl": oil_price.round(2),
    })
    for month in [1, 2]:
        out = raw_dir / "fuel_price" / f"fuel_price_2026{month:02d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        fuel[fuel["datetime"].dt.month == month].to_csv(
            out, index=False, encoding="utf-8-sig"
        )
        created_files.append(out)

    # ═══ 3. 电力负荷 ═══
    # 日内双峰: 上午 10 点 + 傍晚 19 点
    peak_am = 5000 * np.exp(-0.5 * ((hour_of_day - 10) / 2.5) ** 2)
    peak_pm = 6000 * np.exp(-0.5 * ((hour_of_day - 19) / 2.5) ** 2)
    base_load = 35000
    weekend_factor = np.where(day_of_week >= 5, 0.82, 1.0)
    # 冷天负荷更高（供暖）
    temp_effect = -300 * temperature
    load_mw = (base_load + peak_am + peak_pm + temp_effect) * weekend_factor
    load_mw += np.random.normal(0, 800, n)

    # 日前预测: 实际值 + 预测误差
    forecast_error = np.random.normal(0, 600, n)
    load_forecast = load_mw + forecast_error

    load_df = pd.DataFrame({
        "datetime": hours,
        "load_mw": load_mw.round(0),
        "load_forecast_mw": load_forecast.round(0),
    })
    for month in [1, 2]:
        out = raw_dir / "load_actual" / f"load_actual_2026{month:02d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        load_df[load_df["datetime"].dt.month == month].to_csv(
            out, index=False, encoding="utf-8-sig"
        )
        created_files.append(out)

    # ═══ 4. 新能源出力 ═══
    # 光伏: 与太阳辐照成正比, 装机 20GW
    solar_mw = 20000 * (solar_rad / solar_max.max()) * np.random.uniform(0.85, 1.0, n)
    solar_mw = np.maximum(0, solar_mw)

    # 风电: 与风速三次方成正比 (简化), 装机 30GW
    wind_cf = np.minimum(1, (wind_speed / 12) ** 3) * np.random.uniform(0.7, 1.0, n)
    wind_mw = 30000 * wind_cf

    renew = pd.DataFrame({
        "datetime": hours,
        "wind_mw": wind_mw.round(0),
        "solar_mw": solar_mw.round(0),
    })
    for month in [1, 2]:
        out = raw_dir / "renewable_output" / f"renewable_2026{month:02d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        renew[renew["datetime"].dt.month == month].to_csv(
            out, index=False, encoding="utf-8-sig"
        )
        created_files.append(out)

    # ═══ 5. 碳排放权价格 ═══ (日频)
    carbon_walk = np.cumsum(np.random.normal(0.02, 0.4, nd))
    carbon_cny = 85 + carbon_walk  # 全国碳市场约 80-100 CNY/ton
    eu_ets = 65 + np.cumsum(np.random.normal(0.01, 0.3, nd))

    carbon = pd.DataFrame({
        "datetime": days,
        "carbon_cny_ton": carbon_cny.round(2),
        "eu_ets_eur_ton": eu_ets.round(2),
    })
    for month in [1, 2]:
        out = raw_dir / "carbon_price" / f"carbon_price_2026{month:02d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        carbon[carbon["datetime"].dt.month == month].to_csv(
            out, index=False, encoding="utf-8-sig"
        )
        created_files.append(out)

    return created_files
