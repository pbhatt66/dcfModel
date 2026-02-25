import os
from pathlib import Path

def _load_toml_secrets():
    secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}
    try:
        import tomllib
    except Exception:
        import tomli as tomllib
    with secrets_path.open("rb") as f:
        return tomllib.load(f)

def get_secret(key: str):
    if os.getenv(key):
        return os.getenv(key)

    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets.get(key)
    except Exception:
        pass

    # 3) secrets.toml
    secrets = _load_toml_secrets()
    return secrets.get(key)