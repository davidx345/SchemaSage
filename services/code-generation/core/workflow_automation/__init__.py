"""
Workflow automation orchestrator module
Manages all workflow automation components
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import uuid

from .models import (
    WorkflowDefinition, WorkflowExecution, WorkflowTask, TaskExecution,
    WorkflowTemplate, ExecutionStatus, TaskStatus
)
from .engine import WorkflowEngine
from .task_handlers import TaskHandlerRegistry
from .trigger_handlers import TriggerHandlerRegistry
from .template_manager import WorkflowTemplateManager

logger = logging.getLogger(__name__)


class WorkflowAutomationOrchestrator:
    """
    Main orchestrator for workflow automation system
    Coordinates workflow definitions, execution, and template management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the workflow automation orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Core components
        self.engine = WorkflowEngine(config.get('engine', {}))
        self.task_handlers = TaskHandlerRegistry()
        self.trigger_handlers = TriggerHandlerRegistry()
        self.template_manager = WorkflowTemplateManager(
            config.get('template_directory', 'templates/workflows')
        )
        
        # State management
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        # Background tasks
        self._monitoring_task = None
        self._cleanup_task = None
        self._trigger_monitoring_task = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'workflow_started': [],
            'workflow_completed': [],
            'workflow_failed': [],
            'task_started': [],
            'task_completed': [],
            'task_failed': []
        }
        
        logger.info("Workflow automation orchestrator initialized")
    
    async def start(self):
        """Start the orchestrator and background tasks"""
        try:
            # Start background monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitor_executions())
            self._cleanup_task = asyncio.create_task(self._cleanup_old_executions())
            self._trigger_monitoring_task = asyncio.create_task(self._monitor_triggers())
            
            logger.info("Workflow automation orchestrator started")
        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            raise
    
    async def stop(self):
        """Stop the orchestrator and background tasks"""
        try:
            # Cancel background tasks
            if self._monitoring_task:
                self._monitoring_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._trigger_monitoring_task:
                self._trigger_monitoring_task.cancel()
            
            # Stop any running workflows
            for execution in self.active_executions.values():
                if execution.status == ExecutionStatus.RUNNING:
                    await self.engine.stop_workflow(execution.execution_id)
            
            logger.info("Workflow automation orchestrator stopped")
        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
    
    # Workflow Definition Management
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        try:
            self.workflows[workflow.workflow_id] = workflow
            logger.info(f"Registered workflow: {workflow.name} ({workflow.workflow_id})")
        except Exception as e:
            logger.error(f"Error registering workflow {workflow.workflow_id}: {e}")
            raise
    
    def unregister_workflow(self, workflow_id: str):
        """Unregister a workflow definition"""
        try:
            if workflow_id in self.workflows:
                workflow = self.workflows.pop(workflow_id)
                logger.info(f"Unregistered workflow: {workflow.name} ({workflow_id})")
            else:
                logger.warning(f"Workflow {workflow_id} not found for unregistration")
        except Exception as e:
            logger.error(f"Error unregistering workflow {workflow_id}: {e}")
            raise
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all registered workflows"""
        return list(self.workflows.values())
    
    def update_workflow(self, workflow: WorkflowDefinition):
        """Update a workflow definition"""
        try:
            if workflow.workflow_id in self.workflows:
                workflow.updated_at = datetime.utcnow()
                self.workflows[workflow.workflow_id] = workflow
                logger.info(f"Updated workflow: {workflow.name} ({workflow.workflow_id})")
            else:
                raise ValueError(f"Workflow {workflow.workflow_id} not found")
        except Exception as e:
            logger.error(f"Error updating workflow {workflow.workflow_id}: {e}")
            raise
    
    # Workflow Execution Management
    
    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: Dict[str, Any] = None,
        execution_name: str = None
    ) -> str:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of workflow to execute
            parameters: Execution parameters
            execution_name: Optional name for execution
            
        Returns:
            Execution ID
        """
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            execution_id = str(uuid.uuid4())
            execution_name = execution_name or f"{workflow.name} - {datetime.utcnow().isoformat()}"
            
            # Create execution
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                execution_name=execution_name,
                parameters=parameters or {},
                status=ExecutionStatus.PENDING
            )
            
            # Register execution
            self.active_executions[execution_id] = execution
            
            # Start execution
            await self.engine.execute_workflow(workflow, execution)
            
            # Fire event
            await self._fire_event('workflow_started', {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'execution': execution
            })
            
            logger.info(f"Started workflow execution: {execution_name} ({execution_id})")
            return execution_id
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            raise
    
    async def stop_workflow(self, execution_id: str, reason: str = None):
        """Stop a running workflow execution"""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            await self.engine.stop_workflow(execution_id)
            
            # Update execution status
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            if reason:
                execution.error_message = f"Cancelled: {reason}"
            
            # Move to history
            self.execution_history.append(execution)
            del self.active_executions[execution_id]
            
            logger.info(f"Stopped workflow execution: {execution_id}")
            
        except Exception as e:
            logger.error(f"Error stopping workflow {execution_id}: {e}")
            raise
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID"""
        # Check active executions first
        execution = self.active_executions.get(execution_id)
        if execution:
            return execution
        
        # Check history
        for historical_execution in self.execution_history:
            if historical_execution.execution_id == execution_id:
                return historical_execution
        
        return None
    
    def list_executions(
        self,
        workflow_id: str = None,
        status: ExecutionStatus = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters"""
        executions = list(self.active_executions.values()) + self.execution_history
        
        # Apply filters
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by created_at descending and limit
        executions.sort(key=lambda x: x.created_at, reverse=True)
        return executions[:limit]
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get execution status"""
        execution = self.get_execution(execution_id)
        return execution.status if execution else None
    
    # Template Management
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template"""
        return self.template_manager.get_template(template_id)
    
    def list_templates(self, category: str = None) -> List[WorkflowTemplate]:
        """List workflow templates"""
        return self.template_manager.list_templates(category)
    
    async def create_workflow_from_template(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        workflow_name: str = None,
        auto_register: bool = True
    ) -> WorkflowDefinition:
        """
        Create workflow from template
        
        Args:
            template_id: Template ID
            parameters: Template parameters
            workflow_name: Optional workflow name
            auto_register: Whether to automatically register the workflow
            
        Returns:
            Created workflow definition
        """
        try:
            workflow = self.template_manager.instantiate_template(
                template_id, parameters, workflow_name
            )
            
            if auto_register:
                self.register_workflow(workflow)
            
            logger.info(f"Created workflow from template {template_id}: {workflow.name}")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow from template {template_id}: {e}")
            raise
    
    # Event Management
    
    def register_event_handler(self, event_type: str, handler: callable):
        """Register event handler"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(handler)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def unregister_event_handler(self, event_type: str, handler: callable):
        """Unregister event handler"""
        if event_type in self.event_callbacks and handler in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(handler)
    
    async def _fire_event(self, event_type: str, event_data: Dict[str, Any]):
        """Fire event to registered handlers"""
        if event_type in self.event_callbacks:
            for handler in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_data)
                    else:
                        handler(event_data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    # Background Tasks
    
    async def _monitor_executions(self):
        """Monitor active executions for completion and errors"""
        while True:
            try:
                completed_executions = []
                
                for execution_id, execution in self.active_executions.items():
                    # Check if execution is complete
                    engine_execution = await self.engine.get_execution_status(execution_id)
                    if engine_execution and engine_execution.status in [
                        ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED
                    ]:
                        # Update our execution object
                        execution.status = engine_execution.status
                        execution.completed_at = engine_execution.completed_at
                        execution.error_message = engine_execution.error_message
                        execution.task_executions = engine_execution.task_executions
                        
                        completed_executions.append(execution_id)
                        
                        # Fire appropriate event
                        if execution.status == ExecutionStatus.COMPLETED:
                            await self._fire_event('workflow_completed', {
                                'execution_id': execution_id,
                                'execution': execution
                            })
                        elif execution.status == ExecutionStatus.FAILED:
                            await self._fire_event('workflow_failed', {
                                'execution_id': execution_id,
                                'execution': execution
                            })
                
                # Move completed executions to history
                for execution_id in completed_executions:
                    execution = self.active_executions.pop(execution_id)
                    self.execution_history.append(execution)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in execution monitoring: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _cleanup_old_executions(self):
        """Clean up old execution history"""
        while True:
            try:
                # Keep only last 1000 executions in history
                max_history = self.config.get('max_execution_history', 1000)
                if len(self.execution_history) > max_history:
                    # Sort by completion time and keep most recent
                    self.execution_history.sort(
                        key=lambda x: x.completed_at or x.created_at,
                        reverse=True
                    )
                    self.execution_history = self.execution_history[:max_history]
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Error in execution cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def _monitor_triggers(self):
        """Monitor for workflow triggers"""
        while True:
            try:
                for workflow in self.workflows.values():
                    if not workflow.triggers:
                        continue
                    
                    for trigger in workflow.triggers:
                        try:
                            # Check if trigger should fire
                            should_trigger = await self.trigger_handlers.evaluate_trigger(
                                trigger, workflow.workflow_id
                            )
                            
                            if should_trigger:
                                # Start workflow execution
                                await self.execute_workflow(
                                    workflow.workflow_id,
                                    execution_name=f"Triggered: {workflow.name}"
                                )
                                
                        except Exception as e:
                            logger.error(f"Error evaluating trigger for workflow {workflow.workflow_id}: {e}")
                
                await asyncio.sleep(30)  # Check triggers every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in trigger monitoring: {e}")
                await asyncio.sleep(60)
    
    # Statistics and Metrics
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        all_executions = list(self.active_executions.values()) + self.execution_history
        
        total_executions = len(all_executions)
        completed = len([e for e in all_executions if e.status == ExecutionStatus.COMPLETED])
        failed = len([e for e in all_executions if e.status == ExecutionStatus.FAILED])
        running = len([e for e in all_executions if e.status == ExecutionStatus.RUNNING])
        
        # Calculate average execution time for completed workflows
        completed_executions = [
            e for e in all_executions 
            if e.status == ExecutionStatus.COMPLETED and e.completed_at
        ]
        
        avg_duration = None
        if completed_executions:
            durations = [
                (e.completed_at - e.created_at).total_seconds()
                for e in completed_executions
            ]
            avg_duration = sum(durations) / len(durations)
        
        return {
            'total_executions': total_executions,
            'completed': completed,
            'failed': failed,
            'running': running,
            'success_rate': completed / total_executions if total_executions > 0 else 0,
            'average_duration_seconds': avg_duration,
            'active_workflows': len(self.workflows),
            'available_templates': len(self.template_manager.templates)
        }
    
    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get metrics for a specific workflow"""
        workflow_executions = [
            e for e in (list(self.active_executions.values()) + self.execution_history)
            if e.workflow_id == workflow_id
        ]
        
        if not workflow_executions:
            return {
                'total_executions': 0,
                'success_rate': 0,
                'average_duration_seconds': None,
                'last_execution': None
            }
        
        total = len(workflow_executions)
        completed = len([e for e in workflow_executions if e.status == ExecutionStatus.COMPLETED])
        
        # Calculate average duration
        completed_executions = [
            e for e in workflow_executions 
            if e.status == ExecutionStatus.COMPLETED and e.completed_at
        ]
        
        avg_duration = None
        if completed_executions:
            durations = [
                (e.completed_at - e.created_at).total_seconds()
                for e in completed_executions
            ]
            avg_duration = sum(durations) / len(durations)
        
        # Get last execution
        last_execution = max(workflow_executions, key=lambda x: x.created_at)
        
        return {
            'total_executions': total,
            'success_rate': completed / total if total > 0 else 0,
            'average_duration_seconds': avg_duration,
            'last_execution': {
                'execution_id': last_execution.execution_id,
                'status': last_execution.status.value,
                'created_at': last_execution.created_at.isoformat(),
                'completed_at': last_execution.completed_at.isoformat() if last_execution.completed_at else None
            }
        }
