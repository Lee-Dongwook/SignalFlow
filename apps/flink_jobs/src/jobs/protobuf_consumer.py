import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema

def build_flink_protobuf_pipeline():
    env = StreamExecutionEnvironment.get_execution_environment()

    env.enable_checkpointing(10000)
    env.get_checkpoint_config().set_checkpointing_mode(
        StreamExecutionEnvironment.CheckpointingMode.EXACTLY_ONCE
    )

    kafka_props = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        'group.id': 'signalflow_flink_processing_group',
        'auto.offset.reset': 'latest'
    }

    consumer = FlinkKafkaConsumer(
        topics='raw-telemetry-stream',
        deserialization_schema=SimpleStringSchema(), 
        properties=kafka_props
    )

    stream = env.add_source(consumer)

    env.execute("SingalFlow Protobuf Exact-Once Pipeline")

if __name__ == "__main__":
    build_flink_protobuf_pipeline()
