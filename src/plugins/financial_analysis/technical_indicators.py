"""技术指标计算模块

集成 Stock-Analysis-Skill 的核心计算逻辑：
- 多数据源降级策略（Tushare > efinance > akshare > yfinance）
- 完整技术指标计算（MA、MACD、RSI、量能、乖离率、支撑位）
- 100 分评分系统（6 维度）
- 支持 A 股、港股、美股
"""

from typing import Dict, Any, List, Optional


def calc_ma(closes: List[float], periods: List[int]) -> Dict[str, Any]:
    """计算移动平均线

    Args:
        closes: 收盘价列表（按时间正序，最早在前）
        periods: 均线周期列表，如 [5, 10, 20, 60]

    Returns:
        包含各周期均线最新值和趋势状态的字典
    """
    result: Dict[str, Any] = {}
    n = len(closes)

    for p in periods:
        key = f"ma{p}"
        if n >= p:
            ma_val = sum(closes[-p:]) / p
            result[key] = round(ma_val, 2)

            # 判断趋势：价格在均线上方为多头
            if closes[-1] > ma_val:
                result[f"{key}_trend"] = "above"
            else:
                result[f"{key}_trend"] = "below"
        else:
            result[key] = None
            result[f"{key}_trend"] = "insufficient_data"

    # 判断均线排列（多头排列 / 空头排列）
    ma_values = [result.get(f"ma{p}") for p in periods]
    valid_values = [v for v in ma_values if v is not None]
    if len(valid_values) == len(periods):
        if all(valid_values[i] >= valid_values[i + 1] for i in range(len(valid_values) - 1)):
            result["ma_arrangement"] = "bullish"  # 多头排列（短期在上）
        elif all(valid_values[i] <= valid_values[i + 1] for i in range(len(valid_values) - 1)):
            result["ma_arrangement"] = "bearish"  # 空头排列（短期在下）
        else:
            result["ma_arrangement"] = "mixed"  # 交叉排列
    else:
        result["ma_arrangement"] = "insufficient_data"

    return result


def calc_macd(
    closes: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, Any]:
    """计算 MACD 指标

    Args:
        closes: 收盘价列表（时间正序）
        fast: 快线周期（默认 12）
        slow: 慢线周期（默认 26）
        signal: 信号线周期（默认 9）

    Returns:
        包含 DIF、DEA、MACD 柱状值和金叉/死叉信号的字典
    """
    n = len(closes)
    if n < slow + signal:
        return {"error": "数据不足，需要至少 {} 个数据点".format(slow + signal)}

    # 计算 EMA
    def ema(data: List[float], period: int) -> List[float]:
        result = [data[0]]
        multiplier = 2.0 / (period + 1)
        for i in range(1, len(data)):
            val = data[i] * multiplier + result[-1] * (1 - multiplier)
            result.append(val)
        return result

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    # DIF = EMA(fast) - EMA(slow)
    dif = [ema_fast[i] - ema_slow[i] for i in range(n)]

    # DEA = EMA(DIF, signal)
    dea = ema(dif, signal)

    # MACD 柱状值 = 2 * (DIF - DEA)
    macd_hist = [2 * (dif[i] - dea[i]) for i in range(n)]

    # 最新值
    latest_dif = round(dif[-1], 4)
    latest_dea = round(dea[-1], 4)
    latest_macd = round(macd_hist[-1], 4)
    prev_dif = round(dif[-2], 4)
    prev_dea = round(dea[-2], 4)

    # 金叉/死叉判断
    cross_signal = "none"
    if prev_dif <= prev_dea and latest_dif > latest_dea:
        cross_signal = "golden_cross"  # 金叉
    elif prev_dif >= prev_dea and latest_dif < latest_dea:
        cross_signal = "death_cross"  # 死叉

    # MACD 柱状趋势
    if len(macd_hist) >= 2:
        hist_trend = "increasing" if macd_hist[-1] > macd_hist[-2] else "decreasing"
    else:
        hist_trend = "unknown"

    return {
        "dif": latest_dif,
        "dea": latest_dea,
        "macd": latest_macd,
        "cross_signal": cross_signal,
        "hist_trend": hist_trend,
        "above_zero": latest_dif > 0 and latest_dea > 0,
    }


def calc_rsi(
    closes: List[float],
    periods: Optional[List[int]] = None
) -> Dict[str, Any]:
    """计算 RSI 指标

    Args:
        closes: 收盘价列表（时间正序）
        periods: RSI 周期列表，默认 [6, 12, 24]

    Returns:
        包含各周期 RSI 值和超买/超卖状态的字典
    """
    if periods is None:
        periods = [6, 12, 24]

    result: Dict[str, Any] = {}
    n = len(closes)

    for p in periods:
        if n < p + 1:
            result[f"rsi{p}"] = None
            result[f"rsi{p}_status"] = "insufficient_data"
            continue

        # 计算涨跌幅
        gains = []
        losses = []
        for i in range(1, n):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        # 使用最近 p 个数据点计算
        recent_gains = gains[-(p):]
        recent_losses = losses[-(p):]

        avg_gain = sum(recent_gains) / p
        avg_loss = sum(recent_losses) / p

        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))

        result[f"rsi{p}"] = round(rsi_val, 2)

        # 超买/超卖判断
        if rsi_val >= 80:
            result[f"rsi{p}_status"] = "overbought"  # 超买
        elif rsi_val <= 20:
            result[f"rsi{p}_status"] = "oversold"  # 超卖
        elif rsi_val >= 70:
            result[f"rsi{p}_status"] = "near_overbought"
        elif rsi_val <= 30:
            result[f"rsi{p}_status"] = "near_oversold"
        else:
            result[f"rsi{p}_status"] = "neutral"

    return result


def calc_volume_analysis(
    volumes: List[float],
    closes: List[float]
) -> Dict[str, Any]:
    """量能分析

    Args:
        volumes: 成交量列表（时间正序）
        closes: 收盘价列表（时间正序）

    Returns:
        包含量比、量能趋势、放量/缩量状态的字典
    """
    n = len(volumes)
    if n < 10:
        return {"error": "数据不足"}

    # 最新成交量
    latest_vol = volumes[-1]

    # 5 日平均成交量
    avg_vol_5 = sum(volumes[-5:]) / 5 if n >= 5 else sum(volumes) / n

    # 10 日平均成交量
    avg_vol_10 = sum(volumes[-10:]) / 10 if n >= 10 else sum(volumes) / n

    # 量比（当日成交量 / N 日平均）
    vol_ratio_5 = latest_vol / avg_vol_5 if avg_vol_5 > 0 else 0
    vol_ratio_10 = latest_vol / avg_vol_10 if avg_vol_10 > 0 else 0

    # 量能趋势（近 5 日成交量 vs 前 5 日）
    if n >= 10:
        recent_5_avg = sum(volumes[-5:]) / 5
        prev_5_avg = sum(volumes[-10:-5]) / 5
        if prev_5_avg > 0:
            vol_change = (recent_5_avg - prev_5_avg) / prev_5_avg * 100
        else:
            vol_change = 0
    else:
        vol_change = 0

    # 量价关系判断
    if len(closes) >= 2:
        price_up = closes[-1] > closes[-2]
        vol_up = volumes[-1] > volumes[-2]
        if price_up and vol_up:
            price_vol_relation = "bullish_volume"  # 价升量增（健康上涨）
        elif price_up and not vol_up:
            price_vol_relation = "weak_rally"  # 价升量缩（上涨动力不足）
        elif not price_up and vol_up:
            price_vol_relation = "bearish_volume"  # 价跌量增（恐慌抛售）
        else:
            price_vol_relation = "shrinking_decline"  # 价跌量缩（惜售）
    else:
        price_vol_relation = "unknown"

    # 放量/缩量状态
    if vol_ratio_5 >= 2.0:
        vol_status = "heavy_volume"  # 明显放量
    elif vol_ratio_5 >= 1.5:
        vol_status = "moderate_volume"  # 温和放量
    elif vol_ratio_5 <= 0.5:
        vol_status = "heavy_shrink"  # 明显缩量
    elif vol_ratio_5 <= 0.7:
        vol_status = "moderate_shrink"  # 温和缩量
    else:
        vol_status = "normal"

    return {
        "latest_volume": latest_vol,
        "avg_volume_5": round(avg_vol_5, 0),
        "avg_volume_10": round(avg_vol_10, 0),
        "volume_ratio_5": round(vol_ratio_5, 2),
        "volume_ratio_10": round(vol_ratio_10, 2),
        "volume_change_pct": round(vol_change, 2),
        "volume_status": vol_status,
        "price_vol_relation": price_vol_relation,
    }


def calc_bias(closes: List[float], ma_data: Dict[str, Any]) -> Dict[str, Any]:
    """计算乖离率

    乖离率 = (当前价格 - 均线值) / 均线值 * 100

    Args:
        closes: 收盘价列表（时间正序）
        ma_data: calc_ma 返回的均线数据

    Returns:
        包含各周期乖离率的字典
    """
    result: Dict[str, Any] = {}
    current_price = closes[-1]

    for period in [5, 10, 20, 60]:
        ma_val = ma_data.get(f"ma{period}")
        if ma_val is not None and ma_val > 0:
            bias = (current_price - ma_val) / ma_val * 100
            result[f"bias{period}"] = round(bias, 2)

            # 乖离率状态判断
            if bias > 5:
                result[f"bias{period}_status"] = "overstretched_up"  # 过度偏离向上
            elif bias > 3:
                result[f"bias{period}_status"] = "high_positive"
            elif bias < -5:
                result[f"bias{period}_status"] = "overstretched_down"  # 过度偏离向下
            elif bias < -3:
                result[f"bias{period}_status"] = "high_negative"
            else:
                result[f"bias{period}_status"] = "normal"
        else:
            result[f"bias{period}"] = None
            result[f"bias{period}_status"] = "insufficient_data"

    return result


def calc_support(
    closes: List[float],
    ma_data: Dict[str, Any]
) -> Dict[str, Any]:
    """计算支撑位和压力位

    基于均线和近期高低点计算支撑/压力位。

    Args:
        closes: 收盘价列表（时间正序）
        ma_data: calc_ma 返回的均线数据

    Returns:
        包含支撑位和压力位的字典
    """
    current_price = closes[-1]
    n = len(closes)

    # 从均线获取支撑位（价格下方的均线）
    support_levels = []
    resistance_levels = []

    for period in [5, 10, 20, 60]:
        ma_val = ma_data.get(f"ma{period}")
        if ma_val is not None:
            if ma_val < current_price:
                support_levels.append({
                    "type": "ma",
                    "period": period,
                    "price": ma_val,
                    "distance_pct": round((current_price - ma_val) / current_price * 100, 2)
                })
            else:
                resistance_levels.append({
                    "type": "ma",
                    "period": period,
                    "price": ma_val,
                    "distance_pct": round((ma_val - current_price) / current_price * 100, 2)
                })

    # 从近期高低点获取支撑/压力位
    lookback = min(20, n)
    if lookback >= 5:
        recent_data = closes[-lookback:]
        recent_high = max(recent_data)
        recent_low = min(recent_data)

        if recent_low < current_price:
            support_levels.append({
                "type": "recent_low",
                "period": lookback,
                "price": recent_low,
                "distance_pct": round((current_price - recent_low) / current_price * 100, 2)
            })

        if recent_high > current_price:
            resistance_levels.append({
                "type": "recent_high",
                "period": lookback,
                "price": recent_high,
                "distance_pct": round((recent_high - current_price) / current_price * 100, 2)
            })

    # 按距离排序
    support_levels.sort(key=lambda x: x["distance_pct"])
    resistance_levels.sort(key=lambda x: x["distance_pct"])

    return {
        "current_price": current_price,
        "support_levels": support_levels[:3],  # 最近的 3 个支撑位
        "resistance_levels": resistance_levels[:3],  # 最近的 3 个压力位
        "nearest_support": support_levels[0]["price"] if support_levels else None,
        "nearest_resistance": resistance_levels[0]["price"] if resistance_levels else None,
    }


def calc_trend_score(
    ma_data: Dict[str, Any],
    macd_data: Dict[str, Any],
    rsi_data: Dict[str, Any],
    vol_data: Dict[str, Any],
    bias_data: Dict[str, Any],
    support_data: Dict[str, Any]
) -> Dict[str, Any]:
    """计算 100 分趋势评分系统

    6 个维度评分：
    1. 均线趋势（20 分）
    2. MACD 信号（20 分）
    3. RSI 状态（15 分）
    4. 量能分析（15 分）
    5. 乖离率（15 分）
    6. 支撑位（15 分）

    Args:
        ma_data: 均线数据
        macd_data: MACD 数据
        rsi_data: RSI 数据
        vol_data: 量能数据
        bias_data: 乖离率数据
        support_data: 支撑位数据

    Returns:
        包含总分、各维度分数和信号的字典
    """
    scores: Dict[str, float] = {}
    details: Dict[str, str] = {}

    # --- 1. 均线趋势（20 分）---
    ma_score = 10.0  # 基础分
    arrangement = ma_data.get("ma_arrangement", "unknown")
    if arrangement == "bullish":
        ma_score = 20.0
        details["ma"] = "多头排列，满分"
    elif arrangement == "bearish":
        ma_score = 0.0
        details["ma"] = "空头排列，零分"
    elif arrangement == "mixed":
        # 根据价格相对均线位置加分
        above_count = sum(1 for p in [5, 10, 20, 60]
                        if ma_data.get(f"ma{p}_trend") == "above")
        ma_score = 5 + above_count * 3.75
        details["ma"] = f"交叉排列，价格在 {above_count} 条均线上方"
    else:
        details["ma"] = "数据不足"
    scores["ma"] = round(ma_score, 1)

    # --- 2. MACD 信号（20 分）---
    macd_score = 10.0
    cross = macd_data.get("cross_signal", "none")
    dif = macd_data.get("dif", 0)
    dea = macd_data.get("dea", 0)
    macd_val = macd_data.get("macd", 0)
    hist_trend = macd_data.get("hist_trend", "unknown")

    if cross == "golden_cross":
        macd_score = 20.0
        details["macd"] = "MACD 金叉，满分"
    elif cross == "death_cross":
        macd_score = 0.0
        details["macd"] = "MACD 死叉，零分"
    else:
        if dif > 0 and dea > 0:
            macd_score = 15.0
            details["macd"] = "DIF/DEA 均在零轴上方"
        elif dif < 0 and dea < 0:
            macd_score = 5.0
            details["macd"] = "DIF/DEA 均在零轴下方"
        else:
            macd_score = 10.0
            details["macd"] = "DIF/DEA 零轴附近"

        # MACD 柱状趋势加减分
        if hist_trend == "increasing":
            macd_score = min(20, macd_score + 2)
        elif hist_trend == "decreasing":
            macd_score = max(0, macd_score - 2)

    scores["macd"] = round(macd_score, 1)

    # --- 3. RSI 状态（15 分）---
    rsi_score = 7.5
    # 取 RSI12 作为主要参考
    rsi12 = rsi_data.get("rsi12")
    rsi12_status = rsi_data.get("rsi12_status", "unknown")

    if rsi12 is not None:
        if rsi12_status in ("neutral",):
            rsi_score = 12.0
            details["rsi"] = f"RSI12={rsi12}，中性区间"
        elif rsi12_status in ("near_oversold",):
            rsi_score = 13.0
            details["rsi"] = f"RSI12={rsi12}，接近超卖（可能反弹）"
        elif rsi12_status in ("oversold",):
            rsi_score = 15.0
            details["rsi"] = f"RSI12={rsi12}，超卖（反弹概率高）"
        elif rsi12_status in ("near_overbought",):
            rsi_score = 8.0
            details["rsi"] = f"RSI12={rsi12}，接近超买"
        elif rsi12_status in ("overbought",):
            rsi_score = 3.0
            details["rsi"] = f"RSI12={rsi12}，超买（回调风险）"
        else:
            details["rsi"] = f"RSI12={rsi12}"
    else:
        details["rsi"] = "RSI 数据不足"

    scores["rsi"] = round(rsi_score, 1)

    # --- 4. 量能分析（15 分）---
    vol_score = 7.5
    vol_status = vol_data.get("volume_status", "unknown")
    price_vol = vol_data.get("price_vol_relation", "unknown")

    if "error" not in vol_data:
        if price_vol == "bullish_volume":
            vol_score = 15.0
            details["volume"] = "价升量增，健康上涨"
        elif price_vol == "shrinking_decline":
            vol_score = 12.0
            details["volume"] = "价跌量缩，惜售"
        elif price_vol == "weak_rally":
            vol_score = 5.0
            details["volume"] = "价升量缩，上涨动力不足"
        elif price_vol == "bearish_volume":
            vol_score = 2.0
            details["volume"] = "价跌量增，恐慌抛售"
        else:
            details["volume"] = f"量能状态: {vol_status}"
    else:
        details["volume"] = "量能数据不足"

    scores["volume"] = round(vol_score, 1)

    # --- 5. 乖离率（15 分）---
    bias_score = 7.5
    bias20 = bias_data.get("bias20")

    if bias20 is not None:
        if bias_data.get("bias20_status") == "overstretched_down":
            bias_score = 15.0
            details["bias"] = f"BIAS20={bias20}%，过度偏离向下（超卖反弹机会）"
        elif bias_data.get("bias20_status") == "high_negative":
            bias_score = 12.0
            details["bias"] = f"BIAS20={bias20}%，负乖离较大"
        elif bias_data.get("bias20_status") == "normal":
            bias_score = 10.0
            details["bias"] = f"BIAS20={bias20}%，正常范围"
        elif bias_data.get("bias20_status") == "high_positive":
            bias_score = 5.0
            details["bias"] = f"BIAS20={bias20}%，正乖离较大"
        elif bias_data.get("bias20_status") == "overstretched_up":
            bias_score = 2.0
            details["bias"] = f"BIAS20={bias20}%，过度偏离向上（回调风险）"
        else:
            details["bias"] = f"BIAS20={bias20}"
    else:
        details["bias"] = "乖离率数据不足"

    scores["bias"] = round(bias_score, 1)

    # --- 6. 支撑位（15 分）---
    support_score = 7.5
    current_price = support_data.get("current_price", 0)
    nearest_support = support_data.get("nearest_support")
    nearest_resistance = support_data.get("nearest_resistance")
    support_levels = support_data.get("support_levels", [])
    resistance_levels = support_data.get("resistance_levels", [])

    if nearest_support is not None and current_price > 0:
        support_dist = (current_price - nearest_support) / current_price * 100
        resistance_dist = ((nearest_resistance - current_price) / current_price * 100
                          if nearest_resistance else 100)

        # 距离支撑近、距离压力远 = 好
        if support_dist < 2 and resistance_dist > 5:
            support_score = 15.0
            details["support"] = f"接近支撑位 {nearest_support}，上方空间大"
        elif support_dist < 3:
            support_score = 12.0
            details["support"] = f"距离支撑位 {nearest_support} 较近"
        elif resistance_dist < 2:
            support_score = 3.0
            details["support"] = f"接近压力位 {nearest_resistance}，上行受阻"
        elif resistance_dist < 3:
            support_score = 6.0
            details["support"] = f"距离压力位 {nearest_resistance} 较近"
        else:
            support_score = 9.0
            details["support"] = "支撑压力适中"
    else:
        details["support"] = "支撑位数据不足"

    scores["support"] = round(support_score, 1)

    # --- 综合评分 ---
    total_score = sum(scores.values())

    # 确定信号
    if total_score >= 75:
        signal = "strong_buy"
        signal_cn = "强烈买入"
    elif total_score >= 60:
        signal = "buy"
        signal_cn = "买入"
    elif total_score >= 45:
        signal = "hold"
        signal_cn = "持有"
    elif total_score >= 30:
        signal = "sell"
        signal_cn = "卖出"
    else:
        signal = "strong_sell"
        signal_cn = "强烈卖出"

    return {
        "total_score": round(total_score, 1),
        "max_score": 100,
        "scores": scores,
        "details": details,
        "signal": signal,
        "signal_cn": signal_cn,
    }
