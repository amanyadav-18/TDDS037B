from app.database import engine, Base
from app import models  # noqa: F401

Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully.")