import sys
import time
from collections import Counter

import requests

# ---------------- Configuration ----------------
LB_URL = "http://127.0.0.1:8000/"
LB_STATUS_URL = "http://127.0.0.1:8000/lb-status"

# Number of requests can be passed on the command line, e.g.: python test_requests.py 100
TOTAL_REQUESTS = int(sys.argv[1]) if len(sys.argv) > 1 else 60

DELAY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05


def main():
    served_by = Counter()   # how many requests each backend handled
    failed = 0              # requests that did not get a valid response
    latencies = []          # response time of each request, in milliseconds

    print(f"Sending {TOTAL_REQUESTS} requests to {LB_URL}\n")

    for i in range(1, TOTAL_REQUESTS + 1):
        start = time.perf_counter()
        try:
            response = requests.get(LB_URL, timeout=5)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                # The load balancer reports which backend served the request
                server = response.headers.get("X-Served-By", "unknown")
                served_by[server] += 1
                latencies.append(elapsed_ms)
                print(f"Request {i:>3} -> {server}  ({elapsed_ms:.1f} ms)")
            else:
                failed += 1
                print(f"Request {i:>3} -> FAILED (status {response.status_code})")
        except requests.RequestException as error:
            failed += 1
            print(f"Request {i:>3} -> FAILED ({type(error).__name__})")

        # Small pause so the output is easy to follow
        time.sleep(DELAY)

    # ---------------- Summary ----------------
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"{'Backend':<28}{'Requests':>10}{'Share':>10}")
    print("-" * 50)

    successful = sum(served_by.values())
    for server, count in sorted(served_by.items()):
        share = (count / successful) * 100 if successful else 0
        print(f"{server:<28}{count:>10}{share:>9.1f}%")

    print("-" * 50)
    print(f"Successful: {successful}   Failed: {failed}")
    if latencies:
        print(f"Average latency: {sum(latencies) / len(latencies):.1f} ms")
        print(f"Slowest request: {max(latencies):.1f} ms")

    # Cross-check with the load balancer's own counters
    try:
        status = requests.get(LB_STATUS_URL, timeout=5).json()
        print(f"\nLoad balancer total (all-time): {status['total_requests']}")
    except requests.RequestException:
        print("\nCould not fetch /lb-status from the load balancer.")


if __name__ == "__main__":
    main()