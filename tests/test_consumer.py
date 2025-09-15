import datetime as dt
from kafka_consumer import validate_and_parse

def test_validate_and_parse_minimal():
    sample = {
        "timestamp": "2025-01-01T12:00:00+00:00",
        "timestamp_ms": 1735732800000,
        "symbol": "ETHUSDT",
        "price": 3500.5,
        "volume": 2.75,
        "received_at": "2025-01-01T12:00:01+00:00",
    }
    row = validate_and_parse(sample)

    # basic shape & types only
    assert isinstance(row, tuple)
    assert len(row) == 6
    assert isinstance(row[0], dt.datetime) and row[0].tzinfo is not None  # timestamp
    assert isinstance(row[1], int)                                        # timestamp_ms
    assert isinstance(row[2], str) and row[2] == "ETHUSDT"                # symbol
    assert isinstance(row[3], float)                                      # price
    assert isinstance(row[4], float)                                      # volume
    assert isinstance(row[5], dt.datetime) and row[5].tzinfo is not None  # received_at
