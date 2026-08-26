import json
from typing import Any, Dict, List

import httpx  # pyright: ignore[reportMissingImports]


class LLMJudgeEvaluator:
    def __init__(self, vllm_url: str = "http://localhost:8000/v1"):
        self.vllm_url = vllm_url
    
    async def evaluate_context_relevance(self, query: str, contexts: List[str]) -> float:
        prompt = f"""
        [System]
        You are an expert evaluator assessing the relevance of retrieved contexts for a user query.
        Rate the relevance on a scale from 1 to 5, where 1 is completely irrelevant and 5 is perfectly relevant.
        Respond with ONLY a JSON object containing "score" (integer 1-5) and "reason" (short string).

        [Query]
        {query}

        [Retrieved Contexts]
        {json.dumps(
            contexts, 
            ensure_ascii=False
        )}
        """  # noqa: E501

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.vllm_url}/chat/completions",
                    json={
                        "model": "Qwen/Qwen2.5-7B-Instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0
                    }
                )
                content = res.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                score = parsed.get("score", 3)
                return round((score-1) / 4.0, 2)
        except Exception:
            return 0.50
