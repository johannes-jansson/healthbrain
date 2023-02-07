from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pydantic import BaseSettings
from sqlalchemy import create_engine


alpha = 0.1  # Used for ewm calculations
days = 3
relevant_metrics = ['weight_body_mass', 'dietary_energy']


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

relevant_metrics_string = '\',\''.join(relevant_metrics)
sql = """
select
  date, name, qty
from metrics
where name in {metrics}
""".format(metrics=f"('{relevant_metrics_string}')")
df = pd.read_sql(sql, engine)
df = df.pivot(index='date',columns='name',values='qty').reset_index()
df['weight_body_mass'] = df['weight_body_mass'].interpolate(method='linear', limit_direction='forward', axis=0)
df['weight_ewm'] = df['weight_body_mass'].ewm(alpha=alpha).mean() # https://deaddy.net/on-tracking-bodyweight.html
df['weight_diff_weekly_ewm'] = df['weight_ewm'] - df['weight_ewm'].shift(7)

# weight_ewm today vs 7 days ago
weight_ewm_change_xd = df.iloc[-1]['weight_ewm'] - df.iloc[-(days+1)]['weight_ewm']
in_avg_xd = df.iloc[-(days+1):-1]['dietary_energy'].mean()
outstring = f"current {days}-day weight diff is {round(weight_ewm_change_xd, 2)} kg on {round(in_avg_xd)} kcal (goal is 0.11)"

fig = px.line(df, x="date", y="weight_body_mass")
fig.add_trace(go.Scatter(x=df['date'], y=df['weight_ewm']))

fig2 = px.bar(df, x="date", y="dietary_energy")

app.layout = html.Div(children=[
    html.H1(children='HealthBrain 🧠'),
    html.Div(children=outstring),
    dcc.Graph(
        id='weight-graph',
        figure=fig
    ),
    dcc.Graph(
        id='kcal-graph',
        figure=fig2
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
