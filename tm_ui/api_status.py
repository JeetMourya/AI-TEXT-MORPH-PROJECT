"""Hugging Face API status checks and readable error guidance."""

import requests

GUIDANCE = {
    "success": "The latest real pipeline request completed successfully.",
    "configured": "An API key is present, but it has not yet been verified. Use Verify connection.",
    "not_configured": "No Hugging Face token was found. Add HF_API_KEY=your_token to src/.env and restart Streamlit.",
    "invalid_token": "Hugging Face rejected the token. Create or copy a valid token from https://huggingface.co/settings/tokens and update src/.env.",
    "unauthorized": "The provider rejected the credentials. Check that the token is valid and has permission to use Inference Providers.",
    "forbidden": "The token does not have permission for this request or model. Check token permissions and model access.",
    "rate_limited": "The provider rate-limited the request. Wait briefly and try again; check provider quotas if it continues.",
    "model_loading": "The selected model may be loading. Wait and retry; if it persists, check the model/provider status.",
    "model_unavailable": "The selected model or provider is unavailable. Check the model ID and provider availability.",
    "network_error": "A network connection to the provider failed. Check internet access, proxy and firewall settings, then retry.",
    "timeout": "The provider did not respond in time. Retry with shorter text or try again later.",
    "bad_request": "The provider rejected the request. Check the input length, model parameters and backend configuration.",
    "server_error": "The provider returned a server error. Retry later; this may be temporary.",
    "unknown_error": "The request failed for an unclassified reason. Read the error details and inspect the backend configuration.",
}


def state_info(state: str):
    mapping = {
        "success": ("Working", "ok"),
        "configured": ("Key configured", "neutral"),
        "not_configured": ("Key missing", "bad"),
        "invalid_token": ("Invalid token", "bad"),
        "unauthorized": ("Unauthorized", "bad"),
        "forbidden": ("Permission denied", "bad"),
        "rate_limited": ("Rate limited", "warn"),
        "model_loading": ("Model loading", "warn"),
        "model_unavailable": ("Model unavailable", "bad"),
        "network_error": ("Network error", "warn"),
        "timeout": ("Timed out", "warn"),
        "bad_request": ("Request rejected", "bad"),
        "server_error": ("Provider error", "warn"),
        "unknown_error": ("Unknown error", "bad"),
    }
    return mapping.get(state, ("Unknown status", "neutral"))


def classify_pipeline_error(message: str) -> str:
    msg = (message or "").lower()
    if any(x in msg for x in ("401", "invalid token", "invalid credentials", "token is invalid")):
        return "invalid_token"
    if any(x in msg for x in ("403", "forbidden", "permission")):
        return "forbidden"
    if any(x in msg for x in ("429", "rate limit", "too many requests")):
        return "rate_limited"
    if any(x in msg for x in ("loading", "503", "currently loading")):
        return "model_loading"
    if any(x in msg for x in ("404", "model not found", "not supported")):
        return "model_unavailable"
    if any(x in msg for x in ("timeout", "timed out", "readtimeout")):
        return "timeout"
    if any(x in msg for x in ("connectionerror", "connection error", "name or service not known", "network is unreachable", "dns")):
        return "network_error"
    if any(x in msg for x in ("400", "bad request", "unprocessable entity", "422")):
        return "bad_request"
    if any(x in msg for x in ("500", "502", "503", "504", "internal server error", "bad gateway")):
        return "server_error"
    if any(x in msg for x in ("unauthorized", "401")):
        return "unauthorized"
    return "unknown_error"


def verify_hf_token(token: str):
    """Verify token against HF whoami endpoint; never return or log the token."""
    import time
    if not token:
        return {"state": "not_configured", "detail": "No HF_API_KEY was found.", "ts": time.time()}
    try:
        response = requests.get(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {token}"}, timeout=12,
        )
        if response.ok:
            return {"state": "success", "detail": "Hugging Face accepted the token.", "ts": time.time()}
        state = "invalid_token" if response.status_code == 401 else ("forbidden" if response.status_code == 403 else classify_pipeline_error(f"HTTP {response.status_code}"))
        return {"state": state, "detail": f"Hugging Face returned HTTP {response.status_code}.", "ts": time.time()}
    except requests.Timeout:
        return {"state": "timeout", "detail": "The verification request timed out.", "ts": time.time()}
    except requests.RequestException as exc:
        return {"state": "network_error", "detail": f"Connection failed: {type(exc).__name__}.", "ts": time.time()}
