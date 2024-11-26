import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static
import json
import matplotlib.pyplot as plt
import seaborn as sns


# Function to generate a unique color for each consultant or cluster
def get_color_mapping(consultants):
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
              'gray', 'black', 'lightgray']
    return {consultant: colors[i % len(colors)] for i, consultant in enumerate(consultants)}


final_assignments = pd.read_csv('data/newregion.csv')


with open('data/AVG_consultants_locations.json', 'r') as json_file:
    consultants_locations = json.load(json_file)

#options are: orig_consultant / suggested_consultant_opt_2
cons_col_name = 'orig_consultant'
cons_col_name = 'suggested_consultant_opt_2'

#options are:  orig_distance / distance_opt_2
dist_col_name = 'orig_distance'
dist_col_name = 'distance_opt_2'
combined_color_mapping = get_color_mapping(final_assignments[cons_col_name].unique())




# Streamlit app title
st.title("Contracts Map by Consultant")

# Add a multiselect widget to filter consultants
selected_consultants = st.multiselect(
    'Select Consultants to Display Contracts',
    options=list(consultants_locations.keys()),
    default=list(consultants_locations.keys())  # Default to showing all consultants
)

# Filter the final_assignments dataframe based on the selected consultants
filtered_assignments = final_assignments[final_assignments[cons_col_name].isin(selected_consultants)]

# Initialize the map centered at the average location of the filtered assignments
if len(filtered_assignments) > 0:
    map_center = [filtered_assignments['lat'].mean(), filtered_assignments['lon'].mean()]
else:
    map_center = [final_assignments['lat'].mean(), final_assignments['lon'].mean()]  # Default center if no consultants selected

mymap = folium.Map(location=map_center, zoom_start=6)

# Plot the contracts' locations for the selected consultants
for idx, row in filtered_assignments.iterrows():
    popup_info = (
        f"Werknemer: {row[cons_col_name]}<br>"
        f"Distance: {row[dist_col_name]} km<br>"
        f"Establishment: {row['establishment_name']}<br>"
        f"Landcode: : {row['Landcode']}<br>"
        f"Language: : {row['lang_short']}<br>"
        f"Contract Number: {row['QGuardContractNummer']}<br>"
        f"Address: {row['company_address']}"
    )
    color = combined_color_mapping.get(row[cons_col_name], 'gray')  # Default to gray if not found
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_info, max_width=300),
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(mymap)

# Plot the consultants' locations (always visible)
for consultant, coords in consultants_locations.items():
    folium.Marker(
        location=[coords['lat'], coords['lon']],
        popup=f"Consultant: {consultant}",
        icon=folium.Icon(color='gray', icon='home', prefix='fa')
    ).add_to(mymap)

# Display the map in Streamlit using folium_static
folium_static(mymap)



# Display final assignments in Streamlit using st.table()
st.title("Consultants' Assignment Summary")
# Group by consultant name ('Werknemer') to get the summary
summary = final_assignments.groupby(cons_col_name).agg(
    num_contracts=('id', 'count'),
    sum_refresh = ('refresh_hours', 'sum'),
    sum_open_hours=('open_hours_not_linked_to_refresh', 'sum'),
    sum_total_hours=('total_hours_to_perform', 'sum'),
    total_distance=(dist_col_name, 'sum'),  # Total Distance Traveled
    avg_distance=(dist_col_name, 'mean'),   # Average Distance per Contract
    max_distance=(dist_col_name, 'max'),    # Maximum Distance Traveled by Any Consultant
    std_distance=(dist_col_name, 'std')     # Standard Deviation of Distances
).reset_index()


st.dataframe(summary)


with open('data/AVG_consultants_locations.json', 'r') as json_file:
    consultants_dictionary = json.load(json_file)

# Filter combined_df to include only consultants from the provided dictionary
consultants_from_dict = list(consultants_dictionary.keys())

# Filter the DataFrame to include only relevant consultants
transfers = final_assignments[
    (final_assignments['orig_consultant'].isin(consultants_from_dict)) & 
    (final_assignments[cons_col_name].isin(consultants_from_dict))
]

transfers = final_assignments[
    (final_assignments[cons_col_name].isin(consultants_from_dict))
]

# Ensure transfers DataFrame is not empty
if not transfers.empty:
    # Prepare a sorted list of consultants for both axes
    sorted_consultants = sorted(consultants_from_dict)

    # Create the transfer matrix including retained cases with full alignment on both axes
    transfer_matrix = (
        transfers.groupby(['orig_consultant', cons_col_name])
        .size()
        .reindex(pd.MultiIndex.from_product([sorted_consultants, sorted_consultants]), fill_value=0)
        .unstack(fill_value=0)
    )

    # Display the heatmap of training transfers including retained trainings
    st.subheader("Heatmap Training Transfers")
    plt.figure(figsize=(12, 8))
    sns.heatmap(transfer_matrix, cmap='Blues', annot=True, fmt='d', linewidths=.5, xticklabels=True, yticklabels=True)
    plt.xlabel('Nieuwe Consultant')
    plt.ylabel('Originele Consultant')
    plt.title("Training Transfers")
    st.pyplot(plt)
    plt.close()  # Close the plot to prevent overlap


    # Distance statistics calculations
st.title("Distance Statistics Comparison")

# Calculate distance stats
result_df = final_assignments  # Assuming the DataFrame is pre-loaded
distance_stats = {
    "Metric": [
        "Total Distance Traveled",
        "Average Distance per Contract",
        "Maximum Distance Traveled by Any Consultant",
        "Standard Deviation of Distances"
    ],
    "Old Assignments": [
        result_df['orig_distance'].sum(),
        result_df['orig_distance'].mean(),
        result_df['orig_distance'].max(),
        result_df['orig_distance'].std()
    ],
    "Opt 2 Assignments": [
        result_df['distance_opt_2'].sum(),
        result_df['distance_opt_2'].mean(),
        result_df['distance_opt_2'].max(),
        result_df['distance_opt_2'].std()
    ],
    "% Difference Opt 2": [
        (result_df['distance_opt_2'].sum() - result_df['orig_distance'].sum()) / result_df['orig_distance'].sum() if result_df['orig_distance'].sum() else None,
        (result_df['distance_opt_2'].mean() - result_df['orig_distance'].mean()) / result_df['orig_distance'].mean() if result_df['orig_distance'].mean() else None,
        (result_df['distance_opt_2'].max() - result_df['orig_distance'].max()) / result_df['orig_distance'].max() if result_df['orig_distance'].max() else None,
        (result_df['distance_opt_2'].std() - result_df['orig_distance'].std()) / result_df['orig_distance'].std() if result_df['orig_distance'].std() else None
    ]
}

# Convert distance stats to a DataFrame
distance_stats_df = pd.DataFrame(distance_stats)

# Display the statistics in Streamlit
st.dataframe(distance_stats_df)

# Visualize the distance statistics
st.subheader("Distance Comparison Chart")

distance_stats_df_filt = distance_stats_df[distance_stats_df['Metric'].isin(["Average Distance per Contract", "Maximum Distance Traveled by Any Consultant", "Standard Deviation of Distances"])]
distance_stats_melted = distance_stats_df_filt.melt(id_vars=["Metric"], var_name="Assignment Type", value_name="Value")

# Create the bar plot
plt.figure(figsize=(12, 8))
ax = sns.barplot(
    data=distance_stats_melted, 
    x="Metric", 
    y="Value", 
    hue="Assignment Type", 
    palette="viridis"
)

# Add labels on top of the bars
for container in ax.containers:
    # Add labels for each bar
    ax.bar_label(
        container, 
        fmt="%.2f",  # Format values with 2 decimal places
        label_type="edge",  # Labels are placed outside the bars
        color="black", 
        fontsize=10
    )

# Set chart properties
plt.title("Distance Metrics Comparison")
plt.xticks(rotation=45)
plt.tight_layout()

# Display the plot in Streamlit
st.pyplot(plt)
plt.close()


st.title("Optimization Summary By Consultant")


summary_orig = result_df.groupby(cons_col_name).agg(
    num_contracts=('id', 'count'),
    sum_refresh = ('refresh_hours', 'sum'),
    sum_open_hours=('open_hours_not_linked_to_refresh', 'sum'),
    sum_total_hours=('total_hours_to_perform', 'sum'),
    total_distance=(dist_col_name, 'sum'),  # Total Distance Traveled
    avg_distance=(dist_col_name, 'mean'),   # Average Distance per Contract
    max_distance=(dist_col_name, 'max'),    # Maximum Distance Traveled by Any Consultant
    std_distance=(dist_col_name, 'std')     # Standard Deviation of Distances
).reset_index()

# Display the statistics in Streamlit
st.dataframe(summary_orig)