from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., "N12", "Al Jazeera"
    location = Column(String) # e.g., "Israel", "Qatar"
    political_orientation = Column(String) # e.g., "Center", "Right"
    known_bias = Column(String) # Notes on specific bias
    base_url = Column(String)
    
    articles = relationship("Article", back_populates="source")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    average_title_en = Column(String)
    average_title_he = Column(String)
    comparative_summary_en = Column(Text)
    comparative_summary_he = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    category = Column(String, index=True) # General News, Economics, Culture, Technology, Geopolitics

    articles = relationship("Article", back_populates="cluster")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    original_title = Column(String)
    title_en = Column(String, nullable=True)
    title_he = Column(String, nullable=True)
    original_url = Column(String, unique=True, index=True)
    published_at = Column(DateTime)
    bias_warning_en = Column(String, nullable=True)
    bias_warning_he = Column(String, nullable=True)
    
    source_id = Column(Integer, ForeignKey("sources.id"))
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)

    source = relationship("Source", back_populates="articles")
    cluster = relationship("Cluster", back_populates="articles")
