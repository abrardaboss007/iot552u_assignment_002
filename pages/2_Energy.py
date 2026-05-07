import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

st.set_page_config(layout="wide")

#-------------------------------------------------------------------------------------
# Cache all data loading
#-------------------------------------------------------------------------------------
@st.cache_data
def load_england_regions_gdf():
    gdf = gpd.read_file("england_eer.geojson")
    gdf = gdf.rename(columns={'EER13CD': 'eer_code', 'EER13NM': 'region_name'})
    gdf = gdf[['eer_code', 'region_name', 'geometry']]
    gdf['geometry'] = gdf['geometry'].simplify(0.001)
    return gdf

@st.cache_data
def load_energy_region_mapping():
    mapping_df = pd.read_csv("energy_region_mapping.csv")
    mapping_df = mapping_df[['eer_code', 'standardised_name', 'name_in_csv']]
    return mapping_df

@st.cache_data
def load_electricity_data():
    df = pd.read_csv("electricity_unit_prices_by_region.csv", encoding="latin-1")

    df = df.rename(columns={
        'Year': 'year',
        'Region [Note 1]': 'source_region_name',
        'Overall: Average variable unit price (£/kWh)[Note 2]': 'unit_rate',
        'Overall: Average fixed cost (£/year)[Note 3]': 'standing_charge'
    })

    df = df[['year', 'source_region_name', 'unit_rate', 'standing_charge']].copy()
    df['year'] = df['year'].astype(str).str.extract(r'(\d{4})')[0]
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['unit_rate'] = pd.to_numeric(df['unit_rate'], errors='coerce')
    df['standing_charge'] = pd.to_numeric(df['standing_charge'], errors='coerce')

    england_regions = [
        'North East', 'North West', 'Yorkshire', 'East Midlands',
        'West Midlands', 'Eastern', 'London', 'South East', 'South West'
    ]
    df = df[df['source_region_name'].isin(england_regions)].copy()

    TYPICAL_ELECTRICITY_KWH = 2700
    df['total_bill'] = (df['unit_rate'] * TYPICAL_ELECTRICITY_KWH) + df['standing_charge']

    return df.dropna(subset=['year', 'source_region_name'])

@st.cache_data
def load_gas_data():
    df = pd.read_csv("gas_unit_prices_by_region.csv", encoding="latin-1")

    df = df.rename(columns={
        'Year': 'year',
        'Region': 'source_region_name',
        'Overall: Average variable unit price (£/kWh)[Note 1]': 'unit_rate',
        'Overall: Average fixed cost (£/year)[Note 2]': 'standing_charge'
    })

    df = df[['year', 'source_region_name', 'unit_rate', 'standing_charge']].copy()
    df['year'] = df['year'].astype(str).str.extract(r'(\d{4})')[0]
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['unit_rate'] = pd.to_numeric(df['unit_rate'], errors='coerce')
    df['standing_charge'] = pd.to_numeric(df['standing_charge'], errors='coerce')

    england_regions = [
        'North East', 'North West', 'Yorkshire', 'East Midlands',
        'West Midlands', 'Eastern', 'London', 'South East', 'South West'
    ]
    df = df[df['source_region_name'].isin(england_regions)].copy()

    TYPICAL_GAS_KWH = 11500
    df['total_bill'] = (df['unit_rate'] * TYPICAL_GAS_KWH) + df['standing_charge']

    return df.dropna(subset=['year', 'source_region_name'])

@st.cache_data
def standardise_energy_data(df):
    mapping_df = load_energy_region_mapping()

    merged = df.merge(
        mapping_df,
        left_on='source_region_name',
        right_on='name_in_csv',
        how='inner'
    )

    return merged

@st.cache_data
def predict_energy_2026(df):
    predictions = []

    for eer_code in df['eer_code'].unique():
        region_data = df[df['eer_code'] == eer_code].copy()

        pred_row = {
            'eer_code': eer_code,
            'standardised_name': region_data['standardised_name'].iloc[0],
            'source_region_name': region_data['source_region_name'].iloc[0],
            'year': 2026
        }

        train = region_data[['year', 'total_bill']].dropna()
        if len(train) >= 3:
            model = LinearRegression()
            model.fit(train[['year']], train['total_bill'])
            pred_row['total_bill'] = model.predict([[2026]])[0]
        else:
            pred_row['total_bill'] = np.nan

        predictions.append(pred_row)

    pred_df = pd.DataFrame(predictions)
    full_df = pd.concat([df, pred_df], ignore_index=True)
    full_df = full_df.sort_values(['eer_code', 'year']).reset_index(drop=True)
    return full_df

#-------------------------------------------------------------------------------------
# Load data
#-------------------------------------------------------------------------------------
england_regions_gdf = load_england_regions_gdf()

electricity_df = load_electricity_data()
electricity_df = standardise_energy_data(electricity_df)
electricity_df = electricity_df[electricity_df['year'].between(2018, 2025)]
electricity_df = predict_energy_2026(electricity_df)

gas_df = load_gas_data()
gas_df = standardise_energy_data(gas_df)
gas_df = gas_df[gas_df['year'].between(2018, 2025)]
gas_df = predict_energy_2026(gas_df)

#-------------------------------------------------------------------------------------
# Dashboard title
#-------------------------------------------------------------------------------------
st.title("Regional Energy Prices Dashboard")
st.caption(
    "**Interactive choropleth map showing estimated annual regional energy bills across England, "
    "using overall average tariffs and a standardised region-mapping table to align source data with dashboard geography. "
    "Values for 2026 are estimated using linear regression (Interactive Data Table below!)**"
)

#-------------------------------------------------------------------------------------
# Controls
#-------------------------------------------------------------------------------------
energy_type = st.selectbox("**Energy type:**", ["Electricity", "Gas"])

selected_year = st.slider("**Year:**", min_value=2018, max_value=2026)

if selected_year == 2026:
    st.info("**2026 values are predicted using linear regression based on historical regional data.**")

#-------------------------------------------------------------------------------------
# Select dataframe
#-------------------------------------------------------------------------------------
if energy_type == "Electricity":
    energy_df = electricity_df
    value_label = "Estimated Annual Electricity Bill (£)"
else:
    energy_df = gas_df
    value_label = "Estimated Annual Gas Bill (£)"

#-------------------------------------------------------------------------------------
# Filter and merge for map
#-------------------------------------------------------------------------------------
energy_year = energy_df[energy_df['year'] == selected_year].copy()

energy_merged = england_regions_gdf.merge(
    energy_year[['eer_code', 'standardised_name', 'source_region_name', 'total_bill']],
    on='eer_code',
    how='left'
)

#-------------------------------------------------------------------------------------
# Plotly map
#-------------------------------------------------------------------------------------
fig = px.choropleth_mapbox(
    energy_merged,
    geojson=energy_merged.geometry.__geo_interface__,
    locations=energy_merged.index,
    color='total_bill',
    color_continuous_scale='YlOrRd',
    mapbox_style='carto-positron',
    center={"lat": 53.0, "lon": -1.5},
    zoom=5,
    opacity=0.7,
    hover_data={
        'region_name': True,
        'standardised_name': True,
        'total_bill': ':.2f'
    },
    labels={'total_bill': value_label}
)

fig.update_layout(
    height=600,
    margin=dict(l=0, r=0, t=0, b=0)
)

st.plotly_chart(fig, use_container_width=True)

#-------------------------------------------------------------------------------------
# Interactive data table
#-------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("Interactive Data Table")

table_data = energy_year[['year', 'standardised_name', 'source_region_name', 'total_bill']].copy()
table_data = table_data.dropna(subset=['total_bill'])
table_data = table_data.sort_values('total_bill', ascending=False).reset_index(drop=True)

table_data['Energy Type'] = energy_type
table_data['Metric'] = value_label

table_data = table_data[['year', 'Energy Type', 'Metric', 'standardised_name', 'source_region_name', 'total_bill']]
table_data.columns = ['Year', 'Energy Type', 'Metric', 'Standardised Region', 'Source Region Name', 'Value']

st.dataframe(table_data, use_container_width=True, hide_index=True)