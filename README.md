# SignalFlow

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

### 실행 단계

#### 1. 컨테이너 실행

- `docker compose up -d`

#### 2. Kafka 토픽 실행

- `docker exec -it <kafka-container-id> kafka-topics --create --topic raw-intelligence-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1`

#### 3. Flink 대시보드 접속
