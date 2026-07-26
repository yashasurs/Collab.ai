import asyncio
import httpx
import time
import json

API_URL = "http://localhost:8000/api/sessions/create"
NUM_REQUESTS = 500
CONCURRENCY = 50

async def make_request(client, results):
    start = time.perf_counter()
    try:
        resp = await client.post(API_URL, json={
            "osType": "ubuntu",
            "userId": "test-user-123",
            "username": "load_tester"
        })
        success = resp.status_code == 200
    except Exception as e:
        success = False
    
    elapsed = time.perf_counter() - start
    results.append({"time": elapsed, "success": success})

async def worker(client, queue, results):
    while True:
        try:
            _ = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        await make_request(client, results)
        queue.task_done()

async def run_load_test():
    queue = asyncio.Queue()
    for _ in range(NUM_REQUESTS):
        queue.put_nowait(1)
        
    results = []
    
    print(f"Starting load test: {NUM_REQUESTS} requests, {CONCURRENCY} concurrent connections...")
    
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=100)
    async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
        start_time = time.perf_counter()
        
        tasks = []
        for _ in range(CONCURRENCY):
            task = asyncio.create_task(worker(client, queue, results))
            tasks.append(task)
            
        await queue.join()
        
        total_time = time.perf_counter() - start_time
        
        successful = sum(1 for r in results if r["success"])
        times = [r["time"] for r in results if r["success"]]
        
        tps = successful / total_time
        
        if times:
            times.sort()
            p95 = times[int(len(times) * 0.95)] * 1000  # in ms
            avg = (sum(times) / len(times)) * 1000
        else:
            p95 = 0
            avg = 0
            
        print("\n--- RESULTS ---")
        print(f"Total Time: {total_time:.2f} s")
        print(f"Successful Requests: {successful}/{NUM_REQUESTS}")
        print(f"Transactions Per Second (TPS): {tps:.2f}")
        print(f"Average Latency: {avg:.2f} ms")
        print(f"P95 Latency: {p95:.2f} ms")
        
        # Save to JSON for parsing
        with open("benchmark_results.json", "w") as f:
            json.dump({
                "tps": round(tps, 2),
                "p95_ms": round(p95, 2),
                "avg_ms": round(avg, 2),
                "success_rate": round((successful/NUM_REQUESTS)*100, 2)
            }, f)

if __name__ == "__main__":
    asyncio.run(run_load_test())
