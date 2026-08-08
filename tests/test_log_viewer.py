import threading
import time

from pylibs.log_viewer import follow_file, format_sse, sse_stream_from_iterator, tail_lines


def test_tail_lines_returns_last_n(tmp_path):
    path = tmp_path / "app.log"
    path.write_text("".join(f"line{i}\n" for i in range(10)))

    lines = tail_lines(path, n=3)
    assert [line.strip() for line in lines] == ["line7", "line8", "line9"]


def test_tail_lines_missing_file_returns_empty(tmp_path):
    assert tail_lines(tmp_path / "missing.log") == []


def test_follow_file_yields_appended_lines(tmp_path):
    path = tmp_path / "app.log"
    path.write_text("")

    stop_flag = {"stop": False}
    collected = []

    def consume():
        for line in follow_file(path, poll_interval=0.05, stop=lambda: stop_flag["stop"]):
            collected.append(line.strip())

    thread = threading.Thread(target=consume, daemon=True)
    thread.start()
    time.sleep(0.1)

    with path.open("a") as fh:
        fh.write("new entry\n")

    time.sleep(0.3)
    stop_flag["stop"] = True
    thread.join(timeout=1)

    assert "new entry" in collected


def test_format_sse_basic():
    assert format_sse("hello") == "data: hello\n\n"


def test_format_sse_with_event():
    assert format_sse("hello", event="log") == "event: log\ndata: hello\n\n"


def test_sse_stream_from_iterator():
    result = list(sse_stream_from_iterator(iter(["a\n", "b\n"])))
    assert result == ["data: a\n\n", "data: b\n\n"]
