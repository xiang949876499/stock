"""缓存系统测试"""

import pytest
import time
from src.infra.cache import LRUCache


def test_cache_init():
    """测试缓存初始化"""
    cache = LRUCache(max_size=100, ttl=60)
    assert cache.max_size == 100
    assert cache.ttl == 60


def test_cache_set_get():
    """测试设置和获取"""
    cache = LRUCache(max_size=100, ttl=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_get_missing():
    """测试获取不存在的键"""
    cache = LRUCache(max_size=100, ttl=60)
    assert cache.get("missing") is None


def test_cache_set_overwrite():
    """测试覆盖写入"""
    cache = LRUCache(max_size=100, ttl=60)
    cache.set("key1", "value1")
    cache.set("key1", "value2")
    assert cache.get("key1") == "value2"


def test_cache_eviction():
    """测试淘汰策略"""
    cache = LRUCache(max_size=2, ttl=60)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # key1 应该被淘汰
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_cache_ttl():
    """测试过期时间"""
    cache = LRUCache(max_size=100, ttl=1)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_delete():
    """测试删除"""
    cache = LRUCache(max_size=100, ttl=60)
    cache.set("key1", "value1")
    cache.delete("key1")
    assert cache.get("key1") is None


def test_cache_clear():
    """测试清空"""
    cache = LRUCache(max_size=100, ttl=60)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None
