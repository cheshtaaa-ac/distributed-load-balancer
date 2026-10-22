import sys
import uvicorn
from fastapi import FastAPI

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
SERVER_NAME = f"Backend-{PORT}"

app = FastAPI(title=SERVER_NAME)

request_count = 0

@app.get("/")
def home():
    global request_count
    request_count += 1
    return {
        "server": SERVER_NAME,
        "port": PORT,
        "requests_handled": request_count,
        "message": f"Hello! This response has come from {SERVER_NAME}",
    }


@app.get("/health")
def health():
    # Load balancer isse check karega ki server zinda hai ya nahi
    return {"status": "healthy", "server": SERVER_NAME}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)