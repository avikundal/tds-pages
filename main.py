from fastapi import FastAPI, Query, Request, Response, HTTPException, Header
import time, uuid, json, collections, jwt

EMAIL = "24f2006551@ds.study.iitm.ac.in"
app = FastAPI()

START_TIME = time.time()
REQUEST_COUNT = 0
LOGS = []
rate_store = collections.defaultdict(list)
order_rate = collections.defaultdict(list)
created_orders = {}
order_counter = 1000


@app.middleware("http")
async def middleware(request: Request, call_next):
    global REQUEST_COUNT
    start = time.perf_counter()
    REQUEST_COUNT += 1

    incoming_id = request.headers.get("X-Request-ID")
    request_id = incoming_id or str(uuid.uuid4())

    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    # CRITICAL: always force echo inbound ID
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    LOGS.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    })
    if len(LOGS) > 100:
        LOGS.pop(0)

    return response


@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/stats")
def stats(values: str = Query(...)):
    nums = [int(x) for x in values.split(",") if x.strip()]
    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }


API_KEY = "ak_b777c9etokh2kre2b2ntcj1j"

@app.post("/analytics")
def analytics(data: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

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
            config[key] = value.lower() in ["true", "1", "yes", "on"]
        else:
            config[key] = value

    config["api_key"] = "****"
    return config


@app.get("/ping")
def ping(request: Request):
    now = time.time()

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    client = request.headers.get("X-Client-Id", "default")
    rate_store[client] = [t for t in rate_store[client] if now - t < 10]

    if len(rate_store[client]) >= 14:
        raise HTTPException(status_code=429)

    rate_store[client].append(now)

    return {
        "email": EMAIL,
        "request_id": request_id
    }


@app.get("/work")
def work(n: int = 1):
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    return Response(
        content=f"# TYPE http_requests_total counter\nhttp_requests_total {REQUEST_COUNT}\n",
        media_type="text/plain"
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": time.time() - START_TIME}


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    return LOGS[-limit:]


PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

@app.post("/verify")
def verify(data: dict):
    try:
        payload = jwt.decode(
            data["token"],
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="https://idp.exam.local",
            audience="tds-5my9dk6o.apps.exam.local"
        )
        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }
    except Exception:
        raise HTTPException(status_code=401, detail={"valid": False})


@app.post("/orders")
def create_order(idempotency_key: str = Header(None)):
    global order_counter

    if idempotency_key in created_orders:
        return created_orders[idempotency_key]

    order_counter += 1
    order = {"id": str(order_counter)}
    created_orders[idempotency_key] = order

    return Response(
        content=json.dumps(order),
        status_code=201,
        media_type="application/json"
    )


@app.get("/orders")
def list_orders(request: Request, limit: int = 10, cursor: str = None):
    client = request.headers.get("X-Client-Id", "default")
    now = time.time()

    order_rate[client] = [x for x in order_rate[client] if now - x < 10]

    if len(order_rate[client]) >= 20:
        r = Response(status_code=429)
        r.headers["Retry-After"] = "10"
        return r

    order_rate[client].append(now)

    start = int(cursor) if cursor else 1
    end = min(start + limit, 60)

    return {
        "items": [{"id": i} for i in range(start, end)],
        "next_cursor": str(end) if end <= 59 else None
    }
