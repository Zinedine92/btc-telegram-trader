#!/usr/bin/env python3
"""Debug script to understand Request.header_items() behavior."""

from urllib.request import Request

# Test how Request handles headers in Python 3.11
request = Request(
    "https://example.com/test",
    headers={"X-MBX-APIKEY": "test-key"},
    method="GET",
)

print("Testing Request.header_items():")
print(f"Type of request: {type(request)}")
print(f"Header items: {request.header_items()}")
print(f"As dict: {dict(request.header_items())}")

# Try to access the header
headers_dict = dict(request.header_items())
print(f"\nHeaders dict keys: {list(headers_dict.keys())}")
print(f"Trying to access with 'X-MBX-APIKEY': {headers_dict.get('X-MBX-APIKEY')}")
print(f"Trying to access with 'x-mbx-apikey': {headers_dict.get('x-mbx-apikey')}")

# Check if header is there at all
for key, value in headers_dict.items():
    print(f"  Key: '{key}', Value: '{value}'")
