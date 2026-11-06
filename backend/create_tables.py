from app.database import Base, engine
from app.models import (
    User,
    Document,
    DocumentPermission,
    AuditLog,
)

print("Creating TrustVault database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")

for table_name in Base.metadata.tables:
    print(f"Created table: {table_name}")