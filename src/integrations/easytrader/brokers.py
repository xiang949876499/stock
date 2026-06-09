"""券商配置"""

from enum import Enum


class BrokerType(str, Enum):
    """券商类型"""
    THS = "ths"          # 同花顺
    YH = "yh"            # 银河证券
    HT = "ht"            # 华泰证券
    GJ = "gj"            # 国金证券


BROKER_CONFIGS = {
    BrokerType.THS: {
        "name": "同花顺",
        "description": "同花顺客户端",
        "requires_client": True,
    },
    BrokerType.YH: {
        "name": "银河证券",
        "description": "银河双子星客户端",
        "requires_client": True,
    },
    BrokerType.HT: {
        "name": "华泰证券",
        "description": "华泰通达信客户端",
        "requires_client": True,
    },
    BrokerType.GJ: {
        "name": "国金证券",
        "description": "国金同花顺客户端",
        "requires_client": True,
    },
}


def get_broker_config(broker: str) -> dict:
    """获取券商配置"""
    return BROKER_CONFIGS.get(broker, {})
