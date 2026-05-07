# Import relevant modules
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import plotly.express as px

@st.cache_data
def load_priority_places():
    england_lsoa_gdf = gpd.read_file("england_lsoa.geojson")
    england_lsoa_gdf = england_lsoa_gdf.rename(columns={'LSOA21CD': 'lsoa_code', 'LSOA21NM': 'lsoa_region_name'})
    england_lsoa_gdf = england_lsoa_gdf[['lsoa_code', 'lsoa_region_name', 'geometry']]

    # Simplify geometry to reduce file size
    england_lsoa_gdf['geometry'] = england_lsoa_gdf['geometry'].simplify(0.001)

    priority_places_for_food = pd.read_csv("priority_places_for_food_index.csv")
    priority_places_for_food = priority_places_for_food.rename(
        columns={'lsoa21cd': 'lsoa_code', 'pp_dec_combined': 'food_deprivation_index'}
    )
    priority_places_for_food = priority_places_for_food[['lsoa_code', 'food_deprivation_index']]

    merged = england_lsoa_gdf.merge(priority_places_for_food, on='lsoa_code', how='left')
    return merged

merged_df = load_priority_places()

st.title("Priority Places for Food Index Dashboard")
st.caption(
    "**Interactive choropleth map showing food priority decile rankings across England at LSOA level. "
    "Decile 1 represents the highest-priority areas for food-related support, while decile 10 represents the lowest priority.**"
)

st.info("**Tip:** Zoom into the map to inspect local patterns more clearly.")

fig = px.choropleth_mapbox(
    merged_df,
    geojson=merged_df.geometry.__geo_interface__,
    locations=merged_df.index,
    color='food_deprivation_index',
    color_continuous_scale='RdYlGn',
    range_color=[1, 10],
    mapbox_style='carto-positron',
    center={"lat": 53, "lon": -1.5},
    zoom=5,
    opacity=0.7,
    hover_data=['lsoa_code', 'lsoa_region_name', 'food_deprivation_index'],
    labels={'food_deprivation_index': 'Deprivation Decile'}
)

fig.update_layout(
    height=600,
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(title="Decile", tickvals=list(range(1, 11)))
)

st.plotly_chart(fig, use_container_width=True)

# Table toggle
if st.toggle("Show priority places data", value=False, key='food_priority_table'):
    st.dataframe(merged_df.drop(columns=['geometry']), use_container_width=True, hide_index=True)