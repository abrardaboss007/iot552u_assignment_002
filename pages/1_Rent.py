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
def load_london_gdf():
    gdf = gpd.read_file('london_boroughs.geojson')
    gdf = gdf[['BOROUGH', 'geometry']]
    gdf = gdf.rename(columns={'BOROUGH': 'borough'})
    gdf['borough'] = gdf['borough'].str.replace('&', 'and', regex=False)
    gdf['geometry'] = gdf['geometry'].simplify(0.001)
    return gdf


@st.cache_data
def load_england_gdf():
    gdf = gpd.read_file('england_lad24.geojson')
    gdf = gdf[['LAD24CD', 'LAD24NM', 'geometry']]
    gdf = gdf.rename(columns={'LAD24CD': 'lad_code', 'LAD24NM': 'district'})
    gdf['geometry'] = gdf['geometry'].simplify(0.001)
    return gdf


@st.cache_data
def load_rent_data():
    rent_df = pd.read_csv('rent_prices.csv', low_memory=False)
    rent_df['Time period'] = pd.to_datetime(rent_df['Time period'], format='%b-%y')
    rent_df['Year'] = rent_df['Time period'].dt.year

    price_cols = ['Rental price one bed', 'Rental price two bed',
                  'Rental price three bed', 'Rental price four or more bed']
    for col in price_cols:
        rent_df[col] = pd.to_numeric(rent_df[col], errors='coerce')

    yearly_avg = rent_df.groupby(['Area code', 'Area name', 'Region or country name', 'Year'])[price_cols].mean().reset_index()
    yearly_avg = yearly_avg.sort_values(['Area code', 'Year'])

    for col in price_cols:
        change_col = col.replace('Rental price', 'Pct_Change')
        yearly_avg[change_col] = yearly_avg.groupby('Area code')[col].pct_change() * 100

    # Predictive analysis for 2026
    predictions = []
    for area_code in yearly_avg['Area code'].unique():
        area_data = yearly_avg[yearly_avg['Area code'] == area_code].copy()
        area_name = area_data['Area name'].iloc[0]
        region = area_data['Region or country name'].iloc[0]

        pred_row = {
            'Area code': area_code,
            'Area name': area_name,
            'Region or country name': region,
            'Year': 2026
        }

        for col in price_cols:
            train = area_data[['Year', col]].dropna()
            if len(train) >= 3:
                model = LinearRegression()
                model.fit(train[['Year']], train[col])
                pred_row[col] = model.predict([[2026]])[0]
            else:
                pred_row[col] = np.nan

        predictions.append(pred_row)

    pred_df = pd.DataFrame(predictions)
    yearly_avg = pd.concat([yearly_avg, pred_df], ignore_index=True)
    yearly_avg = yearly_avg.sort_values(['Area code', 'Year']).reset_index(drop=True)

    for col in price_cols:
        change_col = col.replace('Rental price', 'Pct_Change')
        yearly_avg[change_col] = yearly_avg.groupby('Area code')[col].pct_change() * 100

    return yearly_avg

#-------------------------------------------------------------------------------------
# Load data (cached)
#-------------------------------------------------------------------------------------
london_boroughs_gdf = load_london_gdf()
england_local_authority_district_gdf = load_england_gdf()
yearly_avg = load_rent_data()

# Add LAD code to London GDF
lad_lookup = england_local_authority_district_gdf[['lad_code', 'district']].copy()
london_boroughs_gdf = london_boroughs_gdf.merge(
    lad_lookup, left_on='borough', right_on='district', how='left'
).drop(columns=['district'])
london_boroughs_gdf = london_boroughs_gdf[['lad_code', 'borough', 'geometry']]

# Filter to 2018-2026
yearly_avg_display = yearly_avg[(yearly_avg['Year'] >= 2018) & (yearly_avg['Year'] <= 2026)].copy()

#-------------------------------------------------------------------------------------
# Controls
#-------------------------------------------------------------------------------------
st.title("Rent Prices Dashboard")
st.caption("**Interactive choropleth maps and filtered data table (see bottom) for comparing rental affordability across London boroughs and England local authorities, with 2026 values estimated using linear regression.**")

bedroom_options = {
    '1 Bedroom': 'one bed',
    '2 Bedrooms': 'two bed',
    '3 Bedrooms': 'three bed',
    '4+ Bedrooms': 'four or more bed'
}

col1, col2 = st.columns(2)
with col1:
    selected_bedroom = st.selectbox("**Bedroom type:**", list(bedroom_options.keys()))

with col2:
    show_pct_change = st.toggle("**Show % Change**", value=False)

st.markdown("")
selected_year = st.slider("**Year**", min_value=2018, max_value=2026)

if selected_year == 2026:
    st.info("2026 values are **predicted** using linear regression on historical data.")

price_col = f'Rental price {bedroom_options[selected_bedroom]}'
change_col = f'Pct_Change {bedroom_options[selected_bedroom]}'

if show_pct_change:
    display_col = change_col
    colour_scale = 'RdYlGn_r'
    colour_label = 'YoY % Change'
else:
    display_col = price_col
    colour_scale = 'YlOrRd'
    colour_label = 'Avg Rent (£/month)'

# Filter rent data for selected year
rent_year = yearly_avg_display[yearly_avg_display['Year'] == selected_year].copy()

#-------------------------------------------------------------------------------------
# Merge rent data into GeoDataFrames
#-------------------------------------------------------------------------------------
london_merged = london_boroughs_gdf.merge(
    rent_year[['Area code', 'Area name', display_col]],
    left_on='lad_code',
    right_on='Area code',
    how='left'
).drop(columns=['Area code'])

england_merged = england_local_authority_district_gdf.merge(
    rent_year[['Area code', 'Area name', display_col]],
    left_on='lad_code',
    right_on='Area code',
    how='left'
).drop(columns=['Area code'])

#-------------------------------------------------------------------------------------
# Display maps side by side using Plotly
#-------------------------------------------------------------------------------------
if show_pct_change:
    st.markdown(f"### Year-on-Year % Change — {selected_bedroom} — {selected_year}")
else:
    st.markdown(f"### Average Monthly Rent — {selected_bedroom} — {selected_year}")

map_col1, map_col2 = st.columns(2)

with map_col1:
    st.markdown("**London Boroughs**")

    fig_london = px.choropleth_mapbox(
        london_merged,
        geojson=london_merged.geometry.__geo_interface__,
        locations=london_merged.index,
        color=display_col,
        color_continuous_scale=colour_scale,
        mapbox_style='carto-positron',
        center={"lat": 51.48, "lon": -0.10},
        zoom=9,
        opacity=0.7,
        hover_data={'borough': True, display_col: ':.1f'},
        labels={display_col: colour_label}
    )
    fig_london.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_london, use_container_width=True)

with map_col2:
    st.markdown("**England (Local Authority Districts)**")

    fig_england = px.choropleth_mapbox(
        england_merged,
        geojson=england_merged.geometry.__geo_interface__,
        locations=england_merged.index,
        color=display_col,
        color_continuous_scale=colour_scale,
        mapbox_style='carto-positron',
        center={"lat": 53.0, "lon": -1.5},
        zoom=5,
        opacity=0.7,
        hover_data={'district': True, display_col: ':.1f'},
        labels={display_col: colour_label}
    )
    fig_england.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_england, use_container_width=True)
#-------------------------------------------------------------------------------------
# Data table
#-------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("Interactive Data Table")

table_data = rent_year[['Area code', 'Area name', 'Region or country name', display_col]].copy()
table_data = table_data.dropna(subset=[display_col])
table_data = table_data.sort_values(display_col, ascending=False).reset_index(drop=True)

# Add selected filters as explicit columns
table_data['Year'] = selected_year
table_data['Bedroom Type'] = selected_bedroom
table_data['Metric'] = colour_label

# Reorder columns
table_data = table_data[['Year', 'Bedroom Type', 'Area code', 'Area name', 'Region or country name', display_col]]

# Rename columns for presentation
table_data.columns = ['Year', 'Bedroom Type', 'Area Code', 'Area', 'Region', colour_label]

st.dataframe(table_data, use_container_width=True, hide_index=True)
