import sys
from pyspark.sql import SparkSession

def compact_iceberg_table(catalog_name, db_name, table_name):
    full_table_name = f"{catalog_name}.{db_name}.{table_name}"
    print(f"Starting Compaction for Iceberg Table: {full_table_name}")

    spark = SparkSession.builder \
        .appName(f"IcebergCompaction_{db_name}_{table_name}") \
        .getOrCreate()
    
    compaction_sql = f"""
       CALL {catalog_name}.system.rewrite_data_files(
            table => '{db_name}.{table_name}',
            options => map(
                'target-file-size-bytes', '134217728',
                'min-input-files', '5'
            )
       )
    """

    print(f"Running SQL: {compaction_sql}")
    compaction_result = spark.sql(compaction_sql)
    compaction_result.show(truncate=False)

    expire_sql = f"""
        CALL {catalog_name}.system.expire.snapshots(
            table => '{db_name}.{table_name}'
            older_than => TIMESTAMPADD(DAY, -1, CURRENT_TIMESTAMP())
        )
    """
    print(f"Running Shanpshot Cleanup: {expire_sql}")
    expire_result = spark.sql(expire_sql)
    expire_result.show(truncate=False)

    spark.stop()
    print("Compaction and Maintenance Completed Successfully.")

if __name__ == "__main__" :
    catalog = sys.argv[1] if len(sys.argv) > 1 else "iceberg_catalog"
    db = sys.argv[2] if len(sys.argv) > 2 else "intelligence"
    table = sys.argv[3] if len(sys.argv) > 3 else "valid_events_iceberg"

    compact_iceberg_table(catalog, db, table)
