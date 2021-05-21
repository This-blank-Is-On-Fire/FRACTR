"""
Hydrant_analysis.py takes as input the hydrant_coords.geojson file,
sorts the hydrants based on flowrate (gallons per minute), 
and outputs the following geojson files:
- hydrant_unknown.geojson (hydrants with unknown flow rate)
- hydrant_red.geojson (less than 500 gpm)
- hydrant_orange.geojson (between 500 and 1000 gpm)
- hydrant_green.geojson (between 1000 and 1500 gpm)
- hydrant_blue.geojson (more than 1500 gpm)

These files contain geometric circles drawn around every hydrant. The circle radius
is 600 feet (183 meters), as this is the average maximum distance from which a fire engine 
can source water from the fire hydrant.

Authors: Halcyon Brown & John Cambefort
"""

import osmnx as ox
import geopandas as gpd
from tqdm import tqdm

ox.config(log_console=False, use_cache=True)

# Returns a circular buffer (in meters) around a hydrant given the hydrant coordinates 
# and the radius of the buffer
def make_buffer(hydrant, radius):
    # Create the buffer
    buffer = hydrant.buffer(radius)

    # Convert from Polygon to GeoSeries and undo projection
    buffer_series = gpd.GeoSeries(buffer, crs=3395)
    buffer_series = buffer_series.to_crs("EPSG:4326")

    # Convert from GeoSeries to GeoDataFrame
    buffer_gdf = gpd.GeoDataFrame([buffer_series])
    # Return the GeoDataFrame
    return buffer_gdf

########################################

if __name__ == "__main__":

    # Read in hydrant coordinate data
    hydrants = gpd.read_file("data/hydrant_coords.geojson")
    
    # Project the hydrant coordinates to Mercator
    hydrants = hydrants.to_crs(epsg=3395)

    # Initialize the dataframe that will hold all of the hydrant polygons
    hydrant_polys_gdf = gpd.GeoDataFrame()

    # Figure out the different hydrant flow rate categories
    for i in range(len(hydrants)):
        flow_rate = hydrants['FLOWRATE'].loc[i]
        if flow_rate is not None:
            edited_rate = flow_rate.split("g")[0]
            hydrants['FLOWRATE'].loc[i] = int(edited_rate)
        flow = hydrants['FLOWRATE'].loc[i]

    # Make a list containing the different hydrant colors based on flow rate (NFPA)
    flow_rate_list = ['blue', 'green', 'orange', 'red', 'unknown']

    # List of dataframes for each flow rate
    gdf_list = []
 
    # Initialize as many GeoDataFrames as there are flow rate bins
    # Store these new GeoDataFrames in the gdf_list array.
    for i in range(len(flow_rate_list)):
        gdf_list.append(gpd.GeoDataFrame())

    # Iterate through all of the hydants, creating the buffer polygons and add them to dataframe
    for i in tqdm(range(len(hydrants))):
        # Obtain the hydrant coordinates
        hydrant_of_interest = hydrants['geometry'].loc[i]

        # Obtain the flowrate
        flow_rate = hydrants['FLOWRATE'].loc[i]

        # Figure out what hydrant type the flow_rate corresponds to
        hydrant_type = ""
        if (flow_rate == None):
            hydrant_type = 'unknown' 
        elif (int(flow_rate) >= 1500):
            hyrant_type = 'blue'
        elif (int(flow_rate) >= 1000 and int(flow_rate) < 1500):
            hydrant_type = 'green'
        elif (int(flow_rate) >= 500 and int(flow_rate) < 1000):
            hydrant_type = 'orange'
        else:
            hydrant_type = 'red'
      
        # The buffer is initialized as 183 meters (600ft) - 305 meters = 1000ft
        buffer = make_buffer(hydrant_of_interest, 183)

        # Rename the geometry column
        buffer.columns = ['geometry']
        # Add a flowrate column to buffer dataframe
        buffer["FLOWRATE"] = hydrant_type
        # Add the buffer to the dataframe for all hydrant buffers
        hydrant_polys_gdf = hydrant_polys_gdf.append(buffer)

    for j in range(len(flow_rate_list)):
        row = hydrant_polys_gdf.loc[
            (hydrant_polys_gdf['FLOWRATE'] == flow_rate_list[j]), 
            ['FLOWRATE', 'geometry']
        ]
        gdf_list[j] = gdf_list[j].append(row)

    # Convert each of the flow rate GeoDataFrames to geoJson files to be read by Leaflet
    for i in range(len(gdf_list)):
        flow = flow_rate_list[i]
        # Check to see if any dataframes are empty and if so, do not export them to geojson
        if (gdf_list[i]).empty:
            continue
        else:
            gdf_list[i].to_file("data/%s.geojson" % ("hydrant_" + str(flow)), driver="GeoJSON")