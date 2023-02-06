from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pydantic import BaseSettings
from sqlalchemy import create_engine


alpha = 0.1


class Settings(BaseSettings):
    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str
    CLIENT_ORIGIN: str

    class Config:
        env_file = './.env'


settings = Settings()

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

app = Dash(__name__)

sql = """
select
  date, qty
from metrics
where name = 'weight_body_mass'
"""
df = pd.read_sql(sql, engine)
df['weight_ewm'] = df['qty'].ewm(alpha=alpha).mean() # https://deaddy.net/on-tracking-bodyweight.html
df['weight_diff_weekly_ewm'] = df['weight_ewm'] - df['weight_ewm'].shift(7)

# weight_ewm today vs 7 days ago
weight_ewm_change_7d = df.iloc[-1]['weight_ewm'] - df.iloc[-8]['weight_ewm']
weight_ewm_change_4d = df.iloc[-1]['weight_ewm'] - df.iloc[-5]['weight_ewm']
outstring = f"current weekly weight diff is {round(weight_ewm_change_7d, 2)} kg (goal is 0.19)"
outstring = f"current 4-day weight diff is {round(weight_ewm_change_4d, 2)} kg (goal is 0.11)"

fig = px.line(df, x="date", y="qty")
fig.add_trace(go.Scatter(x=df['date'], y=df['weight_ewm']))

app.layout = html.Div(children=[
    html.H1(children='HealthBrain'),
    html.Div(children=outstring),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
