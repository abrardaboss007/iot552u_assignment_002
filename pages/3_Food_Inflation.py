# Import relevant modules
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

#-------------------------------------------------------------------------------------
# Food / Restaurant / Overall Inflation Graph with Predictions
#-------------------------------------------------------------------------------------
@st.cache_data
def load_inflation_data():
    # --- Food inflation ---
    food_df = pd.read_csv('food_inflation.csv', skiprows=5, usecols=[0, 1],
                          names=['Date', 'Food_inflation'], header=None)
    food_df = food_df.dropna(subset=['Date'])
    food_df = food_df[food_df['Date'].str.strip() != '']
    food_df['Food_inflation'] = pd.to_numeric(food_df['Food_inflation'], errors='coerce')
    food_df = food_df.dropna(subset=['Food_inflation'])
    food_df['Date'] = pd.to_datetime(food_df['Date'].str.strip(), format='%b-%y')

    # --- Restaurant and cafe inflation ---
    rest_df = pd.read_csv('restaurant_and_cafe_inflation.csv', skiprows=6, usecols=[0, 1],
                          names=['Date', 'Restaurant_inflation'], header=None,
                          encoding='latin-1')
    rest_df = rest_df.dropna(subset=['Date'])
    rest_df = rest_df[rest_df['Date'].str.strip() != '']
    rest_df['Restaurant_inflation'] = pd.to_numeric(rest_df['Restaurant_inflation'], errors='coerce')
    rest_df = rest_df.dropna(subset=['Restaurant_inflation'])
    rest_df['Date'] = pd.to_datetime(rest_df['Date'].str.strip(), format='%b-%y')

    # --- Overall CPI inflation ---
    cpih_df = pd.read_csv('inflation_rate.csv', skiprows=8, usecols=[0, 1],
                          names=['Date', 'CPIH_overall'], header=None)
    cpih_df = cpih_df.dropna(subset=['Date'])
    cpih_df['Date'] = cpih_df['Date'].str.strip().str.strip('"')
    cpih_df['CPIH_overall'] = cpih_df['CPIH_overall'].astype(str).str.strip().str.strip('"')
    cpih_df['CPIH_overall'] = pd.to_numeric(cpih_df['CPIH_overall'], errors='coerce')
    cpih_df = cpih_df[cpih_df['Date'].str.contains(r'\d{4}\s[A-Z]{3}', regex=True, na=False)]
    cpih_df = cpih_df.dropna(subset=['CPIH_overall'])
    cpih_df['Date'] = pd.to_datetime(cpih_df['Date'], format='%Y %b')

    # --- Merge all three ---
    combined = food_df.merge(rest_df, on='Date', how='outer')
    combined = combined.merge(cpih_df, on='Date', how='outer')
    combined = combined.sort_values('Date').reset_index(drop=True)

    # --- Filter to Oct 2012 onwards ---
    combined = combined[combined['Date'] >= '2012-10-01'].copy()

    return combined

@st.cache_data
def predict_inflation(combined):
    date_min = combined['Date'].min()

    # --- Step 1: Predict CPI overall with linear regression ---
    cpi_data = combined[['Date', 'CPIH_overall']].dropna()
    cpi_last_date = cpi_data['Date'].max()

    future_dates_cpi = pd.date_range(
        start=cpi_last_date + pd.DateOffset(months=1),
        end='2026-12-01',
        freq='MS'
    )

    cpi_data['date_num'] = (cpi_data['Date'] - date_min).dt.days
    cpi_recent = cpi_data.tail(24)

    cpi_model = LinearRegression()
    cpi_model.fit(cpi_recent[['date_num']], cpi_recent['CPIH_overall'])

    future_num_cpi = (future_dates_cpi - date_min).days.values.reshape(-1, 1)
    cpi_predicted_values = cpi_model.predict(future_num_cpi)

    cpi_pred_df = pd.DataFrame({
        'Date': future_dates_cpi,
        'CPIH_overall': cpi_predicted_values
    })

    # --- Step 2: Build full CPI series (actual + predicted) ---
    full_cpi = pd.concat([
        cpi_data[['Date', 'CPIH_overall']],
        cpi_pred_df
    ]).sort_values('Date').reset_index(drop=True)

    # --- Step 3: Predict food and restaurant based on average spread to CPI ---
    food_rest_preds = {}

    for col in ['Food_inflation', 'Restaurant_inflation']:
        overlap = combined[['Date', col, 'CPIH_overall']].dropna()
        overlap['spread'] = overlap[col] - overlap['CPIH_overall']

        # Use average spread from last 6 months (stable recent relationship)
        avg_spread = overlap['spread'].tail(6).mean()

        col_last_date = combined[['Date', col]].dropna()['Date'].max()

        future_dates_col = pd.date_range(
            start=col_last_date + pd.DateOffset(months=1),
            end='2026-12-01',
            freq='MS'
        )

        # Get CPI values for those future dates (real where available, predicted where not)
        cpi_for_future = full_cpi[full_cpi['Date'].isin(future_dates_col)].set_index('Date')
        cpi_values = cpi_for_future.loc[future_dates_col, 'CPIH_overall'].values

        # Predicted = actual/predicted CPI + average recent spread
        predicted_values = cpi_values + avg_spread

        food_rest_preds[col] = pd.DataFrame({
            'Date': future_dates_col,
            col: predicted_values
        })

    # --- Step 4: Combine all predictions ---
    all_pred = cpi_pred_df.copy()
    for col, df in food_rest_preds.items():
        all_pred = all_pred.merge(df, on='Date', how='outer')

    all_pred['type'] = 'Predicted'
    combined['type'] = 'Actual'

    full = pd.concat([combined, all_pred], ignore_index=True)
    full = full.sort_values('Date').reset_index(drop=True)

    return full

# Load and predict
inflation_combined = load_inflation_data()
inflation_full = predict_inflation(inflation_combined)

# --- Plot ---
st.title("Inflation Trends Dashboard")
st.caption(
    "**Interactive line chart comparing overall CPI inflation with food and restaurant/café inflation. "
    "Dashed lines represent predictive estimates up to December 2026.**"
)

st.subheader("CPI, Food, and Restaurant/Café Inflation Rates")

fig = go.Figure()

actual = inflation_full[inflation_full['type'] == 'Actual']
predicted = inflation_full[inflation_full['type'] == 'Predicted']

# Actual lines
fig.add_trace(go.Scatter(x=actual['Date'], y=actual['CPIH_overall'],
                         mode='lines', name='CPI Overall',
                         line=dict(color='blue', width=2)))
fig.add_trace(go.Scatter(x=actual['Date'], y=actual['Food_inflation'],
                         mode='lines', name='Food & Non-Alcoholic Beverages',
                         line=dict(color='red', width=2)))
fig.add_trace(go.Scatter(x=actual['Date'], y=actual['Restaurant_inflation'],
                         mode='lines', name='Restaurants & Cafes',
                         line=dict(color='green', width=2)))

# Predicted lines (dashed, connecting from last actual point)
for col, color, name in [
    ('CPIH_overall', 'blue', 'CPI Overall (Predicted)'),
    ('Food_inflation', 'red', 'Food (Predicted)'),
    ('Restaurant_inflation', 'green', 'Restaurants (Predicted)')
]:
    col_actual = actual[['Date', col]].dropna()
    last_actual_point = col_actual.tail(1)
    col_predicted = predicted[['Date', col]].dropna()
    bridge = pd.concat([last_actual_point, col_predicted])
    fig.add_trace(go.Scatter(x=bridge['Date'], y=bridge[col],
                             mode='lines', name=name,
                             line=dict(color=color, width=2, dash='dash')))

fig.update_layout(
    xaxis_title='Date',
    yaxis_title='Annual % Change',
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Table toggles
if st.toggle("Show inflation data table", value=False, key='inflation_table'):
    st.dataframe(inflation_full, use_container_width=True, hide_index=True)
