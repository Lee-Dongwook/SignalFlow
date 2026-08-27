# SignalFlow

> 실시간 비정형 이벤트를 수집·검증하고, 장애 이벤트를 DLQ와 멀티 에이전트로 복구하며, 검색·관측 레이어에 제공하는 스트리밍 데이터 플랫폼입니다.

## 프로젝트 소개

SignalFlow는 Kafka로 유입된 Protobuf 이벤트를 Flink로 처리합니다. 처리 과정에서 데이터 품질을 검사하고, 임베딩 및 그래프 정보를 ClickHouse와 Neo4j에 적재합니다. 오류 이벤트는 DLQ에서 분리한 뒤 자가복구 워커가 재처리합니다. FastAPI 제어 API와 Next.js 대시보드는 파이프라인 상태를 확인하는 데 사용합니다.

### 핵심 기능

- **실시간 이벤트 처리**: Kafka → PyFlink 스트림에서 Protobuf 이벤트를 파싱하고 데이터 품질을 평가합니다.
- **안전한 DLQ 복구 검토**: AI가 오류 원인, 수정안, 변경 diff, 신뢰도를 구조화해 제안하고 Pydantic 검증과 운영자 승인을 거쳐 처리합니다.
- **다중 저장소 서빙**: 벡터·메타데이터는 ClickHouse, 엔터티 관계는 Neo4j로 전달합니다.
- **검색 파이프라인**: ClickHouse 하이브리드 검색, 리랭킹, Neo4j 그래프 컨텍스트를 결합합니다.
- **운영 화면/API**: FastAPI의 상태·SSE 메트릭·복구 API와 Next.js 대시보드를 제공합니다.
- **관측 및 인프라**: Prometheus, Grafana, Jaeger, MinIO, Elasticsearch 등을 Docker Compose로 구성합니다.

## 아키텍처

```text
Producer (Protobuf/Base64)
          │
          ▼
Kafka: unstructured-events
          │
          ▼
PyFlink: 역직렬화 → 데이터 품질 평가 → 임베딩
          │                       │
          │                       └── DLQ: dlq-intelligence-stream
          ▼                                      │
ClickHouse Vector Sink + Neo4j Graph Sink        ▼
                                          DLQ Self-Healing Agent
                                                  │
                                                  └── raw-telemetry-stream 재투입

FastAPI Control API ── SSE 메트릭 / DLQ 검토·승인 ── Next.js Dashboard
```

## 기술 스택

| 영역        | 구성                                                            |
| ----------- | --------------------------------------------------------------- |
| 메시징·처리 | Kafka, Apache Flink/PyFlink, Protobuf                           |
| 저장·검색   | MinIO/Iceberg, ClickHouse, Elasticsearch, Neo4j                 |
| AI·복구     | vLLM 임베딩, LangGraph 기반 복구 흐름, Tenacity 재시도          |
| API·UI      | FastAPI, SSE, Next.js 14, React, Tailwind CSS                   |
| 관측·배포   | Prometheus, Grafana, Jaeger, Docker Compose, Kubernetes/Argo CD |

## 프로젝트 구조

```text
.
├── apps/
│   ├── backend_api/          # FastAPI 제어 API
│   ├── dashboard/            # Next.js 모니터링 대시보드
│   ├── dlq_healing_agent/    # DLQ 자가복구 워커와 서킷 브레이커
│   ├── flink_jobs/           # Flink Docker 이미지와 스트림 작업 예제
│   ├── producer/             # 이벤트 생산기
│   └── retrieval/            # 하이브리드 검색·리랭킹·그래프 컨텍스트
├── jobs/                     # 로컬 PyFlink 스트리밍 파이프라인
├── schemas/                  # Protobuf 이벤트 계약
├── scripts/                  # 이벤트 생산, E2E·검색 테스트 스크립트
├── tests/                    # API, 복구, 스키마, 인프라 테스트
├── infra/                    # 저장소·관측 도구 설정
├── k8s/                      # Argo CD, Helm, Flink, Chaos 실험 매니페스트
└── orchestration/            # Airflow·dbt 배치 작업
```

## 시작하기

### 1. 준비물

- Docker Desktop과 Docker Compose
- Python 3.10 이상
- Node.js 18 이상 및 pnpm 9

### 2. 환경 변수 설정

예시 파일을 복사한 후, 사용하는 포트와 자격 증명을 채웁니다. 실제 비밀값은 커밋하지 않습니다.

```bash
cp .env.example .env
```

최소한 `KAFKA_PORT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_PORT`, `MINIO_CONSOLE_PORT`, `CLICKHOUSE_PORT`, `ELASTICSEARCH_PORT`, `GRAFANA_PORT`를 설정해야 기본 Compose 구성이 시작됩니다. LLM 기반 복구 분석을 실행할 때만 서버 환경변수 `OPENAI_API_KEY`가 필요합니다. 키가 없어도 fixture 기반 DLQ 검토·승인·재처리 시뮬레이션은 동작합니다.

### 3. 인프라 시작

```bash
docker compose up -d
docker compose ps
```

컨테이너가 시작된 뒤 Kafka 토픽을 생성합니다. 이미 있으면 생성 명령은 오류를 반환할 수 있습니다.

```bash
docker exec kafka kafka-topics --create --if-not-exists \
  --topic unstructured-events --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1

docker exec kafka kafka-topics --create --if-not-exists \
  --topic dlq-intelligence-stream --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

docker exec kafka kafka-topics --create --if-not-exists \
  --topic raw-telemetry-stream --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1
```

### 4. Python 환경과 API 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn apps.backend_api.main:app --reload --port 8001
```

다른 터미널에서 API를 확인합니다.

```bash
curl http://localhost:8001/health
curl -N http://localhost:8001/api/v1/stream/metrics
curl -X POST http://localhost:8001/api/v1/agents/heal \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"evt-9012","target_agent":"SchemaAgent"}'

curl http://localhost:8001/api/v1/dlq/events
curl http://localhost:8001/api/v1/dlq/events/evt-schema-001
curl -X POST http://localhost:8001/api/v1/dlq/events/evt-schema-001/decision \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approve"}'
```

`/health`는 서비스 상태를, `/api/v1/stream/metrics`는 1초 간격의 SSE 메트릭을 반환합니다. `/api/v1/dlq/events`는 검토 대상 목록·상세를 제공하고, `decision` API는 승인 또는 보류 결정을 감사 로그에 남깁니다. 현재 DLQ API는 데모 fixture를 메모리에 보관하며, Kafka 재투입은 승인 이력과 분리된 다음 확장 단계입니다.

### DLQ 복구 안전 흐름

DLQ 복구 판단은 다음 단계로 처리합니다.

```text
오류 이벤트 → 구조화된 원인 분류 → 수정 제안과 diff → Pydantic 검증 → 운영자 승인 또는 보류
```

- `schema_error`이고 검증을 통과한 제안만 `pending` 승인 대기 상태가 됩니다.
- 필수 비즈니스 값이 누락됐거나 JSON을 안전하게 복원할 수 없는 이벤트는 `on_hold`로 격리합니다.
- LLM이 제안한 결과는 서버의 이벤트 스키마 검증을 반드시 통과해야 하며, 검증 통과만으로 자동 재처리하지 않습니다.

### 5. 대시보드 실행

```bash
cd apps/dashboard
pnpm install
pnpm dev
```

브라우저에서 `http://localhost:3000`을 엽니다. 현재 대시보드의 차트와 복구 로그는 데모용 시뮬레이션 데이터이며, API 연동은 이후 확장 지점입니다.

### 6. 로컬 스트림 실행 (선택)

Kafka 커넥터 JAR가 `.flink/lib/flink-sql-connector-kafka-3.1.0-1.18.jar`에 있어야 합니다. 다른 위치라면 `FLINK_KAFKA_CONNECTOR_JAR`로 지정합니다.

```bash
python scripts/produce_events.py
# 별도 터미널
python jobs/streaming_pipeline_job.py
```

## 테스트

의존성을 설치한 가상환경에서 다음 명령으로 단위·통합 테스트를 실행합니다.

```bash
pytest tests/test_backend_api.py tests/test_dashboard_integration.py tests/test_schemas.py
pytest tests/test_agent_resilience.py
```

Docker 기반 전체 인프라 검증은 다음처럼 실행할 수 있습니다.

```bash
docker compose -f docker-compose.test.yml up -d
pytest tests/infrastructure
docker compose -f docker-compose.test.yml down
```

vLLM·Kafka·ClickHouse·Neo4j까지 포함한 E2E 흐름은 추가 자원과 모델 다운로드가 필요합니다.

```bash
python scripts/run_e2e_test.py
```

실패 시에는 `docker compose ps`, `docker compose logs <서비스명>`, Flink UI와 애플리케이션 로그를 함께 확인합니다.

## 주요 접속 주소

| 서비스           | 주소                                     |
| ---------------- | ---------------------------------------- |
| FastAPI 문서     | `http://localhost:8001/docs`             |
| Next.js 대시보드 | `http://localhost:3000`                  |
| Flink UI         | `http://localhost:8081`                  |
| Grafana          | `http://localhost:${GRAFANA_PORT}`       |
| Prometheus       | `http://localhost:9090`                  |
| Jaeger           | `http://localhost:16686`                 |
| MinIO Console    | `http://localhost:${MINIO_CONSOLE_PORT}` |
| Neo4j Browser    | `http://localhost:7474`                  |

### DLQ 복구 지표 수집

- `apps/dlq_healing_agent/src/metrics.py`에 DLQ 복구 시도 횟수, 복구 처리 시간, 서킷 브레이커 상태를 위한 Prometheus 메트릭을 추가했습니다.
- `apps/dlq_healing_agent/src/worker.py`의 `SchemaAgentWorker`가 복구 처리 과정에서 위 메트릭을 기록합니다.
- Prometheus 설정에 `dlq-healing-agent` 스크레이프 대상(`host.docker.internal:8002`)을 추가했습니다.

메트릭 서버만 별도로 실행하려면 다음 명령을 사용합니다.

```bash
python apps/dlq_healing_agent/src/worker.py
```

실행 후 `http://localhost:8002/metrics`에서 Prometheus 형식의 지표를 확인할 수 있습니다. Docker 환경과 운영체제에 따라 `host.docker.internal` 주소가 해석되지 않을 수 있으므로, 해당 경우 Prometheus의 스크레이프 대상을 실행 환경에 맞게 조정해야 합니다.

### 대시보드 실시간 연결

- 대시보드가 `/api/v1/stream/metrics` SSE 스트림을 구독해 TPS, DLQ 건수, 서킷 브레이커 상태를 표시하도록 확장했습니다.
- `evt-9012`를 대상으로 `SchemaAgent` 복구를 요청하는 수동 복구 버튼을 추가했습니다.
- API 기본 주소는 `NEXT_PUBLIC_API_URL` 환경 변수로 변경할 수 있으며, 지정하지 않으면 `http://localhost:8001`을 사용합니다.

현재 Backend API가 보내는 SSE 예제에는 `tps`만 포함되어 있습니다. `dlq_count`, `circuit_breaker_open`은 실제 메트릭 수집 로직과 연결할 때 표시됩니다.

### 검색 평가와 부하 확인

- `apps/retrieval/evaluator.py`에 vLLM 호환 Chat Completions API로 검색 문맥 관련도를 0~1 범위로 평가하는 `LLMJudgeEvaluator`를 추가했습니다.
- `scripts/evaluate_search.py`에 Golden Dataset 기반 GraphRAG 검색 평가 예제를 추가했습니다.
- `scripts/run_load_test.py`에 Kafka 더미 이벤트 100건 주입, API 상태 확인, 에이전트 검색 요청을 묶은 부하 확인 스크립트를 추가했습니다.
- `apps/backend_api/router/search.py`와 `apps/retrieval/tools.py`에 하이브리드 벡터·키워드 검색 및 Neo4j 그래프 컨텍스트 조회를 위한 에이전트 검색 구성 요소를 추가했습니다.

### Chaos Mesh 실험

- `k8s/experiments/network_delay_experiment.yaml`: vLLM 대상으로 2초 지연과 200ms 지터를 주입합니다.
- `k8s/experiments/pod_kill_experiment.yaml`: Kafka Pod 하나를 5분마다 종료하는 복원력 실험입니다.
- Argo CD 애플리케이션 이름을 `signalflow-platform`으로 변경했습니다.
