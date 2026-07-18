from fastapi import FastAPI

app = FastAPI(
    title="ShipTrack API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "ShipTrack API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }