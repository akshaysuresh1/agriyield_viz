# Load required packages.
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
############################################################
# Load shapefile of Indian districts.
shp = gpd.read_file('Data/India_dld.shp')

# Load argiculture data set.
df = pd.read_csv('Data/ICRISAT_allcrops.csv')
df['dist_state'] = df['Dist Name']+', '+df['State Name']
############################################################
# Creating application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Quantity to plot
quantity_options = [{'label':'Harvested area', 'value':'Area (1000 ha)'},
                    {'label':'Production', 'value':'Production (1000 tons)'}, 
                    {'label':'Yield', 'value':'Yield (kg per ha)'}
                   ]

# List of crops
crops_options = [{'label':'Cotton', 'value':'Cotton'},
                 {'label':'Groundnut', 'value':'Groundnut'},
                 {'label':'Rice', 'value':'Rice'},
                 {'label':'Sugarcane', 'value':'Sugarcane'},
                 {'label':'Wheat', 'value':'Wheat'}
                ]

# Setting application layout
app.layout = dbc.Container([
                            html.Center(html.H2('District-level Distribution of Annual Crop Growth in India')),
                            html.Hr(),
                            dbc.Row([# Column 1: Quantity to plot 
                                     dbc.Col([dbc.Label('Quantity to visualize'),
                                              dcc.Dropdown(id='quantity-dropdown', options=quantity_options, placeholder='Select quantity...', value='Yield (kg per ha)'),
                                            ]),
                                    # Column 2: Select crop.
                                     dbc.Col([dbc.Label('Crop'),
                                              dcc.Dropdown(id='crops-dropdown', options=crops_options, placeholder='Select crop...', value='Wheat'),
                                            ]),
                                    # Column 3: Select year.
                                      dbc.Col([dbc.Label('Year'),
                                               dcc.Slider(1990, 2017, 1, id='year-slider', marks=None, tooltip={"placement": "bottom", "always_visible": True},
                                                          className='m-4', value=2010),
                                            ]),                                           
                                   ]),
                            dcc.Graph(id='choropleth-dashboard'),
                            html.Hr(),
                            dcc.Link('Github repository', href='https://github.com/akshaysuresh1/agriyield_viz', id='github-link'),
                            html.Br(),
                            dcc.Link('ICRISAT district-level agriculture database', href='http://data.icrisat.org/dashboard/dld/src/crops.html', id='datasource-link'),
                           ], fluid=True, )

# Setting the callback
@app.callback(
    Output('choropleth-dashboard', 'figure'), 
    [Input('quantity-dropdown', 'value'), Input('crops-dropdown', 'value'), Input('year-slider', 'value')])
def display_choropleth(quantity, crop, year):
    # Column of interest in  agriculture data set
    column = str(crop) + ' ' + str(quantity)
    selection_allyears = df[['Year', 'dist_state', column]]
    selection_chosenyear = selection_allyears.loc[selection_allyears['Year']==year, ['dist_state', column]].reset_index(drop=True)
    selection_chosenyear['text'] = selection_chosenyear['dist_state'] + '<br>' + column + ' = ' + selection_chosenyear[column].astype(str)
    # Separate districts in shape file into two categories: ones with available crop growth data, and ones without available agriculture data.
    diststates_in_df, counts = np.unique(selection_chosenyear['dist_state'], return_counts=True)
    diststates_not_in_df = [x for x in shp['dist_state'] if x not in diststates_in_df]
    # Assign NaNs to districts in shape file with no available crop growth data.
    df_comp = pd.DataFrame({'dist_state': diststates_not_in_df, column: np.ones(len(diststates_not_in_df))*-1})
    df_comp['text'] = df_comp['dist_state'] + '<br>' + pd.Series(['Data not available']*len(diststates_not_in_df))
    final_df = selection_chosenyear.append(df_comp, ignore_index=True)
    # Merge shapefile and agriculture data on common field "dist_state".
    final_shp = shp.merge(final_df, on='dist_state')
    # Set up color scheme for plotting.
    cmin = final_df.loc[final_df[column]>=0, column].min()
    cmax = final_df[column].max()
    #  Set up custom color map.
    ylgn = px.colors.sequential.YlGn
    colorscale =  [[0, 'lightgray'], [(cmin+1)/(cmax+1), 'lightgray'], [(cmin+1)/(cmax+1), ylgn[0]], [1, ylgn[-2]]]   
    # Plotting
    fig = px.choropleth(final_shp, geojson=final_shp.geometry,
                        locations=final_shp.index, color=column, projection="mercator", 
                        color_continuous_scale=colorscale, hover_data={'text':False, 'dist_state':False, column:False},
                        custom_data=['text'])
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_traces(hovertemplate='%{customdata[0]}')
    fig.update_layout(height=600, autosize=True, margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      coloraxis_colorbar=dict(len=0.5,x=0.95,xanchor='right',y=0.5,yanchor='middle'),)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)

# END OF CODE
############################################################
