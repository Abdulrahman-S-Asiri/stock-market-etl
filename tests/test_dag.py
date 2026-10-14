"""DAG integrity tests. They need Airflow, so they run inside the Docker container."""

from pathlib import Path

import pytest

pytest.importorskip("airflow")  # skipped on Windows, where Airflow is not installed

from airflow.dag_processing.dagbag import DagBag

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"


@pytest.fixture(scope="module")
def dagbag():
    return DagBag(dag_folder=str(DAGS_DIR))


def test_dag_file_has_no_import_errors(dagbag):
    assert dagbag.import_errors == {}


def test_tasks_run_in_etl_order(dagbag):
    dag = dagbag.get_dag("stock_etl")

    assert dag.get_task("extract").downstream_task_ids == {"transform"}
    assert dag.get_task("transform").downstream_task_ids == {"load"}
    assert dag.get_task("load").downstream_task_ids == set()


def test_runs_one_at_a_time_without_catchup(dagbag):
    dag = dagbag.get_dag("stock_etl")

    assert dag.catchup is False
    assert dag.max_active_runs == 1
