import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# load the data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_excel(os.path.join(BASE_DIR, 'Bakery_supporting_document.xlsx'))


# fix missing values
df['Units Sold'] = df['Units Sold'].fillna(df['Units Sold'].median())
df['Revenue(£)'] = df['Revenue(£)'].fillna(df['Revenue(£)'].median())
df['Cost(£)'] = df['Cost(£)'].fillna(df['Cost(£)'].median())
df['Profit(£)'] = df['Profit(£)'].fillna(df['Profit(£)'].median())

# clean up product names, there were some typos in the data
df['Confectionary'] = df['Confectionary'].str.strip()
df['Confectionary'] = df['Confectionary'].replace({
    'Choclate Chunk': 'Chocolate Chunk',
    'Caramel nut': 'Caramel Nut'
})

# get the year from date column
df['Year'] = df['Date'].dt.year

# start the app
app = Dash(__name__)
server = app.server

app.layout = html.Div([

    html.H1('European Bakery Sales Dashboard (2000-2005)',
            style={'textAlign': 'center', 'color': '#1A4F6E', 'fontFamily': 'Arial', 'paddingTop': '20px'}),

    html.P('Select cities and products from the dropdowns to filter the charts below.',
           style={'textAlign': 'center', 'color': 'grey', 'fontFamily': 'Arial'}),

    # dropdowns section
    html.Div([

        html.Div([
            html.Label('City:', style={'fontFamily': 'Arial', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='city-dropdown',
                options=[{'label': c, 'value': c} for c in df['City'].unique()],
                value=df['City'].unique().tolist(),
                multi=True
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),

        html.Div([
            html.Label('Product:', style={'fontFamily': 'Arial', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='product-dropdown',
                options=[{'label': p, 'value': p} for p in df['Confectionary'].unique()],
                value=df['Confectionary'].unique().tolist(),
                multi=True
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

    ], style={'padding': '15px', 'backgroundColor': '#f0f8ff', 'margin': '15px', 'borderRadius': '5px'}),

    # first row of charts
    html.Div([
        dcc.Graph(id='city-bar', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='product-bar', style={'width': '50%', 'display': 'inline-block'})
    ]),

    # second row
    html.Div([
        dcc.Graph(id='trend-line', style={'width': '60%', 'display': 'inline-block'}),
        dcc.Graph(id='revenue-pie', style={'width': '40%', 'display': 'inline-block'})
    ]),

    # heatmap at the bottom
    html.Div([
        dcc.Graph(id='profit-heatmap')
    ])

], style={'backgroundColor': 'white'})


# this updates all charts when dropdowns change
@app.callback(
    Output('city-bar', 'figure'),
    Output('product-bar', 'figure'),
    Output('trend-line', 'figure'),
    Output('revenue-pie', 'figure'),
    Output('profit-heatmap', 'figure'),
    Input('city-dropdown', 'value'),
    Input('product-dropdown', 'value')
)
def update(cities, products):

    # filter data based on what user selected
    filtered = df[df['City'].isin(cities) & df['Confectionary'].isin(products)]

    # chart 1 - profit by city
    city_data = filtered.groupby('City')['Profit(£)'].sum().sort_values(ascending=False).reset_index()
    fig1 = px.bar(city_data, x='City', y='Profit(£)', title='Profit by City',
                  color_discrete_sequence=['#2C6E91'])
    fig1.update_layout(plot_bgcolor='#f9f9f9')

    # chart 2 - profit by product
    product_data = filtered.groupby('Confectionary')['Profit(£)'].sum().sort_values().reset_index()
    fig2 = px.bar(product_data, x='Profit(£)', y='Confectionary', orientation='h',
                  title='Profit by Product', color_discrete_sequence=['#3A9DC4'])
    fig2.update_layout(plot_bgcolor='#f9f9f9')

    # chart 3 - yearly trend per city
    yearly = filtered.groupby(['Year', 'City'])['Profit(£)'].sum().reset_index()
    fig3 = px.line(yearly, x='Year', y='Profit(£)', color='City',
                   markers=True, title='Profit Trend Over Time')
    fig3.update_layout(plot_bgcolor='#f9f9f9')

    # chart 4 - revenue share pie chart
    rev_data = filtered.groupby('City')['Revenue(£)'].sum().reset_index()
    fig4 = px.pie(rev_data, names='City', values='Revenue(£)',
                  title='Revenue Share by City', hole=0.3)

    # chart 5 - heatmap city vs product
    pivot = filtered.groupby(['City', 'Confectionary'])['Profit(£)'].sum().unstack(fill_value=0)
    fig5 = go.Figure(go.Heatmap(
        z=pivot.values / 1000,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='YlOrBr',
        text=[[f'£{v:.0f}K' for v in row] for row in pivot.values / 1000],
        texttemplate='%{text}'
    ))
    fig5.update_layout(title='Profit Heatmap - City vs Product (£K)')

    return fig1, fig2, fig3, fig4, fig5


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)

