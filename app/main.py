from fastapi import FastAPI
from app.api.webhook import router as webhook_router

app = FastAPI(title="AI GitHub PR Reviewer Gateway")

# Register webhook router
app.include_router(webhook_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}