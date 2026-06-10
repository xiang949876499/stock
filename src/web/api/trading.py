"""模拟交易 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.infra.database import Database
from src.trading.engine import SimulationEngine
from src.infra.logger import get_logger

logger = get_logger("trading_api")

router = APIRouter(prefix="/trading", tags=["trading"])

# ── 模块级引擎实例 ──────────────────────────────────────────────

_engine: Optional[SimulationEngine] = None


def get_engine() -> SimulationEngine:
    """获取或创建 SimulationEngine 实例"""
    global _engine
    if _engine is None:
        db = Database("./data/sim_trading.db")
        db.connect()
        db.init_sim_tables()
        _engine = SimulationEngine(db)
    return _engine


# ── 请求模型 ────────────────────────────────────────────────────


class ResetRequest(BaseModel):
    """重置账户请求"""
    initial_capital: float = Field(..., gt=0, description="初始资金")


# ── 账户 ────────────────────────────────────────────────────────


@router.get("/account")
async def get_account(engine: SimulationEngine = Depends(get_engine)):
    """获取模拟账户信息"""
    try:
        return engine._get_account()
    except Exception as e:
        logger.error(f"获取账户失败: {e}")
        raise HTTPException(500, f"获取账户失败: {e}")


@router.post("/account/reset")
async def reset_account(
    request: ResetRequest,
    engine: SimulationEngine = Depends(get_engine),
):
    """重置模拟账户（清空所有数据，重新创建账户）"""
    try:
        db = engine.db
        account_id = engine.account_id

        # 删除所有 5 张表的数据
        db.execute("DELETE FROM sim_accounts WHERE account_id = ?", (account_id,))
        db.execute("DELETE FROM sim_positions WHERE account_id = ?", (account_id,))
        db.execute("DELETE FROM sim_trades WHERE account_id = ?", (account_id,))
        db.execute("DELETE FROM sim_daily_reports WHERE account_id = ?", (account_id,))
        db.execute("DELETE FROM sim_analysis_logs WHERE account_id = ?", (account_id,))

        # 重新插入账户
        db.execute(
            "INSERT INTO sim_accounts (account_id, initial_capital, balance, frozen, total_assets) "
            "VALUES (?, ?, ?, ?, ?)",
            (account_id, request.initial_capital, request.initial_capital, 0.0, request.initial_capital),
        )
        db.commit()
        logger.info(f"重置模拟账户 {account_id}，初始资金 {request.initial_capital}")

        return engine._get_account()
    except Exception as e:
        logger.error(f"重置账户失败: {e}")
        raise HTTPException(500, f"重置账户失败: {e}")


# ── 持仓 ────────────────────────────────────────────────────────


@router.get("/positions")
async def get_positions(engine: SimulationEngine = Depends(get_engine)):
    """获取当前持仓"""
    try:
        return engine._get_positions()
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(500, f"获取持仓失败: {e}")


# ── 交易记录 ────────────────────────────────────────────────────


@router.get("/trades")
async def get_trades(
    date: Optional[str] = None,
    engine: SimulationEngine = Depends(get_engine),
):
    """获取交易记录（可按日期过滤）"""
    try:
        return engine._get_trades(trade_date=date)
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(500, f"获取交易记录失败: {e}")


# ── 每日报告 ────────────────────────────────────────────────────


@router.get("/reports")
async def get_reports(engine: SimulationEngine = Depends(get_engine)):
    """获取每日报告列表"""
    try:
        rows = engine.db.execute(
            "SELECT * FROM sim_daily_reports WHERE account_id = ? ORDER BY report_date DESC",
            (engine.account_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}")
        raise HTTPException(500, f"获取报告列表失败: {e}")


@router.get("/reports/{date}")
async def get_report(date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取指定日期的报告"""
    try:
        row = engine.db.execute(
            "SELECT * FROM sim_daily_reports WHERE account_id = ? AND report_date = ?",
            (engine.account_id, date),
        ).fetchone()
        if not row:
            raise HTTPException(404, f"未找到 {date} 的报告")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告失败: {e}")
        raise HTTPException(500, f"获取报告失败: {e}")


@router.get("/reports/{date}/mistakes")
async def get_mistakes(date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取指定日期的交易失误"""
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
        raise HTTPException(500, f"获取失误记录失败: {e}")


# ── 分析日志 ────────────────────────────────────────────────────


@router.get("/analysis-logs")
async def get_analysis_logs(
    date: Optional[str] = None,
    engine: SimulationEngine = Depends(get_engine),
):
    """获取分析日志（可按日期过滤）"""
    try:
        if date:
            rows = engine.db.execute(
                "SELECT * FROM sim_analysis_logs WHERE account_id = ? AND DATE(created_at) = ? ORDER BY created_at",
                (engine.account_id, date),
            ).fetchall()
        else:
            rows = engine.db.execute(
                "SELECT * FROM sim_analysis_logs WHERE account_id = ? ORDER BY created_at",
                (engine.account_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"获取分析日志失败: {e}")
        raise HTTPException(500, f"获取分析日志失败: {e}")


# ── 引擎控制 ────────────────────────────────────────────────────


@router.post("/start")
async def start_trading(engine: SimulationEngine = Depends(get_engine)):
    """启动交易"""
    try:
        engine.start()
        return {"status": "running"}
    except Exception as e:
        logger.error(f"启动交易失败: {e}")
        raise HTTPException(500, f"启动交易失败: {e}")


@router.post("/analyze")
async def run_analysis(engine: SimulationEngine = Depends(get_engine)):
    """手动触发一次分析"""
    try:
        await engine.run_analysis_cycle()
        return {"status": "completed", "message": "分析完成"}
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(500, f"分析失败: {e}")


@router.post("/stop")
async def stop_trading(engine: SimulationEngine = Depends(get_engine)):
    """停止交易"""
    try:
        engine.stop()
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"停止交易失败: {e}")
        raise HTTPException(500, f"停止交易失败: {e}")


@router.get("/status")
async def get_status(engine: SimulationEngine = Depends(get_engine)):
    """获取引擎运行状态"""
    try:
        return engine.get_status()
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(500, f"获取状态失败: {e}")
