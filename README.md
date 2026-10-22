# Distributed Load Balancer

A load balancer built with Python and FastAPI that distributes incoming HTTP requests
across multiple backend servers using round-robin scheduling, with health checks and
automatic failover. Everything runs locally; no cloud account is needed.

## Architecture

```
                         +------------------+
                         |  Backend-8001    |
                    +--> |  (FastAPI)       |
                    |    +------------------+
+----------+   +----------------+
|  Client  |-->| Load Balancer  |    +------------------+
| (browser |   |   port 8000    |--> |  Backend-8002    |
|  / test) |   | round-robin +  |    +------------------+
+----------+   | health checks  |
               +----------------+    +------------------+
                    |                |  Backend-8003    |
                    +--------------> +------------------+
```

## Features

- **Round-robin distribution**: requests rotate evenly across all healthy servers.
- **Active health checks**: a background task polls each backend's `/health` endpoint every 5 seconds.
- **Automatic failover**: if a backend fails mid-request, the request is retried on the next healthy server.
- **Automatic recovery**: a restarted backend rejoins the rotation after the next health check.
- **Monitoring endpoint**: `/lb-status` shows each server's health and request count.
- **Load test script**: sends N requests and prints the distribution and latency.

## Project structure

| File | Purpose |
|---|---|
| `backend_server.py` | Simple backend server; the port is passed as an argument |
| `load_balancer.py` | Load balancer with round-robin, health checks and failover |
| `test_requests.py` | Sends test requests and prints a summary |
| `requirements.txt` | Python dependencies |

## Setup

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

## How to run

Open 5 terminals, each with the virtual environment activated.

```
# Terminals 1-3: backend servers
python backend_server.py 8001
python backend_server.py 8002
python backend_server.py 8003

# Terminal 4: load balancer
python load_balancer.py

# Terminal 5: test
python test_requests.py 60
```

## Failover demo

1. Run `python test_requests.py 100 0.5`
2. After about 10 seconds, stop one backend with `Ctrl + C`
3. Requests continue with zero failures, served by the remaining servers
4. Restart the backend; it rejoins the rotation within 5 seconds

## Endpoints

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Forwards the request to the next healthy backend |
| `http://127.0.0.1:8000/lb-status` | Health and request counts for all backends |
| `http://127.0.0.1:800X/health` | Health endpoint of an individual backend |

## Concepts demonstrated

Load balancing, round-robin scheduling, health checking, fault tolerance, failover,
horizontal scaling, and distributed request handling.

## Limitations and future work

- Single load balancer is itself a single point of failure (could run two behind a virtual IP).
- Round-robin ignores server load (could add least-connections or weighted routing).
- Only GET requests are forwarded.