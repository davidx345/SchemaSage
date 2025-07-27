"""
Workflow execution engine
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Set, Callable, Deque
from datetime import datetime, timedelta
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import uuid

from models.schemas import SchemaResponse

from .models import (
    WorkflowDefinition, WorkflowExecution, WorkflowTask, TaskExecution,
    WorkflowStatus, TaskStatus, TaskType, TriggerType, WorkflowMetrics,
    ApprovalRequest, WorkflowEvent
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Main workflow execution engine that orchestrates workflow execution,
    task scheduling, and state management.
    """
    
    def __init__(self):
        """Initialize the workflow engine"""
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.metrics: Dict[str, WorkflowMetrics] = {}
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.events: List[WorkflowEvent] = []
        
        # Task and trigger handlers
        self.task_handlers: Dict[TaskType, Callable] = {}
        self.trigger_handlers: Dict[TriggerType, Callable] = {}
        
        # Execution management
        self.execution_queue: Deque[str] = deque()
        self.running_executions: Dict[str, threading.Thread] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Engine state
        self._engine_running = True
        self._engine_thread = threading.Thread(target=self._engine_loop, daemon=True)
        self._engine_thread.start()
        
        # Initialize built-in handlers
        self._initialize_task_handlers()
        self._initialize_trigger_handlers()
    
    def _initialize_task_handlers(self):
        """Initialize built-in task handlers"""
        from .task_handlers import (
            handle_schema_analysis, handle_code_generation, handle_validation,
            handle_deployment, handle_notification, handle_data_transformation,
            handle_integration, handle_approval, handle_conditional,
            handle_parallel, handle_webhook, handle_script
        )
        
        self.task_handlers[TaskType.SCHEMA_ANALYSIS] = handle_schema_analysis
        self.task_handlers[TaskType.CODE_GENERATION] = handle_code_generation
        self.task_handlers[TaskType.VALIDATION] = handle_validation
        self.task_handlers[TaskType.DEPLOYMENT] = handle_deployment
        self.task_handlers[TaskType.NOTIFICATION] = handle_notification
        self.task_handlers[TaskType.DATA_TRANSFORMATION] = handle_data_transformation
        self.task_handlers[TaskType.INTEGRATION] = handle_integration
        self.task_handlers[TaskType.APPROVAL] = handle_approval
        self.task_handlers[TaskType.CONDITIONAL] = handle_conditional
        self.task_handlers[TaskType.PARALLEL] = handle_parallel
        self.task_handlers[TaskType.WEBHOOK] = handle_webhook
        self.task_handlers[TaskType.SCRIPT] = handle_script
    
    def _initialize_trigger_handlers(self):
        """Initialize built-in trigger handlers"""
        from .trigger_handlers import (
            handle_manual_trigger, handle_scheduled_trigger, handle_schema_change_trigger,
            handle_file_upload_trigger, handle_api_request_trigger, handle_webhook_trigger
        )
        
        self.trigger_handlers[TriggerType.MANUAL] = handle_manual_trigger
        self.trigger_handlers[TriggerType.SCHEDULED] = handle_scheduled_trigger
        self.trigger_handlers[TriggerType.SCHEMA_CHANGE] = handle_schema_change_trigger
        self.trigger_handlers[TriggerType.FILE_UPLOAD] = handle_file_upload_trigger
        self.trigger_handlers[TriggerType.API_REQUEST] = handle_api_request_trigger
        self.trigger_handlers[TriggerType.WEBHOOK] = handle_webhook_trigger
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        if not self._validate_workflow_structure(workflow.tasks):
            raise ValueError("Invalid workflow structure")
        
        self.workflows[workflow.workflow_id] = workflow
        self.metrics[workflow.workflow_id] = WorkflowMetrics()
        
        logger.info(f"Registered workflow {workflow.workflow_id}: {workflow.name}")
    
    def _validate_workflow_structure(self, tasks: List[WorkflowTask]) -> bool:
        """Validate workflow structure for cycles and dependencies"""
        task_map = {task.task_id: task for task in tasks}
        
        # Check if all dependencies exist
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_map:
                    logger.error(f"Task {task.task_id} depends on non-existent task {dep_id}")
                    return False
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = task_map.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id):
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            if task.task_id not in visited:
                if has_cycle(task.task_id):
                    logger.error(f"Cycle detected in workflow involving task {task.task_id}")
                    return False
        
        return True
    
    async def start_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        triggered_by: str = "manual",
        trigger_data: Dict[str, Any] = None
    ) -> str:
        """Start a workflow execution"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow {workflow_id} is not active")
        
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            input_data=input_data or {},
            context=workflow.variables.copy(),
            triggered_by=triggered_by,
            trigger_data=trigger_data or {}
        )
        
        # Initialize context with input data
        execution.context.update(execution.input_data)
        
        self.executions[execution_id] = execution
        self.execution_queue.append(execution_id)
        
        # Create workflow event
        self._create_event("workflow_started", workflow_id, execution_id)
        
        logger.info(f"Started workflow execution {execution_id} for workflow {workflow_id}")
        return execution_id
    
    def _engine_loop(self):
        """Main workflow engine loop"""
        while self._engine_running:
            try:
                # Process execution queue
                if self.execution_queue:
                    execution_id = self.execution_queue.popleft()
                    
                    if execution_id not in self.running_executions:
                        # Start execution in separate thread
                        thread = threading.Thread(
                            target=self._execute_workflow,
                            args=(execution_id,),
                            daemon=True
                        )
                        thread.start()
                        self.running_executions[execution_id] = thread
                
                # Clean up completed executions
                completed_executions = []
                for execution_id, thread in self.running_executions.items():
                    if not thread.is_alive():
                        completed_executions.append(execution_id)
                
                for execution_id in completed_executions:
                    del self.running_executions[execution_id]
                
                # Process approval timeouts
                self._process_approval_timeouts()
                
                time.sleep(1)  # Prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error in workflow engine loop: {e}")
                time.sleep(5)
    
    def _execute_workflow(self, execution_id: str):
        """Execute a workflow"""
        try:
            execution = self.executions[execution_id]
            workflow = self.workflows[execution.workflow_id]
            
            logger.info(f"Executing workflow {workflow.workflow_id} (execution {execution_id})")
            
            # Build task dependency graph
            task_graph = self._build_task_graph(workflow.tasks)
            
            # Execute tasks in topological order
            completed_tasks = set()
            failed_tasks = set()
            
            while len(completed_tasks) + len(failed_tasks) < len(workflow.tasks):
                # Find tasks ready to execute
                ready_tasks = []
                
                for task in workflow.tasks:
                    if (task.task_id not in completed_tasks and 
                        task.task_id not in failed_tasks and
                        all(dep in completed_tasks for dep in task.dependencies)):
                        
                        # Check conditions
                        if task.should_execute(execution.context):
                            ready_tasks.append(task)
                
                if not ready_tasks:
                    # No tasks ready, check if we're waiting for approvals
                    waiting_for_approval = any(
                        task_exec.status == TaskStatus.PENDING and 
                        workflow.get_task_by_id(task_exec.task_id).task_type == TaskType.APPROVAL
                        for task_exec in execution.task_executions.values()
                    )
                    
                    if waiting_for_approval:
                        time.sleep(5)  # Wait for approvals
                        continue
                    else:
                        break  # Deadlock or all tasks completed/failed
                
                # Execute ready tasks
                for task in ready_tasks:
                    try:
                        result = self._execute_task(task, execution)
                        
                        if result.get('status') == 'success':
                            completed_tasks.add(task.task_id)
                        else:
                            failed_tasks.add(task.task_id)
                            
                            # Check if workflow should continue on task failure
                            if not task.configuration.get('continue_on_failure', False):
                                break
                                
                    except Exception as e:
                        logger.error(f"Task {task.task_id} failed: {e}")
                        failed_tasks.add(task.task_id)
                        
                        if not task.configuration.get('continue_on_failure', False):
                            break
            
            # Update execution status
            if failed_tasks and not all(
                workflow.get_task_by_id(task_id).configuration.get('continue_on_failure', False)
                for task_id in failed_tasks
            ):
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Tasks failed: {', '.join(failed_tasks)}"
            else:
                execution.status = WorkflowStatus.COMPLETED
            
            execution.completed_at = datetime.now()
            
            # Update metrics
            self._update_workflow_metrics(execution)
            
            # Create completion event
            event_type = "workflow_completed" if execution.status == WorkflowStatus.COMPLETED else "workflow_failed"
            self._create_event(event_type, execution.workflow_id, execution_id)
            
            logger.info(f"Workflow execution {execution_id} {execution.status.value}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {e}")
            execution = self.executions[execution_id]
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            self._create_event("workflow_failed", execution.workflow_id, execution_id, {"error": str(e)})
    
    def _build_task_graph(self, tasks: List[WorkflowTask]) -> Dict[str, List[str]]:
        """Build task dependency graph"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = task.dependencies.copy()
        return graph
    
    def _execute_task(self, task: WorkflowTask, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single task"""
        task_execution = TaskExecution(
            task_id=task.task_id,
            execution_id=execution.execution_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        
        execution.add_task_execution(task_execution)
        
        try:
            logger.info(f"Executing task {task.task_id} ({task.task_type.value})")
            
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler for task type {task.task_type}")
            
            # Execute task with timeout
            start_time = time.time()
            
            # Prepare task context
            task_context = {
                'task': task,
                'execution': execution,
                'workflow': self.workflows[execution.workflow_id],
                'input_data': execution.input_data,
                'context': execution.context.copy(),
                'configuration': task.configuration
            }
            
            # Execute handler
            result = handler(task_context)
            
            # Handle async results
            if asyncio.iscoroutine(result):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(result)
                finally:
                    loop.close()
            
            execution_time = time.time() - start_time
            
            # Update task execution
            task_execution.status = TaskStatus.COMPLETED
            task_execution.completed_at = datetime.now()
            task_execution.result = result
            
            # Update execution context with task results
            if isinstance(result, dict) and 'output' in result:
                execution.context.update(result['output'])
            
            logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
            return {'status': 'success', 'result': result}
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error_message = str(e)
            
            # Retry logic
            if task_execution.retry_count < task.retry_count:
                task_execution.retry_count += 1
                logger.info(f"Retrying task {task.task_id} (attempt {task_execution.retry_count})")
                time.sleep(task.retry_delay)
                return self._execute_task(task, execution)
            
            return {'status': 'failed', 'error': str(e)}
    
    def _update_workflow_metrics(self, execution: WorkflowExecution):
        """Update workflow execution metrics"""
        metrics = self.metrics[execution.workflow_id]
        
        metrics.total_executions += 1
        
        if execution.status == WorkflowStatus.COMPLETED:
            metrics.successful_executions += 1
            metrics.last_success = execution.completed_at
        else:
            metrics.failed_executions += 1
            metrics.last_failure = execution.completed_at
        
        metrics.last_execution = execution.completed_at
        
        # Update average duration
        if execution.duration():
            total_duration = metrics.average_duration * (metrics.total_executions - 1) + execution.duration()
            metrics.average_duration = total_duration / metrics.total_executions
    
    def _process_approval_timeouts(self):
        """Process approval request timeouts"""
        current_time = datetime.now()
        
        for request in list(self.approval_requests.values()):
            if request.is_expired() and request.status == "pending":
                request.status = "expired"
                
                # Find corresponding execution and fail the approval task
                execution = self.executions.get(request.execution_id)
                if execution:
                    task_execution = execution.get_task_execution(request.task_id)
                    if task_execution:
                        task_execution.status = TaskStatus.FAILED
                        task_execution.error_message = "Approval request expired"
                        task_execution.completed_at = current_time
                
                logger.info(f"Approval request {request.request_id} expired")
    
    def _create_event(
        self, 
        event_type: str, 
        workflow_id: str = None, 
        execution_id: str = None,
        task_id: str = None,
        data: Dict[str, Any] = None
    ):
        """Create a workflow event"""
        event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            workflow_id=workflow_id,
            execution_id=execution_id,
            task_id=task_id,
            data=data or {},
            source="workflow_engine"
        )
        
        self.events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    def pause_workflow(self, execution_id: str):
        """Pause a workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.status = WorkflowStatus.PAUSED
            logger.info(f"Paused workflow execution {execution_id}")
    
    def resume_workflow(self, execution_id: str):
        """Resume a paused workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == WorkflowStatus.PAUSED:
                execution.status = WorkflowStatus.RUNNING
                self.execution_queue.append(execution_id)
                logger.info(f"Resumed workflow execution {execution_id}")
    
    def cancel_workflow(self, execution_id: str):
        """Cancel a workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            
            # Stop running thread if exists
            if execution_id in self.running_executions:
                thread = self.running_executions[execution_id]
                # Note: Python threads cannot be forcefully stopped
                # In a real implementation, you'd use cooperative cancellation
                logger.warning(f"Workflow {execution_id} marked as cancelled but thread may continue")
            
            self._create_event("workflow_cancelled", execution.workflow_id, execution_id)
            logger.info(f"Cancelled workflow execution {execution_id}")
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            'execution_id': execution.execution_id,
            'workflow_id': execution.workflow_id,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration': execution.duration(),
            'task_executions': {
                task_id: {
                    'status': task_exec.status.value,
                    'started_at': task_exec.started_at.isoformat() if task_exec.started_at else None,
                    'completed_at': task_exec.completed_at.isoformat() if task_exec.completed_at else None,
                    'error_message': task_exec.error_message,
                    'retry_count': task_exec.retry_count
                }
                for task_id, task_exec in execution.task_executions.items()
            }
        }
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow metrics"""
        metrics = self.metrics.get(workflow_id)
        if not metrics:
            return None
        
        return {
            'total_executions': metrics.total_executions,
            'successful_executions': metrics.successful_executions,
            'failed_executions': metrics.failed_executions,
            'success_rate': metrics.success_rate(),
            'failure_rate': metrics.failure_rate(),
            'average_duration': metrics.average_duration,
            'last_execution': metrics.last_execution.isoformat() if metrics.last_execution else None,
            'last_success': metrics.last_success.isoformat() if metrics.last_success else None,
            'last_failure': metrics.last_failure.isoformat() if metrics.last_failure else None
        }
    
    def shutdown(self):
        """Shutdown the workflow engine"""
        self._engine_running = False
        
        # Wait for running executions to complete (with timeout)
        for execution_id, thread in self.running_executions.items():
            thread.join(timeout=30)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Workflow engine shut down")
