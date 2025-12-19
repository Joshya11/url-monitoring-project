import app
def test_check_target_localhost():
    # We can only assert function returns a dict with expected keys
    r = app.check_target('example.com', timeout=5)
    assert 'target' in r and 'status' in r and 'latency_ms' in r
