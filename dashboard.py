import dash
from dash import dcc, html, Input, Output
import pandas as pd
import os
from ML.Code.Predicts.scenario4 import predict_future_sales
import plotly.express as px

def init_dash(server):
    file_path = f'{os.getcwd()}/ML/data/raw_data/Scenario4.csv'
    model_dir = f'{os.getcwd()}/ML/models/'
    pred_df = predict_future_sales(model_dir,file_path,5,5)

    product_sales_df = (
        pred_df.groupby('Product Name')['Predicted Sales']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dash/',
        suppress_callback_exceptions=True
    )

    categories = ['All'] + sorted(pred_df['Category'].unique())
    subcategories = ['All'] + sorted(pred_df['Sub-Category'].unique())
    products = ['All'] + sorted(pred_df['Product Name'].unique())

    dash_app.layout = html.Div([
        html.H2("Store Forecast Dashboard"),

        html.Div([
            html.Label("Category"),
            dcc.Dropdown(id='category-dropdown', options=[{'label': c, 'value': c} for c in categories], value='All'),

            html.Label("Sub-Category"),
            dcc.Dropdown(id='subcat-dropdown', options=[{'label': s, 'value': s} for s in subcategories], value='All'),

            html.Label("Product"),
            dcc.Dropdown(id='product-dropdown', options=[{'label': p, 'value': p} for p in products], value='All'),

            html.Label("Top N Products"),
            dcc.Slider(id='top-n-slider', min=5, max=30, step=1, value=10, marks={i: str(i) for i in range(5,31,5)}),
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='trend-plot'),
            dcc.Graph(id='top-products-plot')
        ], style={'width': '65%', 'display': 'inline-block', 'paddingLeft': '20px'})
    ])

    @dash_app.callback(
        Output('subcat-dropdown', 'options'),
        Output('subcat-dropdown', 'value'),
        Input('category-dropdown', 'value'),
    )
    def update_subcat_options(category):
        if category == 'All':
            subcats = sorted(pred_df['Sub-Category'].unique())
        else:
            subcats = sorted(pred_df[pred_df['Category'] == category]['Sub-Category'].unique())
        options = [{'label': s, 'value': s} for s in ['All'] + subcats]
        return options, 'All'

    @dash_app.callback(
        Output('product-dropdown', 'options'),
        Output('product-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('subcat-dropdown', 'value'),
    )
    def update_product_options(category, subcat):
        temp_df = pred_df
        if category != 'All':
            temp_df = temp_df[temp_df['Category'] == category]
        if subcat != 'All':
            temp_df = temp_df[temp_df['Sub-Category'] == subcat]
        prods = sorted(temp_df['Product Name'].unique())
        if prods:
            options = [{'label': p, 'value': p} for p in ['All'] + prods]
            return options, 'All'
        else:
            return [{'label': 'No Products', 'value': 'No Products'}], 'No Products'

    @dash_app.callback(
        Output('trend-plot', 'figure'),
        Input('category-dropdown', 'value'),
        Input('subcat-dropdown', 'value'),
        Input('product-dropdown', 'value'),
    )
    def update_trend_plot(category, subcat, product):
        filtered = pred_df[
            ((pred_df['Category'] == category) | (category == 'All')) &
            ((pred_df['Sub-Category'] == subcat) | (subcat == 'All'))
        ]

        if product != 'All' and product != 'No Products':
            filtered = filtered[filtered['Product Name'] == product]
        elif product == 'No Products':
            return px.scatter(title="⚠️ No products available for selected filters.")

        if filtered.empty:
            return px.scatter(title="⚠️ No data for selected filters.")

        if product == 'All':
            filtered = filtered.groupby('Predicted Month', as_index=False)['Predicted Sales'].sum()

        fig = px.line(filtered, x='Predicted Month', y='Predicted Sales',
                      title=f'Sales Forecast for {"All Products" if product == "All" else product}',
                      markers=True)
        return fig

    @dash_app.callback(
        Output('top-products-plot', 'figure'),
        Input('top-n-slider', 'value')
    )
    def update_top_products_plot(top_n):
        top = product_sales_df.head(top_n)
        fig = px.bar(top, x='Predicted Sales', y='Product Name', orientation='h',
                     title=f'Top {top_n} Products by Total Predicted Sales',
                     color='Predicted Sales', color_continuous_scale='magma')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        return fig
