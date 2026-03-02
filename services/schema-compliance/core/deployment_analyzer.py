"""
Deployment Analyzer Module
Uses OpenAI to analyze natural language descriptions and generate schema recommendations
"""

import openai
import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DeploymentAnalyzer:
    """Analyzes deployment requirements using AI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. AI analysis will not work.")
            self.client = None
        else:
            openai.api_key = self.api_key
            self.client = openai
    
    async def analyze_description(
        self,
        description: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze natural language description and generate schema
        
        Args:
            description: User's natural language database description
            preferences: Optional user preferences (provider, region, budget)
            
        Returns:
            Dict containing analysis, recommendations, and schema
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(description, preferences)
            
            # Call OpenAI
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add recommendations
            recommendations = self._generate_recommendations(result, preferences)
            result['recommendations'] = recommendations
            
            # Generate schema in multiple formats
            schema_formats = self._generate_schema_formats(result)
            result['schema'] = schema_formats
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ValueError("AI returned invalid JSON")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise ValueError(f"Analysis failed: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI"""
        return """You are an expert database architect. Analyze user requirements and return structured JSON.

Your task is to:
1. Identify the database type (postgresql, mysql, mongodb)
2. Determine appropriate version
3. Design table structures with columns, types, and constraints
4. Identify relationships between tables
5. Suggest features needed (auth, search, etc.)
6. Estimate database size

Return ONLY valid JSON in this exact format:
{
  "database_type": "postgresql",
  "version": "15",
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "integer", "constraints": ["primary_key", "auto_increment"]},
        {"name": "email", "type": "varchar(255)", "constraints": ["unique", "not_null"]}
      ],
      "purpose": "Store user accounts"
    }
  ],
  "relationships": [
    {"from": "orders", "to": "users", "type": "many_to_one", "foreign_key": "user_id"}
  ],
  "features": ["authentication", "full_text_search"],
  "estimated_size": "5GB"
}

Be thorough but concise. Include all necessary tables and relationships."""
    
    def _build_analysis_prompt(
        self,
        description: str,
        preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Build the user prompt"""
        prompt = f"User Request: {description}\n\n"
        
        if preferences:
            prompt += "User Preferences:\n"
            if preferences.get('provider'):
                prompt += f"- Preferred provider: {preferences['provider']}\n"
            if preferences.get('region'):
                prompt += f"- Preferred region: {preferences['region']}\n"
            if preferences.get('budget'):
                prompt += f"- Monthly budget: ${preferences['budget']}\n"
        
        prompt += "\nAnalyze this request and return structured JSON with database design."
        
        return prompt
    
    def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate cloud provider recommendations based on analysis"""
        
        # Extract requirements
        database_type = analysis.get('database_type', 'postgresql')
        estimated_size = analysis.get('estimated_size', '10GB')
        table_count = len(analysis.get('tables', []))
        
        # Parse size
        size_gb = self._parse_size(estimated_size)
        
        # Determine instance type based on complexity
        instance_type = self._recommend_instance_type(
            size_gb=size_gb,
            table_count=table_count,
            provider=preferences.get('provider') if preferences else None
        )
        
        # Get preferred provider or default to AWS
        provider = preferences.get('provider', 'aws') if preferences else 'aws'
        
        # Calculate cost
        cost = self._estimate_cost(provider, instance_type, size_gb)
        
        # Generate reasoning
        reasoning = f"Based on {table_count} tables with estimated {estimated_size} storage, "
        reasoning += f"the {instance_type} instance provides optimal performance for your workload. "
        reasoning += f"This configuration supports moderate traffic and includes automated backups."
        
        # Generate alternatives
        alternatives = self._generate_alternatives(
            database_type,
            instance_type,
            size_gb,
            provider
        )
        
        return {
            "provider": provider,
            "instance_type": instance_type,
            "storage": size_gb,
            "cost_per_month": cost,
            "reasoning": reasoning,
            "alternatives": alternatives
        }
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to GB"""
        size_str = size_str.lower().strip()
        
        if 'tb' in size_str:
            return int(float(size_str.replace('tb', '').strip()) * 1024)
        elif 'gb' in size_str:
            return int(float(size_str.replace('gb', '').strip()))
        elif 'mb' in size_str:
            return max(1, int(float(size_str.replace('mb', '').strip()) / 1024))
        else:
            # Default to 10GB
            return 10
    
    def _recommend_instance_type(
        self,
        size_gb: int,
        table_count: int,
        provider: Optional[str]
    ) -> str:
        """Recommend instance type based on requirements"""
        
        provider = provider or 'aws'
        
        # Simple recommendation logic
        if provider == 'aws':
            if size_gb < 20 and table_count < 5:
                return 'db.t3.micro'
            elif size_gb < 50 and table_count < 10:
                return 'db.t3.small'
            elif size_gb < 100 and table_count < 20:
                return 'db.t3.medium'
            else:
                return 'db.t3.large'
        elif provider == 'gcp':
            if size_gb < 20 and table_count < 5:
                return 'db-f1-micro'
            elif size_gb < 50 and table_count < 10:
                return 'db-g1-small'
            elif size_gb < 100 and table_count < 20:
                return 'db-n1-standard-1'
            else:
                return 'db-n1-standard-2'
        else:  # azure
            if size_gb < 20 and table_count < 5:
                return 'Basic'
            elif size_gb < 50 and table_count < 10:
                return 'GeneralPurpose_Gen5_2'
            else:
                return 'GeneralPurpose_Gen5_4'
    
    def _estimate_cost(self, provider: str, instance_type: str, storage_gb: int) -> float:
        """
        Estimate monthly cost using AWS Pricing API for AWS, fallback to hardcoded for others
        """
        
        if provider == 'aws':
            try:
                # Try to use AWS Pricing API
                return self._get_aws_pricing_from_api(instance_type, storage_gb)
            except Exception as e:
                logger.warning(f"Failed to get AWS pricing from API, using fallback: {e}")
                # Fall back to hardcoded pricing
                return self._get_fallback_pricing(provider, instance_type, storage_gb)
        else:
            # Use hardcoded pricing for GCP and Azure
            return self._get_fallback_pricing(provider, instance_type, storage_gb)
    
    def _get_aws_pricing_from_api(self, instance_type: str, storage_gb: int) -> float:
        """Get real-time AWS RDS pricing from Pricing API"""
        try:
            import boto3
            import json
            
            # Create pricing client (must use us-east-1 region)
            pricing_client = boto3.client('pricing', region_name='us-east-1')
            
            # Get RDS instance pricing
            response = pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'instanceType',
                        'Value': instance_type
                    },
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'databaseEngine',
                        'Value': 'PostgreSQL'
                    },
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'deploymentOption',
                        'Value': 'Single-AZ'
                    }
                ],
                MaxResults=1
            )
            
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                
                # Extract on-demand pricing
                terms = price_item['terms']['OnDemand']
                price_dimensions = list(terms.values())[0]['priceDimensions']
                hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
                
                # Calculate monthly compute cost
                compute_cost = hourly_price * 730
                
                # Storage pricing (gp3)
                storage_cost = storage_gb * 0.115
                
                # Backup cost (50% of storage)
                backup_cost = storage_cost * 0.5
                
                total = compute_cost + storage_cost + backup_cost
                
                logger.info(f"AWS Pricing API: {instance_type} = ${hourly_price}/hr, total ${total}/month")
                
                return round(total, 2)
            else:
                raise Exception("No pricing data returned")
                
        except Exception as e:
            logger.error(f"AWS Pricing API error: {e}")
            raise
    
    def _get_fallback_pricing(self, provider: str, instance_type: str, storage_gb: int) -> float:
        """Fallback to hardcoded pricing"""
        
        # Hardcoded pricing (as of 2024)
        pricing = {
            'aws': {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068,
                'db.t3.large': 0.136,
                'db.t3.xlarge': 0.272,
                'db.t3.2xlarge': 0.544,
                'db.m5.large': 0.192,
                'db.m5.xlarge': 0.384,
                'db.m5.2xlarge': 0.768,
                'storage': 0.115
            },
            'gcp': {
                'db-f1-micro': 0.0150,
                'db-g1-small': 0.0350,
                'db-n1-standard-1': 0.0700,
                'db-n1-standard-2': 0.1400,
                'db-n1-standard-4': 0.2800,
                'db-n1-highmem-2': 0.1800,
                'db-n1-highmem-4': 0.3600,
                'storage': 0.170
            },
            'azure': {
                'Basic': 0.0200,
                'Standard_B1ms': 0.0280,
                'Standard_B2s': 0.0560,
                'GeneralPurpose_Gen5_2': 0.0800,
                'GeneralPurpose_Gen5_4': 0.1600,
                'GeneralPurpose_Gen5_8': 0.3200,
                'storage': 0.115
            }
        }
        
        provider_pricing = pricing.get(provider, pricing['aws'])
        
        # Compute cost (hourly * 730 hours/month)
        compute_cost = provider_pricing.get(instance_type, 0.068) * 730
        
        # Storage cost (per GB/month)
        storage_cost = storage_gb * provider_pricing.get('storage', 0.115)
        
        # Backup cost (50% of storage)
        backup_cost = storage_cost * 0.5
        
        total = compute_cost + storage_cost + backup_cost
        
        return round(total, 2)
    
    def _generate_alternatives(
        self,
        database_type: str,
        current_instance: str,
        storage_gb: int,
        current_provider: str
    ) -> List[Dict[str, Any]]:
        """Generate alternative provider options"""
        
        alternatives = []
        
        # Add other providers
        other_providers = ['aws', 'gcp', 'azure']
        other_providers.remove(current_provider)
        
        for provider in other_providers:
            instance = self._recommend_instance_type(storage_gb, 10, provider)
            cost = self._estimate_cost(provider, instance, storage_gb)
            
            alternatives.append({
                "provider": provider,
                "instance_type": instance,
                "cost_per_month": cost
            })
        
        return alternatives
    
    def _generate_schema_formats(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate schema in multiple formats"""
        
        tables = analysis.get('tables', [])
        relationships = analysis.get('relationships', [])
        
        return {
            "sqlalchemy": self._generate_sqlalchemy(tables, relationships),
            "prisma": self._generate_prisma(tables, relationships),
            "typeorm": self._generate_typeorm(tables, relationships),
            "raw_sql": self._generate_raw_sql(tables, relationships, analysis.get('database_type')),
            "tables": tables
        }
    
    def _generate_sqlalchemy(self, tables: List[Dict], relationships: List[Dict]) -> str:
        """Generate SQLAlchemy model code"""
        code = "from sqlalchemy import Column, Integer, String, ForeignKey\n"
        code += "from sqlalchemy.ext.declarative import declarative_base\n"
        code += "from sqlalchemy.orm import relationship\n\n"
        code += "Base = declarative_base()\n\n"
        
        for table in tables:
            class_name = ''.join(word.capitalize() for word in table['name'].split('_'))
            code += f"class {class_name}(Base):\n"
            code += f"    __tablename__ = '{table['name']}'\n"
            
            for col in table.get('columns', []):
                col_def = f"    {col['name']} = Column("
                
                # Map type
                if 'int' in col['type'].lower():
                    col_def += "Integer"
                elif 'varchar' in col['type'].lower() or 'text' in col['type'].lower():
                    col_def += "String"
                else:
                    col_def += "String"
                
                # Add constraints
                if 'primary_key' in col.get('constraints', []):
                    col_def += ", primary_key=True"
                if 'not_null' in col.get('constraints', []):
                    col_def += ", nullable=False"
                
                col_def += ")\n"
                code += col_def
            
            code += "\n"
        
        return code
    
    def _generate_prisma(self, tables: List[Dict], relationships: List[Dict]) -> str:
        """Generate Prisma schema"""
        code = "// Prisma schema\n\n"
        
        for table in tables:
            code += f"model {table['name'].capitalize()} {{\n"
            
            for col in table.get('columns', []):
                col_type = "Int" if 'int' in col['type'].lower() else "String"
                is_id = 'primary_key' in col.get('constraints', [])
                
                code += f"  {col['name']} {col_type}"
                if is_id:
                    code += " @id @default(autoincrement())"
                code += "\n"
            
            code += "}\n\n"
        
        return code
    
    def _generate_typeorm(self, tables: List[Dict], relationships: List[Dict]) -> str:
        """Generate TypeORM entity code"""
        code = "import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';\n\n"
        
        for table in tables:
            class_name = ''.join(word.capitalize() for word in table['name'].split('_'))
            code += f"@Entity()\nexport class {class_name} {{\n"
            
            for col in table.get('columns', []):
                if 'primary_key' in col.get('constraints', []):
                    code += f"  @PrimaryGeneratedColumn()\n"
                else:
                    code += f"  @Column()\n"
                
                col_type = "number" if 'int' in col['type'].lower() else "string"
                code += f"  {col['name']}: {col_type};\n\n"
            
            code += "}\n\n"
        
        return code
    
    def _generate_raw_sql(self, tables: List[Dict], relationships: List[Dict], db_type: str) -> str:
        """Generate raw SQL CREATE TABLE statements"""
        sql = f"-- {db_type.upper()} Schema\n\n"
        
        for table in tables:
            sql += f"CREATE TABLE {table['name']} (\n"
            
            columns = []
            for col in table.get('columns', []):
                col_def = f"  {col['name']} {col['type'].upper()}"
                
                constraints = col.get('constraints', [])
                if 'primary_key' in constraints:
                    col_def += " PRIMARY KEY"
                if 'auto_increment' in constraints:
                    col_def += " AUTO_INCREMENT" if db_type == 'mysql' else " SERIAL"
                if 'not_null' in constraints:
                    col_def += " NOT NULL"
                if 'unique' in constraints:
                    col_def += " UNIQUE"
                
                columns.append(col_def)
            
            sql += ",\n".join(columns)
            sql += "\n);\n\n"
        
        # Add foreign keys
        for rel in relationships:
            sql += f"ALTER TABLE {rel['from']} "
            sql += f"ADD FOREIGN KEY ({rel['foreign_key']}) "
            sql += f"REFERENCES {rel['to']}(id);\n"
        
        return sql


# Global instance
_analyzer = None


def get_deployment_analyzer() -> DeploymentAnalyzer:
    """Get or create global deployment analyzer instance"""
    global _analyzer
    
    if _analyzer is None:
        _analyzer = DeploymentAnalyzer()
    
    return _analyzer
