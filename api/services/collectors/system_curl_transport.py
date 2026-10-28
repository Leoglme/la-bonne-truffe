"""
An httpx transport that sends each request through the ``curl`` command of the computer.

On Léo's Windows PC, Cloudflare accepts the system ``curl`` and refuses Python's own TLS stack with the
very same headers (docs/02-sources.md): the collectors keep their httpx code and only change transport.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

CURL_EXECUTABLE_NAME = "curl"
CURL_TIMEOUT_EXIT_CODE = 28
SECONDS_LEFT_TO_CURL_BEFORE_KILLING_IT = 5.0
SKIPPED_REQUEST_HEADERS: frozenset[str] = frozenset({"host", "accept-encoding", "connection", "content-length"})
SKIPPED_RESPONSE_HEADERS: frozenset[str] = frozenset({"content-encoding", "content-length", "transfer-encoding"})


class SystemCurlTransport(httpx.BaseTransport):
    """Runs ``curl`` once per request and turns its output into an httpx response."""

    def __init__(self, curl_path: str | None = None, timeout_in_seconds: float = 30.0) -> None:
        """
        Prepare the transport.

        Args:
            curl_path: The ``curl`` executable; the one found on the PATH otherwise.
            timeout_in_seconds: Longest time a request may take.
        """
        self.curl_path = curl_path or shutil.which(CURL_EXECUTABLE_NAME)
        self.timeout_in_seconds = timeout_in_seconds

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """
        Send one request with ``curl``.

        Args:
            request: The request built by the httpx client.

        Returns:
            The response, whatever its status.

        Raises:
            httpx.ConnectError: When ``curl`` is missing or cannot reach the server.
            httpx.ReadTimeout: When the server does not answer in time.
        """
        if self.curl_path is None:
            raise httpx.ConnectError("curl introuvable sur ce poste", request=request)
        body = request.read()
        with tempfile.TemporaryDirectory() as directory:
            header_file = Path(directory) / "headers.txt"
            command = self.build_command(self.curl_path, request, header_file, has_body=bool(body))
            try:
                completed = subprocess.run(
                    command,
                    input=body or None,
                    capture_output=True,
                    timeout=self.timeout_in_seconds + SECONDS_LEFT_TO_CURL_BEFORE_KILLING_IT,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise httpx.ReadTimeout("curl n'a pas répondu à temps", request=request) from error
            if completed.returncode == CURL_TIMEOUT_EXIT_CODE:
                raise httpx.ReadTimeout("délai dépassé", request=request)
            if completed.returncode != 0:
                reason = completed.stderr.decode("utf-8", errors="replace").strip()
                raise httpx.ConnectError(f"curl a échoué ({completed.returncode}) : {reason}", request=request)
            status_code, headers = self.parse_header_block(header_file.read_bytes().decode("iso-8859-1"))
        return httpx.Response(status_code, headers=headers, content=completed.stdout, request=request)

    def build_command(self, curl_path: str, request: httpx.Request, header_file: Path, has_body: bool) -> list[str]:
        """
        The ``curl`` command of a request: its method, its own headers and its URL, nothing more.

        Args:
            curl_path: The ``curl`` executable.
            request: The request.
            header_file: File where ``curl`` writes the response headers.
            has_body: Whether the request body is passed on the standard input.

        Returns:
            The command, one argument per item.
        """
        command = [
            curl_path,
            "--silent",
            "--show-error",
            "--max-time",
            f"{self.timeout_in_seconds:g}",
            "--dump-header",
            str(header_file),
            "--request",
            request.method,
        ]
        for raw_name, raw_value in request.headers.raw:
            name = raw_name.decode("latin-1")
            if name.lower() not in SKIPPED_REQUEST_HEADERS:
                command += ["--header", f"{name}: {raw_value.decode('latin-1')}"]
        if has_body:
            command += ["--data-binary", "@-"]
        command.append(str(request.url))
        return command

    @staticmethod
    def parse_header_block(dumped_headers: str) -> tuple[int, list[tuple[str, str]]]:
        """
        Read the status and the headers of the final response from the file ``curl --dump-header`` wrote.

        Args:
            dumped_headers: The file content, possibly with an interim block before (« 100 Continue »).

        Returns:
            The status code and the headers, without those ``curl`` already applied to the body.

        Raises:
            httpx.RemoteProtocolError: When the file holds no response.
        """
        blocks = [block for block in dumped_headers.replace("\r\n", "\n").split("\n\n") if block.strip()]
        if not blocks:
            raise httpx.RemoteProtocolError("réponse sans en-têtes")
        status_line, *header_lines = blocks[-1].strip().split("\n")
        status_parts = status_line.split()
        if len(status_parts) < 2 or not status_parts[1].isdigit():
            raise httpx.RemoteProtocolError(f"ligne de statut illisible : {status_line}")
        headers: list[tuple[str, str]] = []
        for line in header_lines:
            name, separator, value = line.partition(":")
            if separator and name.strip().lower() not in SKIPPED_RESPONSE_HEADERS:
                headers.append((name.strip(), value.strip()))
        return int(status_parts[1]), headers
