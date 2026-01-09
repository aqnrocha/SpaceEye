#!/bin/bash

export AIRFLOW_HOME=~/airflow_se
export AIRFLOW__CORE__LOAD_EXAMPLES=False

source env/bin/activate

airflow standalone
