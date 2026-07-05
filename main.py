from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse
import time
import uuid

ALLOWED_ORIGIN = "https://dash-jt6yi0.example.com"
EMAIL = "24f2006551@ds.study.iitm.ac.in"

app = FastAPI()


@app.middleware("http")
async def middleware(request: Request, call_next):
    start = time.perf_counter()

    # handle preflight directly
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    origin = request.headers.get("origin")

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/stats")
def stats(values: str = Query(...)):
    nums = [int(x) for x in values.split(",")]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }


API_KEY = "ak_b777c9etokh2kre2b2ntcj1j"

from fastapi import Header

@app.post("/analytics")
def analytics(data: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    events = data["events"]

    users = set()
    revenue = 0
    totals = {}

    for e in events:
        users.add(e["user"])
        amt = e["amount"]

        if amt > 0:
            revenue += amt
            totals[e["user"]] = totals.get(e["user"],0)+amt

    return {
        "email": EMAIL,
        "total_events": len(events),
        "unique_users": len(users),
        "revenue": revenue,
        "top_user": max(totals, key=totals.get)
    }
