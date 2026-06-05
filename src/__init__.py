"""Stock Hub - 量化交易一体化平台"""

__version__ = "0.1.0"

from .config import Settings, get_settings
from .infra import (
    EventBus,
    EventType,
    Event,
    setup_logger,
    get_logger,
    TaskScheduler,
    LRUCache,
    Database,
)
from .data import (
    Market,
    StockDaily,
    StockInfo,
    FinancialData,
    NewsItem,
    TechnicalIndicators,
    DataProvider,
    AkShareProvider,
    InstrumentCatalog,
    ParquetStorage,
    DataService,
)
from .research import (
    Factor,
    FactorRegistry,
    create_default_registry,
    SignalGenerator,
    Signal,
    SignalStatus,
    SignalSource,
    ResearchService,
)
from .execution import (
    SignalBridge,
    OrderPlan,
    RiskManager,
    RiskConfig,
    RiskCheckResult,
    PositionManager,
    CNRules,
    SecurityPolicy,
    KillSwitch,
    ExecutionService,
)
from .analysis import (
    AIModelAdapter,
    AnalysisResult,
    AIModelFactory,
    AnalysisStrategy,
    STRATEGIES,
    BasePusher,
    NotificationManager,
    StockAgent,
    AnalysisService,
)
from .news import (
    NewsCollector,
    EastMoneyCollector,
    deduplicate_news,
    analyze_sentiment,
    NewsAnalyzer,
    NewsService,
)
from .web import (
    router,
    WebSocketManager,
)
from .contracts import (
    SignalV1,
    AgentTool,
    AGENT_TOOLS,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Infra
    "EventBus",
    "EventType",
    "Event",
    "setup_logger",
    "get_logger",
    "TaskScheduler",
    "LRUCache",
    "Database",
    # Data
    "Market",
    "StockDaily",
    "StockInfo",
    "FinancialData",
    "NewsItem",
    "TechnicalIndicators",
    "DataProvider",
    "AkShareProvider",
    "InstrumentCatalog",
    "ParquetStorage",
    "DataService",
    # Research
    "Factor",
    "FactorRegistry",
    "create_default_registry",
    "SignalGenerator",
    "Signal",
    "SignalStatus",
    "SignalSource",
    "ResearchService",
    # Execution
    "SignalBridge",
    "OrderPlan",
    "RiskManager",
    "RiskConfig",
    "RiskCheckResult",
    "PositionManager",
    "CNRules",
    "SecurityPolicy",
    "KillSwitch",
    "ExecutionService",
    # Analysis
    "AIModelAdapter",
    "AnalysisResult",
    "AIModelFactory",
    "AnalysisStrategy",
    "STRATEGIES",
    "BasePusher",
    "NotificationManager",
    "StockAgent",
    "AnalysisService",
    # News
    "NewsCollector",
    "EastMoneyCollector",
    "deduplicate_news",
    "analyze_sentiment",
    "NewsAnalyzer",
    "NewsService",
    # Web
    "router",
    "WebSocketManager",
    # Contracts
    "SignalV1",
    "AgentTool",
    "AGENT_TOOLS",
]
