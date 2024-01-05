from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pydantic import BaseSettings


alpha = 0.1  # Used for ewm calculations
days = 7
weight_change_goal = 0.75
kcal_goal = 2887
kcal_per_kg = 7500
relevant_metrics = ['weight_body_mass', 'dietary_energy', 'active_energy']
start_date = "2023-01-01"


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

app = Dash(__name__)

df = pd.read_excel("app/MacroFactor.xlsx", sheet_name=5)
# Get rid of data missing some cols
df = df.iloc[12:,:]
# 'Date', 'Expenditure', 'Trend Weight (kg)', 'Weight (kg)',
# 'Calories (kcal)', 'Protein (g)', 'Fat (g)', 'Carbs (g)',
# 'Target Calories (kcal)', 'Target Protein (g)', 'Target Fat (g)',
# 'Target Carbs (g)'],



df['Date'] = pd.to_datetime(df['Date'])
# df = df.pivot(index='date',columns='name',values='qty').reset_index()
df['Weight (kg)'] = df['Weight (kg)'].interpolate(method='linear', limit_direction='forward', axis=0)
df['weight_ewm'] = df['Weight (kg)'].ewm(alpha=alpha).mean() # https://deaddy.net/on-tracking-bodyweight.html
df['target_diff'] = df['Calories (kcal)'].astype('float') - df['Target Calories (kcal)'].astype('float')
df['target_diff_r7'] = df['target_diff'].rolling(7).mean()
# df['weight_diff_weekly'] = df['weight_body_mass'] - df['weight_body_mass'].shift(7)
# df['weight_diff_weekly_ewm'] = df['weight_ewm'] - df['weight_ewm'].shift(7)
# df['dietary_energy_r7'] = df['dietary_energy'].rolling(7).mean()
# df = df[df["date"] > start_date].reset_index(drop=True)

# # weight_ewm today vs x days ago
# weight_ewm_change_xd = df.iloc[-1]['weight_ewm'] - df.iloc[-(days+1)]['weight_ewm']
# in_avg_xd = df.iloc[-(days+1):-1]['dietary_energy'].mean()
# outstring = (
#     f"current {days}-day weight diff is {round(weight_ewm_change_xd, 2)} kg "
#     f"on {round(in_avg_xd)} kcal "
#     f"indicating a {round(kcal_per_kg * weight_ewm_change_xd / days, 2)} kcal surplus "
#     f"(goal is {round(weight_change_goal/30*days, 2)})"
# )
outstring = ""

fig = px.line(df, x="Date", y="Trend Weight (kg)")
# fig.add_trace(go.Scatter(x=df['Date'], y=df['weight_ewm']))

fig2 = px.line(df, x="Date", y="Expenditure")
# fig2.add_hline(y=round(weight_change_goal/30*days, 2), line_color="green")

fig3 = px.line(df, x="Date", y="Calories (kcal)") # was px.bar
fig3.add_trace(go.Scatter(x=df['Date'], y=df['Target Calories (kcal)']))
fig3.update_layout(showlegend=False)
# fig3.add_hline(y=kcal_goal, line_color="green")

fig4 = px.line(df, x="Date", y="target_diff")
fig4.add_trace(go.Scatter(x=df['Date'], y=df['target_diff_r7']))
fig4.update_layout(showlegend=False)
# fig4.add_hline(y=600, line_color="green")


app.layout = html.Div(children=[
    html.H1(children='HealthBrain 🧠'),
    html.Div(children=outstring),
    dcc.Graph(
        id='weight-graph',
        figure=fig
    ),
    dcc.Graph(
        id='kcal-graph',
        figure=fig3
    ),
    dcc.Graph(
        id='weight-diff-graph',
        figure=fig2
    ),
    dcc.Graph(
        id='energy-graph',
        figure=fig4
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
