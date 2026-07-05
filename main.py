from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

ALLOWED_ORIGIN = "https://dash-jt6yi0.example.com"
EMAIL = "avijit.kundal@gmail.com"   # replace this exactly

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_required_headers(request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())

    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    process_time = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response


@app.get("/")
def home():
    return {"message": "metrics api running"}


@app.get("/stats")
def stats(values: str = Query(...)):
    try:
        nums = [int(x.strip()) for x in values.split(",") if x.strip() != ""]
    except ValueError:
        raise HTTPException(status_code=400, detail="values must be comma-separated integers")

    if not nums:
        raise HTTPException(status_code=400, detail="values cannot be empty")

    total = sum(nums)

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": total / len(nums),
    }