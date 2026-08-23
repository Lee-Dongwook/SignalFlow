# SignalFlow

## 개요

다량 건의 비정형 텍스트/이벤트 스트림을 밀리초(ms) 단위의 지연 시간으로 수집/정제하고, Data Quality 자동 모니터링과
ACID 레이크하우스 및 LLM RAG/Knowledge Graph 서빙 레이어를 통합한 대규모 실시간 데이터 플랫폼

### 프로젝트 구조

```text
root/
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions CI/CD Pipeline
│
├── apps/                       # 애플리케이션 및 소스 코드
│   ├── producer/               # Data Ingestion (OpenTelemetry Trace Context 주입)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │       ├── main.py
│   │       └── generators.py
│   │
│   ├── flink_jobs/             # Real-time Stream Processing & DQ Gate
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │       └── jobs/
│   │           ├── dedup_and_quality_check.py
│   │           ├── validator_dlq_pipeline.py  # Schema Validation & DLQ Side Output
│   │           ├── flink_to_clickhouse.py     # ClickHouse JDBC Sink
│   │           └── kafka_to_iceberg.py
│   │
│   └── ai_indexer/             # Vector Indexer & Knowledge Graph Sink
│       ├── Dockerfile
│       └── indexer.py
│
├── schemas/
│   └── raw_event.avsc          # Confluent Schema Registry (Avro Data Contract)
│
├── scripts/
│   └── dlq_replay_job.py       # DLQ 격리 메시지 재처리(Replay) Worker
│
├── infra/                      # 인프라 컴포넌트별 상세 설정 (Config & Scripts)
│   ├── minio/
│   │   └── init-buckets.sh
│   ├── clickhouse/
│   │   └── init.sql            # Materialized View & SummingMergeTree DDL
│   ├── elasticsearch/
│   │   └── mappings.json
│   ├── neo4j/
│   │   └── schema.cypher
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
│
├── k8s/                        # GitOps Kubernetes Manifests (ArgoCD)
│   ├── application.yml
│   ├── flink-jobmanager.yml
│   └── flink-taskmanager.yml
│
└── orchestration/              # Batch & Pipeline Workflow (Airflow & dbt)
    ├── dags/
    │   ├── daily_iceberg_compaction.py # Small File Compaction & Expiry DAG
    │   └── dbt_spark_batch_dag.py      # Star Schema 차원 모델링 DAG
    ├── dbt/                    # dbt Spark-Iceberg 프로젝트
    │   ├── dbt_project.yml
    │   ├── profiles.yml
    │   └── models/
    │       ├── staging/
    │       └── marts/
    └── spark_jobs/
        └── iceberg_compaction.py
```

### 기술 스택

1.  Ingestion & Bus

- **Kafka** : 초당 수천 ~ 수만 건의 비정형 이벤트 흡수 및 Loose Coupling 디커플링 구조 확보
- **Confluent Schema Registry(Avro)**: Upstream 스키마 변경 감지 및 데이터 계약 (Data Contract) 강제

2.  Stream Processing

- **Flink, PyFlink** : Event-Time 기반 Deduplication, State TTL 관리, Side Output 기반 Dead Letter Queue(DLQ) 라우팅

3.  Data Lakehouse & Batch Modeling

- **Apache Iceberg, MinIO** : S3 API 기반 ACID 트랜잭선, Time Travel (시점 복구), Schema Evolution 보장
- **Spark & dbt** : Small File Compaction 자동화 및 Star Schema 기반 차원 모델링(Dimension & Fact Table)

4.  Serving & AI Layer

- **ClickHouse** : Materialized View 및 SummingMergeTree 기반 실시간 OLAP 집계 서빙
- **Elasticsearch, Neo4j** : Dense Vector 기반 Hybrid Search(RAG) 및 Entity Knowledge Graph 구축

5.  Data Quality & Observability & GitOps

- **Prometheus, Grafana** : In-flight Drop Ratio, Processing Lag, Operator Throughput 실시간 관측
- **OpenTelemetry & jaeger** : Producer - Flink - DB 전 구간 W3C Context 주입 기반 Distributed Tracing.
- **Github Actions & ArgoCD** : K8s Manifest 연동 기반 무중단 GitOps CI/CD 배포 자동화

### 파이프라인 아키텍처

```text
[ Data Ingestion Layer ]
  - Scraper / News API / RSS Streams (OTel Trace Context Injected)
        │
        ▼
  [ Apache Kafka ] ─── (Topic: raw-intelligence-stream)
        │
        ├───▶ [ Schema Registry ] (Avro Data Contract Validation)
        │
[ Stream Processing & DQ Layer ]
  - [ Apache Flink (PyFlink) ]
      ├── State TTL (1h) & Event-Time Windowing (Deduplication)
      ├── In-flight Data Quality Gate (Validation)
      └── Side Output ──▶ [ Kafka DLQ Topic ] ──▶ [ Replay Worker ]
        │
        ├───────────────────────┬───────────────────────┬───────────────────────┐
        ▼                       ▼                       ▼                       ▼
[ Storage, Serving & AI Layer ]
┌─────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│ Apache Iceberg (MinIO)  │  │ ClickHouse             │  │ Elasticsearch & Neo4j  │  │ OpenTelemetry / Jaeger │
│ - Time Travel & Audit   │  │ - Materialized View    │  │ - Vector Hybrid Search │  │ - E2E Distributed      │
│ - dbt Batch Star Schema │  │ - Low-Latency Aggs     │  │ - Entity Knowledge Graph│ │   Tracing Observability│
└─────────────────────────┘  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

### 실행 단계

#### 1. 인프라 컨테이너 구동

`docker compose up -d`

#### 2. Kafka 토픽 및 DLQ 토픽 생성

```
docker exec -it kafka kafka-topics --create --topic raw-intelligence-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

docker exec -it kafka kafka-topics --create --topic dlq-intelligence-stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

#### 3. ArgoCD GitOps 배포 적용

```
kubectl apply -f k8s/application.yml
```

#### 4. 대시보드 및 모니터링 접속

- Flink UI: http://localhost:8081

- Grafana: http://localhost:3000

- Jaeger UI (Tracing): http://localhost:16686

- ArgoCD UI: http://localhost:8080

---

### 주요 문제 해결 과정 및 Trouble-Shooting

#### 1. Upstream 이중 발송으로 인한 데이터 중복 및 Downstream RAG Index pollution

- **문제** : 네트워크 재시도 및 수집 스크랩퍼의 특성으로 동일한 `event_id`를 가진 중복 데이터가 10% 이상 유입되어,
  서빙 레이어의 계산 오차와 LLM Vector DB 중복 저장 발생

- **해결** :
  - Flink SQL의 `ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ts ASC)` 구문을 적용하여 가장 먼저 유입된 이벤트만 필터링 하는 **Deduplication Pipeline** 구축
  - State 메모리 오버 사용을 방지하고자 `table.exec.state.ttl=1h`를 설정하여 1시간 경과한 Key의 State를 자동으로 Eviction

- **결과** : 중복 수신율 절감, Flink TaskManager 메모리 사용량 안정화 (특정 Peak 구간 대비 State Memory 65% 절감)

#### 2. Upstream 임의 스키마 변경 대응 및 내결함성(DLQ) 확보

- **문제** : Upstream API의 임의 스키마 변경 및 Null 유입 발생 시 Flink 파이프라인 전체가 멈추거나 (Crash Loop), Downstream DB로 비정상 데이터가 적재되는 현상 발생.

- **해결** :
  - Schema Registry(Avro) 기반 데이터 계약을 체결하고, Flink 내부에 ProcessFunction + Side Output 패턴을 구현해 결함 데이터를 Kafka DLQ Topic으로 실시간 분기 처리.
  - 에러 메타데이터가 포함된 DLQ 메시지를 복구하여 메인 토픽으로 다시 보낼 수 있는 DLQ Replay Worker 파이프라인 세팅.

- **결과** : 파이프라인 다운타임 0건 유지, 데이터 손실 없는 내결함성(Fault-tolerance) 체계 구축.

#### 3. Iceberg 레이크하우스 Small File Problem 및 Read Latency 저하

- **문제** : 초 단위로 실시간 무중단 적재되는 Flink Iceberg Sink 특성상 수 KB 크기의 Small Parquet 파일이 기하급수적으로 증가하여 배치 분석 및 쿼리 속도 심각하게 저하.

- **해결** :
  - Airflow 기반 PySpark Compaction DAG를 구축하여 매일 새벽 소형 파일들을 128MB 표준 Parquet 파일로 병합(rewrite_data_files).
  - 24시간이 지난 구 스냅샷 및 Orphan Files을 자동 정제(expire_snapshots)하는 리텐션 주기 적용.

- **결과** : 파일 수 90% 이상 감소 및 Iceberg 레이크하우스 쿼리 Read Latency 대폭 단축.

#### 4. 실시간 집계 쿼리 병목 해소 및 서빙 속도 개선

- **문제** : 대시보드 API 요청 시마다 Raw 테이블 전체 대상 GROUP BY 실시간 집계 쿼리가 실행되어 서빙 지연 시간 증가.

- **해결** :
  - ClickHouse의 Materialized View와 SummingMergeTree 엔진을 조합하여, 쓰기 시점에 1분 단위 집계를 미리 연산하도록 서빙 레이어 구조 변경.

- **결과** : API 조회 쿼리 Latency를 500ms 이상에서 10ms 미만으로 극적 단축.
