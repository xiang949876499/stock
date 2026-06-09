import backtrader as bt
from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.backtrader.data_feed import DataFrameDataFeed, create_data_feed_from_service
from src.integrations.backtrader.strategies import get_strategy_class, list_strategies
from src.infra.logger import get_logger

logger = get_logger("backtrader_adapter")


@dataclass
class BacktestResult:
    """回测结果"""
    backtest_id: str
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: list[dict]
    equity_curve: list[dict]


class BacktraderAdapter(BaseAdapter):
    """Backtrader 回测引擎适配器"""

    def __init__(self, enabled: bool = True):
        super().__init__(name="backtrader", enabled=enabled)

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import backtrader
            self.logger.info(f"Backtrader 初始化成功，版本: {backtrader.__version__}")
            return True
        except ImportError as e:
            self.logger.error(f"Backtrader 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import backtrader
            return True
        except ImportError:
            return False

    def list_strategies(self) -> list[str]:
        """列出可用策略"""
        return list_strategies()

    async def run_backtest(
        self,
        backtest_id: str,
        strategy_name: str,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        params: Optional[dict] = None,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            backtest_id: 回测 ID
            strategy_name: 策略名称
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            params: 策略参数

        Returns:
            BacktestResult: 回测结果
        """
        self.logger.info(f"开始回测: {backtest_id}, 策略: {strategy_name}")

        # 获取策略类
        strategy_class = get_strategy_class(strategy_name)
        if strategy_class is None:
            raise ValueError(f"未知策略: {strategy_name}")

        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(initial_capital)
        cerebro.broker.setcommission(commission=0.001)

        # 添加数据源
        data_count = 0
        for symbol in symbols:
            feed = create_data_feed_from_service(symbol, start_date, end_date)
            if feed is not None:
                cerebro.adddata(feed, name=symbol)
                data_count += 1
                self.logger.info(f"添加数据源: {symbol}")
            else:
                self.logger.warning(f"无法获取数据: {symbol}")

        # 检查是否有数据
        if data_count == 0:
            self.logger.error("没有可用的数据源")
            return BacktestResult(
                backtest_id=backtest_id,
                strategy_name=strategy_name,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_value=initial_capital,
                total_return=0.0,
                annual_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                trades=[],
                equity_curve=[],
            )

        # 添加策略
        if params:
            cerebro.addstrategy(strategy_class, **params)
        else:
            cerebro.addstrategy(strategy_class)

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 运行回测
        results = cerebro.run()
        strat = results[0]

        # 获取结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_capital) / initial_capital

        # 获取分析结果
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        # 构建结果
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=total_return,  # 简化处理
            max_drawdown=drawdown.get('max', {}).get('drawdown', 0),
            sharpe_ratio=sharpe.get('sharperatio', 0) or 0,
            trades=[],
            equity_curve=[],
        )

        self.logger.info(f"回测完成: 收益率={total_return:.2%}, 最大回撤={result.max_drawdown:.2%}")
        return result
