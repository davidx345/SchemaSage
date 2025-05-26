# filepath: c:\\\\Users\\\\femia\\\\Desktop\\\\Code\\\\Projects\\\\SchemaSage\\\\backend\\\\app\\\\models\\\\orm_models.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db.postgresql import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    schemas = relationship(
        "SchemaStorage", back_populates="project", cascade="all, delete-orphan"
    )


class SchemaStorage(Base):
    __tablename__ = "schema_storage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    schema_data = Column(
        JSON, nullable=False
    )  # Using generic JSON, can be JSONB in PostgreSQL
    # Consider adding versioning if needed
    # version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="schemas")
