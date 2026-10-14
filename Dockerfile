# Official Airflow image (same Python as the local .venv) + this project's packages.
FROM apache/airflow:3.3.2-python3.13

COPY requirements.txt /requirements.txt

# Installing apache-airflow in the same command stops pip from changing Airflow's own version.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
