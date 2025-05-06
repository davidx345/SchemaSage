import pytest
import json
from app.core.schema_detector import SchemaDetector, SchemaValidationError

@pytest.fixture
def schema_detector():
    return SchemaDetector()

@pytest.fixture
def sample_json_data():
    return json.dumps([{
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
        "is_active": True,
        "joined_at": "2024-01-01",
        "profile": {"bio": "Test bio"}
    }])

@pytest.fixture
def sample_csv_data():
    return """id,name,email,age,is_active,joined_at
1,Test User,test@example.com,25,true,2024-01-01"""

@pytest.mark.asyncio
async def test_detect_json_schema(schema_detector, sample_json_data):
    """Test JSON schema detection"""
    schema = await schema_detector.detect_from_text(sample_json_data)
    
    assert schema is not None
    assert len(schema.tables) == 1
    
    table = schema.tables[0]
    assert table.name == "main_table"
    
    # Verify column detection
    column_names = {col.name for col in table.columns}
    expected_columns = {"id", "name", "email", "age", "is_active", "joined_at", "profile"}
    assert column_names == expected_columns
    
    # Verify data type inference
    columns_dict = {col.name: col for col in table.columns}
    assert columns_dict["id"].data_type == "INTEGER"
    assert columns_dict["name"].data_type == "String"
    assert columns_dict["email"].data_type == "String"
    assert columns_dict["email"].format == "email"
    assert columns_dict["age"].data_type == "INTEGER"
    assert columns_dict["is_active"].data_type == "Boolean"
    assert columns_dict["joined_at"].data_type == "DateTime"
    assert columns_dict["profile"].data_type == "JSON"

@pytest.mark.asyncio
async def test_detect_csv_schema(schema_detector, sample_csv_data):
    """Test CSV schema detection"""
    schema = await schema_detector.detect_from_text(sample_csv_data)
    
    assert schema is not None
    assert len(schema.tables) == 1
    
    table = schema.tables[0]
    assert table.name == "main_table"
    
    # Verify column detection
    column_names = {col.name for col in table.columns}
    expected_columns = {"id", "name", "email", "age", "is_active", "joined_at"}
    assert column_names == expected_columns

@pytest.mark.asyncio
async def test_invalid_json_data(schema_detector):
    """Test handling of invalid JSON data"""
    with pytest.raises(SchemaValidationError):
        await schema_detector.detect_from_text("invalid json")

@pytest.mark.asyncio
async def test_empty_data(schema_detector):
    """Test handling of empty data"""
    with pytest.raises(SchemaValidationError):
        await schema_detector.detect_from_text("")

@pytest.mark.asyncio
async def test_detection_options(schema_detector):
    """Test schema detection options"""
    data = json.dumps([{
        "user_id": 1,
        "name": None,
        "email": "test@example.com"
    }])
    
    # Test with default options
    schema = await schema_detector.detect_from_text(data)
    assert len(schema.relationships) > 0  # detectRelations=True
    assert any(col.nullable for col in schema.tables[0].columns)  # generateNullable=True
    
    # Test with custom options
    schema_detector.set_detection_options(
        detect_relations=False,
        generate_nullable=False
    )
    schema = await schema_detector.detect_from_text(data)
    assert len(schema.relationships) == 0  # detectRelations=False
    assert not any(col.nullable for col in schema.tables[0].columns)  # generateNullable=False