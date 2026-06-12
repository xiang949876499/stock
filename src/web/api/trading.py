"""模拟交易 API"""

import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.infra.database import Database
from src.trading.engine import SimulationEngine
from src.infra.logger import get_logger

logger = get_logger("trading_api")

router = APIRouter(prefix="/trading", tags=["trading"])

# ── 全局单例 ──────────────────────────────────────────────────

_db: Optional[Database] = None
_engine: Optional[SimulationEngine] = None

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SQLITE_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?$")


def _get_db() -> Database:
    """获取全局数据库实例（单例）"""
    global _db
    if _db is None:
        _db = Database("./data/sim_trading.db")
        _db.connect()
        _db.init_sim_tables()
    return _db


def get_engine() -> SimulationEngine:
    """获取全局 SimulationEngine 实例（单例）"""
    global _engine
    if _engine is None:
        db = _get_db()
        _engine = SimulationEngine(db)
    return _engine


def _validate_date(date: str) -> str:
    """验证日期格式 YYYY-MM-DD"""
    if not _DATE_PATTERN.match(date):
        raise HTTPException(400, f"日期格式错误: {date}，应为 YYYY-MM-DD")
    return date


def _serialize_timestamps(value):
    """将 SQLite UTC 时间标记为 ISO 8601，避免浏览器按本地时间误读。"""
    if isinstance(value, dict):
        return {key: _serialize_timestamps(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_timestamps(item) for item in value]
    if isinstance(value, str) and _SQLITE_UTC_PATTERN.fullmatch(value):
        return value.replace(" ", "T", 1) + "Z"
    return value


# ── 请求模型 ────────────────────────────────────────────────────


class ResetRequest(BaseModel):
    """重置账户请求"""
    initial_capital: float = Field(..., gt=0, description="初始资金")


# ── 账户 ────────────────────────────────────────────────────────


@router.get("/account")
async def get_account(engine: SimulationEngine = Depends(get_engine)):
    """获取模拟账户信息"""
    try:
        return _serialize_timestamps(engine._get_account())
    except Exception as e:
        logger.error(f"获取账户失败: {e}")
        raise HTTPException(500, "获取账户失败")


@router.post("/account/reset")
async def reset_account(
    request: ResetRequest,
    engine: SimulationEngine = Depends(get_engine),
):
    """重置模拟账户（清空所有数据，重新创建账户）"""
    try:
        db = engine.db
        account_id = engine.account_id

        # 在单个事务中完成所有操作
        db.execute_in_transaction([
            ("DELETE FROM sim_accounts WHERE account_id = ?", (account_id,)),
            ("DELETE FROM sim_positions WHERE account_id = ?", (account_id,)),
            ("DELETE FROM sim_trades WHERE account_id = ?", (account_id,)),
            ("DELETE FROM sim_daily_reports WHERE account_id = ?", (account_id,)),
            ("DELETE FROM sim_analysis_logs WHERE account_id = ?", (account_id,)),
            (
                "INSERT INTO sim_accounts (account_id, initial_capital, balance, frozen, total_assets) VALUES (?, ?, ?, ?, ?)",
                (account_id, request.initial_capital, request.initial_capital, 0.0, request.initial_capital),
            ),
        ])
        logger.info(f"重置模拟账户 {account_id}，初始资金 {request.initial_capital}")

        return _serialize_timestamps(engine._get_account())
    except Exception as e:
        logger.error(f"重置账户失败: {e}")
        raise HTTPException(500, "重置账户失败")


# ── 持仓 ────────────────────────────────────────────────────────


@router.get("/positions")
async def get_positions(engine: SimulationEngine = Depends(get_engine)):
    """获取当前持仓"""
    try:
        return _serialize_timestamps(engine._get_positions())
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(500, "获取持仓失败")


# ── 交易记录 ────────────────────────────────────────────────────


@router.get("/trades")
async def get_trades(
    date: Optional[str] = None,
    engine: SimulationEngine = Depends(get_engine),
):
    """获取交易记录（可按日期过滤）"""
    try:
        if date:
            _validate_date(date)
        return _serialize_timestamps(engine._get_trades(trade_date=date))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(500, "获取交易记录失败")


# ── 每日报告 ────────────────────────────────────────────────────


@router.get("/reports")
async def get_reports(engine: SimulationEngine = Depends(get_engine)):
    """获取每日报告列表"""
    try:
        rows = engine.db.execute(
            "SELECT * FROM sim_daily_reports WHERE account_id = ? ORDER BY report_date DESC",
            (engine.account_id,),
        ).fetchall()
        return _serialize_timestamps([dict(r) for r in rows])
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}")
        raise HTTPException(500, "获取报告列表失败")


@router.get("/reports/{date}")
async def get_report(date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取指定日期的报告"""
    _validate_date(date)
    try:
        row = engine.db.execute(
            "SELECT * FROM sim_daily_reports WHERE account_id = ? AND report_date = ?",
            (engine.account_id, date),
        ).fetchone()
        if not row:
            raise HTTPException(404, f"未找到 {date} 的报告")
        return _serialize_timestamps(dict(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告失败: {e}")
        raise HTTPException(500, "获取报告失败")


@router.get("/reports/{date}/mistakes")
async def get_mistakes(date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取指定日期的交易失误"""
    _validate_date(date)
    try:
        row = engine.db.execute(
            "SELECT mistakes FROM sim_daily_reports WHERE account_id = ? AND report_date = ?",
            (engine.account_id, date),
        ).fetchone()
        if not row:
            raise HTTPException(404, f"未找到 {date} 的报告")
        return {"date": date, "mistakes": row["mistakes"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取失误记录失败: {e}")
        raise HTTPException(500, "获取失误记录失败")


# ── 分析日志 ────────────────────────────────────────────────────


@router.get("/analysis-logs")
async def get_analysis_logs(
    date: Optional[str] = None,
    engine: SimulationEngine = Depends(get_engine),
):
    """获取分析日志（可按日期过滤）"""
    try:
        if date:
            _validate_date(date)
            rows = engine.db.execute(
                "SELECT * FROM sim_analysis_logs WHERE account_id = ? AND DATE(created_at) = ? ORDER BY created_at",
                (engine.account_id, date),
            ).fetchall()
        else:
            rows = engine.db.execute(
                "SELECT * FROM sim_analysis_logs WHERE account_id = ? ORDER BY created_at",
                (engine.account_id,),
            ).fetchall()
        return _serialize_timestamps([dict(r) for r in rows])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析日志失败: {e}")
        raise HTTPException(500, "获取分析日志失败")


# ── 引擎控制 ────────────────────────────────────────────────────


@router.post("/start")
async def start_trading(engine: SimulationEngine = Depends(get_engine)):
    """启动交易"""
    try:
        engine.start()
        return {"status": "running"}
    except Exception as e:
        logger.error(f"启动交易失败: {e}")
        raise HTTPException(500, "启动交易失败")


@router.post("/analyze")
async def run_analysis(engine: SimulationEngine = Depends(get_engine)):
    """手动触发一次分析"""
    try:
        result = await engine.run_analysis_cycle()
        if result and result.get("status") == "skipped":
            return result
        return {"status": "completed", "message": "分析完成", **(result or {})}
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(500, "分析失败")


@router.post("/stop")
async def stop_trading(engine: SimulationEngine = Depends(get_engine)):
    """停止交易"""
    try:
        engine.stop()
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"停止交易失败: {e}")
        raise HTTPException(500, "停止交易失败")


@router.get("/status")
async def get_status(engine: SimulationEngine = Depends(get_engine)):
    """获取引擎运行状态"""
    try:
        return _serialize_timestamps(engine.get_status())
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(500, "获取状态失败")
