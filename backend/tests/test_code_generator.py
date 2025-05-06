import pytest
from app.services.code_generator import CodeGenerator, CodeGenerationError
from app.models.schemas import (
    SchemaResponse,
    TableInfo,
    ColumnInfo,
    ColumnStatistics,
    Relationship,
    CodeGenFormat
)

@pytest.fixture
def code_generator():
    return CodeGenerator()

@pytest.fixture
def sample_schema():
    return SchemaResponse(
        tables=[
            TableInfo(
                name="users",
                row_count=100,
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        is_primary_key=True,
                        is_foreign_key=False,
                        nullable=False,
                        statistics=ColumnStatistics(
                            total_rows=100,
                            non_null_count=100,
                            null_count=0,
                            unique_count=100,
                            unique_percentage=100.0,
                            sample_values=[1, 2, 3]
                        )
                    ),
                    ColumnInfo(
                        name="email",
                        data_type="String",
                        is_primary_key=False,
                        is_foreign_key=False,
                        nullable=False,
                        statistics=ColumnStatistics(
                            total_rows=100,
                            non_null_count=100,
                            null_count=0,
                            unique_count=100,
                            unique_percentage=100.0,
                            sample_values=["test@example.com"]
                        ),
                        format="email"
                    ),
                    ColumnInfo(
                        name="profile",
                        data_type="JSON",
                        is_primary_key=False,
                        is_foreign_key=False,
                        nullable=True,
                        statistics=ColumnStatistics(
                            total_rows=100,
                            non_null_count=80,
                            null_count=20,
                            unique_count=80,
                            unique_percentage=100.0,
                            sample_values=[{"bio": "test"}]
                        ),
                        is_complex=True
                    )
                ]
            )
        ],
        relationships=[],
        bridge_tables=[]
    )

@pytest.mark.asyncio
async def test_generate_sqlalchemy_models(code_generator, sample_schema):
    """Test SQLAlchemy model generation"""
    code = await code_generator.generate_code(sample_schema, CodeGenFormat.SQLALCHEMY)
    
    assert code is not None
    assert "class Users(Base):" in code
    assert "id = Column(Integer, primary_key=True)" in code
    assert "email = Column(String" in code
    assert "profile = Column(JSON" in code

@pytest.mark.asyncio
async def test_generate_sql_ddl(code_generator, sample_schema):
    """Test SQL DDL generation"""
    code = await code_generator.generate_code(sample_schema, CodeGenFormat.SQL)
    
    assert code is not None
    assert "CREATE TABLE users" in code
    assert "id INTEGER PRIMARY KEY" in code
    assert "email" in code
    assert "profile JSON" in code

@pytest.mark.asyncio
async def test_generate_json_schema(code_generator, sample_schema):
    """Test JSON Schema generation"""
    code = await code_generator.generate_code(sample_schema, CodeGenFormat.JSON)
    
    assert code is not None
    assert '"title": "Database Schema"' in code
    assert '"type": "object"' in code
    assert '"properties"' in code

@pytest.mark.asyncio
async def test_unsupported_format(code_generator, sample_schema):
    """Test handling of unsupported format"""
    with pytest.raises(NotImplementedError):
        await code_generator.generate_code(sample_schema, CodeGenFormat.DBML)

@pytest.mark.asyncio
async def test_invalid_schema(code_generator):
    """Test handling of invalid schema"""
    invalid_schema = SchemaResponse(
        tables=[],  # Empty tables should raise an error
        relationships=[],
        bridge_tables=[]
    )
    
    with pytest.raises(CodeGenerationError):
        await code_generator.generate_code(invalid_schema, CodeGenFormat.SQL)