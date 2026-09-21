import pytest
from app.config import ConfigurationError,load_settings

def test_config_validation(monkeypatch,tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("API_ID","API_HASH","BOT_TOKEN","ADMIN_TELEGRAM_ID"): monkeypatch.delenv(key,raising=False)
    with pytest.raises(ConfigurationError): load_settings()

