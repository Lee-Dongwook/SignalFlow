from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer

from jobs.deserializers.protobuf_deserializer import IntelligenceEventDeserializer
from jobs.processors.dq_evaluator import DataQualityEvaluator, DLQ_TAG
from jobs.processors.vllm_operator import VLLMEmbeddingOperator
from jobs.sinks.clickhouse_sink import ClickHouseVectorSink
from jobs.sinks.neo4j_sink import Neo4jGraphSink

def run_pipeline():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    kafka_consumer = FlinkKafkaConsumer(
        topics="unstructured-events",
        deserialization_schema=IntelligenceEventDeserializer(),
        properties = {
            "bootstrap.servers": "localhost:9092",
            "group.id": "signalflow-flink-group"
        }
    )

    raw_stream = env.add_source(kafka_consumer)

    dq_processed_stream = raw_stream.process(DataQualityEvaluator())
    dlq_stream = dq_processed_stream.get_side_output(DLQ_TAG)
    dlq_stream.print()

    embedded_stream = dq_processed_stream.map(VLLMEmbeddingOperator())

    embedded_stream.add_sink(Neo4jGraphSink())
    embedded_stream.add_sink(ClickHouseVectorSink())

    env.execute("SignalFlow-vLLM-Streaming-Pipeline")

if __name__ == "__main__":
    run_pipeline()

