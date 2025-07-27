"""
Comprehensive Test Suite for SchemaSage Week 7-8 Features
Tests all implemented functionality including AI critique, schema merging, version control, and performance monitoring
"""
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
import time
from typing import Dict, List, Any

# Test framework
import pytest
from rich.console import Console

# Import all SchemaSage components
from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship
from core.ai_schema_critic import AISchemacritic, CritiqueCategory, SeverityLevel
from core.schema_merger import SchemaMerger, MergeStrategy, ConflictType
from core.schema_version_control import SchemaVersionControl, ChangeType, ChangeImpact
from core.performance_monitor import PerformanceMonitor, MetricType, performance_monitor
from core.data_quality_analyzer import DataQualityAnalyzer
from core.erd_generator import ERDGenerator
from core.api_scaffold_generator import APIScaffoldGenerator

console = Console()

class SchemaSageTestSuite:
    """Comprehensive test suite for all SchemaSage features"""
    
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'performance_metrics': {},
            'test_details': []
        }
        
        # Test schemas
        self.test_schemas = self._create_test_schemas()
        
        # Temporary directory for version control tests
        self.temp_dir = None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        console.print("[bold blue]🧪 Starting SchemaSage Comprehensive Test Suite[/bold blue]")
        
        # Setup
        await self._setup()
        
        try:
            # Week 7-8 Core Feature Tests
            await self._test_ai_schema_critic()
            await self._test_schema_merger()
            await self._test_version_control()
            await self._test_performance_monitoring()
            
            # Integration Tests
            await self._test_data_quality_analyzer()
            await self._test_erd_generator()
            await self._test_api_scaffolding()
            
            # End-to-End Workflow Tests
            await self._test_complete_workflow()
            
            # Performance & Stress Tests
            await self._test_performance_stress()
            
        except Exception as e:
            self._record_error(f"Test suite execution error: {e}")
        
        finally:
            await self._cleanup()
        
        return self._generate_test_report()
    
    async def _setup(self):
        """Setup test environment"""
        console.print("🔧 Setting up test environment...")
        
        # Create temporary directory for version control tests
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Reset performance monitor for clean testing
        global performance_monitor
        performance_monitor = PerformanceMonitor()
    
    async def _cleanup(self):
        """Cleanup test environment"""
        console.print("🧹 Cleaning up test environment...")
        
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    # ==================== AI Schema Critic Tests ====================
    
    async def _test_ai_schema_critic(self):
        """Test AI schema critique system"""
        console.print("\n[bold cyan]Testing AI Schema Critic[/bold cyan]")
        
        try:
            critic = AISchemacritic()
            
            # Test 1: Basic schema analysis
            analysis_result = await critic.analyze_schema(self.test_schemas['problematic'])
            
            self._assert(analysis_result.overall_score >= 0 and analysis_result.overall_score <= 100,
                        "Overall score should be between 0-100")
            self._assert(len(analysis_result.critiques) > 0, "Should identify critiques in problematic schema")
            self._assert(len(analysis_result.recommendations) > 0, "Should provide recommendations")
            
            # Test 2: Specific critique categories
            critique_categories = {critique.category for critique in analysis_result.critiques}
            expected_categories = {CritiqueCategory.PERFORMANCE, CritiqueCategory.NAMING_CONVENTIONS}
            
            self._assert(len(critique_categories) > 0, "Should identify multiple critique categories")
            
            # Test 3: Severity levels
            severity_levels = {critique.severity for critique in analysis_result.critiques}
            self._assert(len(severity_levels) > 0, "Should have various severity levels")
            
            # Test 4: Well-designed schema (should have fewer issues)
            good_analysis = await critic.analyze_schema(self.test_schemas['well_designed'])
            self._assert(good_analysis.overall_score > analysis_result.overall_score,
                        "Well-designed schema should score higher")
            
            self._record_success("AI Schema Critic", "All critique functionality working correctly")
            
        except Exception as e:
            self._record_error(f"AI Schema Critic test failed: {e}")
    
    # ==================== Schema Merger Tests ====================
    
    async def _test_schema_merger(self):
        """Test schema merging system"""
        console.print("\n[bold cyan]Testing Schema Merger[/bold cyan]")
        
        try:
            merger = SchemaMerger()
            
            # Test 1: Basic schema merging
            schemas = [self.test_schemas['schema_a'], self.test_schemas['schema_b']]
            merge_result = await merger.merge_schemas(schemas)
            
            self._assert(merge_result.success, "Basic merge should succeed")
            self._assert(len(merge_result.merged_schema.tables) >= 2, "Should merge tables from both schemas")
            
            # Test 2: Conflict detection
            conflicting_schemas = [self.test_schemas['conflicting_a'], self.test_schemas['conflicting_b']]
            conflict_result = await merger.merge_schemas(conflicting_schemas)
            
            self._assert(len(conflict_result.conflicts) > 0, "Should detect conflicts between schemas")
            
            # Test 3: Strategy application
            strategy_overrides = {ConflictType.COLUMN_TYPE_CONFLICT: MergeStrategy.PREFER_FIRST}
            strategy_result = await merger.merge_schemas(
                conflicting_schemas, 
                strategy_overrides=strategy_overrides
            )
            
            self._assert(strategy_result.success or len(strategy_result.conflicts) < len(conflict_result.conflicts),
                        "Strategy should help resolve conflicts")
            
            # Test 4: Large schema merging
            large_schemas = [self.test_schemas['large_schema_1'], self.test_schemas['large_schema_2']]
            large_result = await merger.merge_schemas(large_schemas)
            
            self._assert(len(large_result.merged_schema.tables) > 10, "Should handle large schema merging")
            
            self._record_success("Schema Merger", "All merging functionality working correctly")
            
        except Exception as e:
            self._record_error(f"Schema Merger test failed: {e}")
    
    # ==================== Version Control Tests ====================
    
    async def _test_version_control(self):
        """Test schema version control system"""
        console.print("\n[bold cyan]Testing Schema Version Control[/bold cyan]")
        
        try:
            vc_path = self.temp_dir / "version_control_test"
            version_control = SchemaVersionControl(str(vc_path))
            
            # Test 1: Repository initialization
            initial_version = await version_control.initialize_repository(
                self.test_schemas['schema_a'], 
                "test_author", 
                "Initial test schema"
            )
            
            self._assert(initial_version is not None, "Should return initial version ID")
            self._assert(vc_path.exists(), "Should create version control directory")
            
            # Test 2: Schema commit
            modified_schema = self._modify_schema(self.test_schemas['schema_a'])
            commit_version = await version_control.commit_schema(
                modified_schema,
                "test_author",
                "Modified schema for testing",
                ["test", "modified"]
            )
            
            self._assert(commit_version != initial_version, "Should create new version ID")
            
            # Test 3: Version listing
            versions = await version_control.list_versions()
            self._assert(len(versions) == 2, "Should have 2 versions")
            self._assert(versions[0].version_id == commit_version, "Latest version should be first")
            
            # Test 4: Version diff
            diff = await version_control.get_version_diff(initial_version, commit_version)
            self._assert(len(diff.changes) > 0, "Should detect changes between versions")
            self._assert(diff.migration_sql is not None, "Should generate migration SQL")
            
            # Test 5: Revert functionality
            revert_version = await version_control.revert_to_version(
                initial_version,
                "test_author",
                "Reverting to initial version"
            )
            
            self._assert(revert_version is not None, "Should create revert version")
            
            # Test 6: Version history
            history = await version_control.get_version_history()
            self._assert(len(history) == 3, "Should have 3 versions in history")
            
            # Test 7: Statistics
            stats = await version_control.get_schema_statistics()
            self._assert(stats['total_versions'] == 3, "Statistics should show 3 versions")
            self._assert('authors' in stats, "Should track authors")
            
            self._record_success("Version Control", "All version control functionality working correctly")
            
        except Exception as e:
            self._record_error(f"Version Control test failed: {e}")
    
    # ==================== Performance Monitoring Tests ====================
    
    async def _test_performance_monitoring(self):
        """Test performance monitoring system"""
        console.print("\n[bold cyan]Testing Performance Monitoring[/bold cyan]")
        
        try:
            monitor = performance_monitor
            
            # Test 1: Basic metric recording
            monitor.record_metric(MetricType.EXECUTION_TIME, 1.5, {"operation": "test"})
            monitor.record_metric(MetricType.MEMORY_USAGE, 100.0, {"operation": "test"})
            
            # Test 2: Operation tracking
            with monitor.track_operation("test_operation", test_param="value") as op_id:
                time.sleep(0.1)  # Simulate work
                self._assert(op_id in monitor.get_active_operations(), "Should track active operation")
            
            # Test 3: Operation statistics
            stats = monitor.get_operation_statistics()
            self._assert("test_operation" in stats, "Should record operation statistics")
            self._assert(stats["test_operation"]["count"] == 1, "Should count operation executions")
            
            # Test 4: Function decorator
            @monitor.track_function("decorated_test")
            def test_function():
                time.sleep(0.05)
                return "test_result"
            
            result = test_function()
            self._assert(result == "test_result", "Decorated function should work normally")
            
            decorated_stats = monitor.get_operation_statistics()
            self._assert("decorated_test" in decorated_stats, "Should track decorated function")
            
            # Test 5: Async function decorator
            @monitor.track_function("async_decorated_test")
            async def async_test_function():
                await asyncio.sleep(0.05)
                return "async_result"
            
            async_result = await async_test_function()
            self._assert(async_result == "async_result", "Decorated async function should work")
            
            # Test 6: System health
            health = monitor.get_system_health()
            self._assert("status" in health, "Should provide system status")
            self._assert("metrics" in health, "Should include metrics in health report")
            
            # Test 7: Performance report
            from datetime import timedelta
            report = monitor.get_performance_report(timedelta(hours=1))
            self._assert("operation_statistics" in report, "Should include operation statistics")
            self._assert("recommendations" in report, "Should provide recommendations")
            
            self._record_success("Performance Monitoring", "All performance monitoring working correctly")
            
        except Exception as e:
            self._record_error(f"Performance Monitoring test failed: {e}")
    
    # ==================== Data Quality Analyzer Tests ====================
    
    async def _test_data_quality_analyzer(self):
        """Test data quality analysis functionality"""
        console.print("\n[bold cyan]Testing Data Quality Analyzer[/bold cyan]")
        
        try:
            analyzer = DataQualityAnalyzer()
            
            # Create test data with quality issues
            test_data = self._create_test_data_with_issues()
            
            # Test 1: Quality analysis
            with performance_monitor.track_operation("data_quality_test"):
                quality_report = await analyzer.analyze_data_quality(test_data)
            
            self._assert(len(quality_report.issues) > 0, "Should detect data quality issues")
            self._assert(quality_report.overall_score <= 100, "Score should be valid")
            
            # Test 2: Issue categorization
            issue_types = {issue.issue_type for issue in quality_report.issues}
            expected_types = {"missing_values", "duplicates", "outliers"}
            self._assert(len(issue_types & expected_types) > 0, "Should detect expected issue types")
            
            # Test 3: Cleaning suggestions
            self._assert(len(quality_report.cleaning_suggestions) > 0, "Should provide cleaning suggestions")
            
            self._record_success("Data Quality Analyzer", "Data quality analysis working correctly")
            
        except Exception as e:
            self._record_error(f"Data Quality Analyzer test failed: {e}")
    
    # ==================== ERD Generator Tests ====================
    
    async def _test_erd_generator(self):
        """Test ERD generation functionality"""
        console.print("\n[bold cyan]Testing ERD Generator[/bold cyan]")
        
        try:
            erd_generator = ERDGenerator()
            
            # Test 1: Basic ERD generation
            with performance_monitor.track_operation("erd_generation_test"):
                erd_result = await erd_generator.generate_erd(
                    self.test_schemas['well_designed'],
                    layout="force_directed"
                )
            
            self._assert("nodes" in erd_result, "Should generate nodes")
            self._assert("edges" in erd_result, "Should generate edges")
            self._assert(len(erd_result["nodes"]) > 0, "Should have nodes for tables")
            
            # Test 2: Multiple layout algorithms
            layouts = ["hierarchical", "circular", "grid"]
            for layout in layouts:
                layout_result = await erd_generator.generate_erd(
                    self.test_schemas['well_designed'],
                    layout=layout
                )
                self._assert("layout_info" in layout_result, f"Should generate {layout} layout")
            
            # Test 3: Complex schema ERD
            complex_erd = await erd_generator.generate_erd(
                self.test_schemas['large_schema_1'],
                layout="force_directed",
                include_columns=True
            )
            
            self._assert(len(complex_erd["nodes"]) > 5, "Should handle complex schemas")
            
            self._record_success("ERD Generator", "ERD generation working correctly")
            
        except Exception as e:
            self._record_error(f"ERD Generator test failed: {e}")
    
    # ==================== API Scaffolding Tests ====================
    
    async def _test_api_scaffolding(self):
        """Test API scaffolding generation"""
        console.print("\n[bold cyan]Testing API Scaffolding[/bold cyan]")
        
        try:
            scaffold_generator = APIScaffoldGenerator()
            
            # Test 1: FastAPI scaffolding
            with performance_monitor.track_operation("api_scaffold_test"):
                fastapi_scaffold = await scaffold_generator.generate_api_scaffold(
                    self.test_schemas['well_designed'],
                    framework="fastapi"
                )
            
            self._assert("components" in fastapi_scaffold, "Should generate API components")
            self._assert("models" in fastapi_scaffold["components"], "Should generate models")
            self._assert("routers" in fastapi_scaffold["components"], "Should generate routers")
            
            # Test 2: Multiple frameworks
            frameworks = ["express", "nestjs", "spring-boot"]
            for framework in frameworks:
                framework_scaffold = await scaffold_generator.generate_api_scaffold(
                    self.test_schemas['schema_a'],
                    framework=framework
                )
                self._assert("components" in framework_scaffold, f"Should generate {framework} scaffold")
            
            # Test 3: Configuration options
            configured_scaffold = await scaffold_generator.generate_api_scaffold(
                self.test_schemas['well_designed'],
                framework="fastapi",
                options={
                    "include_auth": True,
                    "include_tests": True,
                    "include_docker": True
                }
            )
            
            components = configured_scaffold["components"]
            self._assert("auth" in components or "middleware" in components, "Should include auth components")
            self._assert("tests" in components, "Should include test components")
            
            self._record_success("API Scaffolding", "API scaffolding generation working correctly")
            
        except Exception as e:
            self._record_error(f"API Scaffolding test failed: {e}")
    
    # ==================== End-to-End Workflow Tests ====================
    
    async def _test_complete_workflow(self):
        """Test complete SchemaSage workflow"""
        console.print("\n[bold cyan]Testing Complete Workflow[/bold cyan]")
        
        try:
            # Workflow: Schema → Analysis → Improvements → Version Control → ERD → API
            
            # Step 1: Start with problematic schema
            original_schema = self.test_schemas['problematic']
            
            # Step 2: Analyze with AI critic
            critic = AISchemacritic()
            analysis = await critic.analyze_schema(original_schema)
            
            # Step 3: Create improved schema based on suggestions
            improved_schema = self._apply_improvements(original_schema, analysis.critiques)
            
            # Step 4: Version control the improvements
            vc_path = self.temp_dir / "workflow_test"
            version_control = SchemaVersionControl(str(vc_path))
            
            # Initialize with original
            initial_version = await version_control.initialize_repository(
                original_schema, "workflow_test", "Initial problematic schema"
            )
            
            # Commit improvements
            improved_version = await version_control.commit_schema(
                improved_schema, "workflow_test", "Applied AI suggestions", ["improved"]
            )
            
            # Step 5: Generate ERD for visualization
            erd_generator = ERDGenerator()
            erd_result = await erd_generator.generate_erd(improved_schema)
            
            # Step 6: Generate API scaffold
            scaffold_generator = APIScaffoldGenerator()
            api_scaffold = await scaffold_generator.generate_api_scaffold(
                improved_schema, "fastapi"
            )
            
            # Step 7: Final analysis to verify improvements
            final_analysis = await critic.analyze_schema(improved_schema)
            
            # Verify workflow success
            self._assert(final_analysis.overall_score > analysis.overall_score,
                        "Improved schema should score higher")
            self._assert(len(erd_result["nodes"]) > 0, "Should generate ERD")
            self._assert("components" in api_scaffold, "Should generate API scaffold")
            self._assert(improved_version != initial_version, "Should create new version")
            
            self._record_success("Complete Workflow", "End-to-end workflow functioning correctly")
            
        except Exception as e:
            self._record_error(f"Complete Workflow test failed: {e}")
    
    # ==================== Performance & Stress Tests ====================
    
    async def _test_performance_stress(self):
        """Test system performance under load"""
        console.print("\n[bold cyan]Testing Performance & Stress[/bold cyan]")
        
        try:
            # Test 1: Large schema processing
            large_schema = self._create_large_test_schema(100)  # 100 tables
            
            start_time = time.time()
            with performance_monitor.track_operation("large_schema_analysis"):
                critic = AISchemacritic()
                large_analysis = await critic.analyze_schema(large_schema)
            
            analysis_time = time.time() - start_time
            self._assert(analysis_time < 30, "Large schema analysis should complete within 30 seconds")
            self._assert(len(large_analysis.critiques) > 0, "Should analyze large schema")
            
            # Test 2: Concurrent operations
            async def concurrent_analysis(schema_id):
                return await critic.analyze_schema(self.test_schemas['schema_a'])
            
            start_time = time.time()
            concurrent_tasks = [concurrent_analysis(i) for i in range(5)]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            concurrent_time = time.time() - start_time
            
            self._assert(len(concurrent_results) == 5, "Should handle concurrent operations")
            self._assert(concurrent_time < 15, "Concurrent operations should complete reasonably fast")
            
            # Test 3: Memory usage monitoring
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform memory-intensive operations
            for i in range(10):
                await critic.analyze_schema(large_schema)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            self._assert(memory_increase < 500, "Memory usage should not increase excessively")
            
            # Test 4: Performance metrics validation
            stats = performance_monitor.get_operation_statistics()
            self._assert(len(stats) > 0, "Should collect performance statistics")
            
            for op_name, op_stats in stats.items():
                self._assert(op_stats['avg_time'] > 0, f"Should track timing for {op_name}")
                self._assert(op_stats['count'] > 0, f"Should count executions for {op_name}")
            
            self._record_success("Performance & Stress", "System handles performance requirements")
            
        except Exception as e:
            self._record_error(f"Performance & Stress test failed: {e}")
    
    # ==================== Test Utilities ====================
    
    def _create_test_schemas(self) -> Dict[str, SchemaResponse]:
        """Create various test schemas for testing"""
        
        schemas = {}
        
        # Well-designed schema
        schemas['well_designed'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="users",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False, unique=True),
                        ColumnInfo(name="email", type="String", nullable=False, unique=True),
                        ColumnInfo(name="username", type="String", nullable=False, unique=True),
                        ColumnInfo(name="created_at", type="DateTime", nullable=False),
                        ColumnInfo(name="updated_at", type="DateTime", nullable=False),
                    ],
                    description="User accounts"
                ),
                TableInfo(
                    name="posts",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False, unique=True),
                        ColumnInfo(name="title", type="String", nullable=False),
                        ColumnInfo(name="content", type="Text", nullable=False),
                        ColumnInfo(name="user_id", type="Integer", nullable=False),
                        ColumnInfo(name="created_at", type="DateTime", nullable=False),
                        ColumnInfo(name="updated_at", type="DateTime", nullable=False),
                    ],
                    description="User posts"
                )
            ],
            relationships=[
                Relationship(
                    source_table="posts",
                    source_column="user_id",
                    target_table="users",
                    target_column="id",
                    type="many-to-one"
                )
            ],
            schema_format="schemasage",
            metadata={"version": "1.0"}
        )
        
        # Problematic schema (for testing AI critic)
        schemas['problematic'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="User Data",  # Space in name
                    columns=[
                        ColumnInfo(name="user", type="Text"),  # Reserved word, no constraints
                        ColumnInfo(name="email address", type="Text"),  # Space in name
                        ColumnInfo(name="password", type="Text"),  # Plain text password
                    ],
                    description=""
                ),
                TableInfo(
                    name="order",  # Reserved word
                    columns=[
                        ColumnInfo(name="data", type="Text"),  # Too generic
                        ColumnInfo(name="value", type="Text"),  # Reserved word
                    ],
                    description=""
                )
            ],
            relationships=[],  # No relationships
            schema_format="schemasage",
            metadata={}
        )
        
        # Schema A (for merging tests)
        schemas['schema_a'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="customers",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False),
                        ColumnInfo(name="name", type="String", nullable=False),
                        ColumnInfo(name="email", type="String", nullable=False),
                    ],
                    description="Customer data"
                )
            ],
            relationships=[],
            schema_format="schemasage",
            metadata={"source": "schema_a"}
        )
        
        # Schema B (for merging tests)
        schemas['schema_b'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="orders",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False),
                        ColumnInfo(name="customer_id", type="Integer", nullable=False),
                        ColumnInfo(name="total", type="Decimal", nullable=False),
                    ],
                    description="Order data"
                )
            ],
            relationships=[],
            schema_format="schemasage",
            metadata={"source": "schema_b"}
        )
        
        # Conflicting schemas (for merge conflict tests)
        schemas['conflicting_a'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="products",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False),
                        ColumnInfo(name="price", type="Integer", nullable=False),  # Different type
                    ],
                    description="Products A"
                )
            ],
            relationships=[],
            schema_format="schemasage",
            metadata={"source": "conflicting_a"}
        )
        
        schemas['conflicting_b'] = SchemaResponse(
            tables=[
                TableInfo(
                    name="products",
                    columns=[
                        ColumnInfo(name="id", type="Integer", nullable=False),
                        ColumnInfo(name="price", type="Decimal", nullable=True),  # Different type and constraint
                    ],
                    description="Products B"
                )
            ],
            relationships=[],
            schema_format="schemasage",
            metadata={"source": "conflicting_b"}
        )
        
        # Large schemas (for performance tests)
        schemas['large_schema_1'] = self._create_large_test_schema(20)
        schemas['large_schema_2'] = self._create_large_test_schema(15)
        
        return schemas
    
    def _create_large_test_schema(self, table_count: int) -> SchemaResponse:
        """Create a large schema for performance testing"""
        
        tables = []
        relationships = []
        
        for i in range(table_count):
            columns = [
                ColumnInfo(name="id", type="Integer", nullable=False),
                ColumnInfo(name=f"field_{j}", type="String", nullable=True)
                for j in range(10)  # 10 fields per table
            ]
            
            table = TableInfo(
                name=f"table_{i}",
                columns=columns,
                description=f"Test table {i}"
            )
            tables.append(table)
            
            # Add relationships to previous table
            if i > 0:
                relationship = Relationship(
                    source_table=f"table_{i}",
                    source_column="id",
                    target_table=f"table_{i-1}",
                    target_column="id",
                    type="many-to-one"
                )
                relationships.append(relationship)
        
        return SchemaResponse(
            tables=tables,
            relationships=relationships,
            schema_format="schemasage",
            metadata={"test": "large_schema", "table_count": table_count}
        )
    
    def _create_test_data_with_issues(self) -> Dict[str, Any]:
        """Create test data with quality issues"""
        
        import pandas as pd
        import numpy as np
        
        # Create data with various quality issues
        data = {
            'id': [1, 2, 3, 4, 5, 5, 7],  # Duplicate
            'name': ['Alice', 'Bob', None, 'David', 'Eve', 'Frank', 'Grace'],  # Missing value
            'email': ['alice@test.com', 'invalid-email', 'charlie@test.com', 
                     'david@test.com', 'eve@test.com', 'frank@test.com', 'grace@test.com'],  # Invalid format
            'age': [25, 30, 35, 200, 28, 32, 27],  # Outlier (200)
            'salary': [50000, 60000, 55000, 65000, None, 70000, 58000],  # Missing value
        }
        
        return {"test_data": pd.DataFrame(data)}
    
    def _modify_schema(self, schema: SchemaResponse) -> SchemaResponse:
        """Create a modified version of a schema for version control testing"""
        
        # Add a new table
        new_table = TableInfo(
            name="modified_table",
            columns=[
                ColumnInfo(name="id", type="Integer", nullable=False),
                ColumnInfo(name="data", type="String", nullable=True),
            ],
            description="Added for testing"
        )
        
        modified_tables = list(schema.tables) + [new_table]
        
        return SchemaResponse(
            tables=modified_tables,
            relationships=schema.relationships,
            schema_format=schema.schema_format,
            metadata={**schema.metadata, "modified": True}
        )
    
    def _apply_improvements(self, schema: SchemaResponse, critiques: List) -> SchemaResponse:
        """Apply improvements based on AI critiques (simplified)"""
        
        # This is a simplified version - in practice, you'd implement specific fixes
        improved_tables = []
        
        for table in schema.tables:
            # Fix table naming issues
            improved_name = table.name.lower().replace(" ", "_")
            
            # Fix column issues
            improved_columns = []
            for column in table.columns:
                improved_column_name = column.name.lower().replace(" ", "_")
                
                # Avoid reserved words
                if improved_column_name in ['user', 'order', 'value']:
                    improved_column_name = f"{improved_name}_{improved_column_name}"
                
                improved_columns.append(ColumnInfo(
                    name=improved_column_name,
                    type=column.type,
                    nullable=column.nullable,
                    unique=column.unique,
                    description=column.description
                ))
            
            improved_tables.append(TableInfo(
                name=improved_name,
                columns=improved_columns,
                description=table.description or f"Improved {improved_name} table"
            ))
        
        return SchemaResponse(
            tables=improved_tables,
            relationships=schema.relationships,
            schema_format=schema.schema_format,
            metadata={**schema.metadata, "improved": True}
        )
    
    def _assert(self, condition: bool, message: str):
        """Assert condition and record result"""
        if condition:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(message)
            console.print(f"[red]❌ ASSERTION FAILED: {message}[/red]")
    
    def _record_success(self, component: str, message: str):
        """Record successful test"""
        self.test_results['test_details'].append({
            'component': component,
            'status': 'success',
            'message': message
        })
        console.print(f"[green]✅ {component}: {message}[/green]")
    
    def _record_error(self, error_message: str):
        """Record test error"""
        self.test_results['failed'] += 1
        self.test_results['errors'].append(error_message)
        console.print(f"[red]❌ ERROR: {error_message}[/red]")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / max(total_tests, 1)) * 100
        
        # Get performance metrics
        perf_stats = performance_monitor.get_operation_statistics()
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': self.test_results['passed'],
                'failed': self.test_results['failed'],
                'success_rate': success_rate,
                'status': 'PASSED' if success_rate == 100 else 'FAILED'
            },
            'test_details': self.test_results['test_details'],
            'errors': self.test_results['errors'],
            'performance_metrics': perf_stats,
            'system_health': performance_monitor.get_system_health()
        }
        
        return report

# ==================== Test Execution ====================

async def run_comprehensive_tests():
    """Run the comprehensive test suite"""
    
    console.print("[bold green]🚀 SchemaSage Week 7-8 Comprehensive Test Suite[/bold green]")
    console.print("Testing: AI Critique, Schema Merging, Version Control, Performance Monitoring")
    console.print("=" * 80)
    
    test_suite = SchemaSageTestSuite()
    
    try:
        report = await test_suite.run_all_tests()
        
        # Display final report
        console.print("\n" + "=" * 80)
        console.print("[bold blue]📊 FINAL TEST REPORT[/bold blue]")
        console.print("=" * 80)
        
        summary = report['test_summary']
        console.print(f"Total Tests: {summary['total_tests']}")
        console.print(f"Passed: [green]{summary['passed']}[/green]")
        console.print(f"Failed: [red]{summary['failed']}[/red]")
        console.print(f"Success Rate: [{'green' if summary['success_rate'] == 100 else 'red'}]{summary['success_rate']:.1f}%[/{'green' if summary['success_rate'] == 100 else 'red'}]")
        console.print(f"Status: [{'green' if summary['status'] == 'PASSED' else 'red'}]{summary['status']}[/{'green' if summary['status'] == 'PASSED' else 'red'}]")
        
        if report['errors']:
            console.print(f"\n[red]❌ ERRORS:[/red]")
            for error in report['errors']:
                console.print(f"  • {error}")
        
        # Performance summary
        if report['performance_metrics']:
            console.print(f"\n[blue]📈 PERFORMANCE SUMMARY:[/blue]")
            for op_name, stats in report['performance_metrics'].items():
                console.print(f"  {op_name}: {stats['count']} executions, avg {stats['avg_time']:.3f}s")
        
        # Save detailed report
        report_path = Path("test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        console.print(f"\n[blue]📄 Detailed report saved to: {report_path}[/blue]")
        
        return summary['status'] == 'PASSED'
        
    except Exception as e:
        console.print(f"[red]💥 Test suite execution failed: {e}[/red]")
        return False

if __name__ == "__main__":
    # Run the comprehensive test suite
    success = asyncio.run(run_comprehensive_tests())
    
    if success:
        console.print("\n[bold green]🎉 ALL TESTS PASSED! SchemaSage Week 7-8 implementation is complete and functional.[/bold green]")
        exit(0)
    else:
        console.print("\n[bold red]❌ SOME TESTS FAILED! Please review the errors above.[/bold red]")
        exit(1)
