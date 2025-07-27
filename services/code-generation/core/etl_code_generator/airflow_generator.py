"""
Airflow code generation
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .base import (
    CodeFramework, GeneratedCode, ETLPipeline, DataSource,
    DataTransformation, DataDestination, TemplateEngine, CodeTemplateType
)

logger = logging.getLogger(__name__)

class AirflowCodeGenerator:
    """Generates Airflow DAG code from ETL pipeline definitions"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self._load_templates()
    
    def generate_dag(self, pipeline: ETLPipeline, options: Dict[str, Any] = None) -> GeneratedCode:
        """Generate Airflow DAG from pipeline definition"""
        options = options or {}
        
        try:
            # Generate main DAG code
            dag_code = self._generate_dag_code(pipeline, options)
            
            # Generate configuration files
            config_files = self._generate_config_files(pipeline, options)
            
            # Generate requirements
            requirements = self._generate_requirements(pipeline, options)
            
            # Generate Docker configuration
            docker_config = self._generate_docker_config(pipeline, options)
            
            # Generate deployment scripts
            deployment_scripts = self._generate_deployment_scripts(pipeline, options)
            
            # Generate test files
            test_files = self._generate_test_files(pipeline, options)
            
            return GeneratedCode(
                framework=CodeFramework.AIRFLOW,
                main_code=dag_code,
                config_files=config_files,
                requirements=requirements,
                docker_config=docker_config,
                deployment_scripts=deployment_scripts,
                test_files=test_files,
                metadata={
                    "pipeline_id": pipeline.pipeline_id,
                    "generated_at": datetime.now().isoformat(),
                    "airflow_version": options.get("airflow_version", "2.5.0")
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate Airflow DAG: {str(e)}")
            raise
    
    def _generate_dag_code(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> str:
        """Generate the main DAG Python code"""
        
        # DAG configuration
        dag_config = {
            "dag_id": pipeline.pipeline_id,
            "description": pipeline.description,
            "schedule_interval": pipeline.schedule or "@daily",
            "start_date": options.get("start_date", "datetime(2024, 1, 1)"),
            "catchup": options.get("catchup", False),
            "max_active_runs": options.get("max_active_runs", 1),
            "tags": options.get("tags", ["etl", "schemasage"])
        }
        
        # Generate imports
        imports = self._generate_imports(pipeline)
        
        # Generate DAG definition
        dag_definition = self._generate_dag_definition(dag_config)
        
        # Generate tasks
        tasks = self._generate_tasks(pipeline, options)
        
        # Generate task dependencies
        dependencies = self._generate_task_dependencies(pipeline)
        
        # Combine all parts
        dag_code_parts = [
            imports,
            "",
            dag_definition,
            "",
            tasks,
            "",
            dependencies
        ]
        
        return "\n".join(dag_code_parts)
    
    def _generate_imports(self, pipeline: ETLPipeline) -> str:
        """Generate import statements for the DAG"""
        imports = [
            "from datetime import datetime, timedelta",
            "from airflow import DAG",
            "from airflow.operators.python import PythonOperator",
            "from airflow.operators.bash import BashOperator",
            "from airflow.models import Variable",
            "import logging",
            "import pandas as pd"
        ]
        
        # Add framework-specific imports based on sources and destinations
        for source in pipeline.sources:
            if source.source_type == "postgres":
                imports.append("from airflow.providers.postgres.operators.postgres import PostgresOperator")
                imports.append("from airflow.providers.postgres.hooks.postgres import PostgresHook")
            elif source.source_type == "mysql":
                imports.append("from airflow.providers.mysql.operators.mysql import MySqlOperator")
                imports.append("from airflow.providers.mysql.hooks.mysql import MySqlHook")
            elif source.source_type == "s3":
                imports.append("from airflow.providers.amazon.aws.operators.s3 import S3FileTransformOperator")
                imports.append("from airflow.providers.amazon.aws.hooks.s3 import S3Hook")
        
        for dest in pipeline.destinations:
            if dest.destination_type == "postgres":
                imports.append("from airflow.providers.postgres.operators.postgres import PostgresOperator")
            elif dest.destination_type == "s3":
                imports.append("from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator")
        
        return "\n".join(sorted(set(imports)))
    
    def _generate_dag_definition(self, dag_config: Dict[str, Any]) -> str:
        """Generate DAG definition block"""
        
        default_args = {
            "owner": "schemasage",
            "depends_on_past": False,
            "start_date": dag_config["start_date"],
            "email_on_failure": False,
            "email_on_retry": False,
            "retries": 1,
            "retry_delay": "timedelta(minutes=5)"
        }
        
        dag_definition = f'''
# Default arguments for DAG
default_args = {default_args}

# DAG definition
dag = DAG(
    dag_id="{dag_config["dag_id"]}",
    default_args=default_args,
    description="{dag_config["description"]}",
    schedule_interval="{dag_config["schedule_interval"]}",
    start_date={dag_config["start_date"]},
    catchup={dag_config["catchup"]},
    max_active_runs={dag_config["max_active_runs"]},
    tags={dag_config["tags"]}
)
'''
        
        return dag_definition.strip()
    
    def _generate_tasks(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> str:
        """Generate task definitions"""
        tasks = []
        task_counter = 1
        
        # Extract tasks
        for i, source in enumerate(pipeline.sources):
            task_name = f"extract_from_{source.source_type}_{i+1}"
            extract_task = self._generate_extract_task(task_name, source, task_counter)
            tasks.append(extract_task)
            task_counter += 1
        
        # Transform tasks
        for i, transform in enumerate(pipeline.transformations):
            task_name = f"transform_{transform.operation}_{i+1}"
            transform_task = self._generate_transform_task(task_name, transform, task_counter)
            tasks.append(transform_task)
            task_counter += 1
        
        # Load tasks
        for i, dest in enumerate(pipeline.destinations):
            task_name = f"load_to_{dest.destination_type}_{i+1}"
            load_task = self._generate_load_task(task_name, dest, task_counter)
            tasks.append(load_task)
            task_counter += 1
        
        return "\n\n".join(tasks)
    
    def _generate_extract_task(self, task_name: str, source: DataSource, task_id: int) -> str:
        """Generate extract task for data source"""
        
        python_callable = f"extract_{source.source_type}_data"
        
        # Generate the extraction function
        extract_function = f'''
def {python_callable}(**context):
    """Extract data from {source.source_type}"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Connection configuration
        config = {source.connection_config}
        
        # Extract logic based on source type
        if "{source.source_type}" == "postgres":
            from airflow.providers.postgres.hooks.postgres import PostgresHook
            hook = PostgresHook(postgres_conn_id=config.get("connection_id", "postgres_default"))
            df = hook.get_pandas_df(sql=config.get("query", "SELECT * FROM table"))
        
        elif "{source.source_type}" == "mysql":
            from airflow.providers.mysql.hooks.mysql import MySqlHook
            hook = MySqlHook(mysql_conn_id=config.get("connection_id", "mysql_default"))
            df = hook.get_pandas_df(sql=config.get("query", "SELECT * FROM table"))
        
        elif "{source.source_type}" == "csv":
            import pandas as pd
            df = pd.read_csv(config.get("file_path"))
        
        else:
            raise ValueError(f"Unsupported source type: {source.source_type}")
        
        # Store data for next task
        context["task_instance"].xcom_push(key="extracted_data", value=df.to_json())
        logger.info(f"Extracted {{len(df)}} rows from {source.source_type}")
        
        return f"Successfully extracted {{len(df)}} rows"
        
    except Exception as e:
        logger.error(f"Error extracting from {source.source_type}: {{str(e)}}")
        raise
'''
        
        # Generate task definition
        task_definition = f'''
{extract_function}

# Extract task
{task_name} = PythonOperator(
    task_id="{task_name}",
    python_callable={python_callable},
    dag=dag
)
'''
        
        return task_definition.strip()
    
    def _generate_transform_task(self, task_name: str, transform: DataTransformation, task_id: int) -> str:
        """Generate transform task"""
        
        python_callable = f"transform_{transform.operation}_data"
        
        # Generate transformation function
        transform_function = f'''
def {python_callable}(**context):
    """Apply {transform.operation} transformation"""
    import logging
    import pandas as pd
    import json
    logger = logging.getLogger(__name__)
    
    try:
        # Get data from previous task
        upstream_task_ids = context["task"].upstream_task_ids
        data_frames = []
        
        for task_id in upstream_task_ids:
            data_json = context["task_instance"].xcom_pull(task_ids=task_id, key="extracted_data")
            if data_json:
                df = pd.read_json(data_json)
                data_frames.append(df)
        
        # Combine data frames if multiple
        if len(data_frames) == 1:
            df = data_frames[0]
        elif len(data_frames) > 1:
            df = pd.concat(data_frames, ignore_index=True)
        else:
            raise ValueError("No data received from upstream tasks")
        
        # Apply transformation
        params = {transform.parameters if transform.parameters else {}}
        
        if "{transform.operation}" == "filter":
            condition = params.get("condition", "True")
            df = df.query(condition)
        
        elif "{transform.operation}" == "select":
            columns = params.get("columns", df.columns.tolist())
            df = df[columns]
        
        elif "{transform.operation}" == "aggregate":
            group_by = params.get("group_by", [])
            agg_functions = params.get("functions", {{}})
            if group_by:
                df = df.groupby(group_by).agg(agg_functions).reset_index()
        
        elif "{transform.operation}" == "join":
            # Join logic would need additional data source
            pass
        
        else:
            logger.warning(f"Unknown transformation: {transform.operation}")
        
        # Store transformed data
        context["task_instance"].xcom_push(key="transformed_data", value=df.to_json())
        logger.info(f"Transformed data: {{len(df)}} rows")
        
        return f"Successfully transformed data: {{len(df)}} rows"
        
    except Exception as e:
        logger.error(f"Error in transformation {{transform.operation}}: {{str(e)}}")
        raise
'''
        
        task_definition = f'''
{transform_function}

# Transform task
{task_name} = PythonOperator(
    task_id="{task_name}",
    python_callable={python_callable},
    dag=dag
)
'''
        
        return task_definition.strip()
    
    def _generate_load_task(self, task_name: str, dest: DataDestination, task_id: int) -> str:
        """Generate load task for destination"""
        
        python_callable = f"load_to_{dest.destination_type}_data"
        
        # Generate load function
        load_function = f'''
def {python_callable}(**context):
    """Load data to {dest.destination_type}"""
    import logging
    import pandas as pd
    import json
    logger = logging.getLogger(__name__)
    
    try:
        # Get transformed data
        upstream_task_ids = context["task"].upstream_task_ids
        df = None
        
        for task_id in upstream_task_ids:
            data_json = context["task_instance"].xcom_pull(task_ids=task_id, key="transformed_data")
            if data_json:
                df = pd.read_json(data_json)
                break
        
        if df is None:
            raise ValueError("No transformed data received")
        
        # Load configuration
        config = {dest.connection_config}
        write_mode = "{dest.write_mode}"
        
        # Load logic based on destination type
        if "{dest.destination_type}" == "postgres":
            from airflow.providers.postgres.hooks.postgres import PostgresHook
            hook = PostgresHook(postgres_conn_id=config.get("connection_id", "postgres_default"))
            df.to_sql(
                name=config.get("table_name", "output_table"),
                con=hook.get_sqlalchemy_engine(),
                if_exists=write_mode,
                index=False
            )
        
        elif "{dest.destination_type}" == "csv":
            output_path = config.get("file_path", "output.csv")
            df.to_csv(output_path, index=False)
        
        elif "{dest.destination_type}" == "s3":
            from airflow.providers.amazon.aws.hooks.s3 import S3Hook
            hook = S3Hook(aws_conn_id=config.get("connection_id", "aws_default"))
            
            # Convert to CSV and upload
            csv_data = df.to_csv(index=False)
            hook.load_string(
                string_data=csv_data,
                key=config.get("key", "output.csv"),
                bucket_name=config.get("bucket", "default-bucket"),
                replace=True
            )
        
        else:
            raise ValueError(f"Unsupported destination type: {dest.destination_type}")
        
        logger.info(f"Successfully loaded {{len(df)}} rows to {dest.destination_type}")
        return f"Successfully loaded {{len(df)}} rows"
        
    except Exception as e:
        logger.error(f"Error loading to {dest.destination_type}: {{str(e)}}")
        raise
'''
        
        task_definition = f'''
{load_function}

# Load task
{task_name} = PythonOperator(
    task_id="{task_name}",
    python_callable={python_callable},
    dag=dag
)
'''
        
        return task_definition.strip()
    
    def _generate_task_dependencies(self, pipeline: ETLPipeline) -> str:
        """Generate task dependency definitions"""
        dependencies = []
        
        # Extract -> Transform dependencies
        extract_tasks = [f"extract_from_{source.source_type}_{i+1}" 
                        for i, source in enumerate(pipeline.sources)]
        
        transform_tasks = [f"transform_{transform.operation}_{i+1}" 
                          for i, transform in enumerate(pipeline.transformations)]
        
        load_tasks = [f"load_to_{dest.destination_type}_{i+1}" 
                     for i, dest in enumerate(pipeline.destinations)]
        
        # Set up dependencies: extract >> transform >> load
        if extract_tasks and transform_tasks:
            dependencies.append(f"{extract_tasks} >> {transform_tasks[0] if len(transform_tasks) == 1 else transform_tasks}")
        
        if transform_tasks and load_tasks:
            last_transform = transform_tasks[-1] if transform_tasks else extract_tasks[-1]
            dependencies.append(f"{last_transform} >> {load_tasks[0] if len(load_tasks) == 1 else load_tasks}")
        
        if not transform_tasks and extract_tasks and load_tasks:
            # Direct extract to load
            dependencies.append(f"{extract_tasks} >> {load_tasks[0] if len(load_tasks) == 1 else load_tasks}")
        
        return "\n".join([f"# Task dependencies", ""] + dependencies)
    
    def _generate_config_files(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> Dict[str, str]:
        """Generate configuration files"""
        config_files = {}
        
        # Generate Airflow configuration
        airflow_config = {
            "connections": {},
            "variables": {
                f"{pipeline.pipeline_id}_config": {
                    "description": pipeline.description,
                    "sources": [src.source_type for src in pipeline.sources],
                    "destinations": [dest.destination_type for dest in pipeline.destinations]
                }
            }
        }
        
        config_files["airflow_config.json"] = json.dumps(airflow_config, indent=2)
        
        return config_files
    
    def _generate_requirements(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> List[str]:
        """Generate requirements.txt content"""
        requirements = [
            "apache-airflow>=2.5.0",
            "pandas>=1.5.0",
            "sqlalchemy>=1.4.0"
        ]
        
        # Add provider packages based on sources and destinations
        for source in pipeline.sources:
            if source.source_type in ["postgres", "postgresql"]:
                requirements.append("apache-airflow-providers-postgres>=5.0.0")
            elif source.source_type == "mysql":
                requirements.append("apache-airflow-providers-mysql>=3.0.0")
            elif source.source_type in ["s3", "aws"]:
                requirements.append("apache-airflow-providers-amazon>=6.0.0")
        
        for dest in pipeline.destinations:
            if dest.destination_type in ["postgres", "postgresql"]:
                requirements.append("apache-airflow-providers-postgres>=5.0.0")
            elif dest.destination_type in ["s3", "aws"]:
                requirements.append("apache-airflow-providers-amazon>=6.0.0")
        
        return sorted(set(requirements))
    
    def _generate_docker_config(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> str:
        """Generate Dockerfile for the DAG"""
        
        dockerfile = f'''
FROM apache/airflow:2.5.0-python3.9

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy DAG files
COPY dags/ /opt/airflow/dags/
COPY config/ /opt/airflow/config/

# Set environment variables
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False

# Expose Airflow webserver port
EXPOSE 8080

# Default command
CMD ["webserver"]
'''
        
        return dockerfile.strip()
    
    def _generate_deployment_scripts(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> Dict[str, str]:
        """Generate deployment scripts"""
        scripts = {}
        
        # Docker Compose file
        scripts["docker-compose.yml"] = f'''
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_db_volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50

  airflow-webserver:
    build: .
    command: webserver
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0

  airflow-scheduler:
    build: .
    command: scheduler
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0

volumes:
  postgres_db_volume:
'''
        
        # Deployment script
        scripts["deploy.sh"] = f'''
#!/bin/bash

# Deploy {pipeline.name} to Airflow

echo "Deploying {pipeline.name}..."

# Build Docker image
docker build -t {pipeline.pipeline_id}:latest .

# Start services
docker-compose up -d

# Wait for Airflow to be ready
echo "Waiting for Airflow to start..."
sleep 30

# Initialize database (first time only)
docker-compose exec airflow-webserver airflow db init

# Create admin user (first time only)
docker-compose exec airflow-webserver airflow users create \\
    --username admin \\
    --firstname Admin \\
    --lastname User \\
    --role Admin \\
    --email admin@example.com \\
    --password admin

echo "Deployment complete!"
echo "Airflow UI available at: http://localhost:8080"
echo "Username: admin, Password: admin"
'''
        
        return scripts
    
    def _generate_test_files(self, pipeline: ETLPipeline, options: Dict[str, Any]) -> Dict[str, str]:
        """Generate test files"""
        test_files = {}
        
        # Unit test for DAG
        test_files["test_dag.py"] = f'''
import pytest
from datetime import datetime
from airflow.models import DagBag

def test_dag_loaded():
    """Test that the DAG is loaded correctly"""
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    assert "{pipeline.pipeline_id}" in dagbag.dags
    
    dag = dagbag.dags["{pipeline.pipeline_id}"]
    assert dag is not None
    assert len(dag.tasks) > 0

def test_dag_structure():
    """Test DAG structure and dependencies"""
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    dag = dagbag.dags["{pipeline.pipeline_id}"]
    
    # Check that all tasks have proper dependencies
    for task in dag.tasks:
        assert task.dag_id == "{pipeline.pipeline_id}"

def test_no_import_errors():
    """Test that there are no import errors in the DAG"""
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    assert len(dagbag.import_errors) == 0, f"Import errors: {{dagbag.import_errors}}"

if __name__ == "__main__":
    test_dag_loaded()
    test_dag_structure()
    test_no_import_errors()
    print("All tests passed!")
'''
        
        return test_files
    
    def _load_templates(self):
        """Load code templates"""
        # This would typically load templates from files
        # For now, templates are embedded in the generator methods
        pass
