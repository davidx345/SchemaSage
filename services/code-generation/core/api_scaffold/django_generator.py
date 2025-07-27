"""
Django REST Framework scaffolding generator
"""
import logging
from typing import Dict, List, Optional, Any

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .base import APIComponent, ComponentType, APIFramework, TypeMapper, CodeTemplateEngine

logger = logging.getLogger(__name__)

class DjangoGenerator:
    """Generates Django REST Framework scaffolding"""
    
    def __init__(self):
        self.type_mapper = TypeMapper()
        self.template_engine = CodeTemplateEngine()
    
    def generate_models(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Django models"""
        components = []
        
        for table in schema.tables:
            model_component = self._generate_django_model(table, schema, options)
            components.append(model_component)
        
        return components
    
    def _generate_django_model(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single Django model"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from django.db import models",
            "from django.contrib.auth.models import User",
            "from django.core.validators import MinLengthValidator, MaxLengthValidator"
        ]
        
        # Generate fields
        fields = []
        for column in table.columns:
            django_field = self._get_django_field(column)
            fields.append(f"    {column.name} = {django_field}")
        
        content = f'''"""
{class_name} Django model
"""
{self.template_engine.generate_imports(imports)}


class {class_name}(models.Model):
    """Django model for {table.name} table"""
{chr(10).join(fields)}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = '{table.name}'
        ordering = ['-created_at']
        verbose_name = '{class_name}'
        verbose_name_plural = '{class_name}s'
    
    def __str__(self):
        return f"{class_name} {{self.id}}"
    
    def save(self, *args, **kwargs):
        # Add custom save logic here
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('{table.name}-detail', kwargs={{'pk': self.pk}})
'''
        
        return APIComponent(
            name=f"{class_name}Model",
            component_type=ComponentType.MODEL,
            framework=APIFramework.DJANGO,
            content=content,
            file_path=f"models/{table.name}.py",
            dependencies=["django"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "fields_count": len(table.columns)
            }
        )
    
    def _get_django_field(self, column: ColumnInfo) -> str:
        """Map column type to Django field"""
        
        field_map = {
            'int': 'models.IntegerField',
            'bigint': 'models.BigIntegerField',
            'varchar': 'models.CharField',
            'text': 'models.TextField',
            'boolean': 'models.BooleanField',
            'date': 'models.DateField',
            'datetime': 'models.DateTimeField',
            'time': 'models.TimeField',
            'decimal': 'models.DecimalField',
            'float': 'models.FloatField',
            'json': 'models.JSONField',
            'uuid': 'models.UUIDField'
        }
        
        base_type = column.type.lower()
        django_field = field_map.get(base_type, 'models.CharField')
        
        # Add field options
        options = []
        
        if hasattr(column, 'max_length') and column.max_length:
            options.append(f"max_length={column.max_length}")
        
        if not getattr(column, 'required', True):
            options.append("null=True")
            options.append("blank=True")
        
        if hasattr(column, 'unique') and column.unique:
            options.append("unique=True")
        
        if hasattr(column, 'default') and column.default is not None:
            options.append(f"default={repr(column.default)}")
        
        if options:
            return f"{django_field}({', '.join(options)})"
        else:
            return f"{django_field}()"
    
    def generate_serializers(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate DRF serializers"""
        components = []
        
        for table in schema.tables:
            serializer_component = self._generate_serializer(table, schema, options)
            components.append(serializer_component)
        
        return components
    
    def _generate_serializer(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single DRF serializer"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from rest_framework import serializers",
            f"from models.{table.name} import {class_name}"
        ]
        
        # Generate field list
        field_names = [col.name for col in table.columns]
        
        content = f'''"""
{class_name} DRF serializers
"""
{self.template_engine.generate_imports(imports)}


class {class_name}Serializer(serializers.ModelSerializer):
    """Serializer for {class_name} model"""
    
    class Meta:
        model = {class_name}
        fields = {field_names}
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, data):
        """Custom validation logic"""
        # Add custom validation here
        return data
    
    def create(self, validated_data):
        """Custom create logic"""
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Custom update logic"""
        return super().update(instance, validated_data)


class {class_name}CreateSerializer(serializers.ModelSerializer):
    """Serializer for creating {class_name}"""
    
    class Meta:
        model = {class_name}
        fields = {[f for f in field_names if f not in ['id', 'created_at', 'updated_at']]}
    
    def validate(self, data):
        """Validation for creation"""
        # Add creation-specific validation
        return data


class {class_name}UpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating {class_name}"""
    
    class Meta:
        model = {class_name}
        fields = {[f for f in field_names if f not in ['id', 'created_at', 'updated_at']]}
        extra_kwargs = {{
            field: {{'required': False}} for field in {[f for f in field_names if f not in ['id', 'created_at', 'updated_at']]}
        }}
    
    def validate(self, data):
        """Validation for updates"""
        # Add update-specific validation
        return data


class {class_name}ListSerializer(serializers.ModelSerializer):
    """Serializer for listing {class_name} (minimal fields)"""
    
    class Meta:
        model = {class_name}
        fields = ('id', 'created_at', 'updated_at')  # Add key fields here
'''
        
        return APIComponent(
            name=f"{class_name}Serializer",
            component_type=ComponentType.SERIALIZER,
            framework=APIFramework.DJANGO,
            content=content,
            file_path=f"serializers/{table.name}_serializers.py",
            dependencies=["djangorestframework"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "field_count": len(field_names)
            }
        )
    
    def generate_views(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate DRF views"""
        components = []
        
        for table in schema.tables:
            view_component = self._generate_view(table, schema, options)
            components.append(view_component)
        
        return components
    
    def _generate_view(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single DRF view"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from rest_framework import viewsets, status, filters",
            "from rest_framework.decorators import action",
            "from rest_framework.response import Response",
            "from rest_framework.permissions import IsAuthenticated",
            "from django_filters.rest_framework import DjangoFilterBackend",
            f"from models.{table.name} import {class_name}",
            f"from serializers.{table.name}_serializers import {class_name}Serializer, {class_name}CreateSerializer, {class_name}UpdateSerializer"
        ]
        
        content = f'''"""
{class_name} DRF views
"""
{self.template_engine.generate_imports(imports)}


class {class_name}ViewSet(viewsets.ModelViewSet):
    """ViewSet for {class_name} operations"""
    
    queryset = {class_name}.objects.all()
    serializer_class = {class_name}Serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = '__all__'
    search_fields = []  # Add searchable fields
    ordering_fields = '__all__'
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return {class_name}CreateSerializer
        elif self.action in ['update', 'partial_update']:
            return {class_name}UpdateSerializer
        return {class_name}Serializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = {class_name}.objects.all()
        
        # Add custom filtering logic here
        # Example: filter by user ownership
        # if not self.request.user.is_staff:
        #     queryset = queryset.filter(owner=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Custom logic when creating"""
        # Example: set owner to current user
        # serializer.save(owner=self.request.user)
        serializer.save()
    
    def perform_update(self, serializer):
        """Custom logic when updating"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Custom logic when deleting"""
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """Custom action for {class_name}"""
        item = self.get_object()
        # Add custom logic here
        
        return Response({{'message': 'Custom action completed'}})
    
    @action(detail=False)
    def stats(self, request):
        """Get statistics for {class_name}"""
        total_count = self.get_queryset().count()
        
        return Response({{
            'total_count': total_count,
            # Add more statistics here
        }})
'''
        
        return APIComponent(
            name=f"{class_name}ViewSet",
            component_type=ComponentType.VIEW,
            framework=APIFramework.DJANGO,
            content=content,
            file_path=f"views/{table.name}_views.py",
            dependencies=["djangorestframework", "django-filter"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name
            }
        )
    
    def generate_urls(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Django URL configurations"""
        components = []
        
        # Generate individual URL files for each table
        for table in schema.tables:
            url_component = self._generate_table_urls(table, schema, options)
            components.append(url_component)
        
        # Generate main URLs file
        main_urls_component = self._generate_main_urls(schema, options)
        components.append(main_urls_component)
        
        return components
    
    def _generate_table_urls(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate URLs for a single table"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from django.urls import path, include",
            "from rest_framework.routers import DefaultRouter",
            f"from views.{table.name}_views import {class_name}ViewSet"
        ]
        
        content = f'''"""
URLs for {class_name}
"""
{self.template_engine.generate_imports(imports)}

router = DefaultRouter()
router.register(r'{table.name}', {class_name}ViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
'''
        
        return APIComponent(
            name=f"{class_name}URLs",
            component_type=ComponentType.URL,
            framework=APIFramework.DJANGO,
            content=content,
            file_path=f"urls/{table.name}_urls.py",
            dependencies=["djangorestframework"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name
            }
        )
    
    def _generate_main_urls(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate main URLs configuration"""
        
        imports = [
            "from django.urls import path, include"
        ]
        
        url_includes = []
        for table in schema.tables:
            url_includes.append(f"    path('api/{table.name}/', include('urls.{table.name}_urls')),")
        
        content = f'''"""
Main URL configuration
"""
{self.template_engine.generate_imports(imports)}

urlpatterns = [
{chr(10).join(url_includes)}
]
'''
        
        return APIComponent(
            name="MainURLs",
            component_type=ComponentType.URL,
            framework=APIFramework.DJANGO,
            content=content,
            file_path="urls/main.py",
            dependencies=["django"],
            imports=imports,
            metadata={
                "table_count": len(schema.tables)
            }
        )
