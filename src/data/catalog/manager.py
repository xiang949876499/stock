"""标的目录管理器"""

import time
from pathlib import Path
from typing import Optional
import json

from src.infra.logger import get_logger

logger = get_logger("catalog")


class InstrumentCatalog:
    """标的目录管理器"""

    def __init__(self, catalog_path: Optional[Path] = None):
        """初始化目录管理器"""
        self.catalog_path = catalog_path or Path("./data/catalog")
        self.mapping: dict[str, dict] = {}
        self._load_catalog()

    def _load_catalog(self):
        """加载映射表"""
        catalog_file = self.catalog_path / "instruments.json"
        if catalog_file.exists():
            with open(catalog_file, "r", encoding="utf-8") as f:
                self.mapping = json.load(f)
            logger.info(f"加载标的目录: {len(self.mapping)} 条记录")
        else:
            logger.warning(f"标的目录文件不存在: {catalog_file}")
            # 使用默认映射
            self._create_default_mapping()

    def _create_default_mapping(self):
        """创建默认映射"""
        # A股常用股票
        self.mapping = {
            "600519": {
                "vt_symbol": "600519.SSE",
                "name": "贵州茅台",
                "market": "A",
                "lot_size": 100,
            },
            "000858": {
                "vt_symbol": "000858.SZE",
                "name": "五粮液",
                "market": "A",
                "lot_size": 100,
            },
            "601318": {
                "vt_symbol": "601318.SSE",
                "name": "中国平安",
                "market": "A",
                "lot_size": 100,
            },
        }
        # 港股常用股票
        hk_stocks = {
            "00700": {
                "vt_symbol": "00700.HK",
                "name": "腾讯控股",
                "market": "HK",
                "lot_size": 100,
            },
            "09988": {
                "vt_symbol": "09988.HK",
                "name": "阿里巴巴",
                "market": "HK",
                "lot_size": 100,
            },
        }
        self.mapping.update(hk_stocks)

    def save_catalog(self):
        """保存映射表"""
        self.catalog_path.mkdir(parents=True, exist_ok=True)
        catalog_file = self.catalog_path / "instruments.json"
        with open(catalog_file, "w", encoding="utf-8") as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)
        logger.info(f"保存标的目录: {len(self.mapping)} 条记录")

    def qlib_to_vt(self, qlib_id: str) -> str:
        """qlib 代码转 vnpy vt_symbol"""
        # qlib 格式: SH600519 -> 600519.SSE
        if qlib_id.startswith("SH"):
            symbol = qlib_id[2:]
            return f"{symbol}.SSE"
        elif qlib_id.startswith("SZ"):
            symbol = qlib_id[2:]
            return f"{symbol}.SZE"
        elif qlib_id.startswith("HK"):
            symbol = qlib_id[2:]
            return f"{symbol}.HK"
        else:
            raise ValueError(f"未知 qlib 代码: {qlib_id}")

    def vt_to_qlib(self, vt_symbol: str) -> str:
        """vnpy vt_symbol 转 qlib 代码"""
        # vt_symbol 格式: 600519.SSE -> SH600519
        if ".SSE" in vt_symbol:
            symbol = vt_symbol.replace(".SSE", "")
            return f"SH{symbol}"
        elif ".SZE" in vt_symbol:
            symbol = vt_symbol.replace(".SZE", "")
            return f"SZ{symbol}"
        elif ".HK" in vt_symbol:
            symbol = vt_symbol.replace(".HK", "")
            return f"HK{symbol}"
        else:
            raise ValueError(f"未知 vt_symbol: {vt_symbol}")

    def validate_vt_symbol(self, vt_symbol: str) -> bool:
        """验证 vt_symbol 是否合法"""
        return any(
            info.get("vt_symbol") == vt_symbol
            for info in self.mapping.values()
        )

    def get_lot_size(self, vt_symbol: str) -> int:
        """获取最小交易单位"""
        for info in self.mapping.values():
            if info.get("vt_symbol") == vt_symbol:
                return info.get("lot_size", 100)
        return 100

    def get_name(self, symbol: str) -> str:
        """获取股票名称"""
        for info in self.mapping.values():
            if info.get("vt_symbol", "").startswith(symbol):
                return info.get("name", "")
        return ""

    def add_instrument(self, symbol: str, info: dict):
        """添加标的"""
        self.mapping[symbol] = info
        logger.info(f"添加标的: {symbol}")

    def remove_instrument(self, symbol: str):
        """删除标的"""
        if symbol in self.mapping:
            del self.mapping[symbol]
            logger.info(f"删除标的: {symbol}")

    def needs_refresh(self, max_age_hours: int = 24) -> bool:
        """检查目录是否需要刷新

        Args:
            max_age_hours: 最大有效时间（小时），默认 24 小时
        """
        meta_file = self.catalog_path / "catalog_meta.json"
        if not meta_file.exists():
            return True

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            last_refresh = meta.get("last_refresh", 0)
            return (time.time() - last_refresh) > max_age_hours * 3600
        except Exception:
            return True

    async def refresh_from_provider(self, provider):
        """从数据源刷新全量股票目录

        Args:
            provider: AkShareProvider 实例
        """
        logger.info("开始刷新股票目录...")

        # 获取全量股票列表
        a_stocks = await provider.fetch_stock_list_a()
        hk_stocks = await provider.fetch_stock_list_hk()

        if not a_stocks and not hk_stocks:
            logger.warning("未获取到任何股票数据，跳过刷新")
            return

        # 构建新映射，保留已有的元数据
        new_mapping = {}
        for stock in a_stocks + hk_stocks:
            symbol = stock["symbol"]
            # 保留已有的 lot_size 等元数据
            existing = self.mapping.get(symbol, {})
            new_mapping[symbol] = {
                "vt_symbol": existing.get("vt_symbol", self._make_vt_symbol(symbol, stock["market"])),
                "name": stock["name"],
                "market": stock["market"],
                "lot_size": existing.get("lot_size", 100),
            }

        self.mapping = new_mapping

        # 保存目录
        self.save_catalog()

        # 保存刷新时间元数据
        meta_file = self.catalog_path / "catalog_meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({"last_refresh": time.time(), "count": len(self.mapping)}, f)

        logger.info(f"股票目录刷新完成: {len(self.mapping)} 只股票")

    def _make_vt_symbol(self, symbol: str, market: str) -> str:
        """生成 vt_symbol"""
        if market == "A":
            if symbol.startswith("6"):
                return f"{symbol}.SSE"
            else:
                return f"{symbol}.SZE"
        elif market == "HK":
            return f"{symbol}.HK"
        else:
            return f"{symbol}.UNKNOWN"
