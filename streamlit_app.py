import pandas as pd
import numpy as np
from platformdirs import user_state_dir
import pydeck as pdk
from pydeck.types import String
import datetime
from datetime import date
import json
from pygments import highlight
import streamlit as st
import os
import altair as alt
import geopandas as gpd
st.set_page_config(layout='wide')


@st.cache(allow_output_mutation=True)
def load_json():
        cur_json = json.load(open('geojson-data/us_states_20m.json', encoding='ISO-8859-1'))
        path,ext = os.path.splitext('geojson-data/us_states_20m.json')
        new_path =path+"_new"+ext
        with open(new_path,"w", encoding='utf-8') as jsonfile:
                json.dump(cur_json,jsonfile,ensure_ascii=False)
        us_state = gpd.read_file(new_path, driver='GeoJSON')
        us_state = us_state.sort_values(by='NAME')
        us_state['coordinate'] = us_state.geometry.centroid
        us_state['long'] = us_state.coordinate.apply(lambda p:p.x)
        us_state['lat'] = us_state.coordinate.apply(lambda p:p.y)
        try:
                us_state.drop(['GEO_ID', 'STATE', 'LSAD', 'CENSUSAREA', 'coordinate'], axis=1, inplace=True)
        except:
                print('Aready removed the columns')
        return us_state
#data obtained from New York times github : https://github.com/nytimes/covid-19-data
@st.cache
def load_cases_csv():
        us_state_grouped_df = pd.read_csv('covid-data/us_state_cases_grouped.csv')
        daily_total_results = pd.read_csv('covid-data/us_daily_total_results.csv')
        daily_total_results.date = pd.to_datetime(daily_total_results.date)
        return us_state_grouped_df, daily_total_results

@st.cache
def load_mask_geojson():
        county_mask_data = gpd.read_file(r'covid-data\mask_data_cleaned.geojson')
        return county_mask_data

us_state = load_json()
us_state_grouped_df, daily_total_results = load_cases_csv()
us_state_grouped_df = us_state_grouped_df.groupby(by=['date', 'state']).sum()
mask_data = load_mask_geojson()

row1_1, row1_2 = st.columns((2,2))

with row1_1:
        st.title('Covid-19 cases exploration over time')

with row1_2:
        st.write('This web app allows the user to see the coronavirus cases and \
                deaths over time grouped by states. The absolute scales in each \
                figure is different for better visualization.')


cols1,_ = st.columns((1,0.001)) # To make it narrower
format = 'MMM DD, YYYY'  # format output
start_date = datetime.date(2021, 1, 1) 
end_date = datetime.date(2022, 1, 29) 
max_days = end_date-start_date

curr_date = cols1.slider('Select date', min_value=start_date, value=start_date ,max_value=end_date, format=format)

iso_date = curr_date.isoformat() #start_date.isoformat()
covid_daily_cases = us_state_grouped_df.loc[iso_date, 'daily_cases'].values
us_state['daily_cases'] = covid_daily_cases
covid_daily_deaths = us_state_grouped_df.loc[iso_date, 'daily_deaths'].values
us_state['daily_deaths'] = covid_daily_deaths

LAND_COVER = [[[-123.0, 49.196], [-123.0, 49.324], [-123.306, 49.324], [-123.306, 49.196]]]
long = -94.7
lat = 37.090

row2_1, row2_2 = st.columns((2,2))

with row2_1:
        st.write("### Covid-19 cases grouped by states over time")
        INITIAL_VIEW_STATE = pdk.ViewState(latitude=lat, 
                                    longitude=long, 
                                    zoom=3, 
                                    max_zoom=16, 
                                    pitch=60, 
                                    bearing=0)
        text = pdk.Layer(
            "TextLayer",
            us_state,
            #pickable=True,
            get_position=['long', 'lat'],
            get_text="NAME",
            get_size=16,
            get_color=[255, 0, 0],
            get_angle=0,
            # Note that string constants in pydeck are explicitly passed as strings
            # This distinguishes them from columns in a data set
            #get_text_anchor=String("middle"),
            get_alignment_baseline=String("bottom")
        )

        geojson = pdk.Layer(
                "GeoJsonLayer",
                data=us_state,
                opacity=0.1,
                stroked=True,
                filled=True,
                extruded=True,
                wireframe=True,
                #get_elevation='daily_cases',
                #elevation_Scale=100000,
                get_fill_color="[220, 250, 255]",
                get_line_color=[0, 255, 0]
        )

        column = pdk.Layer(
                'ColumnLayer',
                us_state,
                get_position=['long', 'lat'],
                auto_highlight=True,
                elevation_scale=20,
                pickable=True,
                get_elevation='daily_cases',
                elevation_range=[0, 3000],
                extruded=True,
                coverage=45,
                get_fill_color="[255, 255-255*daily_cases/100000, 0]")
        tooltip={"html": "<b>State:</b> {NAME}</br> <b>Cases:</b> {daily_cases}"}
        st.write(pdk.Deck(layers=[text, geojson, column], initial_view_state=INITIAL_VIEW_STATE, tooltip=tooltip))
        
        #plot the daily total results
        daily_total_cases_plot = alt.Chart(daily_total_results).mark_area(
                color="lightblue",
                interpolate='step-after',
                line=True
                ).encode(x='date', y='cases')
        
        vline = pd.DataFrame({'date':[curr_date]})
        vline.date = pd.to_datetime(vline.date)
        rules = alt.Chart(vline).mark_rule().encode(x='date',
                        color=alt.value('#FFAA00'),
                        strokeWidth=alt.value(4),
                        )

        st.altair_chart(daily_total_cases_plot + rules, use_container_width=True)

with row2_2:
        st.write("### Covid-19 deaths grouped by states over time")
        INITIAL_VIEW_STATE = pdk.ViewState(latitude=lat, 
                                    longitude=long, 
                                    zoom=3, 
                                    max_zoom=16, 
                                    pitch=60, 
                                    bearing=0)
        text = pdk.Layer(
            "TextLayer",
            us_state,
            #pickable=True,
            get_position=['long', 'lat'],
            get_text="NAME",
            get_size=16,
            get_color=[255, 0, 0],
            get_angle=0,
            get_alignment_baseline=String("bottom"),
        )

        geojson = pdk.Layer(
                "GeoJsonLayer",
                data=us_state,
                opacity=0.1,
                stroked=True,
                filled=True,
                extruded=True,
                wireframe=True,
                #get_elevation='daily_cases',
                #elevation_Scale=100000,
                get_fill_color="[220, 250, 255]",
                get_line_color=[0, 255, 0]
        )

        column = pdk.Layer(
                'ColumnLayer',
                us_state,
                get_position=['long', 'lat'],
                auto_highlight=True,
                elevation_scale=2000,
                pickable=True,
                get_elevation='daily_deaths',
                elevation_range=[0, 3000],
                extruded=True,
                coverage=45,
                get_fill_color="[255, 255-255*daily_deaths/1000, 0]")
        tooltip={"html": "<b>State:</b> {NAME}</br> <b>Deaths:</b> {daily_deaths}"}
        st.write(pdk.Deck(layers=[text, geojson, column], initial_view_state=INITIAL_VIEW_STATE, tooltip=tooltip))
        
        #plot daily total cases 
        daily_total_cases_plot = alt.Chart(daily_total_results).mark_area(
                color="lightblue",
                interpolate='step-after',
                line=True
                ).encode(x='date', y='deaths')
        vline = pd.DataFrame({'date':[curr_date]})
        vline.date = pd.to_datetime(vline.date)
        rules = alt.Chart(vline).mark_rule().encode(x='date',
                        color=alt.value('#FFAA00'),
                        strokeWidth=alt.value(4))

        st.altair_chart(daily_total_cases_plot + rules, use_container_width=True)

INITIAL_VIEW_STATE = pdk.ViewState(latitude=38.2, 
                                    longitude=-94.7, 
                                    zoom=3.8, 
                                    max_zoom=16, 
                                    pitch=0, 
                                    bearing=0)
geojson = pdk.Layer(
        "GeoJsonLayer",
        data=mask_data,
        pickable=True,
        opacity=0.1,
        stroked=True,
        filled=True,
        extruded=True,
        wireframe=True,
        get_elevation=10,
        elevation_Scale=1,
        get_fill_color="[2.5*255*(1-ALWAYS_and_FREQUENTLY), 255*ALWAYS_and_FREQUENTLY, 0*255*ALWAYS_and_FREQUENTLY]",
        get_line_color=[0, 200, 0]
)

tooltip={"html": "<b>County:</b> {NAME}</br> <b>State:</b> {STATE}</br> <b>Fraction Wear Mask:</b> {ALWAYS_and_FREQUENTLY}"}
st.write('### Figure showing fraction of people who always or freqnently wear masks grouped by counties')
st.write(pdk.Deck(layers=[geojson], initial_view_state=INITIAL_VIEW_STATE, tooltip=tooltip))
st.write('Dark Green color represents a high fraction of people waering mask and dark red represents low fraction of people wearing masks regularly.')
#st.write('Green represents counties where a lot of people always or freqnently \
#        wear masks. Red is where proportion of people who rarely wear mask are high.')
#st.write(pdk.Deck(layers=[geojson], initial_view_state=INITIAL_VIEW_STATE, tooltip=tooltip))
