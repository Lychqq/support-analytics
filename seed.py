import asyncio
from database import engine
from models import Ticket, TicketStatus, TicketCategory,TicketPriority,TicketSentiment
from sqlalchemy.ext.asyncio import AsyncSession

async def fill_tickets():
    async with AsyncSession(engine) as session:
        tickets = [
            Ticket(user_login='aggys', title='Забыл пароль',description='Забыл пароль от учетной записи и потерял доступ к привязанной почте как подтвердить личность помогите не хочу терять аккаунт', category=TicketCategory.complaint, priority=TicketPriority.mid, sentiment=TicketSentiment.neutral),

            Ticket(user_login='mariya_art', title='Баг с загрузкой историй', description='При попытке выложить историю приложение вылетает с ошибкой памяти на iOS', category=TicketCategory.bug, priority=TicketPriority.high, sentiment=TicketSentiment.negative),

            Ticket(user_login='sergey_biz', title='Спам-боты в сообществе', description='Под каждым постом боты оставляют ссылки на скам-казино, настройте фильтр', category=TicketCategory.complaint, priority=TicketPriority.high, sentiment=TicketSentiment.negative),

            Ticket(user_login='pavel_music', title='Папки для плейлистов', description='Сделайте возможность группировать сохраненную музыку по папкам и жанрам', category=TicketCategory.feature_request, priority=TicketPriority.low, sentiment=TicketSentiment.positive, status=TicketStatus.closed, csat=5),

            Ticket(user_login='elena_dev', title='Сломалась темная тема', description='В разделе сообщений белый текст отображается на белом фоне после обновления', category=TicketCategory.ui_ux, priority=TicketPriority.mid, sentiment=TicketSentiment.negative, status=TicketStatus.closed, csat=4),

            Ticket(user_login='dmitry_photo', title='Как подключить монетизацию?', description='Набрал 5000 подписчиков в паблике, подскажите где кнопка подачи заявки в партнерку', category=TicketCategory.question, priority=TicketPriority.low, sentiment=TicketSentiment.neutral, status=TicketStatus.closed, csat=5)
        ]

        session.add_all(tickets)

        await session.commit()


asyncio.run(fill_tickets())
    