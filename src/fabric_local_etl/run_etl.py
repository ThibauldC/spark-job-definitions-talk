from pyspark.sql import SparkSession

def ingest_employees(path: str, spark_session: SparkSession | None = None) -> None:
    spark = spark_session or SparkSession.builder.getOrCreate()
    df = spark.read.json(path)

    df.write.format("delta").mode("append").saveAsTable("job_lakehouse.employees")

if __name__ == "__main__":
    ingest_employees("Files/employees.json")
