# Import relevant modules
import streamlit as st


# #-------------------------------------------------------------------------------------
# # London Choropleth Map divided by borough (For rent prices)
# #-------------------------------------------------------------------------------------
# # Load data
# london_ward_gdf = gpd.read_file('london_boroughs.geojson')
# london_ward_gdf = london_ward_gdf[['BOROUGH', 'geometry']]

# st.dataframe(london_ward_gdf.head())

# # Create and display the folium map
# london_map = folium.Map(location=[51.48, -0.10], zoom_start=10, scrollWheelZoom = False, tiles='cartodb positron')
# folium.GeoJson(london_ward_gdf).add_to(london_map)
# st_folium(london_map, width=700, height=500)

# #-------------------------------------------------------------------------------------
# # England Choropleth Map divided according to EER standards (For Gas and Electricity graph)
# #-------------------------------------------------------------------------------------
# eer_gdf = gpd.read_file('england_eer.geojson')

# st.dataframe(eer_gdf)

# # Create and display the folium map
# eer_map = folium.Map(location=[53, -1.50], zoom_start=6, scrollWheelZoom = False, tiles='cartodb positron')
# folium.GeoJson(eer_gdf).add_to(eer_map)
# st_folium(eer_map, width=700, height=500)

# #-------------------------------------------------------------------------------------
# # England divided by LSOA (For food deprivation index graph)
# #-------------------------------------------------------------------------------------

# st.subheader("Hey Jonathan 👋🏼")

# st.markdown("")
# st.markdown("")
# st.markdown("")

# st.markdown("Welcome to my data solution. Essentially I am analysing the cost of living in England (with visualiations for London specifically as well in the case of rent prices).")
# st.markdown("The purpose is to analyse the ")


st.title("Welcome")

st.markdown("""
Hey Jonathan 👋🏼

Welcome to my data solution. This dashboard analyses the cost of living in England, with additional London-specific visualisations included for rent prices where more localised comparison is useful.

The purpose of this solution is to investigate how affordability pressures differ across housing, energy, food prices, and food deprivation. More specifically, it is designed to answer questions such as which London boroughs are the most expensive for renting, whether rent increases are consistent across regions, how energy prices vary across England, how much weekly shopping costs have risen, how food inflation compares with overall inflation, which areas are most vulnerable to food insecurity, and what future trends may look like for households in relation to rent, energy, and food prices.
""")

st.markdown("---")

st.subheader("What each page covers")

st.markdown("""
**1. Rent Prices Dashboard**  
This page examines rental affordability across England and within London boroughs specifically. It supports comparison of average rent levels by bedroom type, highlights differences in year-on-year rent growth, and helps answer whether London is disproportionately expensive compared with other parts of England.

**2. Inflation Trends Dashboard**  
This page compares overall CPI inflation with food inflation and restaurant/café inflation over time. It is intended to show whether food-related costs have risen faster than general inflation and to provide predictive estimates for how these pressures may develop into 2026.

**3. Weekly Shopping Basket Dashboard**  
This page focuses on the cost of a weekly shopping basket as a more practical household-level measure of affordability. It helps show how much more expensive everyday grocery shopping has become over time and includes short-term predictive analysis for the coming months.

**4. Regional Energy Prices Dashboard**  
This page compares estimated annual household energy costs across English regions. It supports identification of the cheapest and most expensive areas for energy and includes predictive estimates for 2026 to show possible near-future regional cost patterns.

**5. Priority Places for Food Index Dashboard**  
This page maps food deprivation across England using the Priority Places for Food Index. It highlights which areas are currently most vulnerable in terms of access to food and helps place the wider cost-of-living analysis in a broader social and geographic context.
""")