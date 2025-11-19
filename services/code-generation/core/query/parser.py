"""
SQL Query Parser

Parses SQL queries to extract structure, tables, joins, and complexity metrics.
"""

import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Token, Function, Parenthesis
from sqlparse.tokens import Keyword, DML
from typing import List, Dict, Set, Optional, Tuple
import logging

from models.query_models import QueryType

logger = logging.getLogger(__name__)


class SQLParser:
    """Parse and analyze SQL queries"""
    
    def __init__(self):
        self.tables: Set[str] = set()
        self.columns: Set[str] = set()
        self.joins: List[str] = []
        self.where_clauses: List[str] = []
        self.subqueries: int = 0
        self.aggregations: List[str] = []
        
    def parse(self, query: str) -> Dict:
        """
        Parse SQL query and extract metadata
        
        Args:
            query: SQL query string
            
        Returns:
            Dictionary with parsed query metadata
        """
        try:
            # Parse query using sqlparse
            parsed = sqlparse.parse(query)[0]
            
            # Extract query type
            query_type = self._extract_query_type(parsed)
            
            # Extract tables
            self.tables = self._extract_tables(parsed)
            
            # Extract joins
            self.joins = self._extract_joins(query)
            
            # Extract WHERE clauses
            self.where_clauses = self._extract_where_clauses(parsed)
            
            # Count subqueries
            self.subqueries = self._count_subqueries(query)
            
            # Extract aggregations
            self.aggregations = self._extract_aggregations(parsed)
            
            # Calculate complexity
            complexity = self._calculate_complexity()
            
            return {
                "query_type": query_type,
                "tables": list(self.tables),
                "joins": self.joins,
                "where_clauses": self.where_clauses,
                "subqueries": self.subqueries,
                "aggregations": self.aggregations,
                "complexity_score": complexity
            }
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return {
                "query_type": QueryType.SELECT,
                "tables": [],
                "joins": [],
                "where_clauses": [],
                "subqueries": 0,
                "aggregations": [],
                "complexity_score": 0.0
            }
    
    def _extract_query_type(self, parsed) -> QueryType:
        """Extract query operation type (SELECT, INSERT, etc.)"""
        for token in parsed.tokens:
            if token.ttype is DML:
                stmt_type = token.value.upper()
                if stmt_type == "SELECT":
                    return QueryType.SELECT
                elif stmt_type == "INSERT":
                    return QueryType.INSERT
                elif stmt_type == "UPDATE":
                    return QueryType.UPDATE
                elif stmt_type == "DELETE":
                    return QueryType.DELETE
        
        return QueryType.SELECT
    
    def _extract_tables(self, parsed) -> Set[str]:
        """Extract table names from query"""
        tables = set()
        from_seen = False
        
        for token in parsed.tokens:
            if from_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.add(self._clean_table_name(str(identifier)))
                elif isinstance(token, Identifier):
                    tables.add(self._clean_table_name(str(token)))
                elif token.ttype is Keyword and token.value.upper() in ['WHERE', 'GROUP', 'ORDER', 'LIMIT', 'UNION']:
                    break
            
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
        
        return tables
    
    def _clean_table_name(self, name: str) -> str:
        """Clean table name (remove aliases, quotes, schema prefixes)"""
        # Remove AS alias
        if ' as ' in name.lower():
            name = name.lower().split(' as ')[0]
        elif ' ' in name and not '(' in name:
            name = name.split(' ')[0]
        
        # Remove quotes
        name = name.strip('"').strip("'").strip('`')
        
        # Get table name from schema.table
        if '.' in name:
            name = name.split('.')[-1]
        
        return name.strip()
    
    def _extract_joins(self, query: str) -> List[str]:
        """Extract JOIN types from query"""
        joins = []
        join_pattern = r'\b(INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|CROSS JOIN|JOIN)\b'
        
        matches = re.finditer(join_pattern, query, re.IGNORECASE)
        for match in matches:
            joins.append(match.group(1).upper())
        
        return joins
    
    def _extract_where_clauses(self, parsed) -> List[str]:
        """Extract WHERE clause conditions"""
        clauses = []
        
        for token in parsed.tokens:
            if isinstance(token, Where):
                where_str = str(token)
                # Split by AND/OR
                conditions = re.split(r'\bAND\b|\bOR\b', where_str, flags=re.IGNORECASE)
                clauses = [c.strip() for c in conditions if c.strip()]
        
        return clauses
    
    def _count_subqueries(self, query: str) -> int:
        """Count number of subqueries"""
        # Count SELECT statements after the first one
        select_count = len(re.findall(r'\bSELECT\b', query, re.IGNORECASE))
        return max(0, select_count - 1)
    
    def _extract_aggregations(self, parsed) -> List[str]:
        """Extract aggregation functions (COUNT, SUM, AVG, etc.)"""
        aggregations = []
        agg_pattern = r'\b(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT|ARRAY_AGG)\s*\('
        
        query_str = str(parsed)
        matches = re.finditer(agg_pattern, query_str, re.IGNORECASE)
        for match in matches:
            aggregations.append(match.group(1).upper())
        
        return aggregations
    
    def _calculate_complexity(self) -> float:
        """
        Calculate query complexity score (0-100)
        
        Factors:
        - Number of tables (joins)
        - Number of WHERE conditions
        - Subqueries
        - Aggregations
        """
        score = 0.0
        
        # Base complexity from tables
        num_tables = len(self.tables)
        if num_tables == 1:
            score += 10
        elif num_tables == 2:
            score += 25
        elif num_tables <= 5:
            score += 40
        else:
            score += 60
        
        # Add complexity for joins
        score += len(self.joins) * 8
        
        # Add complexity for WHERE clauses
        score += min(len(self.where_clauses) * 3, 15)
        
        # Add complexity for subqueries
        score += self.subqueries * 12
        
        # Add complexity for aggregations
        score += min(len(self.aggregations) * 5, 15)
        
        return min(score, 100.0)


def parse_query(query: str) -> Dict:
    """
    Convenience function to parse a query
    
    Args:
        query: SQL query string
        
    Returns:
        Dictionary with parsed metadata
    """
    parser = SQLParser()
    return parser.parse(query)
