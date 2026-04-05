#!/usr/bin/env python3
"""
Debug upload portal login - detailed output
"""
import requests
import re
from urllib.parse import urljoin

LIVE_SERVER = "https://1capital.in"
LOGIN_URL = urljoin(LIVE_SERVER, "/upload-portal/login/")
CREDS = {'username': 'prerana', 'password': 'prerana@123'}

session = requests.Session()
session.verify = True

print("\n[STEP 1] GET login page...")
response = session.get(LOGIN_URL)
print(f"Status: {response.status_code}")
print(f"Cookies after GET: {dict(session.cookies)}")

# Extract CSRF token
match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
csrf_token = match.group(1) if match else None
print(f"CSRF token: {csrf_token[:30] if csrf_token else 'NOT FOUND'}...")

print("\n[STEP 2] POST login form...")
data = {
    'username': CREDS['username'],
    'password': CREDS['password'],
}
if csrf_token:
    data['csrfmiddlewaretoken'] = csrf_token

headers = {'Referer': LOGIN_URL}

print(f"POST data: {data}")
print(f"Cookies before POST: {dict(session.cookies)}")
print(f"Headers: {headers}")

response = session.post(LOGIN_URL, data=data, headers=headers, allow_redirects=False)
print(f"\nStatus: {response.status_code}")
print(f"Cookies after POST: {dict(session.cookies)}")

# Print the response content (first 2000 chars)
print(f"\nResponse content snippet:")
print(response.text[0:2000])

# Look for the error message
if 'Invalid credentials' in response.text:
    print("\n❌ 'Invalid credentials' found in response")
    # Find and print the error line
    for line in response.text.split('\n'):
        if 'Invalid credentials' in line or 'error' in line.lower():
            print(f"   Error line: {line.strip()[:150]}")
