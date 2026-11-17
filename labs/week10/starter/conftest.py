"""Marker registration, so `-m "not judged"` works without a warning."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "judged: needs a model call. Slow, and skippable on every commit.")


def pytest_report_header(config):
    """Say on the first line of every run which traces the gates judged."""
    from loader import traces_path
    path, reference = traces_path()
    if reference:
        return ("traces: the course REFERENCE (fixtures/reference_traces.jsonl), "
                "because your artifacts/traces.jsonl is missing or empty")
    return f"traces: your own, {path}"


def pytest_terminal_summary(terminalreporter):
    """Repeat it at the end, which `pytest -q` still prints."""
    from loader import traces_path
    if traces_path()[1]:
        terminalreporter.write_line(
            "NOTE: these gates judged the course REFERENCE traces, not yours. "
            "Your artifacts/traces.jsonl is missing or empty.", yellow=True)
