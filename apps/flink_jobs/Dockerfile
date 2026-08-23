FROM flink:1.18.0-scala_2.12

# Required Python & Necessary Utilities
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Required Flink Connector & AWS S3/Iceberg JAR Package
RUN wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.1-1.18/flink-sql-connector-kafka-3.0.1-1.18.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.18/1.4.2/iceberg-flink-runtime-1.18-1.4.2.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.261/aws-java-sdk-bundle-1.12.261.jar

WORKDIR /opt/flink

COPY requirments.txt /opt/flink/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ /opt/flink/src/

CMD ["python3", "/opt/flink/src/jobs/validator_dlq_pipeline.py"]
