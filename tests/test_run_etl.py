from tempfile import TemporaryDirectory

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession, Row
import pytest

from src.run_etl import create_silver_table


@pytest.fixture
def spark() -> SparkSession:
    packages = ["io.delta:delta-spark_2.13:3.2.1"]
    builder = SparkSession.builder\
        .appName("test_etl_script")\
        .master("local[*]")\
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")\
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

    yield configure_spark_with_delta_pip(builder, extra_packages=packages).getOrCreate()

@pytest.fixture
def temp_file() -> str:
    data = [
        '{"id": 1, "name": "Michael Scott", "title": "Regional Manager"}',
        '{"id": 2, "name": "Dwight Schrute", "title": "Assistant to the Regional Manager"}',
        '{"id": 3, "name": "Jim Halpert", "title": "Number Two"}',
    ]

    with TemporaryDirectory() as temp_dir:
        file_name = f"{temp_dir}/employees.json"
        with open(file_name, "w") as f:
            f.write("\n".join(data))
        yield file_name


def test_create_silver_table(spark, temp_file):
    create_silver_table(temp_file, spark)

    silver_table = spark.table("job_lakehouse.employees").collect()

    assert len(silver_table) == 2
    assert silver_table == [
        Row(id=1, name="Michael Scott", title="Regional Manager"),
        Row(id=2, name="Dwight Schrute", title="Assistant to the Regional Manager"),
        Row(id=3, name="Jim Halpert", title="Number Two")
    ]
