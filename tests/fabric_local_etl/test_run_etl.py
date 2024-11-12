from tempfile import TemporaryDirectory

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, StringType, LongType
import pytest

from fabric_local_etl.run_etl import ingest_employees


@pytest.fixture
def spark() -> SparkSession:
    packages = ["io.delta:delta-spark_2.13:3.2.1"]
    with TemporaryDirectory() as temp_dir:
        builder = SparkSession.builder\
            .appName("test_etl_script")\
            .master("local[*]")\
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")\
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
            .config("spark.sql.warehouse.dir", temp_dir)

    yield configure_spark_with_delta_pip(builder, extra_packages=packages).getOrCreate()


@pytest.fixture
def employee_table(spark):
    data = [(1, "Michael Scott", "Regional Manager")]
    schema = StructType([
        StructField("id", LongType(), False),
        StructField("name", StringType(), False),
        StructField("title", StringType(), False),
    ])
    df = spark.createDataFrame(schema=schema, data=data)
    spark.sql("CREATE SCHEMA IF NOT EXISTS fake_schema")
    df.write.format("delta").saveAsTable("fake_schema.employees")
    yield ""
    spark.sql("DROP TABLE fake_schema.employees")


@pytest.fixture
def temp_file() -> str:
    data = [
        '{"id": 2, "name": "Dwight Schrute", "title": "Assistant to the Regional Manager"}',
        '{"id": 3, "name": "Jim Halpert", "title": "Number Two"}',
    ]

    with TemporaryDirectory() as temp_dir:
        file_name = f"{temp_dir}/employees.json"
        with open(file_name, "w") as f:
            f.write("\n".join(data))
        yield file_name


def test_create_silver_table(spark, employee_table, temp_file):
    assert spark.table("fake_schema.employees").count() == 1
    ingest_employees(temp_file, spark)

    employees = spark.table("fake_schema.employees").orderBy("id").collect()

    assert employees == [
        Row(id=1, name="Michael Scott", title="Regional Manager"),
        Row(id=2, name="Dwight Schrute", title="Assistant to the Regional Manager"),
        Row(id=3, name="Jim Halpert", title="Number Two")
    ]
