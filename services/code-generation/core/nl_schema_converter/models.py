"""
Data models and patterns for natural language schema conversion
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class EntityType(Enum):
    """Types of database entities"""
    USER = "user"
    PRODUCT = "product"
    ORDER = "order"
    CONTENT = "content"
    CATEGORY = "category"
    GENERIC = "generic"


class RelationshipType(Enum):
    """Types of database relationships"""
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    match_type: str
    value: str
    confidence: float
    context: Optional[str] = None


@dataclass
class ExtractedEntity:
    """Entity extracted from natural language"""
    name: str
    entity_type: EntityType
    confidence: float
    fields: List[str]
    context: Optional[str] = None


@dataclass
class ExtractedRelationship:
    """Relationship extracted from natural language"""
    source: str
    target: str
    relationship_type: RelationshipType
    confidence: float
    context: Optional[str] = None


@dataclass
class FieldInfo:
    """Information about a field"""
    name: str
    inferred_type: str
    nullable: bool
    is_primary_key: bool = False
    unique: bool = False
    default: Optional[Any] = None
    validation: Optional[str] = None
    description: Optional[str] = None


class NLPatterns:
    """Natural language patterns for entity extraction"""
    
    # Entity extraction patterns
    ENTITY_PATTERNS = {
        'direct_entities': [
            r'\b(user|customer|student|teacher|employee|product|order|item|post|comment|category|subject|course|department|company|project)\b',
            r'\b(\w+) table\b',
            r'\b(\w+) entity\b',
            r'\b(\w+) with\b',
            r'database with (\w+)',
            r'create (\w+)',
            r'(\w+) have\b',
            r'(\w+) can\b'
        ],
        'plural_entities': [
            r'\b(users|customers|students|teachers|employees|products|orders|items|posts|comments|categories|subjects|courses|departments|companies|projects)\b',
            r'multiple (\w+)',
            r'many (\w+)',
            r'several (\w+)'
        ],
        'contextual_entities': [
            r'(\w+) system',
            r'(\w+) management',
            r'manage (\w+)',
            r'track (\w+)',
            r'store (\w+)'
        ]
    }
    
    # Relationship extraction patterns
    RELATIONSHIP_PATTERNS = {
        'one_to_many': [
            r'(\w+) has many (\w+)',
            r'(\w+) can have multiple (\w+)',
            r'each (\w+) can have multiple (\w+)',
            r'(\w+) contains many (\w+)'
        ],
        'many_to_one': [
            r'(\w+) belongs to (\w+)',
            r'(\w+) references (\w+)',
            r'each (\w+) belongs to (\w+)',
            r'(\w+) is part of (\w+)'
        ],
        'many_to_many': [
            r'(\w+) and (\w+) have a many-to-many relationship',
            r'(\w+) can enroll in multiple (\w+)',
            r'(\w+) can be assigned to multiple (\w+)',
            r'many (\w+) (?:can )?(?:have|belong to) many (\w+)'
        ],
        'one_to_one': [
            r'(\w+) has one (\w+)',
            r'each (\w+) has exactly one (\w+)',
            r'(\w+) is linked to one (\w+)'
        ]
    }
    
    # Field extraction patterns
    FIELD_PATTERNS = {
        'explicit_fields': [
            r'(\w+) with (\w+(?:, \w+)*) fields?',
            r'(\w+) containing (\w+(?:, \w+)*)',
            r'(\w+): (\w+(?:, \w+)*)',
            r'(\w+) have (\w+(?:, \w+)*)',
            r'(\w+) has (\w+(?:, \w+)*)'
        ],
        'compound_fields': [
            r'(\w+) have (\w+) and (\w+)',
            r'(\w+) have (\w+), (\w+)',
            r'(\w+) with (\w+) and (\w+)',
            r'(\w+) including (\w+), (\w+), and (\w+)'
        ],
        'descriptive_fields': [
            r'(\w+) should store (\w+)',
            r'(\w+) needs (\w+)',
            r'(\w+) contains (\w+)',
            r'(\w+) tracks (\w+)'
        ]
    }


class StandardFields:
    """Standard fields for different entity types"""
    
    BASE_FIELDS = [
        FieldInfo(
            name="id",
            inferred_type="Integer",
            nullable=False,
            is_primary_key=True,
            description="Primary key"
        ),
        FieldInfo(
            name="created_at",
            inferred_type="DateTime",
            nullable=False,
            default="now()",
            description="Record creation timestamp"
        ),
        FieldInfo(
            name="updated_at",
            inferred_type="DateTime",
            nullable=False,
            default="now()",
            description="Record update timestamp"
        )
    ]
    
    USER_FIELDS = [
        FieldInfo(name="email", inferred_type="String", nullable=False, unique=True, validation="email"),
        FieldInfo(name="first_name", inferred_type="String", nullable=False),
        FieldInfo(name="last_name", inferred_type="String", nullable=False),
        FieldInfo(name="is_active", inferred_type="Boolean", nullable=False, default=True)
    ]
    
    PRODUCT_FIELDS = [
        FieldInfo(name="name", inferred_type="String", nullable=False),
        FieldInfo(name="description", inferred_type="Text", nullable=True),
        FieldInfo(name="price", inferred_type="Float", nullable=True),
        FieldInfo(name="is_active", inferred_type="Boolean", nullable=False, default=True)
    ]
    
    ORDER_FIELDS = [
        FieldInfo(name="total_amount", inferred_type="Float", nullable=False),
        FieldInfo(name="status", inferred_type="String", nullable=False, default="pending"),
        FieldInfo(name="order_date", inferred_type="DateTime", nullable=False, default="now()")
    ]
    
    CONTENT_FIELDS = [
        FieldInfo(name="title", inferred_type="String", nullable=False),
        FieldInfo(name="content", inferred_type="Text", nullable=False),
        FieldInfo(name="is_published", inferred_type="Boolean", nullable=False, default=False),
        FieldInfo(name="published_at", inferred_type="DateTime", nullable=True)
    ]
    
    CATEGORY_FIELDS = [
        FieldInfo(name="name", inferred_type="String", nullable=False, unique=True),
        FieldInfo(name="description", inferred_type="Text", nullable=True),
        FieldInfo(name="is_active", inferred_type="Boolean", nullable=False, default=True)
    ]
    
    @classmethod
    def get_fields_for_entity_type(cls, entity_type: EntityType) -> List[FieldInfo]:
        """Get standard fields for entity type"""
        base_fields = cls.BASE_FIELDS.copy()
        
        if entity_type == EntityType.USER:
            return base_fields + cls.USER_FIELDS
        elif entity_type == EntityType.PRODUCT:
            return base_fields + cls.PRODUCT_FIELDS
        elif entity_type == EntityType.ORDER:
            return base_fields + cls.ORDER_FIELDS
        elif entity_type == EntityType.CONTENT:
            return base_fields + cls.CONTENT_FIELDS
        elif entity_type == EntityType.CATEGORY:
            return base_fields + cls.CATEGORY_FIELDS
        else:
            return base_fields


class TypeInference:
    """Type inference utilities"""
    
    TYPE_PATTERNS = {
        'String': [
            'name', 'title', 'email', 'phone', 'address', 'city', 'state', 'country',
            'first_name', 'last_name', 'username', 'password', 'status', 'type'
        ],
        'Text': [
            'description', 'content', 'text', 'notes', 'comment', 'message', 'body',
            'summary', 'details', 'bio', 'about'
        ],
        'Integer': [
            'age', 'count', 'number', 'quantity', 'rank', 'position', 'level',
            'score', 'rating', 'year', 'month', 'day'
        ],
        'Float': [
            'price', 'amount', 'cost', 'fee', 'rate', 'percentage', 'weight',
            'height', 'width', 'length', 'latitude', 'longitude'
        ],
        'Boolean': [
            'is_active', 'is_enabled', 'is_verified', 'is_published', 'is_deleted',
            'has_', 'can_', 'should_', 'active', 'enabled', 'verified', 'published'
        ],
        'DateTime': [
            'date', 'time', 'created_at', 'updated_at', 'deleted_at', 'published_at',
            'started_at', 'ended_at', 'expires_at', 'birth_date', 'due_date'
        ],
        'JSON': [
            'metadata', 'settings', 'config', 'data', 'attributes', 'properties',
            'options', 'preferences', 'payload'
        ],
        'UUID': [
            'uuid', 'guid', 'token', 'hash'
        ]
    }
    
    @classmethod
    def infer_type_from_field_name(cls, field_name: str) -> str:
        """Infer data type from field name"""
        field_lower = field_name.lower()
        
        # Check each type pattern
        for data_type, patterns in cls.TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in field_lower:
                    return data_type
        
        # Special cases
        if field_lower.endswith('_id') and field_lower != 'id':
            return "Integer"  # Foreign key
        
        if 'email' in field_lower:
            return "String"
        
        if any(word in field_lower for word in ['phone', 'mobile', 'tel']):
            return "String"
        
        # Default to String
        return "String"
    
    @classmethod
    def infer_validation(cls, field_name: str, field_type: str) -> Optional[str]:
        """Infer validation rules from field name and type"""
        field_lower = field_name.lower()
        
        if 'email' in field_lower:
            return "email"
        elif any(word in field_lower for word in ['url', 'website', 'link']):
            return "url"
        elif any(word in field_lower for word in ['phone', 'mobile', 'tel']):
            return "phone"
        
        return None


class EntityClassifier:
    """Classifies entities into types"""
    
    ENTITY_TYPE_KEYWORDS = {
        EntityType.USER: [
            'user', 'customer', 'student', 'teacher', 'employee', 'member',
            'person', 'admin', 'moderator', 'author', 'contributor'
        ],
        EntityType.PRODUCT: [
            'product', 'item', 'merchandise', 'good', 'service', 'offering',
            'article', 'book', 'course', 'lesson'
        ],
        EntityType.ORDER: [
            'order', 'purchase', 'transaction', 'payment', 'invoice', 'receipt',
            'booking', 'reservation', 'appointment'
        ],
        EntityType.CONTENT: [
            'post', 'article', 'blog', 'news', 'story', 'page', 'document',
            'content', 'media', 'file', 'image', 'video'
        ],
        EntityType.CATEGORY: [
            'category', 'tag', 'type', 'classification', 'group', 'section',
            'department', 'division', 'subject', 'topic'
        ]
    }
    
    @classmethod
    def classify_entity(cls, entity_name: str) -> EntityType:
        """Classify entity into type"""
        entity_lower = entity_name.lower()
        
        for entity_type, keywords in cls.ENTITY_TYPE_KEYWORDS.items():
            if any(keyword in entity_lower for keyword in keywords):
                return entity_type
        
        return EntityType.GENERIC
    
    @classmethod
    def get_confidence_score(cls, entity_name: str, entity_type: EntityType) -> float:
        """Get confidence score for entity classification"""
        entity_lower = entity_name.lower()
        keywords = cls.ENTITY_TYPE_KEYWORDS.get(entity_type, [])
        
        # Exact match
        if entity_lower in keywords:
            return 1.0
        
        # Partial match
        matches = sum(1 for keyword in keywords if keyword in entity_lower)
        if matches > 0:
            return 0.7 + (matches * 0.1)
        
        return 0.1  # Default low confidence


# Utility functions
def normalize_entity_name(name: str) -> str:
    """Normalize entity name to standard format"""
    # Convert to lowercase and remove common prefixes/suffixes
    name = name.lower().strip()
    
    # Remove trailing 's' for plural forms
    if name.endswith('s') and len(name) > 3 and name not in ['status', 'address']:
        name = name[:-1]
    
    # Remove common words
    exclude_words = {'table', 'entity', 'model', 'data'}
    if name in exclude_words:
        return None
    
    return name


def is_valid_entity_name(name: str) -> bool:
    """Check if name is a valid entity name"""
    if not name or len(name) < 2:
        return False
    
    # Exclude common stop words
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'with', 'have', 'has', 'can', 'will',
        'database', 'table', 'create', 'multiple', 'each', 'many', 'some', 'all',
        'names', 'emails', 'fields', 'data', 'information'
    }
    
    return name.lower() not in stop_words


def normalize_field_name(name: str) -> str:
    """Normalize field name to snake_case"""
    # Convert spaces and hyphens to underscores
    name = name.replace(' ', '_').replace('-', '_')
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove special characters except underscores
    import re
    name = re.sub(r'[^a-z0-9_]', '', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name
