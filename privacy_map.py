import pandas as pd
import geopandas as gpd
import folium
import re

# File paths for easy modification
csv_file_path = 'privacy_laws.csv' # from pandas, reads data from a Comma Seperated Values file and loads it into a DataFrame (tablestructure for Python)
geo_file_path = r"C:\Users\ricoh\Documents\PythonProjects\ne_110m_admin_1_states_provinces.shp" # Shapefile format. Used for storing geospatial vector data. supported by GeoPandas
map_file_path = "privacy_laws_map_with_legends.html"

# Load the CSV file
df = pd.read_csv(csv_file_path)
geo_df = gpd.read_file(geo_file_path) # from GeoPandas library, allows geospatial data files such as .shp to be read

# Standardize state names for upcoming merging - to avoid potential mismatching of state names between datasets
df['State'] = df['State'].str.title()
geo_df['name'] = geo_df['name'].str.title() # str.title() capitalizes the first letter of each element

# Fines Parsing Function - for numerical comparison
# This step will extract the maximum numeral fines and use it for comparison
def parse_fines(fine_str):
    if pd.isna(fine_str) or fine_str.lower() == "tbd":
        return 0
    if fine_str.lower() == "varies":
        return "Varies"

# Extract all numeral values from the string with regex - regular expression, used to extract numbers from fine strings
# Added re.findall() command so only numerical values are extracted from strings that contain both text and numerals
    numbers = re.findall(r'\d+(?:,\d+)?', fine_str) # Finds all occurrences of a pattern in a string
    if numbers:
        # Convert to integers after removing commas
        parsed_values = [int(num.replace(',', '')) for num in numbers]
        # Return the maximum value
        return max(parsed_values)
    return 0

# Apply Fines parsing
df['Fines'] = df['Fines'].apply(parse_fines)

# Noncompliance Penalty Category Function
def determine_penalty_category(penalty):
    if penalty == "Varies":
        return "Varies"
    elif penalty <= 500:
        return "Low"
    elif penalty <= 10000:
        return "Medium"
    elif penalty <= 50000:
        return "High"
    else:
        return "Severe"

# Apply penalty category function
df['Penalty Category'] = df['Fines'].apply(determine_penalty_category)

# Add strictness levels for each state
def determine_strictness(state):
    pending_states = ["Hawaii", "Maine", "Massachusetts", "Michigan", "Missouri", "New York", "Ohio", "Pennsylvania", "Wisconsin", "West Virginia"]
    strong_states = ["California", "Colorado", "Connecticut", "Delaware", "Indiana", "Montana", "Nevada", "New Hampshire", "New Jersey", "Oregon", "Tennessee", "Virginia"]
    weak_states = ["Florida", "Iowa", "Kentucky", "Minnesota", "Texas", "Utah", "Arizona", "North Carolina"]
    very_weak_states = ["Alabama", "Alaska", "Arkansas", "Georgia", "Idaho", "Illinois", "Kansas", "Louisiana", "Maryland", "Mississippi", "Nebraska", "North Dakota", "Oklahoma", "Rhode Island", "South Carolina", "South Dakota", "Vermont", "Washington", "Wyoming"]
    
    if state in pending_states:
        return "Pending"
    elif state in strong_states:
        return "Strong"
    elif state in weak_states:
        return "Weak"
    elif state in very_weak_states:
        return "Very Weak"
    return "Very Weak"

df['Strictness'] = df['State'].apply(determine_strictness)

# Add detailed penalty information
df['Detailed Penalties'] = df['State'].map({
    "Alabama": "Up to $500,000.",
    "Alaska": "Varies.",
    "Arizona": "Up to $10,000 per violation.",
    "Arkansas": "Up to $10,000 per violation.",
    "California": "Up to $7,500 per intentional violation.",
    "Colorado": "Varies.",
    "Connecticut": "$5,000 per willful violation.",
    "Delaware": "$10,000 per violation.",
    "Florida": "Up to $500,000.",
    "Georgia": "Up to $10,000.",
    "Hawaii": "Varies.",
    "Idaho": "Varies.",
    "Illinois": "Up to $50,000.",
    "Indiana": "Up to $150,000.",
    "Iowa": "$1,000 per violation.",
    "Kansas": "Varies.",
    "Kentucky": "$1,000 per day of delayed notification.",
    "Louisiana": "Up to $5,000 per violation.",
    "Maine": "$500 per violation.",
    "Maryland": "Up to $1,000 per violation.",
    "Massachusetts": "$5,000 per violation.",
    "Michigan": "Up to $750,000.",
    "Minnesota": "$25,000 per violation.",
    "Mississippi": "Up to $10,000.",
    "Missouri": "$1,000 per violation (estimated).",
    "Montana": "Varies.",
    "Nebraska": "$2,000 per violation.",
    "Nevada": "Up to $5,000 per violation.",
    "New Hampshire": "$1,000 per violation.",
    "New Jersey": "Up to $10,000 per violation.",
    "New Mexico": "Up to $150,000.",
    "New York": "$5,000 per violation.",
    "North Carolina": "$5,000 per violation.",
    "North Dakota": "$5,000 per violation.",
    "Ohio": "$1,000 per violation.",
    "Oklahoma": "Varies.",
    "Oregon": "Up to $1,000 per violation.",
    "Pennsylvania": "Up to $10,000.",
    "Rhode Island": "$1,000 per violation.",
    "South Carolina": "Varies.",
    "South Dakota": "Varies.",
    "Tennessee": "$2,500 per violation.",
    "Texas": "$250,000 maximum.",
    "Utah": "Varies.",
    "Vermont": "$10,000 per violation.",
    "Virginia": "Up to $2,500 per violation.",
    "Washington": "$5,000 per violation.",
    "West Virginia": "$5,000 per violation.",
    "Wisconsin": "Up to $1,000 per violation.",
    "Wyoming": "$10,000 per violation."
})

# Merges the CSV data into GeoDataFrame - combines the geospatial data (state shapes) from GeoPandas w/ the privacy law information from Pandas. This keeps everything in one place, because Folium requires this
# Any state without data will be assigned default placeholders (like "No Data Available") using the .fillna() command to avoid any errors.
merged = pd.merge(geo_df, df, how='left', left_on='name', right_on='State').fillna({
    'ComprehensiveLaw': 0,
    'Law': 'No data available',
    'Effective Date': 'No data available',
    'Applicability': 'No data available',
    'Consumer Rights': 'No data available',
    'Enforcer': 'No data available',
    'Strictness': 'Very Weak',
    'Fines': 0,
    'Penalty Category': 'Low',
    'Detailed Penalties': 'No detailed penalty information available'
})

# Create popups for each state that vary based on data shown - comprehensive vs non-comprehensive
def generate_popup(row, law_info=True):
    if law_info and row['ComprehensiveLaw'] == 1:
        return (f"<b>State:</b> {row['name']}<br><br>"
                f"<b>Law:</b> {row['Law']}<br><br>"
                f"<b>Effective Date:</b> {row['Effective Date']}<br><br>"
                f"<b>Applicability:</b> {row['Applicability']}<br><br>"
                f"<b>Consumer Rights:</b> {row['Consumer Rights']}<br><br>"
                f"<b>Enforced by:</b> {row['Enforcer']}<br><br>"
                f"<b>Detailed Penalties:</b> {row['Detailed Penalties']}<br><br>")
    return (f"<b>State:</b> {row['name']}<br><br>"
            f"<i style='color: blue;'>{row['name']} does not currently have a comprehensive data protection law in place. "
            f"However, there are sector-specific regulations or proposed legislation that address certain aspects of privacy protection in {row['name']}.</i><br><br>")

merged['comprehensive_popup'] = merged.apply(lambda row: generate_popup(row, law_info=True), axis=1)
merged['strictness_popup'] = merged.apply(lambda row: f"<b>State:</b> {row['name']}<br><br><b>Strictness Level:</b> {row['Strictness']}", axis=1)
merged['penalty_popup'] = merged.apply(lambda row: f"<b>State:</b> {row['name']}<br><br><b>Penalty Category:</b> {row['Penalty Category']}<br><br><b>Detailed Penalties:</b> {row['Detailed Penalties']}", axis=1)

# Create Folium map
def create_layer(feature_group_name, color_function, popup_field):
    feature_group = folium.FeatureGroup(name=feature_group_name)
    folium.GeoJson(
        merged,
        style_function=color_function,
        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['State:'], localize=True, style="font-size: 20px;"),
        popup=folium.GeoJsonPopup(fields=[popup_field], labels=False, localize=True,
                                  style="font-size: 14px; background-color: white; border: 2px solid grey; padding: 10px; max-width: 800px;"),
        highlight_function=lambda x: {'weight': 3, 'color': 'blue'} #the highlight_function will highlight the borders of a state so that users can clearly know which state they are about to click on
    ).add_to(feature_group)
    return feature_group

# Defines map
m = folium.Map(location=[37.8, -96], zoom_start=4)

# Adds feature layers that can be toggled on and off seperately
m.add_child(create_layer('Comprehensive vs Non-Comprehensive Privacy Laws',
                         lambda feature: {'fillColor': '#09d600' if feature['properties']['ComprehensiveLaw'] == 1 else '#C70039',
                                          'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
                         'comprehensive_popup'))

m.add_child(create_layer('Strictness of Privacy Laws',
                         lambda feature: {'fillColor': '#09d600' if feature['properties']['Strictness'] == "Very Strong" else (
                             '#1f77b4' if feature['properties']['Strictness'] == "Strong" else (
                                 '#FFC300' if feature['properties']['Strictness'] == "Pending" else (
                                     '#FF5733' if feature['properties']['Strictness'] == "Weak" else '#C70039'))),
                                          'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
                         'strictness_popup'))

# Add Varies Category
m.add_child(create_layer('Penalties for Noncompliance',
                         lambda feature: {
                             'fillColor': '#09d600' if feature['properties']['Penalty Category'] == "Low" else (
                                 '#FFC300' if feature['properties']['Penalty Category'] == "Medium" else (
                                     '#FF5733' if feature['properties']['Penalty Category'] == "High" else (
                                         '#C70039' if feature['properties']['Penalty Category'] == "Severe" else '#808080'))),
                             'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
                         'penalty_popup'))

# Add legends using custom HTML elements (I wanted to make the legend, map title, and instructions static, Folium wouldn't let me do that.)
def add_legend(position, html_content):
    legend_html = f"""
        <div style='position: fixed; {position}: 10px; width: 270px; background-color: white; z-index:9999; font-size: 14px; 
                    border:2px solid grey; padding: 10px; box-shadow: 3px 3px 5px grey;'>
        {html_content}
        </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html)) #This command integrates the HTML elements into the root of the Folium map

# Add Comprehensive vs Non-Comprehensive Legend
add_legend('top: 240px; right', """
    <b>Comprehensive vs Non-Comprehensive:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Comprehensive Privacy Laws</b><br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Non-Comprehensive Privacy Laws</b><br>
""")

# Add Strictness Legend
add_legend('bottom: 190px; right', """
    <b>Strictness Level:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Very Strong</b>: No state meets all privacy protection standards to be considered Very Strong.<br>
    <i style='background: #1f77b4; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Strong</b>: States with comprehensive privacy laws including access, deletion, portability, opt-out, and correction.<br>
    <i style='background: #FFC300; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Pending</b>: These states have proposed privacy legislation that has not yet been enacted.<br>
    <i style='background: #FF5733; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Weak</b>: States with some consumer protections, but with gaps in rights or enforcement.<br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Very Weak</b>: States with minimal or sector-specific privacy protections, often lacking comprehensive consumer rights.<br>
""")

# Add Penalties Legend
add_legend('bottom: 20px; right', """
    <b>Penalties for Noncompliance:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Low</b>: $0 - $500<br>
    <i style='background: #FFC300; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Medium</b>: $501 - $10,000<br>
    <i style='background: #FF5733; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>High</b>: $10,001 - $50,000<br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Severe</b>: Above $50,000<br>
    <i style='background: #808080; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> <b>Varies</b>: The fine varies based on circumstances.<br>
""")

# Add maps title
m.get_root().html.add_child(folium.Element("""
     <div style='position: fixed; top: 10px; left: 50%; transform: translateX(-50%); width: 400px; height: auto; 
                 background-color: white; z-index:9999; font-size: 24px; font-weight: bold; text-align: center; 
                 border:2px solid grey; padding: 10px; box-shadow: 3px 3px 5px grey;'>
     Privacy Laws by U.S. State
     </div>
"""))

# Add instructions
instruction_html = """
    <div style='position: fixed; 
                bottom: 10px; left: 10px; width: 330px; height: auto; 
                background-color: white; z-index:9999; font-size: 16px; 
                border:2px solid grey; padding: 10px; box-shadow: 3px 3px 5px grey;'>
    <b>How to Use This Map:</b><br>
    <ul style='font-size: 14px; list-style-type: disc; padding-left: 20px;'>
        <li>Hover over a state to view its name.</li>
        <li>Click on a state to view detailed information, including descriptions.</li>
        <li>Use the layer control in the upper right corner to toggle between the layers.</li>
    </ul>
    </div>
"""
m.get_root().html.add_child(folium.Element(instruction_html))

# Add layer control widget for switching between different map layers and save the map
folium.LayerControl(collapsed=False).add_to(m)
m.save(map_file_path)