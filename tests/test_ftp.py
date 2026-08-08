import pytest

pytest.importorskip("pyftpdlib")

import threading
import time
from pathlib import Path

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from pylibs.ftp import FtpClient, FtpConfig, sync_upload


@pytest.fixture
def ftp_server(tmp_path):
    ftp_root = tmp_path / "ftproot"
    ftp_root.mkdir()

    authorizer = DummyAuthorizer()
    authorizer.add_user("testuser", "testpass", str(ftp_root), perm="elradfmwMT")

    handler = FTPHandler
    handler.authorizer = authorizer
    server = FTPServer(("127.0.0.1", 0), handler)
    port = server.socket.getsockname()[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    yield {"port": port, "root": ftp_root}

    server.close_all()


def _plain_config(port: int) -> FtpConfig:
    return FtpConfig(host="127.0.0.1", user="testuser", password="testpass", port=port, use_tls=False)


def test_upload_file(ftp_server):
    client = FtpClient(_plain_config(ftp_server["port"]))
    with client:
        local = ftp_server["root"] / ".." / "source.txt"
        local = Path(local).resolve()
        local.write_text("hello")
        client.upload_file(local, "/uploaded.txt")

    assert (ftp_server["root"] / "uploaded.txt").read_text() == "hello"


def test_ensure_dir_creates_nested_path(ftp_server):
    client = FtpClient(_plain_config(ftp_server["port"]))
    with client:
        client.ensure_dir("/a/b/c")

    assert (ftp_server["root"] / "a" / "b" / "c").is_dir()


def test_sync_upload_skips_identical_files(tmp_path, ftp_server):
    local_dir = tmp_path / "site"
    local_dir.mkdir()
    (local_dir / "index.html").write_text("hello world")

    client = FtpClient(_plain_config(ftp_server["port"]))
    with client:
        result = sync_upload(local_dir, "/site", client)
        assert "index.html" in result.uploaded

        # Second run: identical size -> skipped.
        result2 = sync_upload(local_dir, "/site", client)
        assert "index.html" in result2.skipped
        assert result2.uploaded == []


def test_sync_upload_deletes_orphans(tmp_path, ftp_server):
    local_dir = tmp_path / "site"
    local_dir.mkdir()
    (local_dir / "keep.html").write_text("keep")

    client = FtpClient(_plain_config(ftp_server["port"]))
    with client:
        sync_upload(local_dir, "/site", client)

        (local_dir / "keep.html").unlink()
        result = sync_upload(local_dir, "/site", client, delete_orphans=True)
        assert "keep.html" in result.deleted

    assert not (ftp_server["root"] / "site" / "keep.html").exists()
