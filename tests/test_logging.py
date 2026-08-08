import logging

from pylibs.logging import SecurityFilter, get_logger, setup_logging


def test_security_filter_redacts_bearer_token():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="Authorization: Bearer abc123XYZ.def456", args=(), exc_info=None,
    )
    SecurityFilter().filter(record)
    assert "abc123XYZ" not in record.getMessage()
    assert "REDACTED" in record.getMessage()


def test_security_filter_redacts_password_kv():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg='connecting with password="hunter2secret"', args=(), exc_info=None,
    )
    SecurityFilter().filter(record)
    assert "hunter2secret" not in record.getMessage()


def test_security_filter_leaves_clean_messages_untouched():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="all good here", args=(), exc_info=None,
    )
    SecurityFilter().filter(record)
    assert record.getMessage() == "all good here"


def test_setup_logging_writes_to_file(tmp_path):
    logger = setup_logging("testservice", log_dir=tmp_path, console=False)
    logger.info("hello from test")

    log_file = tmp_path / "testservice.log"
    assert log_file.exists()
    assert "hello from test" in log_file.read_text()


def test_setup_logging_redacts_secrets_in_file(tmp_path):
    logger = setup_logging("testservice2", log_dir=tmp_path, console=False, redact_secrets=True)
    logger.info('token="supersecrettoken123"')

    log_file = tmp_path / "testservice2.log"
    assert "supersecrettoken123" not in log_file.read_text()


def test_get_logger_returns_named_logger():
    logger = get_logger("my.module")
    assert logger.name == "my.module"
