import monitoring

def test_monitoring_functions_exist():
    assert hasattr(monitoring, "ticks_monitoring")
    assert hasattr(monitoring, "diagnostics_monitoring")
    assert callable(monitoring.ticks_monitoring)
    assert callable(monitoring.diagnostics_monitoring)
