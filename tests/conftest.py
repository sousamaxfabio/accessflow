import os


# Keep test collection and application lifespan isolated from local project data.
os.environ.setdefault("ACCESSFLOW_DATABASE_URL", "sqlite://")
