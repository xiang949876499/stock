"""SimulatedGateway tests"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from src.execution.gateways.base import Order, Account, Position
from src.execution.gateways.simulated import SimulatedGateway, COMMISSION_RATE
from src.infra.database import Database


@pytest.fixture
def db(tmp_path):
    """Create an in-memory-like Database for testing."""
    db = Database(db_path=str(tmp_path / "test_sim.db"))
    db.connect()
    db.init_sim_tables()
    return db


@pytest.fixture
def gateway(db):
    """Create a SimulatedGateway instance."""
    return SimulatedGateway(db=db)


@pytest.mark.asyncio
async def test_connect_creates_account(gateway, db):
    """connect() should create a sim account with 100万 initial capital."""
    result = await gateway.connect({})
    assert result is True

    # Verify account was created in DB
    rows = db.execute(
        "SELECT * FROM sim_accounts WHERE account_id = ?", ("sim_001",)
    ).fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert row["account_id"] == "sim_001"
    assert row["initial_capital"] == 1_000_000.0
    assert row["balance"] == 1_000_000.0
    assert row["frozen"] == 0.0


@pytest.mark.asyncio
async def test_connect_idempotent(gateway, db):
    """connect() called twice should not overwrite existing account."""
    await gateway.connect({})
    # Change balance to simulate trading
    db.execute(
        "UPDATE sim_accounts SET balance = 500000 WHERE account_id = ?",
        ("sim_001",),
    )
    db.commit()

    await gateway.connect({})

    rows = db.execute(
        "SELECT balance FROM sim_accounts WHERE account_id = ?", ("sim_001",)
    ).fetchall()
    assert rows[0]["balance"] == 500_000.0  # unchanged


@pytest.mark.asyncio
async def test_get_account(gateway, db):
    """get_account() should return Account from DB."""
    await gateway.connect({})

    account = await gateway.get_account()
    assert isinstance(account, Account)
    assert account.account_id == "sim_001"
    assert account.balance == 1_000_000.0
    assert account.available == 1_000_000.0
    assert account.frozen == 0.0


@pytest.mark.asyncio
async def test_get_account_before_connect(gateway):
    """get_account() before connect should raise."""
    with pytest.raises(ValueError, match="账户不存在"):
        await gateway.get_account()


@pytest.mark.asyncio
@patch("src.execution.gateways.simulated.get_current_price", return_value=10.0)
async def test_buy_order_deducts_balance_and_creates_position(mock_price, gateway, db):
    """A buy (OPEN) order should deduct balance and create a position."""
    await gateway.connect({})

    order = Order(
        vt_symbol="600519.SH",
        direction="LONG",
        offset="OPEN",
        price=10.0,
        volume=100,
    )

    trade_id = await gateway.send_order(order)
    assert isinstance(trade_id, str)
    assert trade_id.startswith("SIM-")

    # Check balance: 1,000,000 - (10 * 100) - commission
    amount = 10.0 * 100
    commission = amount * COMMISSION_RATE
    expected_balance = 1_000_000.0 - amount - commission

    account = await gateway.get_account()
    assert abs(account.balance - expected_balance) < 0.01

    # Check position created
    positions = await gateway.get_positions()
    assert len(positions) == 1
    pos = positions[0]
    assert pos.vt_symbol == "600519.SH"
    assert pos.volume == 100
    assert abs(pos.price - 10.0) < 0.01

    # Check trade recorded
    trades = db.execute(
        "SELECT * FROM sim_trades WHERE account_id = ?", ("sim_001",)
    ).fetchall()
    assert len(trades) == 1
    assert trades[0]["symbol"] == "600519.SH"
    assert trades[0]["side"] == "BUY"
    assert trades[0]["volume"] == 100


@pytest.mark.asyncio
@patch("src.execution.gateways.simulated.get_current_price", return_value=10.0)
async def test_buy_order_insufficient_funds(mock_price, gateway, db):
    """Buying more than available balance should raise ValueError."""
    await gateway.connect({})

    # Try to buy way more than we can afford
    order = Order(
        vt_symbol="600519.SH",
        direction="LONG",
        offset="OPEN",
        price=10.0,
        volume=200_000,  # 2M > 1M balance
    )

    with pytest.raises(ValueError, match="资金不足"):
        await gateway.send_order(order)


@pytest.mark.asyncio
@patch("src.execution.gateways.simulated.get_current_price", return_value=15.0)
async def test_sell_order_adds_balance_and_removes_position(mock_price, gateway, db):
    """A sell (CLOSE) order should add balance and reduce/remove position."""
    await gateway.connect({})

    # First buy
    buy_order = Order(
        vt_symbol="600519.SH",
        direction="LONG",
        offset="OPEN",
        price=10.0,
        volume=100,
    )
    await gateway.send_order(buy_order)

    # Then sell all
    sell_order = Order(
        vt_symbol="600519.SH",
        direction="SHORT",
        offset="CLOSE",
        price=15.0,
        volume=100,
    )
    await gateway.send_order(sell_order)

    # Position should be removed
    positions = await gateway.get_positions()
    assert len(positions) == 0

    # Check balance: initial - buy_cost - buy_commission + sell_proceeds - sell_commission
    buy_amount = 10.0 * 100
    buy_commission = buy_amount * COMMISSION_RATE
    sell_amount = 15.0 * 100
    sell_commission = sell_amount * COMMISSION_RATE
    expected = 1_000_000.0 - buy_amount - buy_commission + sell_amount - sell_commission

    account = await gateway.get_account()
    assert abs(account.balance - expected) < 0.01

    # Two trades recorded
    trades = db.execute(
        "SELECT * FROM sim_trades WHERE account_id = ?", ("sim_001",)
    ).fetchall()
    assert len(trades) == 2


@pytest.mark.asyncio
@patch("src.execution.gateways.simulated.get_current_price", return_value=10.0)
async def test_sell_partial_position(mock_price, gateway, db):
    """Selling part of a position should reduce volume and keep the rest."""
    await gateway.connect({})

    # Buy 200 shares
    buy_order = Order(
        vt_symbol="600519.SH",
        direction="LONG",
        offset="OPEN",
        price=10.0,
        volume=200,
    )
    await gateway.send_order(buy_order)

    # Sell 100 shares
    sell_order = Order(
        vt_symbol="600519.SH",
        direction="SHORT",
        offset="CLOSE",
        price=10.0,
        volume=100,
    )
    await gateway.send_order(sell_order)

    # Position should have 100 remaining
    positions = await gateway.get_positions()
    assert len(positions) == 1
    assert positions[0].volume == 100


@pytest.mark.asyncio
async def test_sell_insufficient_volume(gateway, db):
    """Selling more shares than held should raise ValueError."""
    await gateway.connect({})

    order = Order(
        vt_symbol="600519.SH",
        direction="SHORT",
        offset="CLOSE",
        price=10.0,
        volume=100,
    )

    with pytest.raises(ValueError, match="持仓不足"):
        await gateway.send_order(order)


@pytest.mark.asyncio
async def test_disconnect_is_noop(gateway):
    """disconnect() should not raise."""
    await gateway.disconnect()  # should not error


@pytest.mark.asyncio
async def test_cancel_order_logs_warning(gateway):
    """cancel_order() should not raise (no-op)."""
    # cancel_order is a no-op that logs a warning; just verify no exception
    await gateway.cancel_order("SIM-xxx")


@pytest.mark.asyncio
async def test_get_positions_empty(gateway, db):
    """get_positions() with no positions should return empty list."""
    await gateway.connect({})
    positions = await gateway.get_positions()
    assert positions == []


@pytest.mark.asyncio
@patch("src.execution.gateways.simulated.get_current_price", return_value=10.0)
async def test_multiple_symbols(mock_price, gateway, db):
    """Buying different symbols should create separate positions."""
    await gateway.connect({})

    order1 = Order(vt_symbol="600519.SH", direction="LONG", offset="OPEN", price=10.0, volume=100)
    order2 = Order(vt_symbol="000001.SZ", direction="LONG", offset="OPEN", price=20.0, volume=50)

    await gateway.send_order(order1)
    await gateway.send_order(order2)

    positions = await gateway.get_positions()
    assert len(positions) == 2
    symbols = {p.vt_symbol for p in positions}
    assert symbols == {"600519.SH", "000001.SZ"}
