import json
import logging
from pyflink.common import Types, WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.functions import ProcessFunction
from pyflink.util import OutputTag

DLQ_TAG = OutputTag("dlq-side-output", Types.STRING())

class DataContractValidatorProcess(ProcessFunction):
    """
    In-flight Data Quality & Data Contract 검증 프로세서.
    스키마 미준수 사항 혹은 데이터 결함 시, DLQ Side Output으로 전송
    """

    def process_element(self, value, ctx):
        try:
          record = json.loads(value)

          event_id = record.get("event_id")
          timestamp = record.get("timestamp")
          content = record.get("content")

          if not event_id or not isinstance(event_id, str):
                raise ValueError("Data Contract Violation: 'event_id' is missing or not string.")
            
          if not timestamp or not isinstance(timestamp, int):
                raise ValueError("Data Contract Violation: Invalid or missing 'timestamp'.")

          if not content or len(content.strip()) == 0:
                raise ValueError("Data Quality Violation: Empty 'content' body.")
          
          yield value
        
        except Exception as e:
            error_payload = {
                "raw_data": value,
                "error_message": str(e),
                "failed_at": ctx.timestamp() if ctx.timestamp() else 0
            }
            ctx.output(DLQ_TAG, json.dumps(error_payload))

def run_contract_and_dlq_pipeline():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers("kafka:9092") \
        .set_topics("raw-intelligence-stream") \
        .set_group_id("contract-validator-group") \
        .set_value_only_deserializer(JsonRowDeserializationSchema.builder().build()) \
        .build()

    stream = env.from_source(kafka_source, WatermarkStrategy.no_watermarks(), "Kafka Source")

    validated_stream = stream.process(DataContractValidatorProcess(), output_type_or_type_information=Types.STRING())

    main_sink = KafkaSink.builder() \
        .set_bootstrap_servers("kafka:9092") \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
                .set_topic("validated-intelligence-stream")
                .set_value_serialization_schema(JsonRowDeserializationSchema.builder().build())
                .build()
        ) \
        .build()
    
    validated_stream.sink_to(main_sink)

    dlq_stream = validated_stream.get_side_output(DLQ_TAG)

    dlq_sink = KafkaSink.builder() \
        .set_bootstrap_servers("kafka:9092") \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
                .set_topic("dlq-intelligence-stream")
                .set_value_serialization_schema(JsonRowDeserializationSchema.builder().build())
                .build()
        ) \
        .build()
    
    dlq_stream.sink_to(dlq_sink)
    env.execute("Flink Schema Validation & DLQ Pipeline")

if __name__ == "__main__":
    run_contract_and_dlq_pipeline()
