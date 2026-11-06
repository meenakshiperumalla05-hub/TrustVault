
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, documents, admin

app = FastAPI(
    title="TrustVault API",
    description="Secure document sharing with a verifiable audit trail",
    version="1.0.0",
)

# Allow the local React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(admin.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "application": "TrustVault"
    }
