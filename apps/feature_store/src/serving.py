from fastapi import FastAPI, HTTPException
import redis

app = FastAPI(title="SignalFlow Feature Serving API")
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@app.get("/v1/features/{event_id}")
async def get_online_features(event_id: str):
    redis_key = f"feature:event:{event_id}"
    features = r.hgetall(redis_key)

    if not features:
        raise HTTPException(status_code=404, detail="Feature vector not found or expired")
    
    return {
        "event_id": event_id,
        "features": {
            "category_frequency_1h": int(features.get("category_frequency_1h", 0)),
            "sentiment_score": float(features.get("sentiment_score", 0.0)),
            "anomaly_score": float(features.get("anomaly_score", 0.0))
        }
    }
