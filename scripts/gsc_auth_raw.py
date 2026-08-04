#!/usr/bin/env python3
"""Shared GSC OAuth helper using raw requests (no google-auth dependency).

The Hermes venv's cryptography package is currently broken, so anything that
imports google.oauth2/googleapiclient fails. This module does the OAuth token
load + refresh via plain `requests` and returns an authenticated requests.Session
with the bearer token attached. Works around the broken crypto package.

Usage:
    from gsc_auth_raw import get_session, SITE
    s = get_session()
    r = s.post(f".../searchAnalytics/query", json=payload)
"""
import os
import json
import time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(HERE, "..", ".gsc_token.json")
SITE = "https://www.aitoolssolo.com/"


def _refresh(creds: dict) -> dict:
    """Exchange refresh_token for a new access token via raw POST."""
    resp = requests.post(
        creds.get("token_uri", "https://oauth2.googleapis.com/token"),
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    creds["token"] = data["access_token"]
    creds["expiry_ts"] = time.time() + data.get("expires_in", 3600)
    # Persist refreshed access token so we don't refresh every run
    with open(TOKEN_PATH, "w") as f:
        json.dump(creds, f, indent=2)
    return creds


def _load() -> dict:
    with open(TOKEN_PATH) as f:
        return json.load(f)


def get_credentials() -> dict:
    """Return creds dict with a valid (unexpired) access token."""
    creds = _load()
    expires = creds.get("expiry_ts", 0)
    if not creds.get("token") or time.time() >= expires - 60:
        creds = _refresh(creds)
    return creds


def get_session() -> requests.Session:
    """Return a requests.Session with Bearer auth attached."""
    creds = get_credentials()
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {creds['token']}"})
    return s


if __name__ == "__main__":
    c = get_credentials()
    print("Access token valid, expires in",
          int(c.get("expiry_ts", 0) - time.time()), "s")
