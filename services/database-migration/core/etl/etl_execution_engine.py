"""
ETL Execution Engine Module
Advanced ETL pipeline execution with support for large datasets and complex transformations.
"""
from typing import List, Dict, Any, Optional, AsyncGenerator, Callable
from datetime import datetime, timedelta
import asyncio
import json
import uuid

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.data_migration import (
    ETLPipeline, DataTransformation, DataMapping, 
    LargeDatasetStrategy, DataQualityRule,
    ETLExecution, TransformationType, DataQualityStatus
)
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import ETLExecutionError

logger = get_logger(__name__)

class ETLExecutionEngine:
    """Advanced ETL pipeline execution engine."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_executions: Dict[str, ETLExecution] = {}
        
    async def execute_pipeline(
        self, 
        pipeline: ETLPipeline,
        session: AsyncSession,
        progress_callback: Optional[Callable] = None
    ) -> ETLExecution:
        """Execute complete ETL pipeline."""
        
        execution = ETLExecution(
            pipeline_id=pipeline.pipeline_id,
            workspace_id=pipeline.workspace_id,
            source_connection_id=pipeline.source_connection_id,
            target_connection_id=pipeline.target_connection_id
        )
        
        self.active_executions[execution.execution_id] = execution
        
        try:
            # Pre-execution validation
            await self._validate_pipeline(pipeline, session)
            
            # Initialize execution
            execution.status = "running"
            execution.started_at = datetime.utcnow()
            
            if progress_callback:
                await progress_callback(0, "Starting pipeline execution")
            
            # Execute phases
            total_phases = len(pipeline.execution_phases)
            
            for phase_index, phase in enumerate(pipeline.execution_phases):
                logger.info(f"Executing phase {phase_index + 1}/{total_phases}: {phase.get('name', 'Unnamed')}")
                
                await self._execute_phase(pipeline, phase, execution, session)
                
                progress = ((phase_index + 1) / total_phases) * 100
                if progress_callback:
                    await progress_callback(progress, f"Completed phase {phase_index + 1}")
            
            # Post-execution validation
            await self._validate_results(pipeline, execution, session)
            
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
            
            logger.info(f"Pipeline execution completed: {execution.execution_id}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Pipeline execution failed: {e}")
            raise ETLExecutionError(f"Pipeline execution failed: {e}")
        
        finally:
            del self.active_executions[execution.execution_id]
        
        return execution
    
    async def _validate_pipeline(self, pipeline: ETLPipeline, session: AsyncSession):
        """Validate pipeline before execution."""
        
        # Check source connection
        source_conn = await self.db_manager.get_connection(pipeline.source_connection_id)
        if not source_conn:
            raise ETLExecutionError(f"Source connection not found: {pipeline.source_connection_id}")
        
        # Check target connection
        target_conn = await self.db_manager.get_connection(pipeline.target_connection_id)
        if not target_conn:
            raise ETLExecutionError(f"Target connection not found: {pipeline.target_connection_id}")
        
        # Validate data mappings
        for mapping in pipeline.data_mappings:
            await self._validate_mapping(mapping, source_conn, target_conn)
        
        # Validate transformations
        for transformation in pipeline.transformations:
            await self._validate_transformation(transformation)
    
    async def _execute_phase(
        self, 
        pipeline: ETLPipeline, 
        phase: Dict[str, Any], 
        execution: ETLExecution, 
        session: AsyncSession
    ):
        """Execute a single pipeline phase."""
        
        phase_type = phase.get("type")
        
        if phase_type == "extract":
            await self._execute_extract_phase(pipeline, phase, execution, session)
        elif phase_type == "transform":
            await self._execute_transform_phase(pipeline, phase, execution, session)
        elif phase_type == "load":
            await self._execute_load_phase(pipeline, phase, execution, session)
        elif phase_type == "validate":
            await self._execute_validate_phase(pipeline, phase, execution, session)
        else:
            raise ETLExecutionError(f"Unknown phase type: {phase_type}")
    
    async def _execute_extract_phase(
        self, 
        pipeline: ETLPipeline, 
        phase: Dict[str, Any], 
        execution: ETLExecution, 
        session: AsyncSession
    ):
        """Execute data extraction phase."""
        
        source_conn = await self.db_manager.get_connection(pipeline.source_connection_id)
        
        for mapping in pipeline.data_mappings:
            if mapping.source_table in phase.get("tables", []):
                
                # Apply large dataset strategy if needed
                if pipeline.large_dataset_strategy:
                    async for batch in self._extract_in_batches(
                        source_conn, mapping, pipeline.large_dataset_strategy
                    ):
                        execution.rows_extracted += len(batch)
                        # Store batch for transformation
                        await self._store_batch(execution.execution_id, mapping.source_table, batch)
                else:
                    # Standard extraction
                    data = await self._extract_table_data(source_conn, mapping)
                    execution.rows_extracted += len(data)
                    await self._store_batch(execution.execution_id, mapping.source_table, data)
    
    async def _extract_in_batches(
        self, 
        connection: Any, 
        mapping: DataMapping, 
        strategy: LargeDatasetStrategy
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Extract large datasets in batches."""
        
        batch_size = strategy.batch_size
        offset = 0
        
        while True:
            if strategy.partitioning_strategy:
                # Use partitioning strategy
                query = self._build_partitioned_query(mapping, strategy, offset, batch_size)
            else:
                # Use simple offset/limit
                query = f"""
                SELECT {', '.join(mapping.source_columns) if mapping.source_columns else '*'}
                FROM {mapping.source_table}
                ORDER BY {strategy.sort_column or '1'}
                LIMIT {batch_size} OFFSET {offset}
                """
            
            async with connection.execute(text(query)) as result:
                rows = await result.fetchall()
                
                if not rows:
                    break
                
                batch = [dict(row) for row in rows]
                yield batch
                
                offset += batch_size
                
                # Apply rate limiting if configured
                if strategy.rate_limit_delay_seconds > 0:
                    await asyncio.sleep(strategy.rate_limit_delay_seconds)
    
    async def _execute_transform_phase(
        self, 
        pipeline: ETLPipeline, 
        phase: Dict[str, Any], 
        execution: ETLExecution, 
        session: AsyncSession
    ):
        """Execute data transformation phase."""
        
        for transformation in pipeline.transformations:
            if transformation.target_table in phase.get("tables", []):
                
                # Load source data
                source_data = await self._load_batch(execution.execution_id, transformation.source_table)
                
                # Apply transformations
                transformed_data = await self._apply_transformations(source_data, transformation)
                
                # Store transformed data
                await self._store_batch(execution.execution_id, f"{transformation.target_table}_transformed", transformed_data)
                
                execution.rows_transformed += len(transformed_data)
    
    async def _apply_transformations(
        self, 
        data: List[Dict[str, Any]], 
        transformation: DataTransformation
    ) -> List[Dict[str, Any]]:
        """Apply transformation rules to data."""
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        for rule in transformation.transformation_rules:
            rule_type = rule.get("type")
            
            if rule_type == TransformationType.COLUMN_MAPPING:
                df = self._apply_column_mapping(df, rule)
            elif rule_type == TransformationType.DATA_TYPE_CONVERSION:
                df = self._apply_type_conversion(df, rule)
            elif rule_type == TransformationType.VALUE_TRANSFORMATION:
                df = self._apply_value_transformation(df, rule)
            elif rule_type == TransformationType.AGGREGATION:
                df = self._apply_aggregation(df, rule)
            elif rule_type == TransformationType.FILTERING:
                df = self._apply_filtering(df, rule)
            elif rule_type == TransformationType.CUSTOM_FUNCTION:
                df = await self._apply_custom_function(df, rule)
        
        return df.to_dict('records')
    
    def _apply_column_mapping(self, df: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        """Apply column mapping transformation."""
        mapping = rule.get("mapping", {})
        
        # Rename columns
        df = df.rename(columns=mapping)
        
        # Select only mapped columns if specified
        if rule.get("select_only_mapped", False):
            df = df[list(mapping.values())]
        
        return df
    
    def _apply_type_conversion(self, df: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        """Apply data type conversion."""
        conversions = rule.get("conversions", {})
        
        for column, target_type in conversions.items():
            if column in df.columns:
                try:
                    if target_type == "datetime":
                        df[column] = pd.to_datetime(df[column])
                    elif target_type == "numeric":
                        df[column] = pd.to_numeric(df[column], errors='coerce')
                    elif target_type == "string":
                        df[column] = df[column].astype(str)
                    elif target_type == "boolean":
                        df[column] = df[column].astype(bool)
                except Exception as e:
                    logger.warning(f"Type conversion failed for column {column}: {e}")
        
        return df
    
    async def _execute_load_phase(
        self, 
        pipeline: ETLPipeline, 
        phase: Dict[str, Any], 
        execution: ETLExecution, 
        session: AsyncSession
    ):
        """Execute data loading phase."""
        
        target_conn = await self.db_manager.get_connection(pipeline.target_connection_id)
        
        for mapping in pipeline.data_mappings:
            if mapping.target_table in phase.get("tables", []):
                
                # Load transformed data
                transformed_data = await self._load_batch(
                    execution.execution_id, 
                    f"{mapping.target_table}_transformed"
                )
                
                # Load to target database
                await self._load_to_target(target_conn, mapping, transformed_data)
                
                execution.rows_loaded += len(transformed_data)
    
    async def _execute_validate_phase(
        self, 
        pipeline: ETLPipeline, 
        phase: Dict[str, Any], 
        execution: ETLExecution, 
        session: AsyncSession
    ):
        """Execute data validation phase."""
        
        validation_results = []
        
        for rule in pipeline.data_quality_rules:
            result = await self._execute_quality_rule(rule, execution, session)
            validation_results.append(result)
            
            if result["status"] == DataQualityStatus.FAILED:
                execution.validation_errors.append(result)
        
        execution.data_quality_score = self._calculate_quality_score(validation_results)
    
    async def _execute_quality_rule(
        self, 
        rule: DataQualityRule, 
        execution: ETLExecution, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a single data quality rule."""
        
        try:
            target_conn = await self.db_manager.get_connection(execution.target_connection_id)
            
            # Execute validation query
            async with target_conn.execute(text(rule.validation_query)) as result:
                validation_result = await result.fetchone()
            
            # Check if rule passes
            passed = bool(validation_result[0]) if validation_result else False
            
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "status": DataQualityStatus.PASSED if passed else DataQualityStatus.FAILED,
                "result_value": validation_result[0] if validation_result else None,
                "expected_result": rule.expected_result,
                "executed_at": datetime.utcnow()
            }
            
        except Exception as e:
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "status": DataQualityStatus.ERROR,
                "error_message": str(e),
                "executed_at": datetime.utcnow()
            }
