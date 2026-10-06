"""Secure Binance credential loader.

Only reads credentials from environment variables.
Does not connect to Binance, place orders, or print secrets.
"""
import os

def get_binance_credentials():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Binance API credentials are not configured.")
    return api_key, api_secret
