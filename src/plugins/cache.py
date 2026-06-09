"""插件缓存工具"""

import time
from typing import Dict, Any, Optional
from functools import wraps


class PluginCache:
    """插件结果缓存"""

    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["time"] < self._ttl:
                return entry["data"]
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: Any) -> None:
        """设置缓存"""
        self._cache[key] = {
            "data": data,
            "time": time.time()
        }

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


# 全局缓存实例
plugin_cache = PluginCache(ttl=300)


def cached(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试获取缓存
            result = plugin_cache.get(cache_key)
            if result is not None:
                return result

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            plugin_cache.set(cache_key, result)

            return result
        return wrapper
    return decorator
