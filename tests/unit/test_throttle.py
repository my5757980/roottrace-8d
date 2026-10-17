from app.main import LiveThrottle


def test_live_throttle_limits_per_key_and_window():
    now = [0.0]
    t = LiveThrottle(limit=2, window_s=600, clock=lambda: now[0])
    assert t.allow("a") and t.allow("a")
    assert not t.allow("a")
    assert t.allow("b")
    now[0] = 601
    assert t.allow("a")
