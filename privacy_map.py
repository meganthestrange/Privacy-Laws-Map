import pandas as pd
import geopandas as gpd
import folium
import re

# File paths
csv_file_path = "privacy_laws.csv"
geo_file_path = r"C:\Users\ricoh\Documents\PythonProjects\ne_110m_admin_1_states_provinces.shp"
map_file_path = "privacy_laws_map_with_legends.html"

# Load data
df = pd.read_csv(csv_file_path)
geo_df = gpd.read_file(geo_file_path)

# Standardize state names
df['State'] = df['State'].str.title()
geo_df['name'] = geo_df['name'].str.title()

# Fines parsing
def parse_fines(fine_str):
    if pd.isna(fine_str) or fine_str.lower() == "tbd":
        return 0
    if fine_str.lower() == "varies":
        return "Varies"
    numbers = re.findall(r'\d+(?:,\d+)?', str(fine_str))
    if numbers:
        return max(int(num.replace(',', '')) for num in numbers)
    return 0

df['Fines'] = df['Fines'].apply(parse_fines)

# Penalty category
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

df['Penalty Category'] = df['Fines'].apply(determine_penalty_category)

# Strictness determination
def determine_strictness(state):
    pending_states = ["Hawaii", "Maine", "Massachusetts", "Michigan", "Missouri", "New York", "Ohio", "Pennsylvania", "Wisconsin", "West Virginia"]
    strong_states = ["California", "Colorado", "Connecticut", "Delaware", "Indiana", "Montana", "Nevada", "New Hampshire", "New Jersey", "Oregon", "Tennessee", "Virginia"]
    weak_states = ["Florida", "Iowa", "Kentucky", "Minnesota", "Texas", "Utah", "Arizona", "North Carolina"]
    very_weak_states = ["Alabama", "Alaska", "Arkansas", "Georgia", "Idaho", "Illinois", "Kansas", "Louisiana", "Maryland", "Mississippi", "Nebraska", "North Dakota", "Oklahoma", "Rhode Island", "South Carolina", "South Dakota", "Vermont", "Washington", "Wyoming", "New Mexico"]
    
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

# Merge datasets
merged = pd.merge(geo_df, df, how='left', left_on='name', right_on='State').fillna({
    'ComprehensiveLaw': 0,
    'Law': 'None',
    'Statute': 'No data available',
    'Effective Date': 'No data available',
    'Applicability': 'No data available',
    'Consumer Rights': 'No data available',
    'Enforcer': 'No data available',
    'Fines': 0,
    'Penalty Category': 'Low',
    'Detailed Penalties': 'No detailed penalty information available'
})

# Comprehensive vs Noncomprehensive popup
merged['comprehensive_popup'] = merged.apply(
    lambda row: (f"<b>State:</b> {row['name']}<br><br><b>Comprehensive Privacy Law:</b> {row['Law']}"
                 if row['ComprehensiveLaw'] == 1 else
                 f"<b>State:</b> {row['name']}<br><br>"
                 f"<i style='color: blue;'>{row['name']} does not currently have a comprehensive data protection law in place. "
                 f"However, there are sector-specific regulations or proposed legislation that address certain aspects of privacy protection in {row['name']}.</i><br><br>"),
    axis=1
)

# Strictness popup
merged['strictness_popup'] = merged.apply(
    lambda row: f"<b>State:</b> {row['name']}<br><b>Strictness Level:</b> {row['Strictness']}<br>", axis=1)

# Penalty popup with additional details
merged['penalty_popup'] = merged.apply(
    lambda row: (f"<b>State:</b> {row['name']}<br><br>"
                 f"<b>Penalty Category:</b> {row['Penalty Category']}<br>"
                 f"<b>Fines:</b> {row['Fines']}<br>"
                 f"<b>Statute:</b> {row['Statute']}<br>"
                 f"<b>Applicability:</b> {row['Applicability']}<br>"
                 f"<b>Consumer Rights:</b> {row['Consumer Rights']}<br>"
                 f"<b>Effective Date:</b> {row['Effective Date']}<br>"
                 f"<b>Enforced By:</b> {row['Enforcer']}<br>"
                 f"<b>Detailed Penalties:</b> {row['Detailed Penalties']}<br>"), axis=1)

# Map setup
m = folium.Map(location=[37.8, -96], zoom_start=4)

# Layers
def create_layer(name, color_function, popup_field):
    feature_group = folium.FeatureGroup(name=name)
    folium.GeoJson(
        merged,
        style_function=color_function,
        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['State:'], style="font-size: 14px;"),
        popup=folium.GeoJsonPopup(fields=[popup_field], labels=False, style="font-size: 14px; background-color: white; border: 2px solid grey; padding: 10px; max-width: 800px;")
    ).add_to(feature_group)
    return feature_group

# Comprehensive vs Noncomprehensive Layer
m.add_child(create_layer(
    "Comprehensive vs Non-Comprehensive Privacy Laws",
    lambda feature: {'fillColor': '#09d600' if feature['properties']['ComprehensiveLaw'] == 1 else '#C70039',
                     'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
    'comprehensive_popup'
))

# Strictness Layer
m.add_child(create_layer(
    "Strictness of Privacy Laws",
    lambda feature: {'fillColor': '#09d600' if feature['properties']['Strictness'] == "Very Strong" else (
                     '#1f77b4' if feature['properties']['Strictness'] == "Strong" else (
                     '#FFC300' if feature['properties']['Strictness'] == "Pending" else (
                     '#FF5733' if feature['properties']['Strictness'] == "Weak" else '#C70039'))),
                     'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
    'strictness_popup'
))

# Penalties Layer
m.add_child(create_layer(
    "Penalties for Data Breach Noncompliance",
    lambda feature: {'fillColor': '#09d600' if feature['properties']['Penalty Category'] == "Low" else (
                     '#FFC300' if feature['properties']['Penalty Category'] == "Medium" else (
                     '#FF5733' if feature['properties']['Penalty Category'] == "High" else (
                     '#C70039' if feature['properties']['Penalty Category'] == "Severe" else '#808080'))),
                     'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
    'penalty_popup'
))

# Add title
m.get_root().html.add_child(folium.Element("""
    <div style='position: fixed; top: 10px; left: 50%; transform: translateX(-50%); 
                width: 400px; height: auto; background-color: white; z-index:9999; 
                font-size: 20px; font-weight: bold; text-align: center; 
                border:2px solid grey; padding: 10px;'>
        Privacy Laws by U.S. State
    </div>
"""))

# Add instructions
m.get_root().html.add_child(folium.Element("""
    <div style='position: fixed; 
                bottom: 10px; left: 10px; width: 330px; height: auto; 
                background-color: white; z-index:9999; font-size: 16px; 
                border:2px solid grey; padding: 10px; box-shadow: 3px 3px 5px grey;'>
        <b>How to Use This Map:</b><br>
        <ul style='font-size: 14px; list-style-type: disc; padding-left: 20px;'>
            <li>Hover over a state to view its name.</li>
            <li>Click on a state to view detailed information.</li>
            <li>Use the layer control in the upper right corner to toggle layers.</li>
        </ul>
    </div>
"""))

# Add legends
def add_legend(position, html_content):
    legend_html = f"""
        <div style='position: fixed; {position}; width: 270px; background-color: white; z-index:9999; font-size: 14px; 
                    border:2px solid grey; padding: 10px; box-shadow: 3px 3px 5px grey;'>
        {html_content}
        </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

# Comprehensive Legend
add_legend("top: 320px; right: 10px", """
    <b>Comprehensive vs Non-Comprehensive:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> Comprehensive<br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> Non-Comprehensive<br>
""")

# Strictness Legend
add_legend("top: 430px; right: 10px", """
    <b>Strictness Level:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> 
    <b>Very Strong:</b> States that fully meet comprehensive privacy protection standards (no states currently).<br>
    <i style='background: #1f77b4; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> 
    <b>Strong:</b> States with comprehensive privacy laws including access, deletion, portability, opt-out, and correction.<br>
    <i style='background: #FFC300; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> 
    <b>Pending:</b> States with proposed privacy legislation not yet enacted.<br>
    <i style='background: #FF5733; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> 
    <b>Weak:</b> States with limited privacy protections or gaps in rights and enforcement.<br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> 
    <b>Very Weak:</b> States with minimal privacy protections, often sector-specific or inadequate.<br>
""")


# Penalties Legend
add_legend("top: 780px; right: 10px", """
    <b>Penalties for Data Breach Noncompliance:</b><br>
    <i style='background: #09d600; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> Low<br>
    <i style='background: #FFC300; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> Medium<br>
    <i style='background: #FF5733; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> High<br>
    <i style='background: #C70039; width: 18px; height: 18px; float: left; margin-right: 8px;'></i> Severe<br>
""")

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Save map
m.save(map_file_path)
