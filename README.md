# SignalFlow

## 개요

다량 건의 비정형 텍스트/이벤트 스트림을 밀리초(ms) 단위의 지연 시간으로 수집/정제하고, Data Quality 자동 모니터링과
ACID 레이크하우스 및 LLM RAG/Knowledge Graph 서빙 레이어를 통합한 대규모 실시간 데이터 플랫폼

### 프로젝트 구조

```text
root/
├── README.md
├── docker-compose.yml          # 전체 로컬 데이터 인프라 정의
├── .env                        # 포트, 계정 정보, 환경 변수 통합 관리
│
├── apps/                       # 애플리케이션 및 소스 코드
│   ├── producer/               # Data Ingestion (더미/실제 프로듀서)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │       ├── main.py
│   │       └── generators.py
│   │
│   ├── flink_jobs/             # Real-time Stream Processing
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── src/
│   │   │   ├── jobs/
│   │   │   │   └── streaming_dedup.py
│   │   │   └── utils/
│   │   └── jars/               # Flink Connector Jars (Kafka, Iceberg 등)
│   │
│   └── quality_checker/        # Data Quality & Validation (Great Expectations/Soda)
│       ├── requirements.txt
│       └── checks/
│
├── infra/                      # 인프라 컴포넌트별 상세 설정 (Config & Scripts)
│   ├── minio/
│   │   └── init-buckets.sh     # Iceberg용 S3 버킷 자동 생성 스크립트
│   ├── clickhouse/
│   │   └── init.sql            # ClickHouse 데이터베이스/테이블 초기화
│   ├── elasticsearch/
│   │   └── mappings.json       # ES 인덱스 맵핑
│   ├── prometheus/
│   │   └── prometheus.yml      # Prometheus 스크랩 설정
│   └── grafana/
│       └── provisioning/       # 대시보드 및 데이터소스 자동 설정
│
└── orchestration/              # Batch & Pipeline Workflow (Airflow)
    ├── dags/
    │   └── daily_iceberg_compaction.py
    └── plugins/
```

### 기술 스택

- 1. Ingestion & Bus
  - **Kafka** : 초당 수천 ~ 수만 건의 비정형 이벤트 흡수 및 Loose Coupling 디커플링 구조 확보

- 2. Stream Processing
  - **Flink, PyFlink** : Event-Time 기반 Out-of-order 데이터 처리, Window Deduplication, State TTL 관리

- 3. Data Lakehouse
  - **Apache Iceberg, MinIO** : S3 API 기반 ACID 트랜잭선, Time Travel (시점 복구), Schema Evolution 보장

- 4. Serving & AI Layer
  - **ClickHouse, Elasticsearch, Neo4j** : OLAP 집계, Dense Vector 기반 Hybrid Search(RAG), Knowledge Graph

- 5. Data Quality & Obs.
  - **Prometheus, Grafana** : In-flight Drop Ratio, Processing Lag, Operator Throughput 실시간 관측성 확보

### 파이프라인 아키텍처

```text
[ Data Ingestion Layer ]
  - Web Scraper / News API / RSS Event Streams
        │
        ▼
  [ Apache Kafka ] ─── (Topic: raw-intelligence-stream)
        │
        ├───▶ [ Prometheus Exporter ] ──▶ [ Grafana Dashboard ] (Throughput, Lag, Drop Ratio)
        │
[ Stream Processing & DQ Layer ]
  - [ Apache Flink (PyFlink) ]
      ├── State TTL (1h) & Event-Time Windowing (Deduplication)
      └── In-flight Data Quality Gate (Validation & Drop filtering)
        │
        ├───────────────────────┬───────────────────────┐
        ▼                       ▼                       ▼
[ Storage & Serving Layer ]
┌─────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│ Apache Iceberg (MinIO)  │  │ ClickHouse             │  │ Elasticsearch & Neo4j  │
│ - Time Travel & Audit   │  │ - Real-time OLAP Metrics│ │ - Vector Hybrid Search │
│ - Parquet Data Lakehouse│  │ - Low-Latency Aggs     │  │ - Entity Knowledge Graph│
└─────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

### 실행 단계

#### 1. 컨테이너 실행

- `docker compose up -d`

#### 2. Kafka 토픽 실행

- `docker exec -it <kafka-container-id> kafka-topics --create --topic raw-intelligence-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1`

#### 3. Flink 대시보드 접속

---

### 주요 문제 해결 과정 및 Trouble-Shooting

#### 1. Upstream 이중 발송으로 인한 데이터 중복 및 Downstream RAG Index pollution

- **문제** : 네트워크 재시도 및 수집 스크랩퍼의 특성으로 동일한 `event_id`를 가진 중복 데이터가 10% 이상 유입되어,
  서빙 레이어의 계산 오차와 LLM Vector DB 중복 저장 발생

- **해결** :
  - Flink SQL의 `ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ts ASC)` 구문을 적용하여 가장 먼저 유입된 이벤트만 필터링 하는 **Deduplication Pipeline** 구축
  - State 메모리 오버 사용을 방지하고자 `table.exec.state.ttl=1h`를 설정하여 1시간 경과한 Key의 State를 자동으로 Eviction

- **결과** : 중복 수신율 절감, Flink TaskManager 메모리 사용량 안정화 (특정 Peak 구간 대비 State Memory 65% 절감)

#### 2. In-flight Data Quality 검증 및 장애 복구(Time Travel) 체계 미비

- **문제** : Upstream API의 임의 스키마 변경 및 Null ID 유입으로 파이프라인 하위 게층 전체 멈춤 및 검색 인덱스 훼손 현상 발생.

- **해결** :
  - Flink 내부에 Data Quality Gate를 배치하여 필수 키 결측치, 미래 시점 Timestamp 등 비정상 데이터를 파이프라인 상위 계층에서 즉시 Drop 처리.
  - 데이터 레이크하우스로 Apache Iceberg를 도입하여 롤백이 필요한 경우 Time Travel Snapshot Rollback을 실행할 수 있는 백업/복구 절차 매뉴얼화.
  - Drop 비율 및 Consumer Lag 지표를 Prometheus 커스텀 메트릭으로 노출하고 Grafana 대시보드 자동 프로비저닝 구축.

- **결과** : Data Quality 오류로 인한 Downstream 장애 건수 감소, P99 Pipeline Processing Latency 300ms 이내 보장.
