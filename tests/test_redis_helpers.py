import json
import logging

import fakeredis

from pylibs.log_viewer.redis_reader import read_redis_logs
from pylibs.logging.redis_handler import RedisLogHandler


def test_read_redis_logs_filters_by_level():
    client = fakeredis.FakeStrictRedis(decode_responses=True)
    client.rpush("logs:test", json.dumps({"ts": 1, "level": "INFO", "msg": "a"}))
    client.rpush("logs:test", json.dumps({"ts": 2, "level": "ERROR", "msg": "b"}))

    entries = read_redis_logs(client, "logs:test", level="ERROR")
    assert len(entries) == 1
    assert entries[0]["msg"] == "b"


def test_read_redis_logs_filters_by_since():
    client = fakeredis.FakeStrictRedis(decode_responses=True)
    client.rpush("logs:test", json.dumps({"ts": 100, "level": "INFO", "msg": "old"}))
    client.rpush("logs:test", json.dumps({"ts": 200, "level": "INFO", "msg": "new"}))

    entries = read_redis_logs(client, "logs:test", since=150)
    assert [e["msg"] for e in entries] == ["new"]


def test_read_redis_logs_skips_malformed_json():
    client = fakeredis.FakeStrictRedis(decode_responses=True)
    client.rpush("logs:test", "not json")
    client.rpush("logs:test", json.dumps({"ts": 1, "level": "INFO", "msg": "ok"}))

    entries = read_redis_logs(client, "logs:test")
    assert len(entries) == 1


def test_redis_log_handler_emits_and_trims():
    client = fakeredis.FakeStrictRedis(decode_responses=True)
    handler = RedisLogHandler(client, key_prefix="logs:test2", max_entries=2, ttl=60)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger("redis-handler-test")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    for i in range(3):
        logger.info(f"entry {i}")

    stored = client.lrange("logs:test2", 0, -1)
    assert len(stored) == 2  # trimmed to max_entries
    assert json.loads(stored[-1])["msg"] == "entry 2"

    logger.removeHandler(handler)
