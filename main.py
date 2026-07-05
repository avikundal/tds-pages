from fastapi import FastAPI, Query, Request, Response, HTTPException, Header
import time
import uuid

ALLOWED_ORIGIN = "https://dash-jt6yi0.example.com"
EMAIL = "24f2006551@ds.study.iitm.ac.in"

app = FastAPI()


@app.middleware("http")
async def middleware(request: Request, call_next):
    start = time.perf_counter()

    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    origin = request.headers.get("origin")

    # allow exam browser + Q1 origin
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


@app.get("/")
def home():
    return {"status": "ok"}


# ---------------- Q1 ----------------

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


# ---------------- Q5 ----------------

API_KEY = "ak_b777c9etokh2kre2b2ntcj1j"

@app.post("/analytics")
def analytics(data: dict, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="invalid api key"
        )

    events = data["events"]

    users = set()
    revenue = 0
    totals = {}

    for e in events:
        user = e["user"]
        amount = e["amount"]

        users.add(user)

        if amount > 0:
            revenue += amount
            totals[user] = totals.get(user, 0) + amount

    return {
        "email": EMAIL,
        "total_events": len(events),
        "unique_users": len(users),
        "revenue": revenue,
        "top_user": max(totals, key=totals.get),
    }


# ---------------- Q3 ----------------

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    config = {
        "port": 8323,
        "workers": 4,
        "debug": False,
        "log_level": "debug",
        "api_key": "key-yg65gbhcqr"
    }

    for item in set:
        key, value = item.split("=", 1)

        if key in ["port", "workers"]:
            config[key] = int(value)

        elif key == "debug":
            config[key] = value.lower() in [
                "true",
                "1",
                "yes",
                "on"
            ]

        else:
            config[key] = value

    config["api_key"] = "****"

    return config

# ---------------- Q10 ----------------

import collections

MW_ALLOWED_ORIGIN = "https://app-5rn8vj.example.com"
RATE_LIMIT = 14

rate_store = collections.defaultdict(list)


@app.get("/ping")
def ping(request: Request, response: Response):

    now = time.time()

    # request id handling
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    response.headers["X-Request-ID"] = request_id


    # rate limit by client id
    client = request.headers.get(
        "X-Client-Id",
        "default"
    )

    # keep only last 10 seconds
    rate_store[client] = [
        t for t in rate_store[client]
        if now - t < 10
    ]

    if len(rate_store[client]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="rate limit"
        )

    rate_store[client].append(now)

    return {
        "email": EMAIL,
        "request_id": request_id
    }

    
    
