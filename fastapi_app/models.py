from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    gender = Column(String, nullable=True)
    relationship_context = Column(String, nullable=True)
    relationship_perception = Column(String, nullable=True)
    relationship_goals = Column(String, nullable=True)
    relationship_goals_long = Column(String, nullable=True)
    personality = Column(String, nullable=True)
    language = Column(String, nullable=True)

    # Relationships
    conversation_snippets = relationship("ConversationSnippet", back_populates="target")
    love_analyses = relationship("LoveAnalysis", back_populates="target")
    styles = relationship("Style", back_populates="target")
    chat_strategies = relationship("ChatStrategy", back_populates="target")
    reply_options_flows = relationship("ReplyOptionsFlow", back_populates="target")


class ConversationSnippet(Base):
    __tablename__ = "conversation_snippets"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Foreign key and relationship
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    target = relationship("Target", back_populates="conversation_snippets")


class LoveAnalysis(Base):
    __tablename__ = "love_analysis"

    id = Column(Integer, primary_key=True, index=True)
    convo = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Foreign key and relationship
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    target = relationship("Target", back_populates="love_analyses")


class Style(Base):
    __tablename__ = "styles"

    id = Column(Integer, primary_key=True, index=True)
    convo = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Foreign key and relationship
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    target = relationship("Target", back_populates="styles")


class ChatStrategy(Base):
    __tablename__ = "chat_strategies"

    id = Column(Integer, primary_key=True, index=True)
    convo = Column(String, nullable=False)
    love_analysis = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Foreign key and relationship
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    target = relationship("Target", back_populates="chat_strategies")


class ReplyOptionsFlow(Base):
    __tablename__ = "reply_options_flows"

    id = Column(Integer, primary_key=True, index=True)
    chat_strategy = Column(String, nullable=False)
    convo = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)

    # Foreign key and relationship
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    target = relationship("Target", back_populates="reply_options_flows")
