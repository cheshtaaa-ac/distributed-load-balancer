import asyncio
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ---------------- Configuration ----------------
BACKENDS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003",
]
HEALTH_CHECK_INTERVAL = 5  # seconds

# ---------------- State ----------------
healthy = {url: True for url in BACKENDS}  
stats = {url: 0 for url in BACKENDS}        
rr_index = 0                                


# ---------------- Round Robin ----------------
def get_next_server():
    
    global rr_index
    for _ in range(len(BACKENDS)):
        server = BACKENDS[rr_index % len(BACKENDS)]
        rr_index += 1
        if healthy[server]:
            return server
    return None


# ---------------- Health Check (background) ----------------
async def health_check_loop():
    while True:
        for url in BACKENDS:
            try:
                r = await client.get(f"{url}/health", timeout=2)
                is_up = r.status_code == 200
            except httpx.RequestError:
                is_up = False

            if is_up != healthy[url]:
                print(f"[HEALTH] {url} is now {'UP' if is_up else 'DOWN'}")
            healthy[url] = is_up
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient(timeout=3)
    task = asyncio.create_task(health_check_loop())
    yield
    task.cancel()
    await client.aclose()


app = FastAPI(title="Load Balancer", lifespan=lifespan)


# ---------------- Routes ----------------
@app.get("/lb-status")
async def lb_status():
    
    return {
        "servers": [
            {"url": url, "healthy": healthy[url], "requests_served": stats[url]}
            for url in BACKENDS
        ],
        "total_requests": sum(stats.values()),
    }


@app.get("/")
async def forward_request():
   
    for _ in range(len(BACKENDS)):
        server = get_next_server()
        if server is None:
            break
        try:
            response = await client.get(f"{server}/")
            stats[server] += 1
            print(f"[ROUTE] request -> {server}")
            return JSONResponse(
                content=response.json(),
                headers={"X-Served-By": server},
            )
        except httpx.RequestError:
           
            healthy[server] = False
            print(f"[FAILOVER] {server} failed, trying next server")

    return JSONResponse(
        status_code=503,
        content={"error": "No backend server is available"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)