import os

# Ensures the test suite never depends on a real credential being present in the ambient
# environment. resume_scorer.py / skill_matcher.py / resume_editor.py instantiate OpenAI
# clients at import time, which requires *some* value to be set (even though every actual
# API call is mocked in these tests) — this must run before any app module is imported.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")
