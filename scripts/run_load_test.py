import asyncio
import time

import httpx  # pyright: ignore[reportMissingImports]

from scripts.produce_events import produce_dummy_events

API_URL = "http://localhost:8001"

async def monitor_metrics(duration_sec: int = 10):
    print("[Real-time Metrics Monitoring Started]")
    async with httpx.AsyncClient() as client:
        for _ in range(duration_sec):
            try:
                res = await client.get(f"{API_URL}/health")
                print(f"  * System Health Status: {res.status_code} | Time: {time.strftime('%H:%M:%S')}")  # noqa: E501
            except Exception as e:
                print(f"  * Health Check Failed: {e}")
            await asyncio.sleep(1)

async def run_load_test():
    print("[1] Kafka 이벤트 주입")
    produce_dummy_events(count=100)

    print("[2] 시스템 metric 관측 시작")
    asyncio.run(monitor_metrics(duration_sec=5))

    print("[3] Agentic Search API 라우팅 테스트")
    async with httpx.AsyncClient() as client:
        res = asyncio.run(client.post(
            f"{API_URL}/api/v1/search/agentic",
            json={"query": "Kafka 토폴로지 연결 상태 및 장애 이력 조회"}
        ))
        print("  * Agentic Search Response:")
        print(f"    - Selected Tools: {res.json().get('selected_tools')}")

if __name__ == "__main__":
    run_load_test()
