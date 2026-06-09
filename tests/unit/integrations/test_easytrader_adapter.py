import pytest
from unittest.mock import Mock, patch, MagicMock
from src.integrations.easytrader.adapter import EasytraderAdapter, TradeResult
from src.integrations.easytrader.brokers import BrokerType, BROKER_CONFIGS, get_broker_config


@pytest.fixture
def adapter():
    return EasytraderAdapter(broker="ths")


# --- 适配器创建 ---

def test_adapter_creation(adapter):
    """测试适配器创建"""
    assert adapter.name == "easytrader"
    assert adapter.broker == "ths"
    assert adapter.connected is False


def test_adapter_creation_default_broker():
    """测试默认券商"""
    adapter = EasytraderAdapter()
    assert adapter.broker == "ths"


def test_adapter_is_available(adapter):
    """测试适配器可用"""
    assert adapter.is_available() is True


# --- 券商列表 ---

def test_adapter_list_brokers(adapter):
    """测试列出支持的券商"""
    brokers = adapter.list_brokers()
    assert "ths" in brokers
    assert "yh" in brokers
    assert "ht" in brokers
    assert "gj" in brokers
    assert len(brokers) == 4


# --- 券商配置 ---

def test_broker_type_enum():
    """测试券商类型枚举"""
    assert BrokerType.THS == "ths"
    assert BrokerType.YH == "yh"
    assert BrokerType.HT == "ht"
    assert BrokerType.GJ == "gj"


def test_broker_configs():
    """测试券商配置"""
    assert "ths" in BROKER_CONFIGS
    assert BROKER_CONFIGS[BrokerType.THS]["name"] == "同花顺"
    assert BROKER_CONFIGS[BrokerType.YH]["name"] == "银河证券"
    assert BROKER_CONFIGS[BrokerType.HT]["name"] == "华泰证券"
    assert BROKER_CONFIGS[BrokerType.GJ]["name"] == "国金证券"


def test_get_broker_config():
    """测试获取券商配置"""
    config = get_broker_config("ths")
    assert config["name"] == "同花顺"
    assert config["requires_client"] is True


def test_get_broker_config_unknown():
    """测试获取未知券商配置"""
    config = get_broker_config("unknown")
    assert config == {}


# --- 初始化 ---

@pytest.mark.asyncio
async def test_initialize_without_easytrader(adapter):
    """测试未安装 easytrader 时初始化失败"""
    with patch.dict('sys.modules', {'easytrader': None}):
        result = await adapter.initialize()
        assert result is False


@pytest.mark.asyncio
async def test_initialize_with_easytrader(adapter):
    """测试安装 easytrader 后初始化成功"""
    mock_easytrader = MagicMock()
    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        result = await adapter.initialize()
        assert result is True


# --- 健康检查 ---

@pytest.mark.asyncio
async def test_health_check_not_connected(adapter):
    """测试未连接时健康检查"""
    mock_easytrader = MagicMock()
    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        result = await adapter.health_check()
        assert result is False


@pytest.mark.asyncio
async def test_health_check_connected(adapter):
    """测试已连接时健康检查"""
    mock_easytrader = MagicMock()
    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        adapter.connected = True
        result = await adapter.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_no_easytrader(adapter):
    """测试未安装 easytrader 时健康检查"""
    with patch.dict('sys.modules', {'easytrader': None}):
        result = await adapter.health_check()
        assert result is False


# --- 连接 ---

@pytest.mark.asyncio
async def test_connect_success(adapter):
    """测试连接成功"""
    mock_trader = MagicMock()
    mock_easytrader = MagicMock()
    mock_easytrader.use.return_value = mock_trader

    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        result = await adapter.connect()

    assert result.success is True
    assert result.message == "连接成功"
    assert adapter.connected is True
    mock_easytrader.use.assert_called_once_with("ths")


@pytest.mark.asyncio
async def test_connect_with_account(adapter):
    """测试带账户文件连接"""
    mock_trader = MagicMock()
    mock_easytrader = MagicMock()
    mock_easytrader.use.return_value = mock_trader

    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        result = await adapter.connect(account_path="/path/to/account.json")

    assert result.success is True
    mock_trader.prepare.assert_called_once_with("/path/to/account.json")


@pytest.mark.asyncio
async def test_connect_failure(adapter):
    """测试连接失败"""
    mock_easytrader = MagicMock()
    mock_easytrader.use.side_effect = Exception("连接超时")

    with patch.dict('sys.modules', {'easytrader': mock_easytrader}):
        result = await adapter.connect()

    assert result.success is False
    assert "连接超时" in result.message
    assert adapter.connected is False


# --- 断开连接 ---

@pytest.mark.asyncio
async def test_disconnect(adapter):
    """测试断开连接"""
    adapter.connected = True
    adapter.trader = MagicMock()

    result = await adapter.disconnect()

    assert result.success is True
    assert result.message == "已断开"
    assert adapter.connected is False
    assert adapter.trader is None


# --- 买入 ---

@pytest.mark.asyncio
async def test_buy_success(adapter):
    """测试买入成功"""
    mock_trader = MagicMock()
    mock_trader.buy.return_value = {"entrust_no": "12345"}
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.buy("000001", price=10.5, amount=100)

    assert result.success is True
    assert result.order_id == "12345"
    assert result.message == "买入成功"
    mock_trader.buy.assert_called_once_with("000001", price=10.5, amount=100)


@pytest.mark.asyncio
async def test_buy_not_connected(adapter):
    """测试未连接时买入"""
    result = await adapter.buy("000001", price=10.5, amount=100)

    assert result.success is False
    assert result.message == "未连接券商"


@pytest.mark.asyncio
async def test_buy_failure(adapter):
    """测试买入失败"""
    mock_trader = MagicMock()
    mock_trader.buy.side_effect = Exception("余额不足")
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.buy("000001", price=10.5, amount=100)

    assert result.success is False
    assert "余额不足" in result.message


# --- 卖出 ---

@pytest.mark.asyncio
async def test_sell_success(adapter):
    """测试卖出成功"""
    mock_trader = MagicMock()
    mock_trader.sell.return_value = {"entrust_no": "67890"}
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.sell("000001", price=11.0, amount=100)

    assert result.success is True
    assert result.order_id == "67890"
    assert result.message == "卖出成功"
    mock_trader.sell.assert_called_once_with("000001", price=11.0, amount=100)


@pytest.mark.asyncio
async def test_sell_not_connected(adapter):
    """测试未连接时卖出"""
    result = await adapter.sell("000001", price=11.0, amount=100)

    assert result.success is False
    assert result.message == "未连接券商"


@pytest.mark.asyncio
async def test_sell_failure(adapter):
    """测试卖出失败"""
    mock_trader = MagicMock()
    mock_trader.sell.side_effect = Exception("持仓不足")
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.sell("000001", price=11.0, amount=100)

    assert result.success is False
    assert "持仓不足" in result.message


# --- 查询资金 ---

@pytest.mark.asyncio
async def test_get_balance(adapter):
    """测试查询资金"""
    mock_trader = MagicMock()
    mock_trader.balance = {"available": 100000.0, "frozen": 5000.0}
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.get_balance()

    assert result == {"available": 100000.0, "frozen": 5000.0}


@pytest.mark.asyncio
async def test_get_balance_not_connected(adapter):
    """测试未连接时查询资金"""
    result = await adapter.get_balance()
    assert result == {}


@pytest.mark.asyncio
async def test_get_balance_failure(adapter):
    """测试查询资金失败"""
    mock_trader = MagicMock()
    type(mock_trader).balance = property(lambda self: (_ for _ in ()).throw(Exception("查询失败")))
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.get_balance()
    assert result == {}


# --- 查询持仓 ---

@pytest.mark.asyncio
async def test_get_positions(adapter):
    """测试查询持仓"""
    mock_trader = MagicMock()
    mock_trader.position = [{"symbol": "000001", "amount": 100}]
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.get_positions()

    assert len(result) == 1
    assert result[0]["symbol"] == "000001"


@pytest.mark.asyncio
async def test_get_positions_not_connected(adapter):
    """测试未连接时查询持仓"""
    result = await adapter.get_positions()
    assert result == []


@pytest.mark.asyncio
async def test_get_positions_failure(adapter):
    """测试查询持仓失败"""
    mock_trader = MagicMock()
    type(mock_trader).position = property(lambda self: (_ for _ in ()).throw(Exception("查询失败")))
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.get_positions()
    assert result == []


# --- 撤单 ---

@pytest.mark.asyncio
async def test_cancel_order_success(adapter):
    """测试撤单成功"""
    mock_trader = MagicMock()
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.cancel_order("12345")

    assert result.success is True
    assert result.message == "撤单成功"
    mock_trader.cancel_entrust.assert_called_once_with("12345")


@pytest.mark.asyncio
async def test_cancel_order_not_connected(adapter):
    """测试未连接时撤单"""
    result = await adapter.cancel_order("12345")

    assert result.success is False
    assert result.message == "未连接券商"


@pytest.mark.asyncio
async def test_cancel_order_failure(adapter):
    """测试撤单失败"""
    mock_trader = MagicMock()
    mock_trader.cancel_entrust.side_effect = Exception("撤单失败")
    adapter.trader = mock_trader
    adapter.connected = True

    result = await adapter.cancel_order("12345")

    assert result.success is False
    assert "撤单失败" in result.message


# --- TradeResult ---

def test_trade_result_success():
    """测试交易结果 - 成功"""
    result = TradeResult(success=True, order_id="123", message="ok", data={"key": "val"})
    assert result.success is True
    assert result.order_id == "123"
    assert result.message == "ok"
    assert result.data == {"key": "val"}


def test_trade_result_failure():
    """测试交易结果 - 失败"""
    result = TradeResult(success=False, message="error")
    assert result.success is False
    assert result.order_id is None
    assert result.data is None


def test_trade_result_defaults():
    """测试交易结果 - 默认值"""
    result = TradeResult(success=True)
    assert result.success is True
    assert result.order_id is None
    assert result.message == ""
    assert result.data is None


# --- 不同券商 ---

def test_adapter_different_brokers():
    """测试不同券商创建"""
    for broker in ["ths", "yh", "ht", "gj"]:
        adapter = EasytraderAdapter(broker=broker)
        assert adapter.broker == broker
        assert adapter.name == "easytrader"
