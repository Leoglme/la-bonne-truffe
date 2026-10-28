"""SystemCurlTransport: the curl command, the headers it reads back, and its failures, with curl faked."""

import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest

from services.collectors.centrale_canine import SCC_BROWSER_USER_AGENT, CentraleCanineCollector, CentraleCanineError
from services.collectors.system_curl_transport import SystemCurlTransport

URL = "https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker-spaniel-anglais/chiots-de-la-race/0"


def fake_curl(monkeypatch: pytest.MonkeyPatch, dumped_headers: str, body: bytes, exit_code: int = 0) -> list[list[str]]:
    """
    Replace the run of curl: write the headers where curl would, print the body.

    Args:
        monkeypatch: Pytest patcher.
        dumped_headers: What curl writes with ``--dump-header``.
        body: What curl prints.
        exit_code: Exit code of curl.

    Returns:
        The commands run, filled as the test goes.
    """
    commands: list[list[str]] = []

    def run(command: list[str], **_options: Any) -> subprocess.CompletedProcess[bytes]:
        """Behave like curl."""
        commands.append(command)
        Path(command[command.index("--dump-header") + 1]).write_text(dumped_headers, encoding="iso-8859-1")
        return subprocess.CompletedProcess(command, exit_code, stdout=body, stderr=b"curl: (6) Could not resolve host")

    monkeypatch.setattr(subprocess, "run", run)
    return commands


def test_request_is_sent_with_its_own_headers_only(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = fake_curl(monkeypatch, "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n", b'{"litters": {}}')
    client = httpx.Client(transport=SystemCurlTransport(curl_path="curl"))

    response = client.get(URL, params={"department": "t_41"}, headers={"User-Agent": SCC_BROWSER_USER_AGENT})

    assert response.status_code == 200
    assert response.json() == {"litters": {}}
    command = commands[0]
    headers = [command[index + 1] for index, argument in enumerate(command) if argument == "--header"]
    assert f"User-Agent: {SCC_BROWSER_USER_AGENT}" in headers
    assert not any(header.lower().startswith(("host:", "accept-encoding:", "connection:")) for header in headers)
    assert command[-1] == f"{URL}?department=t_41"


def test_status_and_headers_come_from_the_final_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_curl(
        monkeypatch,
        "HTTP/1.1 100 Continue\r\n\r\nHTTP/2 403\r\ncf-mitigated: challenge\r\ncontent-encoding: gzip\r\n\r\n",
        b"Just a moment...",
    )
    client = httpx.Client(transport=SystemCurlTransport(curl_path="curl"))

    response = client.get(URL)

    assert response.status_code == 403
    assert response.headers["cf-mitigated"] == "challenge"
    assert "content-encoding" not in response.headers
    assert response.text == "Just a moment..."


def test_curl_failure_reaches_the_collector_as_an_unreachable_source(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_curl(monkeypatch, "", b"", exit_code=6)
    collector = CentraleCanineCollector(
        http_client=httpx.Client(transport=SystemCurlTransport(curl_path="curl")), sleep=lambda _seconds: None
    )

    with pytest.raises(CentraleCanineError, match="Could not resolve host"):
        collector.fetch_first_page_of_all_departments("cocker-spaniel-anglais")


def test_curl_timeout_is_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_curl(monkeypatch, "", b"", exit_code=28)
    client = httpx.Client(transport=SystemCurlTransport(curl_path="curl"))

    with pytest.raises(httpx.ReadTimeout):
        client.get(URL)


def test_missing_curl_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    client = httpx.Client(transport=SystemCurlTransport())

    with pytest.raises(httpx.ConnectError, match="curl introuvable"):
        client.get(URL)
