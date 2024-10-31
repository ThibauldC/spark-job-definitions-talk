from pyspark.sql import SparkSession

def create_silver_table(path: str, spark_session: SparkSession | None = None) -> None:
    spark = spark_session or SparkSession.builder.getOrCreate()
    df = spark.read.json(path)

    spark.sql("CREATE SCHEMA IF NOT EXISTS job_lakehouse")
    df.write.format("delta").saveAsTable("job_lakehouse.employees")

if __name__ == "__main__":
    create_silver_table("Files/employees.json")
