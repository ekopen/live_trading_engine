import config

def test_basic_config_sanity():
    assert isinstance(config.SYMBOL, str) and ":" in config.SYMBOL
    assert isinstance(config.DATA_DURATION, (int, float)) and config.DATA_DURATION > 0
    assert isinstance(config.HEARTBEAT_FREQUENCY, (int, float)) and config.HEARTBEAT_FREQUENCY > 0
    assert isinstance(config.EMPTY_LIMIT, int) and config.EMPTY_LIMIT >= 1
    assert config.WS_LAG_THRESHOLD > 0
    assert config.PROC_LAG_THRESHOLD > 0
