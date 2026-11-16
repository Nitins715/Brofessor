import logging
import os
import time
from typing import Any, Dict, Optional
import requests

from django.conf import settings
from apps.rag.llm.registry import get_system_ai_config, save_system_ai_config, sync_langsmith_env

logger = logging.getLogger("brofessor")


def mask_key(key: Optional[str]) -> str:
    """Mask a secret key for UI display (e.g., 'lsv2_...abcd')."""
    if not key or not str(key).strip():
        return ""
    clean = str(key).strip()
    if len(clean) <= 8:
        return "••••••••"
    return f"{clean[:5]}••••••{clean[-4:]}"


def verify_langsmith_key(
    api_key: Optional[str],
    project_name: Optional[str] = "brofessor-rag",
    timeout_seconds: float = 4.0,
) -> Dict[str, Any]:
    """
    Perform a live network check / ping against LangSmith API.
    Returns status dict indicating whether credentials are valid and reachable.
    """
    clean_key = (api_key or "").strip()
    project = (project_name or "brofessor-rag").strip()

    if not clean_key:
        return {
            "configured": False,
            "connected": False,
            "status": "not_configured",
            "project": project,
            "message": "No LangSmith API key provided.",
            "latency_ms": None,
        }

    start_time = time.time()

    # 1. First attempt: Direct HTTP auth check with requests for fast response
    try:
        endpoint = getattr(settings, "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")
        # The /sessions or /tenants endpoint validates auth header x-api-key
        resp = requests.get(
            f"{endpoint}/sessions?limit=1",
            headers={"x-api-key": clean_key, "Accept": "application/json"},
            timeout=timeout_seconds,
        )
        latency_ms = round((time.time() - start_time) * 1000, 1)

        if resp.status_code == 200:
            return {
                "configured": True,
                "connected": True,
                "status": "connected",
                "project": project,
                "message": f"Connected to LangSmith (Ping: {latency_ms}ms). Tracing enabled for '{project}'.",
                "latency_ms": latency_ms,
            }
        elif resp.status_code in (401, 403):
            return {
                "configured": True,
                "connected": False,
                "status": "unauthorized",
                "project": project,
                "message": "Authentication failed: Invalid LangSmith API Key.",
                "latency_ms": latency_ms,
            }
        else:
            # Other HTTP status
            return {
                "configured": True,
                "connected": False,
                "status": "http_error",
                "project": project,
                "message": f"LangSmith returned HTTP {resp.status_code}.",
                "latency_ms": latency_ms,
            }
    except requests.exceptions.Timeout:
        return {
            "configured": True,
            "connected": False,
            "status": "timeout",
            "project": project,
            "message": f"LangSmith ping timed out after {timeout_seconds}s.",
            "latency_ms": None,
        }
    except requests.exceptions.ConnectionError as e:
        # Check if due to offline / sandbox / DNS
        return {
            "configured": True,
            "connected": False,
            "status": "unreachable",
            "project": project,
            "message": "Network check failed: Unable to reach https://api.smith.langchain.com (Host unreachable or offline).",
            "error": str(e),
            "latency_ms": None,
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "status": "error",
            "project": project,
            "message": f"LangSmith check error: {str(e)}",
            "error": str(e),
            "latency_ms": None,
        }


def verify_gemini_key(
    api_key: Optional[str],
    model_name: Optional[str] = "gemini-3.6-flash",
    timeout_seconds: float = 4.0,
) -> Dict[str, Any]:
    """
    Perform a live network check / ping against Google Generative Language API.
    """
    clean_key = (api_key or "").strip()
    model = (model_name or "gemini-3.6-flash").strip()

    if not clean_key:
        return {
            "configured": False,
            "connected": False,
            "status": "not_configured",
            "model": model,
            "message": "No Gemini API key configured. Local Ollama model active as fallback.",
            "latency_ms": None,
        }

    start_time = time.time()
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
        resp = requests.get(url, timeout=timeout_seconds)
        latency_ms = round((time.time() - start_time) * 1000, 1)

        if resp.status_code == 200:
            return {
                "configured": True,
                "connected": True,
                "status": "connected",
                "model": model,
                "message": f"Connected to Google Gemini ({model}, Ping: {latency_ms}ms).",
                "latency_ms": latency_ms,
            }
        elif resp.status_code in (400, 401, 403):
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                pass
            return {
                "configured": True,
                "connected": False,
                "status": "unauthorized",
                "model": model,
                "message": f"Invalid Gemini API key: {detail or 'Authorization denied'}.",
                "latency_ms": latency_ms,
            }
        else:
            return {
                "configured": True,
                "connected": False,
                "status": "http_error",
                "model": model,
                "message": f"Gemini API returned status HTTP {resp.status_code}.",
                "latency_ms": latency_ms,
            }
    except requests.exceptions.Timeout:
        return {
            "configured": True,
            "connected": False,
            "status": "timeout",
            "model": model,
            "message": f"Gemini ping timed out after {timeout_seconds}s.",
            "latency_ms": None,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "configured": True,
            "connected": False,
            "status": "unreachable",
            "model": model,
            "message": "Network check failed: Unable to reach Google Generative Language API.",
            "error": str(e),
            "latency_ms": None,
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "status": "error",
            "model": model,
            "message": f"Gemini check error: {str(e)}",
            "error": str(e),
            "latency_ms": None,
        }


def verify_ollama_status(
    base_url: Optional[str] = None,
    model_name: Optional[str] = "llama3.2",
    timeout_seconds: float = 2.0,
) -> Dict[str, Any]:
    """Check if local Ollama daemon is reachable."""
    import sys
    clean_url = (base_url or "http://127.0.0.1:11434").rstrip("/")
    model = model_name or "llama3.2"

    # Avoid socket timeout during unit test execution
    if "test" in sys.argv or getattr(settings, "TESTING", False):
        return {
            "configured": True,
            "connected": False,
            "status": "offline",
            "base_url": clean_url,
            "model": model,
            "message": f"Local Ollama daemon offline (test mode).",
        }

    try:
        resp = requests.get(f"{clean_url}/api/version", timeout=timeout_seconds)
        if resp.status_code == 200:
            version_info = resp.json().get("version", "available")
            return {
                "configured": True,
                "connected": True,
                "status": "connected",
                "base_url": clean_url,
                "model": model,
                "version": version_info,
                "message": f"Ollama v{version_info} active at {clean_url}.",
            }
    except Exception:
        pass

    return {
        "configured": True,
        "connected": False,
        "status": "offline",
        "base_url": clean_url,
        "model": model,
        "message": f"Local Ollama daemon unreachable at {clean_url}.",
    }


def get_current_integrations_status(include_secrets: bool = False) -> Dict[str, Any]:
    """
    Consolidated status check for UI sidebar and settings.
    Returns masked keys and live connectivity checks.
    """
    ai_cfg = get_system_ai_config()

    gemini_key = ai_cfg.get("gemini_api_key", "")
    gemini_model = ai_cfg.get("gemini_model", "gemini-3.6-flash")
    langsmith_key = ai_cfg.get("langsmith_api_key", "")
    langsmith_project = ai_cfg.get("langsmith_project", "brofessor-rag")
    ollama_url = ai_cfg.get("ollama_base_url", "http://127.0.0.1:11434")
    ollama_model = ai_cfg.get("ollama_model", "llama3.2")

    langsmith_check = verify_langsmith_key(langsmith_key, langsmith_project)
    gemini_check = verify_gemini_key(gemini_key, gemini_model)
    ollama_check = verify_ollama_status(ollama_url, ollama_model)

    # Determine primary active LLM provider
    if gemini_key:
        active_llm = {
            "provider": "gemini",
            "name": f"Gemini ({gemini_model})",
            "connected": gemini_check["connected"],
            "status": gemini_check["status"],
            "message": gemini_check["message"],
        }
    else:
        active_llm = {
            "provider": "ollama",
            "name": f"Ollama ({ollama_model})",
            "connected": ollama_check["connected"],
            "status": ollama_check["status"],
            "message": ollama_check["message"],
        }

    data = {
        "langsmith": {
            **langsmith_check,
            "api_key_masked": mask_key(langsmith_key),
            "api_key": langsmith_key if include_secrets else None,
            "project": langsmith_project,
            "tracing_enabled": bool(langsmith_key and ai_cfg.get("langsmith_tracing", True)),
        },
        "gemini": {
            **gemini_check,
            "api_key_masked": mask_key(gemini_key),
            "api_key": gemini_key if include_secrets else None,
            "model": gemini_model,
        },
        "ollama": ollama_check,
        "active_llm": active_llm,
    }
    return data
