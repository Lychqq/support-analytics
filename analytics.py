import pandas as pd
from models import Ticket
import plotly.express as px


def calculated(tickets: list[Ticket]):
    if not tickets:
        return {}
    
    data = [t.model_dump() for t in tickets]
    df = pd.DataFrame(data)

    category = df['category'].value_counts().to_dict()
    status = df['status'].value_counts().to_dict()
    sentiment = df['sentiment'].value_counts().to_dict()
    priority = df['priority'].value_counts().to_dict()

    df['created_date'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
    daily_counts = df['created_date'].value_counts().sort_index().to_dict()

    top_tags = df['tags'].dropna().value_counts().head(5).to_dict() if 'tags' in df else {}

    backlog = int((df['status'] != 'closed').sum())

    csat_avg = round(float(df['csat'].dropna().mean()),1) if 'csat' in df and not df['csat'].dropna().empty else 0.0

    closed_df = df[df['closed_at'].notna()] if 'closed_at' in df else pd.DataFrame()

    if not closed_df.empty:
        time_diff = (pd.to_datetime(closed_df['closed_at']) - pd.to_datetime(closed_df['created_at'])).dt.total_seconds() / 60
        mttr = round(float(time_diff.mean()),1)
        sla_compliance = round(float((time_diff<=120).mean() * 100),1)
    else:
        mttr = 0.0
        sla_compliance = 100.0
    
    high_total = (df['priority'] == 'high').sum()
    high_closed = (closed_df['priority'] == 'high').sum() if not closed_df.empty else 0

    high_priority_rate = round(float((high_closed / high_total) * 100), 1) if high_total > 0 else 100.0

    hypotheses = generate_hyp(df)
    charts= create_charts(df)


    return {'total': len(df), 'backlog':backlog,'mttr': mttr,'sla_compliance':sla_compliance, 'csat_avg': csat_avg,'high_priority_rate':high_priority_rate, 'category':category, 'status': status, 'sentiment': sentiment, 'priority': priority,'daily_counts': daily_counts, 'top_tags':top_tags,'hypotheses':hypotheses,'charts':charts}



def generate_hyp(df: pd.DataFrame) -> list[str]:
    hypotheses = []

    neg = (df['sentiment']=='negative').sum()

    if 'csat' in df and df['csat'].mean() < 3.5:
        hypotheses.append(f"Внимание: низкая удовлетворенность пользователей (CSAT: {round(df['csat'].mean(), 1)})")

    if neg/len(df) > 0.45:
        hypotheses.append(f'Повышенный уровень негативных сообщений: {neg} обращений')

    neww = (df['status']=='new').sum()
     
    if neww/len(df) > 0.35:
        hypotheses.append(f'Внимание:{neww} новых обращений ожидают проверки')
    if 'tags' in df and not df['tags'].dropna().empty:
        top = df['tags'].dropna().mode()[0]
        hypotheses.append(f'Основной поток обращений связан с {top}')
    return hypotheses


def create_charts(df: pd.DataFrame) -> dict:
    fig_cat = px.pie(df,names='category',hole=0.5)
    fig_sent = px.bar(df, x='sentiment', color='sentiment')
    daily_df = df.groupby('created_date').size().reset_index(name='count')
    fig_time = px.line(daily_df,x='created_date', y='count',markers=True)


    charts = {
        'category_chart': fig_cat.to_json(),
        'sentiment_chart': fig_sent.to_json(),
        'timeline_chart': fig_time.to_json()
    }

    if 'tags' in df and not df['tags'].dropna().empty:
        tags_s = df['tags'].dropna().value_counts().head(5)
        fig_tags = px.bar(x=tags_s.index, y=tags_s.values,labels={'x':'Тег', 'y':'Количество'})
        charts['tags_chart'] = fig_tags.to_json()
    
    return charts