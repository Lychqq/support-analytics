
from enum import Enum
from sqlmodel import SQLModel,Field
from datetime import datetime, timezone

class TicketStatus(str, Enum):
    new = 'new'
    closed = 'closed'
    progress = 'in progress'

class TicketCategory(str, Enum):
    bug = "bug"                         
    ui_ux = "ui_ux"                       
    complaint = "complaint"               
    feature_request = "feature_request"  
    question = "question"                 
    other = "other"

class TicketPriority(str, Enum):
    low = 'low'
    mid = 'mid'
    high = 'high'

class TicketSentiment(str,Enum):
    positive='positive'
    negative = 'negative'
    neutral = 'neutral'

class TicketBase(SQLModel):
    user_login: str = Field(index=True)
    description: str
    details: str | None = None

    category: TicketCategory = Field(default=TicketCategory.other)

    priority: TicketPriority = Field(default=TicketPriority.mid)

    sentiment: TicketSentiment = Field(default=TicketSentiment.neutral)


class Ticket(TicketBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default='Обращение')
    tags: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at:datetime | None = Field(default=None)
    csat: int | None = Field(default=None)    
    status: TicketStatus = Field(default=TicketStatus.new)


class TicketCreate(SQLModel):
    user_login: str
    description: str
    details: str | None = None


class TicketUpdate(SQLModel):
    csat: int | None = Field(default=None, ge=1, le=5)    
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    priority: TicketPriority | None = None


class TicketRead(TicketBase):
    id:int
    title:str
    tags:str | None
    status: TicketStatus
    created_at: datetime
    closed_at: datetime| None
    csat:int | None
