# Import relevant modules
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

#-------------------------------------------------------------------------------------
# Food Basket with predictions
#-------------------------------------------------------------------------------------
@st.cache_data
def load_food_basket():
    basket_df = pd.read_csv('shopping_basket_prices.csv')
    basket_df['Date'] = pd.to_datetime(basket_df['Date'], format='%d/%m/%Y')
    for col in ["Women's basket", "Men's basket"]:
        basket_df[col] = pd.to_numeric(basket_df[col], errors='coerce')
    basket_df = basket_df.sort_values('Date').reset_index(drop=True)
    return basket_df

@st.cache_data
def predict_food_basket(basket_df):
    # Number of months to predict ahead — change this value to adjust
    MONTHS_AHEAD = 6

    date_min = basket_df['Date'].min()
    last_date = basket_df['Date'].max()

    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=MONTHS_AHEAD,
        freq='MS'
    )

    predictions = pd.DataFrame({'Date': future_dates})

    for col in ["Women's basket", "Men's basket"]:
        train = basket_df[['Date', col]].dropna()
        train['date_num'] = (train['Date'] - date_min).dt.days
        train_recent = train.tail(36)

        model = LinearRegression()
        model.fit(train_recent[['date_num']], train_recent[col])

        future_num = (future_dates - date_min).days.values.reshape(-1, 1)
        predictions[col] = model.predict(future_num)

    basket_df['type'] = 'Actual'
    predictions['type'] = 'Predicted'

    full = pd.concat([basket_df, predictions], ignore_index=True)
    full = full.sort_values('Date').reset_index(drop=True)
    return full

basket_df = load_food_basket()
basket_full = predict_food_basket(basket_df)

st.title("Weekly Shopping Basket Dashboard")
st.caption(
    "**Interactive line chart tracking the rising cost of weekly food baskets for men and women, "
    " supporting analysis of household food affordability pressures, with six-month predictive estimates generated using linear regression.**"
)

st.subheader("Weekly Shopping Basket Cost")

fig_basket = go.Figure()

actual_basket = basket_full[basket_full['type'] == 'Actual']
predicted_basket = basket_full[basket_full['type'] == 'Predicted']

womens_colour = '#D1006C'
mens_colour = '#0050A0'

# Actual lines
fig_basket.add_trace(go.Scatter(
    x=actual_basket['Date'], y=actual_basket["Women's basket"],
    mode='lines', name="Woman's Basket",
    line=dict(color=womens_colour, width=2)
))
fig_basket.add_trace(go.Scatter(
    x=actual_basket['Date'], y=actual_basket["Men's basket"],
    mode='lines', name="Man's Basket",
    line=dict(color=mens_colour, width=2)
))

# Predicted lines
for col, color, name in [
    ("Women's basket", womens_colour, "Woman's Basket (Predicted)"),
    ("Men's basket", mens_colour, "Man's Basket (Predicted)")
]:
    col_actual_data = actual_basket[['Date', col]].dropna()
    last_point = col_actual_data.tail(1)
    col_pred = predicted_basket[['Date', col]].dropna()
    bridge = pd.concat([last_point, col_pred])
    fig_basket.add_trace(go.Scatter(
        x=bridge['Date'], y=bridge[col],
        mode='lines', name=name,
        line=dict(color=color, width=2, dash='dash')
    ))

fig_basket.update_layout(
    xaxis_title='Date',
    yaxis_title='Weekly Cost (£)',
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=500,
    margin=dict(t=80)
)

st.plotly_chart(fig_basket, use_container_width=True)

#Table toggles
if st.toggle("Show basket data table", value=False, key='basket_table'):
    st.dataframe(basket_full, use_container_width=True, hide_index=True)