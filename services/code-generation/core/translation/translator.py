"""
SQL Dialect Translator

Translates SQL queries between different database dialects.
"""

import logging
import re
import sqlparse
from typing import List, Tuple, Dict
from models.translation_models import (
    TranslationRequest, SyntaxChange, CompatibilityWarning,
    TranslationStatistics, CompatibilityLevel, WarningSeverity, ChangeCategory
)

logger = logging.getLogger(__name__)


class SQLTranslator:
    """Translate SQL between different dialects"""
    
    # Function mappings between dialects
    FUNCTION_MAPPINGS = {
        "postgresql": {
            "mysql": {
                "now()": "now()",
                "current_timestamp": "current_timestamp",
                "string_agg": "group_concat",
                "array_agg": "group_concat",
                "||": "concat",  # String concatenation
                "to_char": "date_format",
                "substring": "substr",
            },
            "sqlserver": {
                "now()": "getdate()",
                "current_timestamp": "getdate()",
                "string_agg": "string_agg",
                "||": "+",  # String concatenation
                "to_char": "format",
                "substring": "substring",
                "random()": "rand()",
            }
        },
        "mysql": {
            "postgresql": {
                "now()": "now()",
                "group_concat": "string_agg",
                "concat": "||",
                "ifnull": "coalesce",
                "auto_increment": "serial",
            },
            "sqlserver": {
                "now()": "getdate()",
                "group_concat": "string_agg",
                "concat": "+",
                "ifnull": "isnull",
                "limit": "top",
            }
        },
        "sqlserver": {
            "postgresql": {
                "getdate()": "now()",
                "isnull": "coalesce",
                "top": "limit",
                "+": "||",  # String concatenation (context-dependent)
                "len": "length",
            },
            "mysql": {
                "getdate()": "now()",
                "isnull": "ifnull",
                "top": "limit",
                "len": "length",
            }
        }
    }
    
    def __init__(self):
        self.syntax_changes: List[SyntaxChange] = []
        self.warnings: List[CompatibilityWarning] = []
        
    def translate(self, request: TranslationRequest) -> Tuple[str, CompatibilityLevel, TranslationStatistics, List[SyntaxChange], List[CompatibilityWarning], List[str]]:
        """
        Translate SQL query between dialects
        
        Args:
            request: Translation request
            
        Returns:
            Tuple of (translated_query, compatibility_level, statistics, syntax_changes, warnings, notes)
        """
        self.syntax_changes = []
        self.warnings = []
        
        source_dialect = request.source_dialect.value
        target_dialect = request.target_dialect.value
        
        # Parse the query
        parsed = sqlparse.parse(request.sql_query)[0]
        
        # Start translation
        translated_query = request.sql_query
        
        # Apply function mappings
        translated_query = self._translate_functions(
            translated_query, source_dialect, target_dialect
        )
        
        # Translate LIMIT/OFFSET syntax
        translated_query = self._translate_limit_offset(
            translated_query, source_dialect, target_dialect
        )
        
        # Translate string concatenation
        translated_query = self._translate_string_concat(
            translated_query, source_dialect, target_dialect
        )
        
        # Translate data types in DDL
        if "create table" in translated_query.lower():
            translated_query = self._translate_data_types(
                translated_query, source_dialect, target_dialect
            )
        
        # Format output if requested
        if request.format_output:
            translated_query = sqlparse.format(
                translated_query,
                reindent=True,
                keyword_case='upper'
            )
        
        # Calculate statistics
        statistics = self._calculate_statistics(request.sql_query, translated_query)
        
        # Determine compatibility level
        compatibility_level = self._determine_compatibility_level()
        
        # Generate notes
        notes = self._generate_notes(source_dialect, target_dialect)
        
        return translated_query, compatibility_level, statistics, self.syntax_changes, self.warnings, notes
    
    def _translate_functions(self, query: str, source: str, target: str) -> str:
        """Translate database-specific functions"""
        if source not in self.FUNCTION_MAPPINGS or target not in self.FUNCTION_MAPPINGS[source]:
            return query
        
        mappings = self.FUNCTION_MAPPINGS[source][target]
        translated = query
        
        for source_func, target_func in mappings.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(source_func), re.IGNORECASE)
            matches = pattern.findall(translated)
            
            if matches:
                translated = pattern.sub(target_func, translated)
                
                self.syntax_changes.append(SyntaxChange(
                    category=ChangeCategory.FUNCTION,
                    original_syntax=source_func,
                    translated_syntax=target_func,
                    reason=f"Function {source_func} translated to {target} equivalent",
                    is_automatic=True
                ))
        
        return translated
    
    def _translate_limit_offset(self, query: str, source: str, target: str) -> str:
        """Translate LIMIT/OFFSET syntax"""
        translated = query
        
        # PostgreSQL/MySQL LIMIT to SQL Server TOP
        if source in ["postgresql", "mysql"] and target == "sqlserver":
            # Match "LIMIT n" pattern
            limit_match = re.search(r'\bLIMIT\s+(\d+)\b', translated, re.IGNORECASE)
            if limit_match:
                limit_num = limit_match.group(1)
                # Add TOP after SELECT
                translated = re.sub(
                    r'\bSELECT\b',
                    f'SELECT TOP {limit_num}',
                    translated,
                    count=1,
                    flags=re.IGNORECASE
                )
                # Remove LIMIT clause
                translated = re.sub(
                    r'\bLIMIT\s+\d+\b',
                    '',
                    translated,
                    flags=re.IGNORECASE
                )
                
                self.syntax_changes.append(SyntaxChange(
                    category=ChangeCategory.LIMIT_SYNTAX,
                    original_syntax=f"LIMIT {limit_num}",
                    translated_syntax=f"TOP {limit_num}",
                    reason="SQL Server uses TOP instead of LIMIT",
                    is_automatic=True
                ))
        
        # SQL Server TOP to PostgreSQL/MySQL LIMIT
        elif source == "sqlserver" and target in ["postgresql", "mysql"]:
            top_match = re.search(r'\bSELECT\s+TOP\s+(\d+)\b', translated, re.IGNORECASE)
            if top_match:
                top_num = top_match.group(1)
                # Remove TOP from SELECT
                translated = re.sub(
                    r'\bSELECT\s+TOP\s+\d+\b',
                    'SELECT',
                    translated,
                    count=1,
                    flags=re.IGNORECASE
                )
                # Add LIMIT at end
                translated += f' LIMIT {top_num}'
                
                self.syntax_changes.append(SyntaxChange(
                    category=ChangeCategory.LIMIT_SYNTAX,
                    original_syntax=f"TOP {top_num}",
                    translated_syntax=f"LIMIT {top_num}",
                    reason="PostgreSQL/MySQL use LIMIT instead of TOP",
                    is_automatic=True
                ))
        
        return translated
    
    def _translate_string_concat(self, query: str, source: str, target: str) -> str:
        """Translate string concatenation operators"""
        translated = query
        
        # PostgreSQL || to SQL Server +
        if source == "postgresql" and target == "sqlserver":
            if "||" in translated:
                # This is complex - need to identify string concatenation vs other uses
                self.warnings.append(CompatibilityWarning(
                    severity=WarningSeverity.WARNING,
                    category=ChangeCategory.STRING_CONCAT,
                    message="String concatenation operator || should be replaced with +",
                    suggestion="Manually review and replace || with + for string concatenation",
                    requires_manual_review=True
                ))
        
        return translated
    
    def _translate_data_types(self, query: str, source: str, target: str) -> str:
        """Translate data types in CREATE TABLE statements"""
        translated = query
        
        # PostgreSQL to MySQL
        if source == "postgresql" and target == "mysql":
            type_mappings = {
                r'\bserial\b': 'int auto_increment',
                r'\bbigserial\b': 'bigint auto_increment',
                r'\btext\b': 'longtext',
                r'\bbytea\b': 'blob',
                r'\bboolean\b': 'tinyint(1)',
            }
            
            for pg_type, mysql_type in type_mappings.items():
                if re.search(pg_type, translated, re.IGNORECASE):
                    translated = re.sub(pg_type, mysql_type, translated, flags=re.IGNORECASE)
                    
                    self.syntax_changes.append(SyntaxChange(
                        category=ChangeCategory.DATA_TYPE,
                        original_syntax=pg_type,
                        translated_syntax=mysql_type,
                        reason=f"PostgreSQL type translated to MySQL equivalent",
                        is_automatic=True
                    ))
        
        return translated
    
    def _calculate_statistics(self, original: str, translated: str) -> TranslationStatistics:
        """Calculate translation statistics"""
        original_lines = len(original.splitlines())
        translated_lines = len(translated.splitlines())
        
        critical_warnings = sum(
            1 for w in self.warnings if w.severity == WarningSeverity.CRITICAL
        )
        
        manual_review = any(w.requires_manual_review for w in self.warnings)
        
        # Calculate confidence score
        if critical_warnings > 0:
            confidence = 30.0
        elif len(self.warnings) > 5:
            confidence = 50.0
        elif len(self.warnings) > 0:
            confidence = 70.0
        elif len(self.syntax_changes) > 10:
            confidence = 80.0
        else:
            confidence = 95.0
        
        return TranslationStatistics(
            original_lines=original_lines,
            translated_lines=translated_lines,
            syntax_changes=len(self.syntax_changes),
            warnings_count=len(self.warnings),
            critical_warnings=critical_warnings,
            manual_review_required=manual_review,
            confidence_score=confidence
        )
    
    def _determine_compatibility_level(self) -> CompatibilityLevel:
        """Determine overall compatibility level"""
        critical_warnings = sum(
            1 for w in self.warnings if w.severity == WarningSeverity.CRITICAL
        )
        
        if critical_warnings > 0:
            return CompatibilityLevel.NOT_COMPATIBLE
        elif any(w.requires_manual_review for w in self.warnings):
            return CompatibilityLevel.MANUAL_REVIEW_NEEDED
        elif len(self.warnings) > 3:
            return CompatibilityLevel.MOSTLY_COMPATIBLE
        else:
            return CompatibilityLevel.FULLY_COMPATIBLE
    
    def _generate_notes(self, source: str, target: str) -> List[str]:
        """Generate general notes about translation"""
        notes = []
        
        notes.append(f"Automatic translation from {source} to {target}")
        notes.append("Always test translated queries thoroughly before production use")
        
        if len(self.syntax_changes) > 0:
            notes.append(f"Applied {len(self.syntax_changes)} automatic syntax transformations")
        
        if len(self.warnings) > 0:
            notes.append(f"Generated {len(self.warnings)} warnings - review carefully")
        
        return notes


def translate_sql(request: TranslationRequest) -> Tuple[str, CompatibilityLevel, TranslationStatistics, List[SyntaxChange], List[CompatibilityWarning], List[str]]:
    """
    Convenience function to translate SQL
    
    Args:
        request: Translation request
        
    Returns:
        Tuple of (translated_query, compatibility_level, statistics, syntax_changes, warnings, notes)
    """
    translator = SQLTranslator()
    return translator.translate(request)
