import os


# Force tests to use isolated, predictable settings.
os.environ["ACCESSFLOW_DATABASE_URL"] = "sqlite://"
os.environ["ACCESSFLOW_APPROVAL_API_KEY"] = "local-development-only"
