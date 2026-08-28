from fastapi import FastAPI

app = FastAPI(
    title="ReviveAI",
    description="AI-powered Revenue Recovery System",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "reviveai-backend",
        "version": "0.1.0",
    }