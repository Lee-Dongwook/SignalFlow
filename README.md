# SignalFlow

### 실행 단계

#### 1. 컨테이너 실행

- `docker compose up -d`

#### 2. Kafka 토픽 실행

- `docker exec -it <kafka-container-id> kafka-topics --create --topic raw-intelligence-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1`

#### 3. Flink 대시보드 접속
