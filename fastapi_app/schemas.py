from pydantic import BaseModel
from typing import Optional


class LoveAnalysisCreate(BaseModel):
    convo: str
    target_id: int


class LoveAnalysisOut(BaseModel):
    content: str

    class Config:
        from_attributes = True


class StyleCreate(BaseModel):
    convo: str
    target_id: int


class Style(StyleCreate):
    content: str


class ChatStrategyCreate(BaseModel):
    target_id: int


class ChatStrategyOut(BaseModel):
    content: str


class ReplyOptionsCreate(BaseModel):
    target_id: int


class ReplyOptionsOut(BaseModel):
    option1: str
    option2: str
    option3: str
    option4: str


class TargetBase(BaseModel):
    name: str
    gender: Optional[str] = None
    relationship_context: Optional[str] = None
    relationship_perception: Optional[str] = None
    relationship_goals: Optional[str] = None
    relationship_goals_long: Optional[str] = None
    personality: Optional[str] = None
    language: Optional[str] = None


class TargetCreate(TargetBase):
    pass


class TargetOut(TargetBase):
    id: int

    class Config:
        from_attributes = True
