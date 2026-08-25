import os
import asyncio
import httpx
from pyflink.datastream import MapFunction
from schemas.event_schema_v1_pb2 import IntelligenceEvent

class VLLMEmbeddingOperator(MapFunction):
    def __init__(self, vllm_url: str = None, model_name: str = "BAAI/bge-m3"):
        # 로컬 docker-compose.test.yml의 vLLM 포트와 맞춘 기본값이다.
        # 다른 환경에서는 VLLM_URL 환경 변수로 덮어쓸 수 있다.
        self.vllm_url = vllm_url or os.getenv("VLLM_URL", "http://localhost:8000")
        self.endpoint = f"{self.vllm_url}/v1/embeddings"
        self.model_name = model_name
        self.client = None

    def open(self, runtime_context):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(2.0, connect=0.5),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    def map(self, value:IntelligenceEvent) -> dict:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        embedding = loop.run_until_complete(self._fetch_embedding(value.payload))

        return {
            "event_id": value.event_id,
            "source": value.source,
            "payload": value.payload,
            "embedding": embedding,
            "timestamp": value.timestamp,
            "trace_id": value.trace_id,
            "span_id": value.span_id,
            "metadata": dict(value.metadata)
        }
    
    async def _fetch_embedding(self, text:str) -> list[float]:
        try:
            response = await self.client.post(
                self.endpoint,
                json = {
                    "model": self.model_name,
                    "input": text
                }    
            )
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except Exception as e:
            print(f"vLLM Error: Failed to fetch embedding: {e}")
            return []
    
    def close(self):
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.client.aclose())
            except Exception:
                pass
