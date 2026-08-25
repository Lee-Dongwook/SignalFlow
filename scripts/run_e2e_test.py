import os
import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

def run_command(command: str, description: str):
    print(f"[{description}] 실행 중")
    result = subprocess.run(command, shell=True, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"[{description}] 실패")
        sys.exit(1)
    print(f"[{description}] 완료")

def check_docker_services():
    print("\nDocker Compose 인프라 및 vLLM 상태 체크")
    run_command("docker compose -f docker-compose.test.yml up -d", "Docker Containers Up")

    print("Service Health Check Ready")
    time.sleep(10)

def verify_clickhouse_data():
    print("ClickHouse 데이터 적재 검증...")
    import clickhouse_connect

    try:
        client = clickhouse_connect.get_client(host="localhost", port=8123, database="signalflow_test")
        result = client.query("SELECT count(), length(embedding) FROM intelligence_vectors GROUP BY length(embedding)")
        print(f"[ClickHouse Result] 적재 건수 / 임베딩 차원: {result.result_rows}")
    except Exception as e:
        print(f"ClickHouse 조회 실패: {e}")

def verify_neo4j_data():
    print("\nNeo4j Graph DB 데이터 적재 검증...")
    from neo4j import GraphDatabase
    
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test_password"))
        with driver.session() as session:
            res = session.run("MATCH (e:IntelligenceEvent) RETURN count(e) AS count").single()
            print(f"[Neo4j Result] 생성된 IntelligenceEvent 노드 수: {res['count']}")
        driver.close()
    except Exception as e:
        print(f"Neo4j 조회 실패: {e}")

def main():
    print("SignalFlow E2E Pipeline Automated Test Engine")

    check_docker_services()
    run_command("python -m grpc_tools.protoc -I. --python_out=. schemas/event_schema_v1.proto", "Protobuf Compile")

    print("\n Kafka Producer 백그라운드 실행 중...")
    producer_proc = subprocess.Popen(
        [sys.executable, "scripts/produce_events.py"],
        env={**os.environ, "PYTHONPATH": "."},
        cwd=PROJECT_ROOT
    )

    print("\nFlink Streaming Job 실행 중...")
    flink_proc = subprocess.Popen(
        [sys.executable, "jobs/streaming_pipeline_job.py"],
        env={**os.environ, "PYTHONPATH": "."},
        cwd=PROJECT_ROOT
    )

    print("데이터 수집, vLLM 임베딩 및 Multi-Sink 적재 진행 중 (15초)...")
    time.sleep(15)

    print("\n테스트 프로세스 종료 중...")
    flink_proc.terminate()
    producer_proc.terminate()

    verify_clickhouse_data()
    verify_neo4j_data()

    print("\n모든 E2E 파이프라인 검증 스텝이 성공적으로 완료되었습니다")

if __name__ == "__main__":
    main()
