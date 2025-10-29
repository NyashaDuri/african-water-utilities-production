import streamlit as st
import pandas as pd
import altair as alt

# Set page configuration
st.set_page_config(layout="wide")

# Constants
FILE_PATH = "data/production_basic_aggregated.csv"
DATE_COLUMN = 'date'
METRIC_COLUMNS = ['production_m3', 'production_m3_per_hour']

@st.cache_data
def load_data():
    data = pd.read_csv(
        FILE_PATH,
        parse_dates=[DATE_COLUMN],
        date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d', errors='coerce')
    )
    # Set date as index and resolve any missing date parsing (coercing errors to NaT)
    data = data.dropna(subset=[DATE_COLUMN])
    data = data.set_index(DATE_COLUMN)
    
    # Rename columns for better display
    data = data.rename(columns={
        'production_m3': 'Production (m³)',
        'service_hours': 'Service Hours',
        'production_m3_per_hour': 'Efficiency (m³/hour)'
    })
    return data

# Load data
try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Error: The file '{FILE_PATH}' was not found. Please ensure your data is saved correctly.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while loading or parsing the data: {e}")
    st.stop()

# --- Title and Header ---
st.title("Water Production Dashboard: Country and Source Analysis")
st.markdown("Analyzing daily production and efficiency metrics over time for water sources.")

# --- Sidebar Filters ---
st.sidebar.header("Filter Data")

# Country selector
countries = df['country'].unique()
selected_countries = st.sidebar.multiselect(
    'Select Country',
    countries,
    default=countries
)

# Source selector (only show sources for selected countries)
filtered_by_country = df[df['country'].isin(selected_countries)]
sources = filtered_by_country['source'].unique()
selected_sources = st.sidebar.multiselect(
    'Select Source',
    sources,
    default=sources
)

# Apply filters
filtered_df = df[
    df['country'].isin(selected_countries) & 
    df['source'].isin(selected_sources)
]

# --- Main Metrics (Kaggs) ---
if not filtered_df.empty:
    col1, col2, col3 = st.columns(3)
    
    # Calculate key metrics for the filtered subset
    total_production = filtered_df['Production (m³)'].sum() / 1_000_000 # Convert to Million m³
    avg_efficiency = filtered_df['Efficiency (m³/hour)'].mean()
    total_service_hours = filtered_df['Service Hours'].sum()
    
    col1.metric(
        "Total Production", 
        f"{total_production:,.2f} M m³", 
        delta_color="off"
    )
    col2.metric(
        "Average Efficiency", 
        f"{avg_efficiency:,.2f} m³/hour",
        delta_color="off"
    )
    col3.metric(
        "Total Service Hours", 
        f"{total_service_hours:,.0f} hours",
        delta_color="off"
    )
    
    st.markdown("---")
    
    # --- Visualization ---
    st.subheader("Production and Efficiency Over Time")

    # Metric Selector for the main chart
    metric_options = ['Production (m³)', 'Efficiency (m³/hour)', 'Service Hours']
    selected_metric = st.selectbox("Select Metric to Visualize", metric_options)

    # Prepare data for Altair chart (reset index to make 'date' a column)
    chart_data = filtered_df.reset_index()
    
    # Create the line chart with tooltips
    chart = alt.Chart(chart_data).mark_line().encode(
        x=alt.X(DATE_COLUMN, title="Date"),
        y=alt.Y(selected_metric, title=selected_metric),
        color='source', # Differentiate lines by source
        tooltip=[DATE_COLUMN, 'country', 'source', selected_metric]
    ).properties(
        title=f'{selected_metric} by Source Over Time'
    ).interactive() # Allows zooming and panning
    
    st.altair_chart(chart, use_container_width=True)

else:
    st.warning("No data found for the selected filters. Please adjust your selections.")

# --- Raw Data Display (Optional) ---
if st.sidebar.checkbox('Show Raw Data'):
    st.subheader('Raw Data (First 100 rows)')
    st.write(filtered_df.head(100))
