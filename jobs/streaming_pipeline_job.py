import logging
import os
import sys
from pathlib import Path

# ``python jobs/streaming_pipeline_job.py``로 실행해도 프로젝트 루트의
# ``jobs``와 ``schemas`` 패키지를 찾을 수 있도록 경로를 보정한다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import Configuration
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer

from jobs.deserializers.protobuf_deserializer import ProtobufEventParser
from jobs.processors.dq_evaluator import DataQualityEvaluator, DLQ_TAG
from jobs.processors.vllm_operator import VLLMEmbeddingOperator
from jobs.sinks.clickhouse_sink import ClickHouseVectorSink
from jobs.sinks.neo4j_sink import Neo4jGraphSink

logging.basicConfig(level=logging.INFO)


def run_pipeline():
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "unstructured-events")
    kafka_group_id = os.getenv("KAFKA_GROUP_ID", "signalflow-flink-group-v2")
    kafka_offset_reset = os.getenv("KAFKA_OFFSET_RESET", "latest")
    default_kafka_connector_jar = (
        PROJECT_ROOT
        / ".flink"
        / "lib"
        / "flink-sql-connector-kafka-3.1.0-1.18.jar"
    )
    kafka_connector_jar = Path(
        os.getenv("FLINK_KAFKA_CONNECTOR_JAR", str(default_kafka_connector_jar))
    ).expanduser()

    if not kafka_connector_jar.is_file():
        raise FileNotFoundError(
            "Kafka connector JAR을 찾을 수 없습니다. "
            "FLINK_KAFKA_CONNECTOR_JAR 환경 변수를 설정하거나 "
            f"{default_kafka_connector_jar}에 "
            "flink-sql-connector-kafka-3.1.0-1.18.jar를 저장하세요."
        )

    # Flink 작업자도 현재 Python 환경에서 사용자 정의 연산자를 실행한다.
    config = Configuration()
    config.set_string("python.executable", sys.executable)
    config.set_string("python.client.executable", sys.executable)

    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.set_parallelism(1)

    # add_jars는 HTTPS 주소가 아니라 로컬 file:// URI만 안정적으로 처리한다.
    env.add_jars(kafka_connector_jar.resolve().as_uri())

    kafka_consumer = FlinkKafkaConsumer(
        topics=kafka_topic,
        deserialization_schema=SimpleStringSchema(),
        properties={
            "bootstrap.servers": kafka_bootstrap_servers,
            "group.id": kafka_group_id,
            "auto.offset.reset": kafka_offset_reset,
        },
    )

    raw_stream = env.add_source(kafka_consumer)
    protobuf_stream = raw_stream.map(ProtobufEventParser())
    dq_processed_stream = protobuf_stream.process(DataQualityEvaluator())

    dlq_stream = dq_processed_stream.get_side_output(DLQ_TAG)
    dlq_stream.print()

    embedded_stream = dq_processed_stream.map(VLLMEmbeddingOperator())

    embedded_stream.map(Neo4jGraphSink())
    embedded_stream.map(ClickHouseVectorSink())

    env.execute("SignalFlow-vLLM-Streaming-Pipeline")

if __name__ == "__main__":
    run_pipeline()
