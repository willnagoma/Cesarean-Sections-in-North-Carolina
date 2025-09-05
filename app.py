import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import numpy as np 
import folium
import json
import plotly.express as px
import streamlit.components.v1 as components
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os

# Set page config
st.set_page_config(
    page_title="Cesarean Deliveries in North Carolina",
    page_icon="🏥",
    layout="wide"
)

# Introduction block
st.write("<h1 style='text-align: center;'>Cesarean Deliveries in North Carolina</h1>", unsafe_allow_html=True)
st.write("#### <div style='text-align: center; font-style: italic;'>Malpractice or medical necessity?</div>", unsafe_allow_html=True)

# Handle image - correct path in data folder
try:
    if os.path.exists('data/delivered_baby.jpeg'):
        st.image('data/delivered_baby.jpeg', width='stretch')
    else:
        st.info("Header image not found in data folder")
except Exception as e:
    st.info("Could not load header image")

st.write("###### <div style='text-align: center; font-weight: normal;'>This app is designed to explore the factors and implications of low-risk cesarean deliveries.  Low-risk is defined by the CDC as singleton, head-first, full-term (37 or more completed weeks) first births.</div>", unsafe_allow_html=True)
st.write("###### <div style='text-align: center; font-weight: normal;'>By Willna Goma</div>", unsafe_allow_html=True)
st.write("###### <div style='text-align: center; font-weight: normal;'>View data on GitHub</div>", unsafe_allow_html=True)
st.markdown("---")

st.write("The United States is facing a growing maternity care crisis.  In 2021, **26.3%** of births in the United States were delivered by cesarean (C-section), a surgical procedure that removes the baby through an abdominal incision.  The World Health Organization recommends rates do not surpass **10-15%**.")
st.markdown("<br><br>", unsafe_allow_html=True)
st.write("Maternal care interventions like cesarean sections, episiotomies, and early elective deliveries can present a host of dangerous complications like **blood clots**, **infections**, and **longer recovery**.  Women who have one C-section are predisposed to having another, while some hospitals do not offer vaginal delivery after C-Section (VBAC) at all.")
st.markdown("---")

# Debug section - show available files
with st.expander("🔍 Debug: Available Files"):
    st.write("**Current directory:**", os.getcwd())
    st.write("**Checking data folder:**")
    try:
        if os.path.exists('data'):
            files = [f for f in os.listdir('data') if f.endswith(('.geojson', '.csv', '.jpeg', '.jpg'))]
            st.write("**Files in data/ folder:**")
            for file in files:
                try:
                    full_path = f'data/{file}'
                    size = os.path.getsize(full_path) / (1024 * 1024)
                    st.write(f"- ✅ {file} ({size:.2f} MB)")
                except:
                    st.write(f"- ❓ {file} (could not read size)")
        else:
            st.error("❌ data/ folder not found!")
            # Show what IS in root directory
            root_files = [f for f in os.listdir('.') if f.endswith(('.geojson', '.csv', '.jpeg', '.jpg'))]
            st.write(f"Files in root directory: {root_files}")
    except Exception as e:
        st.error(f"Could not list files: {str(e)}")

# Helper functions with proper data/ paths
def safe_load_csv(filename):
    """Safely load CSV with error handling"""
    filepath = f'data/{filename}'
    try:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            st.success(f"✅ Successfully loaded {filename} ({len(df)} rows)")
            return df
        else:
            st.error(f"❌ File not found: {filepath}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading {filename}: {str(e)}")
        return pd.DataFrame()

def safe_load_geojson(filename):
    """Safely load GeoJSON with error handling"""
    filepath = f'data/{filename}'
    try:
        if not os.path.exists(filepath):
            st.error(f"❌ File not found: {filepath}")
            return None
        
        # Check file size
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        st.info(f"📁 Loading {filename} ({file_size:.2f} MB)")
        
        # Load the file
        gdf = gpd.read_file(filepath)
        st.success(f"✅ Successfully loaded {filename} ({len(gdf)} features)")
        return gdf
        
    except Exception as e:
        st.error(f"❌ Error loading {filename}: {str(e)}")
        return None

# Load data with correct data/ paths
st.subheader("📊 Loading Data...")

# Load CSV files from data folder
csv_data = safe_load_csv('stateavgs.csv')

# State-specific US map
st.write("#### <div style='text-align: center; font-weight: normal;'>Cesarean Delivery Rate by State</div>", unsafe_allow_html=True)

# Load US C-section rates from data folder
us_geo_data = safe_load_geojson('UScsectionrates.geojson')

if us_geo_data is not None and not us_geo_data.empty:
    try:
        # Clean the data
        us_geo_data = us_geo_data.dropna(subset=['YEAR', 'RATE'])
        us_geo_data['YEAR'] = pd.to_numeric(us_geo_data['YEAR'], errors='coerce')
        us_geo_data['RATE'] = pd.to_numeric(us_geo_data['RATE'], errors='coerce')
        us_geo_data = us_geo_data.dropna()
        
        available_years = sorted(us_geo_data['YEAR'].unique())
        
        if available_years:
            year = st.selectbox('Select Year', options=available_years, index=len(available_years)-1)
            year_data = us_geo_data[us_geo_data['YEAR'] == year]
            
            if not year_data.empty:
                try:
                    # Create folium map
                    m = folium.Map(location=[38, -96.5], zoom_start=4, tiles='cartodbpositron')
                    
                    folium.Choropleth(
                        geo_data=year_data.to_json(),
                        name='choropleth',
                        data=year_data,
                        columns=['shapeName', 'RATE'],
                        key_on='feature.properties.shapeName',
                        fill_color='Blues',
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name='C-Section Rate (%)',
                        highlight=True,
                        line_color='black'
                    ).add_to(m)
                    
                    folium.GeoJson(
                        year_data.to_json(),
                        style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
                        tooltip=folium.GeoJsonTooltip(
                            fields=['shapeName', 'RATE'],
                            aliases=['State:', 'Rate (%):'],
                            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
                        )
                    ).add_to(m)
                    
                    st.components.v1.html(m._repr_html_(), height=600, width=700)
                    
                except Exception as map_error:
                    st.error(f"Map creation failed: {str(map_error)}")
                    # Show data table as fallback
                    st.dataframe(year_data[['shapeName', 'RATE']].sort_values('RATE'))
            else:
                st.error(f"No data available for year {year}")
        else:
            st.error("No valid years found in data")
            
    except Exception as e:
        st.error(f"Error processing US map data: {str(e)}")
        if us_geo_data is not None:
            st.write("Data preview:")
            st.dataframe(us_geo_data.head())
else:
    st.error("Could not load US C-section data from data/UScsectionrates.geojson")

st.markdown("---")
st.write("As of 2021, South Dakota has the lowest C-section rate with an average of **18.1%** while Mississippi has the highest average rate of **31.2%**.  North Carolina has an average rate of 29.3%.")
st.markdown("---")

# County-specific map
st.write("#### <div style='text-align: center; font-weight: normal;'>Cesarean Delivery Rate by County from 2017-2021</div>", unsafe_allow_html=True)

# Load county data from data folder
county_geo_data = safe_load_geojson('Merged_County_Data.geojson')

if county_geo_data is not None and not county_geo_data.empty:
    try:
        # Clean county data
        if 'ck_date' in county_geo_data.columns:
            county_geo_data = county_geo_data.drop(columns=['ck_date'])
        
        county_geo_data['County'] = county_geo_data['County'].astype(str)
        county_geo_data['PERCENT'] = pd.to_numeric(county_geo_data['PERCENT'], errors='coerce')
        county_geo_data = county_geo_data.dropna(subset=['PERCENT'])
        
        county_options = sorted(county_geo_data['County'].unique())
        county_selection = st.selectbox('Select County (optional):', ['All'] + county_options)
        
        # Determine what data to show
        if county_selection != 'All':
            display_data = county_geo_data[county_geo_data['County'] == county_selection]
            if not display_data.empty:
                centroid = display_data.geometry.centroid.iloc[0]
                map_location = [centroid.y, centroid.x]
                zoom_level = 10
            else:
                st.error(f"County '{county_selection}' not found")
                display_data = county_geo_data
                map_location = [35.5, -79.0]
                zoom_level = 6
        else:
            display_data = county_geo_data
            map_location = [35.5, -79.0]
            zoom_level = 6
        
        if not display_data.empty:
            try:
                # Create county map
                n = folium.Map(location=map_location, zoom_start=zoom_level, tiles='cartodbpositron')
                
                folium.Choropleth(
                    geo_data=display_data.to_json(),
                    name='choropleth',
                    data=display_data,
                    columns=['County', 'PERCENT'],
                    key_on='feature.properties.County',
                    fill_color='RdPu',
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name='C-Section Rate (%)',
                    highlight=True,
                    line_color='black'
                ).add_to(n)
                
                folium.GeoJson(
                    display_data.to_json(),
                    style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
                    tooltip=folium.GeoJsonTooltip(
                        fields=['County', 'PERCENT'],
                        aliases=['County:', 'Rate (%):'],
                        style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
                    )
                ).add_to(n)
                
                st.components.v1.html(n._repr_html_(), height=600)
                
            except Exception as county_map_error:
                st.error(f"County map creation failed: {str(county_map_error)}")
                # Show table as fallback
                st.dataframe(display_data[['County', 'PERCENT']].sort_values('PERCENT', ascending=False))
        
    except Exception as e:
        st.error(f"Error processing county data: {str(e)}")
else:
    st.error("Could not load county data from data/Merged_County_Data.geojson")

st.markdown("---")
st.write("Bertie county had the highest rate of C-sections during that period of **39.7%** while Orange county had the lowest rate of **24.6%**.")
st.markdown("---")

# Interactive bar chart
demographic_data = safe_load_csv('Highest_and_Lowest_Counties.csv')

if not demographic_data.empty:
    try:
        attribute_nickname_map = {
            'Less than High School': '<HS',
            'High School Graduate or GED': 'HS Grad',
            'Some College': 'Some College',
            'College Degree': 'College Deg',
            'Inadequate Prenatal Care Index': 'Inadequate',
            'Intermediate Prenatal Care Index': 'Intermediate',
            'Adequate Prenatal Care Index': 'Adequate',
            'Adequate Plus Prenatal Care Index': 'Adequate+'
        }

        groupings = {
            'Age': ['Under 18 Years', '18-34 Years', '35+ Years'],
            'Resident Births': ['Resident Births'],  
            'Maternal Pre-Pregnancy BMI': ['Underweight (<18.5)', 'Normal (18.5-24.9)', 'Overweight (25.0-29.9)', 'Obese (30.0+)'],
            'Education': ['Less than High School', 'High School Graduate or GED', 'Some College', 'College Degree'],
            'Delivery Method': ['Vaginal', 'C-Section'],
            'Kotelchuck Adequacy of Prenatal Care Index': ['Inadequate Prenatal Care Index', 'Intermediate Prenatal Care Index', 'Adequate Prenatal Care Index', 'Adequate Plus Prenatal Care Index']
        }

        def apply_nicknames(attribute):
            return attribute_nickname_map.get(attribute, attribute)

        # Filter groupings to available attributes
        available_attributes = demographic_data['Attribute'].unique()
        filtered_groupings = {}
        for group_name, attributes in groupings.items():
            available_attrs = [attr for attr in attributes if attr in available_attributes]
            if available_attrs:
                filtered_groupings[group_name] = available_attrs

        if filtered_groupings:
            selected_group = st.selectbox("Select a Category or Group:", list(filtered_groupings.keys()))

            filtered_data = demographic_data[demographic_data['Attribute'].isin(filtered_groupings[selected_group])]

            if not filtered_data.empty:
                filtered_data = filtered_data.copy()
                filtered_data['Attribute'] = filtered_data['Attribute'].apply(apply_nicknames)

                percentage_cols = [col for col in ['White_Non_Hispanic_Percentage', 'Black_Non_Hispanic_Percentage', 'Multirace_Other_Non_Hispanic_Percentage', 'Hispanic_Percentage'] if col in filtered_data.columns]
                
                if percentage_cols:
                    melted_data = filtered_data.melt(id_vars=['County', 'Attribute'], 
                                                     value_vars=percentage_cols,
                                                     var_name='Race',
                                                     value_name='Percentage')

                    melted_data['Race'] = melted_data['Race'].str.replace('_Percentage', '').replace({
                        'White_Non_Hispanic': 'White', 
                        'Black_Non_Hispanic': 'Black', 
                        'Multirace_Other_Non_Hispanic': 'Multirace/Other', 
                        'Hispanic': 'Hispanic'})

                    fig = make_subplots(rows=1, cols=len(filtered_groupings[selected_group]), shared_yaxes=True,
                                        subplot_titles=[apply_nicknames(attr) for attr in filtered_groupings[selected_group]])

                    for idx, attribute in enumerate([apply_nicknames(attr) for attr in filtered_groupings[selected_group]], 1):
                        filtered_attr_data = melted_data[melted_data['Attribute'] == attribute]
                        
                        for race in filtered_attr_data['Race'].unique():
                            race_data = filtered_attr_data[filtered_attr_data['Race'] == race]
                            fig.add_trace(go.Bar(
                                x=race_data['County'], 
                                y=race_data['Percentage'], 
                                name=race, 
                                text=race,
                                marker=dict(color=race_data['Race'].apply(lambda x: {'White': 'blue', 'Black': '#6481AF', 'Multirace/Other': '#BB7E9D', 'Hispanic': 'purple'}.get(x))),
                                showlegend=(idx == 1)),
                                row=1, col=idx)

                    fig.update_layout(barmode='stack', title_text=f"Demographic Breakdown by County for {selected_group}*", height=600)

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Required percentage columns not found")
            else:
                st.write(f"No data available for {selected_group}")
        else:
            st.error("No matching attributes found in demographic data")
    except Exception as e:
        st.error(f"Error creating demographic chart: {str(e)}")
else:
    st.error("Demographic data not available from data/Highest_and_Lowest_Counties.csv")

st.markdown("---")
st.write("One of the biggest risk factors is the hospital you choose to attend.  In Orange county, one of the lower averaging counties for C-sections, Duke University hospital allows doulas, offers midwives, and VBAC.  However, the hospital's rate of early elective deliveries, inductions or cesarean sections performed prior to 39 completed weeks gestation without medical necessity, is **13.9%**.  On the other hand, outside of Craven county, ECU Health Beaufort Hospital, with a C-Section rate of **50%**, does not allow doulas, midwives, or VBAC.")
st.markdown("---")
st.write("*Bar graph includes data using all resident births, not just low-risk births.")