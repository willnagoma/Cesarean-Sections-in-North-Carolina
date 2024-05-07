import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import numpy as np 
import folium
import json
import plotly.express as px

import plotly.graph_objs as go
from plotly.subplots import make_subplots

#Introduction block
st.write("<h1 style='text-align: center;'>Cesarean Deliveries in North Carolina</h1>", unsafe_allow_html=True)
st.write("#### <div style='text-align: center; font-style: italic;'>Malpractice or medical necessity?</div>", unsafe_allow_html=True)

image_path = 'delivered_baby.jpeg'
st.image(image_path, use_column_width=True)

st.write("###### <div style='text-align: center; font-weight: normal;'>This app is designed to explore the factors and implications of low-risk cesarean deliveries.  Low-risk is defined by the CDC as singleton, head-first, full-term (37 or more completed weeks) first births.</div>", unsafe_allow_html=True)
st.write("###### <div style='text-align: center; font-weight: normal;'>By Willna Goma</div>", unsafe_allow_html=True)
st.write("###### <div style='text-align: center; font-weight: normal;'>View data on GitHub</div>", unsafe_allow_html=True)
st.markdown("---")

st.write("The United States is facing a growing maternity care crisis.  In 2021, **26.3%** of births in the United States were delivered by cesarean (C-section), a surgical procedure that removes the baby through an abdominal incision.  The World Health Organization recommends rates do not surpass **10-15%**.")
st.markdown("<br><br>", unsafe_allow_html=True)
st.write("Maternal care interventions like cesarean sections, episiotomies, and early elective deliveries can present a host of dangerous complications like **blood clots**, **infections**, and **longer recovery**.  Women who have one C-section are predisposed to having another, while some hospitals do not offer vaginal delivery after C-Section (VBAC) at all.")
st.markdown("---")

#Merging JSON and CSV to have one file with rates and coordinates
csv_file_path = 'data/stateavgs.csv'  
geojson_file_path = 'data/usstates.geojson'  
csv_data = pd.read_csv(csv_file_path)
geo_data = gpd.read_file(geojson_file_path)
merged_data = pd.merge(geo_data, csv_data, left_on='shapeName', right_on='shapeName', how='inner')

#State-specific US map
def load_data():
    geo_data = gpd.read_file('data/UScsectionrates.geojson')
    geo_data.dropna(subset=['YEAR', 'RATE'], inplace=True)  
    geo_data['YEAR'] = geo_data['YEAR'].astype(int)
    geo_data['RATE'] = geo_data['RATE'].astype(float)
    return geo_data

geo_data = load_data()

def generate_map(year):
    year_data = geo_data[geo_data['YEAR'] == year]
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
        legend_name='Rate (%)',
        highlight=True,
        line_color='black',
        show=True,
        overlay=True,
        nan_fill_color='gray'  
    ).add_to(m)

    folium.GeoJson(
        year_data.to_json(),
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
        tooltip=folium.GeoJsonTooltip(
            fields=['shapeName', 'RATE'],
            aliases=['State:', 'Rate:'],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    ).add_to(m)
    return m._repr_html_()

def main():
    st.write("#### <div style='text-align: center; font-weight: normal;'>Cesarean Delivery Rate by State</div>", unsafe_allow_html=True)
    year = st.selectbox('Select Year', options=sorted(geo_data['YEAR'].unique()))
    folium_map_html = generate_map(year)
    st.components.v1.html(folium_map_html, height=600, width=700)

if __name__ == "__main__":
    main()

st.markdown("---")
st.write("As of 2021, South Dakota has the lowest C-section rate with an average of **18.1%** while Mississippi has the highest average rate of **31.2%**.  North Carolina has an average rate of 29.3%.")
st.markdown("---")

#County-specific map
def load_data():
    geo_data = gpd.read_file('data/Merged_County_Data.geojson')
    geo_data.drop(columns=['ck_date'], inplace=True)
    geo_data['County'] = geo_data['County'].astype(str)
    geo_data['PERCENT'] = geo_data['PERCENT'].astype(float)
    return geo_data

geo_data = load_data()

def generate_map(county=None):
    if county:
        county_data = geo_data[geo_data['County'] == county]
        centroid = county_data.geometry.centroid.iloc[0]
        map_location = [centroid.y, centroid.x]
        zoom_level = 10 
    else:
        map_location = [35.5, -79.0]
        zoom_level = 6
        county_data = geo_data

    n = folium.Map(location=map_location, zoom_start=zoom_level, tiles='cartodbpositron')
    folium.Choropleth(
        geo_data=county_data.to_json(),
        name='choropleth',
        data=county_data,
        columns=['County', 'PERCENT'],
        key_on='feature.properties.County',
        fill_color='RdPu',  
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Rate (%)',
        highlight=True,
        line_color='black',
        show=True,
        overlay=True,
        nan_fill_color='gray'
    ).add_to(n)

    folium.GeoJson(
        county_data.to_json(),
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
        tooltip=folium.GeoJsonTooltip(
            fields=['County', 'PERCENT'],
            aliases=['County:', 'PERCENT:'],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    ).add_to(n)
    return n._repr_html_()

def main():
    st.write("#### <div style='text-align: center; font-weight: normal;'>Cesarean Delivery Rate by County from 2017-2021</div>", unsafe_allow_html=True)
    county_options = sorted(geo_data['County'].unique())
    county_selection = st.selectbox('Select County (optional):', ['All'] + county_options)
    if county_selection != 'All':
        folium_map_html = generate_map(county_selection)
    else:
        folium_map_html = generate_map()
    st.components.v1.html(folium_map_html, height=600)

if __name__ == "__main__":
    main()

st.markdown("---")
st.write("Bertie county had the highest rate of C-sections during that period of **39.7%** while Orange county had the lowest rate of **24.6%**.")
st.markdown("---")

#Interactive bar chart
data = pd.read_csv('/Users/lorrainegoma/Desktop/CSectionsNC/data/Highest_and_Lowest_Counties.csv')

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

data = pd.read_csv('/Users/lorrainegoma/Desktop/CSectionsNC/data/Highest_and_Lowest_Counties.csv')

selected_group = st.selectbox("Select a Category or Group:", list(groupings.keys()))

filtered_data = data[data['Attribute'].isin(groupings[selected_group])]

filtered_data['Attribute'] = filtered_data['Attribute'].apply(apply_nicknames)

melted_data = filtered_data.melt(id_vars=['County', 'Attribute'], 
                                 value_vars=[
                                    'White_Non_Hispanic_Percentage', 
                                    'Black_Non_Hispanic_Percentage', 
                                    'Multirace_Other_Non_Hispanic_Percentage', 
                                    'Hispanic_Percentage'],
                                 var_name='Race',
                                 value_name='Percentage')

melted_data['Race'] = melted_data['Race'].str.replace('_Percentage', '').replace({
    'White_Non_Hispanic': 'White', 
    'Black_Non_Hispanic': 'Black', 
    'Multirace_Other_Non_Hispanic': 'Multirace/Other', 
    'Hispanic': 'Hispanic'})

fig = make_subplots(rows=1, cols=len(groupings[selected_group]), shared_yaxes=True,
                    subplot_titles=[apply_nicknames(attr) for attr in groupings[selected_group]])

for idx, attribute in enumerate([apply_nicknames(attr) for attr in groupings[selected_group]], 1):
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

st.plotly_chart(fig)

st.markdown("---")
st.write("One of the biggest risk factors is the hospital you choose to attend.  In Orange county, one of the lower averaging counties for C-sections, Duke University hospital allows doulas, offers midwives, and VBAC.  However, the hospital's rate of early elective deliveries, inductions or cesarean sections performed prior to 39 completed weeks gestation without medical necessity, is **13.9%**.  On the other hand, outside of Craven county, ECU Health Beaufort Hospital, with a C-Section rate of **50%**, does not allow doulas, midwives, or VBAC.")
st.markdown("---")
st.write("*Bar graph includes data using all resident births, not just low-risk births.")
