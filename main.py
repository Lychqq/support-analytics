from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from database import crate_db_and_tables, SessionDep
from models import Ticket, TicketStatus, TicketPriority, TicketCategory, TicketSentiment
from sqlmodel import select
from typing import Annotated
from analytics import calculated
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime,timezone
from fastapi.responses import Response
from summarizer import TicketSummarizer
import asyncio

summarizer = TicketSummarizer()


@asynccontextmanager
async def lifespan(app:FastAPI):
    await crate_db_and_tables()
    yield


app = FastAPI(title='Support Analytics', lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"),name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request,name='index.html')


@app.post('/new_ticket')
async def create_ticket(ticket:Ticket, session:SessionDep):
    summ_data = await asyncio.to_thread(summarizer.extract,ticket.description)
    session.add(ticket)
    ticket.title = summ_data['title']
    ticket.tags = summ_data['tags']
    if summ_data.get('sentiment') in TicketSentiment.__members__:
        ticket.sentiment = TicketSentiment(summ_data['sentiment'])
    if summ_data.get('category') in TicketCategory.__members__:
        ticket.category = TicketCategory(summ_data['category'])
    if summ_data.get('priority') in TicketPriority.__members__:
        ticket.priority = TicketPriority(summ_data['priority'])
    await session.commit()
    await session.refresh(ticket)
    return ticket


@app.get('/tickets/')
async def get_tickets(session:SessionDep):
    result = await session.execute(select(Ticket))
    tickets = result.scalars().all()
    return tickets

@app.get('/tickets/{ticket_id}')
async def get_ticket(ticket_id:int, session:SessionDep):
    ticket = await session.get(Ticket,ticket_id)
    if not ticket:
        raise HTTPException(status_code=404,detail='Тикет не найден')
    return ticket


@app.patch('/tickets/{ticket_id}')
async def update_ticket(ticket: Annotated[Ticket,Depends(get_ticket)],session: SessionDep,status: TicketStatus | None = None,priority:TicketPriority | None = None, csat:int | None = None ):
    if status:
        ticket.status = status
    
    if priority:
        ticket.priority = priority
    if ticket.status == TicketStatus.closed and ticket.closed_at is None:
        ticket.closed_at = datetime.now(timezone.utc)
    elif ticket.status != TicketStatus.closed:
        ticket.closed_at = None
    
    if csat:
        ticket.csat = csat
    await session.commit()

    await session.refresh(ticket)

    return ticket



@app.get('/analytics/summary')
async def get_summary(session: SessionDep,category:TicketCategory | None = None, status:TicketStatus | None = None,priority: TicketPriority | None=None,sentiment: TicketSentiment | None = None):
    stm = select(Ticket)
    if category:
        stm = stm.where(Ticket.category == category)

    if status:
        stm = stm.where(Ticket.status == status)
    
    if priority:
        stm = stm.where(Ticket.priority == priority)
    if sentiment:
        stm = stm.where(Ticket.sentiment == sentiment)
    result = await session.execute(stm)
    tickets = result.scalars().all()

    d = await asyncio.to_thread(calculated, tickets)

    return d


@app.get('/export/csv')
async def export_csv(session:SessionDep):
    result = await session.execute(select(Ticket))

    tickets = result.scalars().all()
    
    import pandas as pd
    import io

    data = [t.model_dump() for t in tickets]

    df = pd.DataFrame(data)

    csv_buffer = io.StringIO()

    df.to_csv(csv_buffer,index=False)

    return Response(
        content=csv_buffer.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=vk_tickets_export.csv'}
    )