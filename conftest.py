def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 5:  # no tests collected
        session.exitstatus = 0
