"""
QuantSentinel — Gemini 3.1 Pro connectivity test via Vertex AI
Run from project root: python test_vertex_gemini.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))

project  = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

print("=" * 55)
print("QuantSentinel — Gemini 3.1 Pro via Vertex AI")
print("=" * 55)
print(f"  Project  : {project}")
print(f"  Location : {location}")
print("=" * 55)

try:
    from google import genai
except ImportError:
    print("\n[X] Run: pip install google-genai")
    sys.exit(1)

print("\n[1/3] Creating Vertex AI client (ADC)...")
client = genai.Client(
    vertexai=True,
    project=project,
    location=location,   # must be 'global' for Gemini 3.1 Pro
)
print("      OK")

# Test cheap model first to confirm ADC works
print("[2/3] Testing gemini-2.5-flash (cheap sanity check)...")
try:
    r = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly: FLASH_OK",
    )
    print(f"      {r.text.strip()}")
except Exception as e:
    print(f"\n[X] Flash failed: {e}")
    print("\nFixes:")
    print("  1. gcloud auth application-default login")
    print(f"  2. gcloud auth application-default set-quota-project {project}")
    print("  3. Enable billing at console.cloud.google.com/billing")
    sys.exit(1)

# Test Gemini 3.1 Pro
print("[3/3] Testing gemini-3.1-pro-preview (the real one)...")
try:
    from google.genai import types
    r = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents="Reply with exactly: PRO_OK",
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.LOW
            )
        ),
    )
    print(f"      {r.text.strip()}")
    print("\n[OK] Gemini 3.1 Pro is working. You are good to build.\n")
except Exception as e:
    print(f"\n[X] Gemini 3.1 Pro failed: {e}")
    print("\nMost likely cause: billing not enabled yet.")
    print(f"Fix: https://console.cloud.google.com/billing/linkedaccount?project={project}")
    sys.exit(1)