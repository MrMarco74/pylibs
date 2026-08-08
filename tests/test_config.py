import os

from pylibs.config import Config, ensure_secrets_file, load_config, load_secrets, save_config
from pylibs.config.secrets import scan_for_leaked_secrets


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "missing.yaml", defaults={"a": 1})
    assert cfg.get("a") == 1


def test_save_and_load_roundtrip_yaml(tmp_path):
    path = tmp_path / "cfg.yaml"
    save_config(path, {"upload": {"ssh": {"host": "example.com"}}})

    cfg = load_config(path)
    assert cfg.get("upload.ssh.host") == "example.com"
    assert (path.stat().st_mode & 0o777) == 0o600


def test_save_and_load_roundtrip_json(tmp_path):
    path = tmp_path / "cfg.json"
    save_config(path, {"a": {"b": 2}})

    cfg = load_config(path)
    assert cfg.get("a.b") == 2


def test_dot_notation_set_and_get():
    cfg = Config()
    cfg.set("a.b.c", 42)
    assert cfg.get("a.b.c") == 42
    assert cfg.get("a.b.missing", "fallback") == "fallback"


def test_env_var_interpolation(tmp_path, monkeypatch):
    monkeypatch.setenv("PYLIBS_TEST_HOST", "example-host")
    path = tmp_path / "cfg.yaml"
    save_config(path, {"host": "${PYLIBS_TEST_HOST}"})

    cfg = load_config(path)
    assert cfg.get("host") == "example-host"


def test_load_secrets_from_file(tmp_path):
    secrets_file = tmp_path / "secrets.yaml"
    ensure_secrets_file(secrets_file)
    save_config(secrets_file, {"hetzner": {"ftp_password": "hunter2"}})

    secrets = load_secrets("hetzner", search_paths=[secrets_file])
    assert secrets["ftp_password"] == "hunter2"


def test_load_secrets_env_override(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.yaml"
    save_config(secrets_file, {"hetzner": {"ftp_password": "from_file"}})
    monkeypatch.setenv("PYLIBS_SECRET_HETZNER_FTP_PASSWORD", "from_env")

    secrets = load_secrets("hetzner", search_paths=[secrets_file])
    assert secrets["ftp_password"] == "from_env"


def test_ensure_secrets_file_fixes_permissions(tmp_path):
    path = tmp_path / "secrets.yaml"
    path.write_text("{}\n")
    os.chmod(path, 0o644)

    ensure_secrets_file(path)
    assert (path.stat().st_mode & 0o777) == 0o600


def test_scan_for_leaked_secrets_finds_hardcoded_password(tmp_path):
    leaky_file = tmp_path / "config.py"
    leaky_file.write_text('DEFAULT_CONFIG = {"ftp": {"password": "bfHD8HTMt3xtr6Pg"}}\n')

    findings = scan_for_leaked_secrets(tmp_path)
    assert any(f[0] == leaky_file for f in findings)


def test_scan_for_leaked_secrets_ignores_short_placeholder(tmp_path):
    clean_file = tmp_path / "config.py"
    clean_file.write_text('password = ""\n')

    findings = scan_for_leaked_secrets(tmp_path)
    assert findings == []
