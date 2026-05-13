import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html
import datetime as dt
import sys
FILE_NAME = 'data.csv'  # Change to your actual file name

# Common Kaggle Column Names (Update these if your CSV uses different headers)
COL_DATE = 'InvoiceDate'  
COL_CUST = 'CustomerID'   
COL_REV  = 'UnitPrice'    
COL_QTY  = 'Quantity'     
try:
    # ISO-8859-1 is a common encoding for Kaggle retail datasets
    df = pd.read_csv(FILE_NAME, encoding='ISO-8859-1', low_memory=False)
except FileNotFoundError:
    print(f"CRITICAL ERROR: The file '{FILE_NAME}' was not found in this folder.")
    sys.exit()

# Standardize Dates and Drop Missing Rows
df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors='coerce')
df = df.dropna(subset=[COL_DATE, COL_CUST, COL_REV, COL_QTY])

# Convert to numeric to ensure math functions work
df[COL_REV] = pd.to_numeric(df[COL_REV], errors='coerce')
df[COL_QTY] = pd.to_numeric(df[COL_QTY], errors='coerce')
df['TotalSales'] = df[COL_REV] * df[COL_QTY]
aov = df['TotalSales'].sum() / len(df)
unique_users = df[COL_CUST].nunique()
avg_purchase_freq = len(df) / unique_users
def get_month(x): return dt.datetime(x.year, x.month, 1)

df['InvoiceMonth'] = df[COL_DATE].apply(get_month)
df['CohortMonth'] = df.groupby(COL_CUST)['InvoiceMonth'].transform('min')

# Calculate the month index (Month 1, Month 2, etc.)
df['CohortIndex'] = ((df['InvoiceMonth'].dt.year - df['CohortMonth'].dt.year) * 12 + 
                     (df['InvoiceMonth'].dt.month - df['CohortMonth'].dt.month) + 1)

# Generate Retention Matrix
cohort_data = df.groupby(['CohortMonth', 'CohortIndex'])[COL_CUST].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values=COL_CUST)
retention = (cohort_pivot.divide(cohort_pivot.iloc[:,0], axis=0) * 100).round(1)

# Format dates for cleaner axis labels
retention.index = retention.index.strftime('%Y-%m')
app = Dash(__name__)

# Create the Heatmap
fig = px.imshow(
    retention,
    text_auto=True,
    color_continuous_scale='Blues',
    labels=dict(x="Months Since First Purchase", y="User Cohort", color="Retention %"),
    title="Customer Retention Deep-Dive"
)

app.layout = html.Div(style={'backgroundColor': '#f4f7f9', 'padding': '40px', 'fontFamily': 'sans-serif'}, children=[
    html.H1("Interactive Business Dashboard", style={'textAlign': 'center', 'color': '#1a2a6c'}),
    
    # KPI Section
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'margin': '30px 0'}, children=[
        html.Div([html.H4("Avg Order Value"), html.H2(f"${aov:.2f}")], className='kpi-box'),
        html.Div([html.H4("Retention (Overall)"), html.H2(f"{retention.mean().mean():.1f}%")], className='kpi-box'),
        html.Div([html.H4("Total Users"), html.H2(f"{unique_users:,}")], className='kpi-box'),
    ]),
    
    # Visualization Section
    html.Div([
        dcc.Graph(figure=fig)
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'})
])

# Injecting CSS for the KPI Boxes
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <style>
            .kpi-box { background: white; padding: 25px; border-radius: 10px; 
                       box-shadow: 0 4px 6px rgba(0,0,0,0.05); width: 28%; text-align: center; }
            .kpi-box h4 { color: #5f6368; margin-bottom: 10px; text-transform: uppercase; font-size: 14px; }
            .kpi-box h2 { color: #1a2a6c; margin: 0; }
        </style>
    </head>
    <body> {%app_entry%} {%config%} {%scripts%} {%renderer%} </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
    