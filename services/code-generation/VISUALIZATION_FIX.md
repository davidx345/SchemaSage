# Schema Visualization Fix

## Problem

The frontend "Visualize" tab was not displaying entities and relationships because the backend API was only returning code strings (SQLAlchemy, Prisma, etc.) without the structured schema data needed for visualization.

## Root Cause

The `/api/schema/generate` endpoint was returning:
```json
{
  "sqlalchemy": "...",
  "prisma": "...",
  "typeorm": "...",
  "django": "...",
  "raw_sql": "...",
  "generated_at": "...",
  "description": "..."
}
```

But the frontend visualization expected:
```json
{
  "sqlalchemy": "...",
  "prisma": "...",
  "tables": [
    {
      "name": "users",
      "columns": [
        { "name": "id", "type": "integer", "is_primary_key": true },
        { "name": "email", "type": "string" }
      ]
    }
  ],
  "relationships": [
    {
      "source_table": "orders",
      "target_table": "users",
      "type": "many-to-one"
    }
  ]
}
```

## Solution

Updated `services/code-generation/routers/schema_generation.py`:

### Changes Made:

1. **Added `tables` and `relationships` to `MultiFormatResponse` model**:
   ```python
   class MultiFormatResponse(BaseModel):
       sqlalchemy: str
       prisma: str
       typeorm: str
       django: str
       raw_sql: str
       generated_at: datetime
       description: str
       tables: list = []  # NEW: For visualization
       relationships: list = []  # NEW: For visualization
   ```

2. **Extracted structured schema data from `schema_response`**:
   ```python
   # Convert schema_response tables to dict
   tables_data = []
   if hasattr(schema_response, 'tables'):
       for table in schema_response.tables:
           table_dict = {
               "name": table.name,
               "columns": [...],
               "primary_keys": table.primary_keys,
               "foreign_keys": table.foreign_keys,
               "description": table.description
           }
           tables_data.append(table_dict)
   
   # Convert relationships to dict
   relationships_data = []
   if hasattr(schema_response, 'relationships'):
       for rel in schema_response.relationships:
           rel_dict = {
               "source_table": rel.source_table,
               "source_column": rel.source_column,
               "target_table": rel.target_table,
               "target_column": rel.target_column,
               "type": rel.type
           }
           relationships_data.append(rel_dict)
   ```

3. **Included structured data in response**:
   ```python
   return MultiFormatResponse(
       sqlalchemy=generated_code.get('sqlalchemy', ''),
       prisma=generated_code.get('prisma', ''),
       typeorm=generated_code.get('typeorm', ''),
       django=generated_code.get('django', ''),
       raw_sql=generated_code.get('raw_sql', ''),
       generated_at=datetime.now(),
       description=request.description,
       tables=tables_data,  # NEW
       relationships=relationships_data  # NEW
   )
   ```

## How It Works

1. **Natural language input** → `nl_converter.convert_to_schema()` generates a `SchemaResponse` object with structured tables and relationships
2. **Code generation** → Loop through formats and generate code strings for each
3. **Schema extraction** → Extract tables and relationships from `SchemaResponse` and convert to JSON-serializable dicts
4. **Complete response** → Return both code strings AND structured schema data

## Schema Structure

### Tables Array:
```json
{
  "name": "users",
  "columns": [
    {
      "name": "id",
      "type": "Integer",
      "nullable": false,
      "is_primary_key": true,
      "is_foreign_key": false,
      "default": null,
      "unique": false,
      "description": "Primary key"
    }
  ],
  "primary_keys": ["id"],
  "foreign_keys": [],
  "description": "Table for managing users data"
}
```

### Relationships Array:
```json
{
  "source_table": "orders",
  "source_column": "user_id",
  "target_table": "users",
  "target_column": "id",
  "type": "many-to-one"
}
```

## Testing

After deploying, test with:
```bash
curl -X POST https://your-api/api/schema/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A blog with users, posts, and comments"
  }'
```

Verify the response includes:
- ✅ `sqlalchemy`, `prisma`, `typeorm`, `django`, `raw_sql` code strings
- ✅ `tables` array with table structures
- ✅ `relationships` array with table relationships

## Frontend Integration

The frontend can now use the `tables` and `relationships` properties to:
- Render entity-relationship diagrams
- Show table structures
- Display relationships visually
- Enable interactive schema exploration

No frontend changes needed - the visualization component already expects this structure!

## Deployment

```bash
git add services/code-generation/routers/schema_generation.py
git commit -m "fix: Add tables and relationships to schema generation response for visualization"
git subtree push --prefix=services/code-generation heroku main
```

## Status

✅ **Fix implemented and ready to deploy**
