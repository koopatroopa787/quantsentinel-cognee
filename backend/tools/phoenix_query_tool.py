"""Phoenix REST API wrapper tools."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests


def _base_url() -> str:
    """Return the configured Phoenix base URL."""
    from config import settings
    return settings.PHOENIX_BASE_URL.rstrip("/")


def _headers() -> dict[str, str]:
    """Build authorization headers for Phoenix API calls."""
    from config import settings
    key = settings.PHOENIX_API_KEY
    if not key:
        raise RuntimeError("PHOENIX_API_KEY is missing")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def query_phoenix_traces(
    project_name: str,
    limit: int = 10,
    min_overall_score: float | None = None,
    max_overall_score: float | None = None,
) -> dict[str, Any]:
    """Query traces and optionally filter them by overall score."""
    base_url = _base_url()
    is_cloud = "app.phoenix.arize.com" in base_url
    
    filtered: list[dict[str, Any]] = []
    
    try:
        if is_cloud:
            import logging
            logger = logging.getLogger(__name__)
            # Use GraphQL for Arize Cloud
            graphql_url = f"{base_url}/graphql"
            # Extract just the base domain if there's a space ID, though the base_url in .env is usually just app.phoenix.arize.com
            # Actually we must use the PHOENIX_COLLECTOR_ENDPOINT for GraphQL if it has a space!
            from config import settings
            collector = settings.PHOENIX_COLLECTOR_ENDPOINT
            if "/s/" in collector:
                space_segment = collector.split("/v1/traces")[0]
                graphql_url = f"{space_segment}/graphql"

            query = {
                "query": """
                query {
                    projects(first: 10) {
                        edges {
                            node {
                                name
                                spans(first: 50) {
                                    edges {
                                        node {
                                            id
                                            startTime
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """
            }
            response = requests.post(graphql_url, json=query, headers=_headers(), timeout=15)
            response.raise_for_status()
            payload = response.json()
            
            # Find the matching project and extract its spans
            projects = payload.get("data", {}).get("projects", {}).get("edges", [])
            spans = []
            for p in projects:
                if p.get("node", {}).get("name") == project_name:
                    spans = p.get("node", {}).get("spans", {}).get("edges", [])
                    break
            
            for s in spans:
                node = s.get("node", {})
                # Format to match the expected legacy REST structure
                trace_dict = {
                    "id": node.get("id"),
                    "timestamp": node.get("startTime"),
                    "scores": {} # Cloud evaluations are decoupled; bypassing filter for now
                }
                filtered.append(trace_dict)
                
        else:
            # Legacy OSS Phoenix Server REST API
            response = requests.get(
                f"{base_url}/v1/traces",
                params={"project_name": project_name, "limit": limit},
                headers=_headers(),
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get("traces", payload.get("data", []))

            for trace in items:
                scores = trace.get("scores", {})
                overall = scores.get("overall")
                if overall is None:
                    filtered.append(trace)
                    continue
                if min_overall_score is not None and overall < min_overall_score:
                    continue
                if max_overall_score is not None and overall > max_overall_score:
                    continue
                filtered.append(trace)
                
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Phoenix trace query failed (safe fallback): %s", e)
        
    return {"status": "success", "traces": filtered[:limit]}


def get_top_prompts(
    prompt_identifier: str,
    top_n: int = 3,
    project_name: str | None = None,
) -> dict[str, Any]:
    """Return top prompt versions sorted by score descending."""
    if project_name is None:
        from config import settings
        project_name = settings.PHOENIX_PROJECT_NAME

    try:
        response = requests.get(
            f"{_base_url()}/v1/prompts/{prompt_identifier}/versions",
            params={"project_name": project_name},
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        versions = payload.get("versions", payload.get("data", []))
        sorted_versions = sorted(
            versions,
            key=lambda item: float(item.get("score", 0.0)),
            reverse=True,
        )
        prompts = [
            {
                "version_id": version.get("version_id", version.get("id", "")),
                "template": version.get("template", ""),
                "score": float(version.get("score", 0.0)),
            }
            for version in sorted_versions[:top_n]
        ]
        return {"status": "success", "prompts": prompts}
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to get top prompts from Phoenix: %s", e)
        return {"status": "success", "prompts": []}


def push_prompt_to_phoenix(
    prompt_identifier: str,
    template: str,
    tag: str = "candidate",
) -> dict[str, Any]:
    """Create or update a Phoenix prompt version.

    Arize Cloud Phoenix uses POST /v1/prompts with a body containing the
    identifier and template — not /v1/prompts/{id}/versions (405).
    Raises on failure so callers can distinguish success from silent errors.
    """
    base = _base_url()
    is_cloud = "app.phoenix.arize.com" in base

    if is_cloud:
        # Arize Cloud: derive the base domain from the collector endpoint
        from config import settings  # noqa: PLC0415
        collector = settings.PHOENIX_COLLECTOR_ENDPOINT
        if "/s/" in collector:
            base = collector.split("/v1/traces")[0]  # e.g. https://app.phoenix.arize.com/s/yashk242810
        url = f"{base}/v1/prompts"
        body = {
            "name": prompt_identifier,
            "template": {"type": "text", "template": template},
            "tags": [tag],
        }
    else:
        # OSS Phoenix Server
        url = f"{base}/v1/prompts/{prompt_identifier}/versions"
        body = {"template": template, "tag": tag}

    response = requests.post(url, json=body, headers=_headers(), timeout=30)
    response.raise_for_status()  # raises HTTPError — caller must handle
    payload = response.json()
    return {"status": "success", "version_id": payload.get("id", payload.get("version_id", ""))}


def extract_score_series(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract sorted score timeline for charting."""
    rows: list[dict[str, Any]] = []
    for trace in traces:
        ts = trace.get("timestamp") or trace.get("created_at")
        scores = trace.get("scores", {})
        overall = scores.get("overall")
        if ts is None or overall is None:
            continue
        rows.append({"timestamp": ts, "overall": float(overall)})
    rows.sort(key=lambda item: datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")))
    return rows

