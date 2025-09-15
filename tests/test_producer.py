import kafka_producer

def test_start_producer_exists():
    assert hasattr(kafka_producer, "start_producer")
    assert callable(kafka_producer.start_producer)
