"""Phoenix OpenTelemetry tracing setup — call setup_tracing() before any imports."""

from __future__ import annotations

import logging
import os
import socket

logger = logging.getLogger(__name__)


def _phoenix_reachable(host: str, timeout: float = 2.0) -> bool:
    """Quick DNS + TCP probe to check if Phoenix is reachable before registering."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False


def setup_tracing() -> None:
    """
    Configure OpenTelemetry to export traces to Phoenix.

    Must be called BEFORE importing google.adk or other instrumented libraries
    so that ADK auto-instrumentation picks up the exporter.
    """
    from dotenv import load_dotenv
    load_dotenv()

    # Silence the noisy OTLP exporter — it logs full stacktraces on every failed span
    logging.getLogger("opentelemetry.exporter.otlp.proto.http.trace_exporter").setLevel(
        logging.CRITICAL
    )
    logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.CRITICAL)

    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "")
    api_key = os.getenv("PHOENIX_API_KEY", "")

    if not endpoint:
        logger.warning(
            "PHOENIX_COLLECTOR_ENDPOINT is not set — Phoenix tracing disabled."
        )
        return

    # Extract hostname from endpoint URL for reachability check
    try:
        from urllib.parse import urlparse
        host = urlparse(endpoint).hostname or "app.phoenix.arize.com"
    except Exception:
        host = "app.phoenix.arize.com"

    if not _phoenix_reachable(host):
        logger.warning(
            "Phoenix host '%s' is not reachable (DNS/network) — tracing disabled. "
            "Traces will NOT be exported this session.",
            host,
        )
        return

    try:
        from phoenix.otel import register

        project_name = os.getenv("PHOENIX_PROJECT_NAME", "quantsentinel")
        
        # Ensure the endpoint explicitly targets the v1/traces path for OTLP exporting
        collector_url = f"{endpoint}/v1/traces" if not endpoint.endswith("/v1/traces") else endpoint
        
        # The register() function natively checks PHOENIX_API_KEY from environment variables
        # and automatically injects the correct `Authorization: Bearer <key>` headers.
        # We specify protocol="http/protobuf" to suppress the protocol inference warning.
        provider = register(
            project_name=project_name,
            endpoint=collector_url,
            protocol="http/protobuf",
        )

        # Try to instrument ADK if the package is available
        try:
            from openinference.instrumentation.google_adk import GoogleADKInstrumentor

            GoogleADKInstrumentor().instrument(tracer_provider=provider)
            logger.info("Phoenix + GoogleADKInstrumentor configured (endpoint=%s)", endpoint)
        except ImportError:
            logger.warning(
                "openinference-instrumentation-google-adk not installed — "
                "ADK spans will not be captured."
            )

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to set up Phoenix tracing: %s", exc)
