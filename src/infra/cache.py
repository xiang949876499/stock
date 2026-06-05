"""缓存系统"""

from collections import OrderedDict
from typing import Any, Optional
import time


class LRUCache:
    """LRU 缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """初始化缓存"""
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None

        # 检查是否过期
        if self._is_expired(key):
            self.delete(key)
            return None

        # 移到末尾（最近使用）
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: Any):
        """设置缓存"""
        if key in self._cache:
            # 覆盖写入
            self._cache.move_to_end(key)
        elif len(self._cache) >= self.max_size:
            # 淘汰最久未使用的
            self._cache.popitem(last=False)

        self._cache[key] = value
        self._timestamps[key] = time.time()

    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()

    def _is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self.ttl
