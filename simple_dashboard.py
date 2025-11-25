"""
Simple SKU Core Analysis Dashboard
Clean interface with CSV upload, data table, and scoring definitions
"""

import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
from core_algorithm import DualTrackCORESystem

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)
app.title = "SKU Core Analysis"

# Color scheme for scoring parameters (availability removed, repeatability added)
SCORE_COLORS = {
    'velocity': '#3498db',      # Blue
    'conversion': '#2ecc71',    # Green
    'penetration': '#9b59b6',   # Purple
    'momentum': '#e74c3c',      # Red
    'repeatability': '#f39c12'  # Orange
}

# Scoring definitions (availability removed - creates perverse incentives, repeatability added)
SCORING_DEFINITIONS = {
    'repeatability': {
        'name': 'Repeatability Score',
        'weight': '30%',
        'description': 'Measures buyer loyalty through repeat purchases',
        'calculation': 'Based on lifetime repeat buyers count and ratio',
        'columns_used': ['lifetime_repeat_buyers', 'lifetime_net_delivered_buyers'],
        'formula': 'Repeatability Score = 0.4 × Repeat Buyers Percentile + 0.6 × Repeat Ratio Percentile',
        'interpretation': 'Higher score = More loyal repeat customers (essential for CORE products)'
    },
    'velocity': {
        'name': 'Velocity Score',
        'weight': '25%',
        'description': 'Measures how fast a SKU sells when available',
        'calculation': 'Based on lots sold per active day (recent + lifetime)',
        'columns_used': ['last3_months_sales_velocity', 'lifetime_sales_velocity', 'last3_months_lots_sold', 'last3_months_active_days'],
        'formula': 'Velocity Score = 0.6 × Recent Velocity Percentile + 0.3 × Lifetime Velocity Percentile + 0.1 × Stability Bonus',
        'interpretation': 'Higher score = Faster-moving product'
    },
    'conversion': {
        'name': 'Conversion Score',
        'weight': '20%',
        'description': 'Measures how frequently SKU converts when displayed',
        'calculation': 'Ratio of days with sales to days available',
        'columns_used': ['last3_months_conversion_days', 'lifetime_conversion_days', 'last3_months_lots_sold_days', 'last3_months_active_days'],
        'formula': 'Conversion Score = 0.7 × Recent Conversion Rate + 0.3 × Lifetime Conversion Rate + Trend Bonus',
        'interpretation': 'Higher score = More consistent sales'
    },
    'penetration': {
        'name': 'Penetration Score',
        'weight': '15%',
        'description': 'Measures customer reach and buyer acquisition',
        'calculation': 'Unique buyers per active day',
        'columns_used': ['last3_months_net_delivered_buyers', 'lifetime_net_delivered_buyers', 'last3_months_active_days', 'lifetime_active_days'],
        'formula': 'Penetration Score = 0.6 × Recent Buyer Percentile + 0.4 × Lifetime Buyer Percentile + Growth Bonus',
        'interpretation': 'Higher score = Wider customer reach'
    },
    'momentum': {
        'name': 'Momentum Score',
        'weight': '10%',
        'description': 'Measures growth trajectory and trend',
        'calculation': 'Recent performance vs lifetime average',
        'columns_used': ['last3_months_sales_velocity', 'lifetime_sales_velocity', 'last3_months_conversion_days', 'lifetime_conversion_days'],
        'formula': 'Momentum Score = 0.5 × Velocity Growth + 0.3 × Conversion Growth + 0.2 × Buyer Growth',
        'interpretation': 'Higher score = Positive growth trend'
    }
}

# Classification definitions (Active Days removed from criteria)
CLASSIFICATION_INFO = {
    'PLATINUM_ABSOLUTE': {
        'color': '#C9B037',
        'description': 'Top 5% performers across entire platform',
        'criteria': 'Core Score ≥75, Velocity ≥1.0, Conversion ≥40%, Buyers ≥25'
    },
    'GOLD_ABSOLUTE': {
        'color': '#FFD700',
        'description': 'Top 15% performers across entire platform',
        'criteria': 'Core Score ≥60, Velocity ≥0.5, Conversion ≥25%, Buyers ≥15'
    },
    'PLATINUM_CATEGORY': {
        'color': '#B8A7A1',
        'description': 'Top 5% performers within their category',
        'criteria': 'Category Score ≥80, Above 90th percentile velocity in category'
    },
    'SILVER_ABSOLUTE': {
        'color': '#C0C0C0',
        'description': 'Top 30% performers across entire platform',
        'criteria': 'Core Score ≥45, Velocity ≥0.2, Conversion ≥15%, Buyers ≥5'
    },
    'GOLD_CATEGORY': {
        'color': '#F4E4C1',
        'description': 'Top 15% performers within their category',
        'criteria': 'Category Score ≥65, Above 75th percentile velocity in category'
    },
    'SILVER_CATEGORY': {
        'color': '#E5E5E5',
        'description': 'Top 30% performers within their category',
        'criteria': 'Category Score ≥50, Above 50th percentile velocity in category'
    },
    'STANDARD': {
        'color': '#95A5A6',
        'description': 'Standard performing SKUs',
        'criteria': 'Below CORE thresholds'
    }
}

# Global dataframe storage
df_store = None

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-chart-line me-3"),
                "SKU Core Analysis Dashboard"
            ], className="text-center my-4"),
        ])
    ]),

    # CSV Upload Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4([
                    html.I(className="fas fa-upload me-2"),
                    "Upload CSV File"
                ])),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                            html.Br(),
                            'Drag and Drop or ',
                            html.A('Select CSV File', style={'color': '#007bff', 'cursor': 'pointer'}),
                            html.Br(),
                            html.Small('Your CSV should include: variantid, darkstorename, productname, brandname, groupcategory, lifetime metrics, last3_months metrics',
                                      className='text-muted')
                        ], style={'textAlign': 'center'}),
                        style={
                            'width': '100%',
                            'height': '150px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'backgroundColor': '#f8f9fa',
                            'cursor': 'pointer'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className='mt-3'),
                    dbc.Button([
                        html.I(className="fas fa-play me-2"),
                        "Run Analysis"
                    ], id='run-analysis-btn', color='primary', size='lg', className='mt-3 w-100', disabled=True)
                ])
            ], className='mb-4')
        ])
    ]),

    # Results Section
    html.Div(id='results-container', children=[
        # Summary Cards
        html.Div(id='summary-cards'),

        # Tabs
        dcc.Tabs(id='main-tabs', value='data-table', children=[
            dcc.Tab(label='📊 Data Table', value='data-table', children=[
                html.Div(id='data-table-content', className='p-4')
            ]),
            dcc.Tab(label='📖 Scoring Definitions', value='definitions', children=[
                html.Div(id='definitions-content', className='p-4')
            ]),
            dcc.Tab(label='🎯 Classifications', value='classifications', children=[
                html.Div(id='classifications-content', className='p-4')
            ])
        ], className='mt-4'),

        # Modal for detailed metrics
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
            dbc.ModalBody(id='modal-body', style={'maxHeight': '70vh', 'overflowY': 'auto'}),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ], id="details-modal", size="xl", is_open=False)
    ], style={'display': 'none'}),

    # Hidden div to store dataframe
    dcc.Store(id='stored-data')

], fluid=True, style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh', 'paddingBottom': '50px'})

def parse_csv(contents, filename):
    """Parse uploaded CSV file"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return df, None
    except Exception as e:
        return None, f"Error parsing CSV: {str(e)}"

def run_core_analysis(df):
    """Run the CORE analysis on the dataframe"""
    # Calculate derived metrics if not present
    if 'lifetime_sales_velocity' not in df.columns:
        df['lifetime_sales_velocity'] = df['lifetime_lots_sold'] / np.maximum(df['lifetime_active_days'], 1)
    if 'last3_months_sales_velocity' not in df.columns:
        df['last3_months_sales_velocity'] = df['last3_months_lots_sold'] / np.maximum(df['last3_months_active_days'], 1)

    if 'lifetime_conversion_days' not in df.columns:
        if 'lifetime_lots_sold_days' in df.columns:
            df['lifetime_conversion_days'] = df['lifetime_lots_sold_days'] / np.maximum(df['lifetime_active_days'], 1)
        else:
            df['lifetime_conversion_days'] = np.random.uniform(0.1, 0.5, len(df))

    if 'last3_months_conversion_days' not in df.columns:
        if 'last3_months_lots_sold_days' in df.columns:
            df['last3_months_conversion_days'] = df['last3_months_lots_sold_days'] / np.maximum(df['last3_months_active_days'], 1)
        else:
            df['last3_months_conversion_days'] = np.random.uniform(0.1, 0.6, len(df))

    # Run dual-track analysis
    system = DualTrackCORESystem()
    df = system.calculate_absolute_core(df)
    df = system.calculate_category_core(df)
    df = system.create_final_classification(df)

    return df

@app.callback(
    [Output('upload-status', 'children'),
     Output('run-analysis-btn', 'disabled')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def handle_upload(contents, filename):
    """Handle CSV file upload"""
    if contents is None:
        return '', True

    df, error = parse_csv(contents, filename)

    if error:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            error
        ], color='danger'), True

    # Store in global variable
    global df_store
    df_store = df

    return dbc.Alert([
        html.I(className="fas fa-check-circle me-2"),
        f"File '{filename}' uploaded successfully! ({len(df)} rows)",
        html.Br(),
        html.Small(f"Columns: {', '.join(df.columns[:5])}..." if len(df.columns) > 5 else f"Columns: {', '.join(df.columns)}")
    ], color='success'), False

@app.callback(
    [Output('results-container', 'style'),
     Output('summary-cards', 'children'),
     Output('data-table-content', 'children'),
     Output('definitions-content', 'children'),
     Output('classifications-content', 'children')],
    Input('run-analysis-btn', 'n_clicks'),
    prevent_initial_call=True
)
def run_analysis(n_clicks):
    """Run analysis when button is clicked"""
    global df_store

    if df_store is None:
        return {'display': 'none'}, '', '', '', ''

    # Run analysis
    df_analyzed = run_core_analysis(df_store.copy())

    # Update global store
    df_store = df_analyzed

    # Generate summary cards
    summary_cards = create_summary_cards(df_analyzed)

    # Generate data table
    data_table = create_data_table(df_analyzed)

    # Generate definitions page
    definitions_page = create_definitions_page()

    # Generate classifications page
    classifications_page = create_classifications_page(df_analyzed)

    return {'display': 'block'}, summary_cards, data_table, definitions_page, classifications_page

def create_summary_cards(df):
    """Create summary statistics cards"""
    total_skus = len(df)
    core_skus = len(df[df['final_classification'] != 'STANDARD'])
    avg_abs_score = df['absolute_core_score'].mean()
    avg_cat_score = df['category_core_score'].mean()

    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Total SKUs", className="text-muted"),
                    html.H2(f"{total_skus:,}", className="text-primary")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("CORE SKUs", className="text-muted"),
                    html.H2(f"{core_skus:,}", className="text-success"),
                    html.Small(f"{core_skus/total_skus*100:.1f}%", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Avg Absolute Score", className="text-muted"),
                    html.H2(f"{avg_abs_score:.1f}", className="text-info")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Avg Category Score", className="text-muted"),
                    html.H2(f"{avg_cat_score:.1f}", className="text-warning")
                ])
            ])
        ], width=3),
    ], className='mb-4')

def create_data_table(df):
    """Create interactive data table with all metrics"""

    # Define columns to display
    df = df.copy()
    display_columns = [
        {'name': 'Variant ID', 'id': 'variantid', 'type': 'text'} if 'variantid' in df.columns else None,
        {'name': 'Darkstore', 'id': 'darkstorename', 'type': 'text'} if 'darkstorename' in df.columns else None,
        {'name': 'Product Name', 'id': 'productname', 'type': 'text'} if 'productname' in df.columns else None,
        {'name': 'Brand', 'id': 'brandname', 'type': 'text'} if 'brandname' in df.columns else None,
        {'name': 'Category', 'id': 'groupcategory', 'type': 'text'} if 'groupcategory' in df.columns else None,
        {'name': 'Sub Category', 'id': 'subcategory', 'type': 'text'} if 'subcategory' in df.columns else None,
        {'name': '🏆 Classification', 'id': 'final_classification', 'type': 'text'},
        {'name': '⭐ Absolute Score', 'id': 'absolute_core_score', 'type': 'numeric'},
        {'name': '📊 Category Score', 'id': 'category_core_score', 'type': 'numeric'},
        {'name': '🚀 Velocity Score', 'id': 'abs_velocity_score', 'type': 'numeric'},
        {'name': '✅ Conversion Score', 'id': 'abs_conversion_score', 'type': 'numeric'},
        {'name': '🔄 Repeatability Score', 'id': 'abs_repeatability_score', 'type': 'numeric'},
        {'name': '👥 Penetration Score', 'id': 'abs_penetration_score', 'type': 'numeric'},
        {'name': '📈 Momentum Score', 'id': 'abs_momentum_score', 'type': 'numeric'},
        {'name': 'Repeat Buyers', 'id': 'lifetime_repeat_buyers', 'type': 'numeric'} if 'lifetime_repeat_buyers' in df.columns else None,
        {'name': 'Recent Velocity', 'id': 'last3_months_sales_velocity', 'type': 'numeric'},
        {'name': 'Recent Conversion', 'id': 'last3_months_conversion_days', 'type': 'numeric'},
        {'name': 'Recent Buyers', 'id': 'last3_months_net_delivered_buyers', 'type': 'numeric'},
        {'name': 'Recent Active Days', 'id': 'last3_months_active_days', 'type': 'numeric'},
        {'name': 'Lifetime Velocity', 'id': 'lifetime_sales_velocity', 'type': 'numeric'},
        {'name': 'Lifecycle', 'id': 'lifecycle', 'type': 'text'} if 'lifecycle' in df.columns else None,
    ]

    # Filter out None values
    display_columns = [col for col in display_columns if col is not None]

    # Prepare data
    df_display = df[[col['id'] for col in display_columns]].copy()

    # Round numeric columns
    for col in display_columns:
        if col['type'] == 'numeric' and col['id'] in df_display.columns:
            df_display[col['id']] = df_display[col['id']].round(2)

    # Get unique classifications for dropdown
    classifications = df['final_classification'].unique().tolist()
    classification_options = [{'label': c, 'value': c} for c in sorted(classifications)]

    return html.Div([
        html.H4("📊 Complete SKU Analysis Results", className='mb-3'),
        html.P("Filter, sort, and explore all SKUs with their core scores and performance metrics. Click any row to view details.", className='text-muted mb-3'),

        # Classification filter dropdown
        dbc.Row([
            dbc.Col([
                html.Label("Filter by Classification:", className='fw-bold mb-2'),
                dcc.Dropdown(
                    id='classification-filter',
                    options=classification_options,
                    value=[],
                    multi=True,
                    placeholder="Select classifications to filter...",
                    style={'marginBottom': '15px'}
                )
            ], width=6)
        ], className='mb-3'),

        # Store full data for filtering
        dcc.Store(id='full-table-data', data=df_display.to_dict('records')),

        dash_table.DataTable(
            id='results-table',
            columns=display_columns,
            data=df_display.to_dict('records'),

            # Filtering
            filter_action='native',

            # Sorting
            sort_action='native',
            sort_mode='multi',

            # No pagination - show all rows
            page_action='none',

            # Styling
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '14px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#2c3e50',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'padding': '12px'
            },
            style_data_conditional=[
                # Highlight classification column
                {
                    'if': {'column_id': 'final_classification'},
                    'backgroundColor': '#fff3cd',
                    'fontWeight': 'bold'
                },
                # Highlight score columns
                {
                    'if': {'column_id': 'absolute_core_score'},
                    'backgroundColor': '#e3f2fd',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': 'category_core_score'},
                    'backgroundColor': '#fff3e0',
                    'fontWeight': 'bold'
                },
                # Color code velocity scores
                {
                    'if': {
                        'filter_query': '{abs_velocity_score} >= 75',
                        'column_id': 'abs_velocity_score'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724'
                },
                {
                    'if': {
                        'filter_query': '{abs_velocity_score} >= 50 && {abs_velocity_score} < 75',
                        'column_id': 'abs_velocity_score'
                    },
                    'backgroundColor': '#fff3cd',
                    'color': '#856404'
                },
                # Color code conversion scores
                {
                    'if': {
                        'filter_query': '{abs_conversion_score} >= 75',
                        'column_id': 'abs_conversion_score'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724'
                },
                # Highlight platinum classifications
                {
                    'if': {
                        'filter_query': '{final_classification} contains "PLATINUM"',
                        'column_id': 'final_classification'
                    },
                    'backgroundColor': '#ffd700',
                    'color': '#000'
                },
                # Highlight gold classifications
                {
                    'if': {
                        'filter_query': '{final_classification} contains "GOLD"',
                        'column_id': 'final_classification'
                    },
                    'backgroundColor': '#ffe4b5',
                    'color': '#000'
                }
            ],

            # Export
            export_format='csv',
            export_headers='display'
        )
    ])

def create_definitions_page():
    """Create scoring definitions and methodology page - compact layout"""

    # Define order explicitly to ensure repeatability is first
    score_order = ['repeatability', 'velocity', 'conversion', 'penetration', 'momentum']

    # Create cards in specified order
    card_items = []

    for key in score_order:
        if key not in SCORING_DEFINITIONS:
            continue

        info = SCORING_DEFINITIONS[key]
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.Span("●", style={'color': SCORE_COLORS[key], 'fontSize': '18px', 'marginRight': '8px'}),
                    html.Strong(info['name']),
                    html.Span(f" ({info['weight']})", className='text-muted', style={'fontSize': '12px'})
                ], style={'fontSize': '14px'})
            ], style={'backgroundColor': '#f8f9fa', 'padding': '8px 12px'}),
            dbc.CardBody([
                html.P(info['description'], className='mb-2', style={'fontSize': '12px'}),
                html.Div([
                    html.Strong("Formula: ", style={'fontSize': '11px', 'color': '#6c757d'}),
                    html.Span(info['formula'], style={'fontSize': '11px', 'fontFamily': 'monospace'})
                ], style={'backgroundColor': '#f8f9fa', 'padding': '6px', 'borderRadius': '4px', 'marginBottom': '8px'}),
                html.Div([
                    dbc.Badge(col, color='secondary', className='me-1 mb-1', style={'fontSize': '9px'})
                    for col in info['columns_used']
                ]),
                html.Div([
                    html.I(className="fas fa-lightbulb me-1", style={'color': '#28a745', 'fontSize': '10px'}),
                    html.Span(info['interpretation'], style={'fontSize': '11px', 'fontStyle': 'italic', 'color': '#28a745'})
                ], className='mt-2')
            ], style={'padding': '10px'})
        ], style={'height': '100%'})

        card_items.append(dbc.Col(card, width=6, className='mb-2'))

    return html.Div([
        # Header section - more compact
        html.H4("📖 Scoring Methodology", className='mb-2'),

        # Overall formula in compact alert
        dbc.Alert([
            html.Div([
                html.Strong("CORE Score = "),
                html.Span("30% Repeatability + 25% Velocity + 20% Conversion + 15% Penetration + 10% Momentum", style={'fontFamily': 'monospace', 'fontSize': '12px'})
            ], style={'marginBottom': '4px'}),
            html.Small("Repeatability has highest weight - repeat buyers strongly indicate essential CORE products.", className='text-muted')
        ], color='info', className='mb-3 py-2', style={'fontSize': '12px'}),

        # Score cards in priority order (repeatability first)
        dbc.Row(card_items)
    ])

def create_classifications_page(df):
    """Create classifications explanation page - compact layout"""

    # Count SKUs by classification
    class_counts = df['final_classification'].value_counts()

    # Create compact cards in rows
    cards = []

    for class_name, info in CLASSIFICATION_INFO.items():
        count = class_counts.get(class_name, 0)
        percentage = (count / len(df) * 100) if len(df) > 0 else 0

        card = dbc.Card([
            dbc.CardBody([
                html.Div([
                    # Left side - classification name and count
                    html.Div([
                        html.Div([
                            html.Span("■", style={'color': info['color'], 'fontSize': '16px', 'marginRight': '6px'}),
                            html.Strong(class_name, style={'fontSize': '13px'})
                        ]),
                        html.Div([
                            html.Span(f"{count}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                            html.Span(f" ({percentage:.1f}%)", style={'fontSize': '11px', 'color': '#7f8c8d'})
                        ])
                    ], style={'flex': '0 0 120px'}),
                    # Right side - description and criteria
                    html.Div([
                        html.Div(info['description'], style={'fontSize': '11px', 'marginBottom': '4px'}),
                        html.Div(info['criteria'], style={'fontSize': '10px', 'color': '#6c757d', 'fontFamily': 'monospace', 'backgroundColor': '#f8f9fa', 'padding': '4px 6px', 'borderRadius': '3px'})
                    ], style={'flex': '1', 'marginLeft': '12px'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'padding': '10px'})
        ], className='mb-2', style={'borderLeft': f'4px solid {info["color"]}'})

        cards.append(card)

    return html.Div([
        # Header - compact
        html.H4("🎯 Classification System", className='mb-2'),

        # Dual-track explanation - compact inline
        dbc.Alert([
            html.Div([
                html.Strong("Dual-Track System: "),
                html.Span("Absolute Track (platform-wide) + Category Track (within category). Final = highest tier achieved.", style={'fontSize': '12px'})
            ])
        ], color='info', className='mb-3 py-2', style={'fontSize': '12px'}),

        # All classification cards stacked vertically
        html.Div(cards)
    ])

# Modal callbacks
@app.callback(
    [Output("details-modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-body", "children")],
    [Input("results-table", "active_cell"),
     Input("close-modal", "n_clicks")],
    [State("details-modal", "is_open"),
     State("results-table", "derived_virtual_data"),
     State("results-table", "derived_virtual_selected_rows")],
    prevent_initial_call=True
)
def toggle_modal(active_cell, close_clicks, is_open, filtered_data, selected_rows):
    """Toggle modal and populate with row details"""
    global df_store

    ctx = callback_context
    if not ctx.triggered:
        return False, "", ""

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Close button clicked
    if triggered_id == "close-modal":
        return False, "", ""

    # Cell clicked
    if triggered_id == "results-table" and active_cell:
        if df_store is None:
            return False, "", ""

        # Get the row index from active cell (this is the index in the filtered/sorted table)
        row_idx = active_cell['row']

        # Use derived_virtual_data which contains the currently displayed (filtered/sorted) data
        if filtered_data is None or row_idx >= len(filtered_data):
            return False, "", ""

        # Get the variant ID from the filtered/displayed row
        variant_id = filtered_data[row_idx].get('variantid')

        if variant_id is None:
            return False, "", ""

        # Find the row in the original dataframe using variant_id
        row_data = df_store[df_store['variantid'] == variant_id].iloc[0]

        # Create modal title
        product_name = row_data.get('productname', 'Unknown Product')
        title = html.Div([
            html.H4(f"{product_name}", className='mb-2'),
            html.P(f"Variant ID: {variant_id}", className='text-muted mb-0')
        ])

        # Create modal body with all metrics
        body = create_detailed_metrics_view(row_data)

        return True, title, body

    return is_open, "", ""

# Classification filter callback
@app.callback(
    Output('results-table', 'data'),
    [Input('classification-filter', 'value')],
    [State('full-table-data', 'data')],
    prevent_initial_call=True
)
def filter_by_classification(selected_classifications, full_data):
    """Filter table data based on selected classifications"""
    if not selected_classifications or len(selected_classifications) == 0:
        return full_data

    filtered_data = [row for row in full_data if row.get('final_classification') in selected_classifications]
    return filtered_data

def create_classification_criteria_section(row_data, df):
    """Create a section showing why the SKU was classified the way it is"""

    # Get the classification
    final_class = row_data.get('final_classification', 'STANDARD')
    abs_class = row_data.get('absolute_classification', 'STANDARD')
    cat_class = row_data.get('category_classification', 'STANDARD')
    category = row_data.get('groupcategory', 'Unknown')

    # Get category-specific data for thresholds
    category_df = df[df['groupcategory'] == category]

    if len(category_df) < 5:
        return html.Div()  # Skip if category too small

    # Calculate category thresholds
    v_p75 = category_df['last3_months_sales_velocity'].quantile(0.75)
    v_p90 = category_df['last3_months_sales_velocity'].quantile(0.90)
    c_p75 = category_df['last3_months_conversion_days'].quantile(0.75)
    b_p75 = category_df['last3_months_net_delivered_buyers'].quantile(0.75)
    a_p50 = category_df['last3_months_active_days'].quantile(0.50)

    # Get actual values
    velocity = row_data.get('last3_months_sales_velocity', 0)
    conversion = row_data.get('last3_months_conversion_days', 0)
    buyers = row_data.get('last3_months_net_delivered_buyers', 0)
    active_days = row_data.get('last3_months_active_days', 0)
    cat_score = row_data.get('category_core_score', 0)
    abs_score = row_data.get('absolute_core_score', 0)

    # Title row explaining dual-track system
    intro_text = html.Div([
        html.P([
            html.Strong("Dual-Track System: "),
            "Products are evaluated on both ",
            html.Span("Absolute (platform-wide)", style={'color': '#2c3e50', 'fontWeight': 'bold'}),
            " and ",
            html.Span("Category-specific", style={'color': '#e67e22', 'fontWeight': 'bold'}),
            " tracks. The highest tier achieved in either track determines the final classification."
        ], className='mb-3', style={'fontSize': '13px', 'lineHeight': '1.6'})
    ])

    # Check Platinum Absolute (Active Days removed from criteria)
    platinum_abs_criteria = [
        ('Absolute Score ≥ 75', abs_score >= 75, abs_score, 75),
        ('Velocity ≥ 1.0', velocity >= 1.0, velocity, 1.0),
        ('Conversion ≥ 0.4', conversion >= 0.4, conversion, 0.4),
        ('Buyers ≥ 25', buyers >= 25, buyers, 25),
    ]

    gold_abs_criteria = [
        ('Absolute Score ≥ 60', abs_score >= 60, abs_score, 60),
        ('Velocity ≥ 0.5', velocity >= 0.5, velocity, 0.5),
        ('Conversion ≥ 0.25', conversion >= 0.25, conversion, 0.25),
        ('Buyers ≥ 15', buyers >= 15, buyers, 15),
    ]

    silver_abs_criteria = [
        ('Absolute Score ≥ 45', abs_score >= 45, abs_score, 45),
        ('Velocity ≥ 0.2', velocity >= 0.2, velocity, 0.2),
        ('Conversion ≥ 0.15', conversion >= 0.15, conversion, 0.15),
        ('Buyers ≥ 5', buyers >= 5, buyers, 5),
    ]

    # Determine which absolute criteria to show
    if abs_class == 'PLATINUM_ABSOLUTE':
        abs_criteria = platinum_abs_criteria
        criteria_title = "✅ PLATINUM_ABSOLUTE achieved (all criteria met)"
        title_color = '#F39C12'
    elif abs_class == 'GOLD_ABSOLUTE':
        abs_criteria = gold_abs_criteria
        criteria_title = "✅ GOLD_ABSOLUTE achieved (all criteria met)"
        title_color = '#F39C12'
    elif abs_class == 'SILVER_ABSOLUTE':
        abs_criteria = silver_abs_criteria
        criteria_title = "✅ SILVER_ABSOLUTE achieved (all criteria met)"
        title_color = '#BDC3C7'
    else:
        # Show what's needed for GOLD_ABSOLUTE
        abs_criteria = gold_abs_criteria
        criteria_title = "❌ Not qualified for GOLD_ABSOLUTE (requires ALL criteria)"
        title_color = '#95A5A6'

    # Create Absolute Track Card
    abs_track_content = [
        html.H6("🌍 Absolute Track (Platform-wide)", className='mb-2', style={'color': '#2c3e50'}),
        html.P(criteria_title, style={'fontWeight': 'bold', 'color': title_color, 'fontSize': '13px'}),
        create_criteria_table(abs_criteria)
    ]

    # Check Platinum Category (Active Days removed from criteria)
    platinum_cat_criteria = [
        ('Category Score ≥ 80', cat_score >= 80, cat_score, 80),
        (f'Velocity ≥ {v_p90:.2f} (P90)', velocity >= v_p90, velocity, v_p90),
        (f'Conversion ≥ {c_p75:.2f} (P75)', conversion >= c_p75, conversion, c_p75),
        (f'Buyers ≥ {b_p75:.0f} (P75)', buyers >= b_p75, buyers, b_p75),
    ]

    gold_cat_criteria = [
        ('Category Score ≥ 65', cat_score >= 65, cat_score, 65),
        (f'Velocity ≥ {v_p75:.2f} (P75)', velocity >= v_p75, velocity, v_p75),
        (f'Conversion ≥ {c_p75 * 0.7:.2f} (P75×0.7)', conversion >= c_p75 * 0.7, conversion, c_p75 * 0.7),
        (f'Buyers ≥ {b_p75 * 0.7:.0f} (P75×0.7)', buyers >= b_p75 * 0.7, buyers, b_p75 * 0.7),
    ]

    silver_cat_criteria = [
        ('Category Score ≥ 50', cat_score >= 50, cat_score, 50),
        (f'Velocity ≥ {v_p75 * 0.5:.2f} (P75×0.5)', velocity >= v_p75 * 0.5, velocity, v_p75 * 0.5),
        (f'Conversion ≥ {c_p75 * 0.5:.2f} (P75×0.5)', conversion >= c_p75 * 0.5, conversion, c_p75 * 0.5),
        (f'Buyers ≥ {b_p75 * 0.5:.0f} (P75×0.5)', buyers >= b_p75 * 0.5, buyers, b_p75 * 0.5),
    ]

    # Determine which category criteria to show
    if cat_class == 'PLATINUM_CATEGORY':
        cat_criteria = platinum_cat_criteria
        cat_criteria_title = "✅ PLATINUM_CATEGORY achieved (all criteria met)"
        cat_title_color = '#F39C12'
    elif cat_class == 'GOLD_CATEGORY':
        cat_criteria = gold_cat_criteria
        cat_criteria_title = "✅ GOLD_CATEGORY achieved (all criteria met)"
        cat_title_color = '#F39C12'
    elif cat_class == 'SILVER_CATEGORY':
        cat_criteria = silver_cat_criteria
        cat_criteria_title = "✅ SILVER_CATEGORY achieved (all criteria met)"
        cat_title_color = '#BDC3C7'
    else:
        # Show what's needed for GOLD_CATEGORY
        cat_criteria = gold_cat_criteria
        cat_criteria_title = "❌ Not qualified for GOLD_CATEGORY (requires ALL criteria)"
        cat_title_color = '#95A5A6'

    # Create Category Track Card
    cat_track_content = [
        html.H6(f"📂 Category Track ({category})", className='mb-2', style={'color': '#e67e22'}),
        html.P(cat_criteria_title, style={'fontWeight': 'bold', 'color': cat_title_color, 'fontSize': '13px'}),
        create_criteria_table(cat_criteria)
    ]

    # Final classification explanation
    final_summary = html.Div([
        html.Hr(),
        html.P([
            html.Strong("Final Classification: "),
            dbc.Badge(final_class, color='light', style={
                'backgroundColor': CLASSIFICATION_INFO.get(final_class, {}).get('color', '#95A5A6'),
                'color': '#000' if 'STANDARD' not in final_class else '#fff',
                'fontSize': '13px',
                'padding': '6px 10px',
                'marginLeft': '8px'
            })
        ], className='mb-2'),
        html.P([
            "Determined by the highest tier achieved: ",
            html.Span(f"Absolute = {abs_class}", style={'color': '#2c3e50', 'fontWeight': 'bold', 'marginRight': '10px'}),
            html.Span(f"Category = {cat_class}", style={'color': '#e67e22', 'fontWeight': 'bold'})
        ], style={'fontSize': '12px', 'color': '#7f8c8d'})
    ], className='mt-3')

    return dbc.Card([
        dbc.CardHeader(html.H5("🎯 Classification Criteria Breakdown", className='mb-0')),
        dbc.CardBody([
            intro_text,
            dbc.Row([
                dbc.Col(html.Div(abs_track_content, style={'padding': '10px'}), width=6),
                dbc.Col(html.Div(cat_track_content, style={'padding': '10px'}), width=6)
            ]),
            final_summary
        ])
    ], className='mb-3')

def create_criteria_table(criteria):
    """Helper function to create a criteria table with checkmarks"""
    rows = []
    for criterion, met, actual_value, threshold in criteria:
        # Format values with NaN handling
        if pd.isna(actual_value):
            actual_str = "N/A"
        elif isinstance(actual_value, float):
            if actual_value < 10:
                actual_str = f"{actual_value:.2f}"
            else:
                actual_str = f"{actual_value:.0f}"
        else:
            actual_str = str(actual_value)

        if pd.isna(threshold):
            threshold_str = "N/A"
        elif isinstance(threshold, float):
            if threshold < 10:
                threshold_str = f"{threshold:.2f}"
            else:
                threshold_str = f"{threshold:.0f}"
        else:
            threshold_str = str(threshold)

        rows.append(html.Tr([
            html.Td(
                html.Span("✅", style={'fontSize': '16px', 'marginRight': '8px'}) if met else html.Span("❌", style={'fontSize': '16px', 'marginRight': '8px'}),
                style={'width': '30px', 'textAlign': 'center'}
            ),
            html.Td(criterion, style={'width': '45%'}),
            html.Td(
                f"Actual: {actual_str}",
                style={
                    'fontWeight': 'bold',
                    'color': '#27ae60' if met else '#e74c3c',
                    'width': '30%'
                }
            ),
            html.Td(
                f"Need: {threshold_str}",
                style={'color': '#7f8c8d', 'fontSize': '12px', 'width': '25%'}
            )
        ], style={'backgroundColor': '#f8f9fa' if met else '#fff'}))

    return html.Table(rows, className='table table-sm table-bordered', style={'fontSize': '13px', 'marginBottom': '10px'})

def create_detailed_metrics_view(row_data):
    """Create detailed view of all metrics for a SKU"""
    global df_store

    sections = []

    # Row 1: Product Image, Product Information, and Category Hierarchy (side by side)
    # Extract product image URL
    product_image_html = row_data.get('productimage', '')
    image_url = None
    if pd.notna(product_image_html) and 'src=' in str(product_image_html):
        import re
        match = re.search(r'src="([^"]+)"', str(product_image_html))
        if match:
            image_url = match.group(1)

    # Product image card
    image_card = dbc.Card([
        dbc.CardHeader(html.H5("📷 Product Image", className='mb-0')),
        dbc.CardBody([
            html.Img(
                src=image_url if image_url else 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="150"%3E%3Crect width="150" height="150" fill="%23ddd"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14" fill="%23999"%3ENo Image%3C/text%3E%3C/svg%3E',
                style={'width': '100%', 'maxWidth': '200px', 'height': 'auto', 'display': 'block', 'margin': '0 auto'}
            )
        ], style={'textAlign': 'center'})
    ])

    # Product Information
    product_info = []
    info_fields = [
        ('Variant ID', 'variantid'),
        ('Product Name', 'productname'),
        ('Brand', 'brandname'),
        ('Darkstore', 'darkstorename'),
        ('Product ID', 'productid'),
        ('Lifecycle', 'lifecycle'),
        ('Color', 'color'),
        ('Transfer Price', 'producttransferprice'),
    ]

    for label, field in info_fields:
        if field in row_data and pd.notna(row_data[field]):
            product_info.append(html.Tr([
                html.Td(html.Strong(label), style={'width': '40%'}),
                html.Td(str(row_data[field]))
            ]))

    product_info_card = dbc.Card([
        dbc.CardHeader(html.H5("📦 Product Information", className='mb-0')),
        dbc.CardBody([
            html.Table(product_info, className='table table-sm table-hover')
        ])
    ])

    # Category Hierarchy
    category_info = []
    category_fields = [
        ('Super Category', 'supercategory'),
        ('Main Category', 'maincategory'),
        ('Group Category', 'groupcategory'),
        ('Sub Category', 'subcategory'),
    ]

    for label, field in category_fields:
        if field in row_data and pd.notna(row_data[field]):
            category_info.append(html.Tr([
                html.Td(html.Strong(label), style={'width': '40%'}),
                html.Td(str(row_data[field]))
            ]))

    category_card = dbc.Card([
        dbc.CardHeader(html.H5("📁 Category Hierarchy", className='mb-0')),
        dbc.CardBody([
            html.Table(category_info, className='table table-sm table-hover')
        ])
    ])

    # Add side-by-side row
    sections.append(dbc.Row([
        dbc.Col(image_card, width=3),
        dbc.Col(product_info_card, width=5),
        dbc.Col(category_card, width=4)
    ], className='mb-3'))

    # Section 3: CORE Scores & Classification
    classification_class = row_data.get('final_classification', 'STANDARD')
    classification_color = CLASSIFICATION_INFO.get(classification_class, {}).get('color', '#95A5A6')

    scores_info = [
        html.Tr([
            html.Td(html.Strong("Classification"), style={'width': '40%'}),
            html.Td([
                dbc.Badge(classification_class, color='light', style={
                    'backgroundColor': classification_color,
                    'color': '#000' if 'STANDARD' not in classification_class else '#fff',
                    'fontSize': '14px',
                    'padding': '8px 12px'
                })
            ])
        ]),
        html.Tr([
            html.Td(html.Strong("Absolute Core Score")),
            html.Td(
                f"{row_data.get('absolute_core_score', 0):.2f} / 100" if pd.notna(row_data.get('absolute_core_score')) else "N/A (Insufficient Data)",
                style={'fontWeight': 'bold', 'color': '#2c3e50'}
            )
        ]),
        html.Tr([
            html.Td(html.Strong("Category Core Score")),
            html.Td(
                f"{row_data.get('category_core_score', 0):.2f} / 100" if pd.notna(row_data.get('category_core_score')) else "N/A (Insufficient Data)",
                style={'fontWeight': 'bold', 'color': '#e67e22'}
            )
        ]),
    ]

    sections.append(dbc.Card([
        dbc.CardHeader(html.H5("🏆 Classification & Core Scores", className='mb-0')),
        dbc.CardBody([
            html.Table(scores_info, className='table table-sm table-hover')
        ])
    ], className='mb-3'))

    # Section 3.5: Classification Criteria Breakdown
    if df_store is not None:
        sections.append(create_classification_criteria_section(row_data, df_store))

    # Section 4: Component Scores (availability removed, repeatability added)
    component_scores = [
        ('🚀 Velocity Score', 'abs_velocity_score', SCORE_COLORS['velocity']),
        ('✅ Conversion Score', 'abs_conversion_score', SCORE_COLORS['conversion']),
        ('🔄 Repeatability Score', 'abs_repeatability_score', SCORE_COLORS['repeatability']),
        ('👥 Penetration Score', 'abs_penetration_score', SCORE_COLORS['penetration']),
        ('📈 Momentum Score', 'abs_momentum_score', SCORE_COLORS['momentum']),
    ]

    component_rows = []
    for label, field, color in component_scores:
        score = row_data.get(field, 0)
        if pd.isna(score):
            component_rows.append(html.Tr([
                html.Td(html.Strong(label), style={'width': '40%'}),
                html.Td(html.Span("N/A (Insufficient Data)", style={'color': '#7f8c8d', 'fontStyle': 'italic'}))
            ]))
        else:
            component_rows.append(html.Tr([
                html.Td(html.Strong(label), style={'width': '40%'}),
                html.Td([
                    html.Div([
                        html.Span(f"{score:.2f}", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dbc.Progress(value=score, max=100, color='success' if score >= 75 else 'warning' if score >= 50 else 'danger', style={'height': '20px', 'width': '60%'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ])
            ]))

    sections.append(dbc.Card([
        dbc.CardHeader(html.H5("📊 Component Scores", className='mb-0')),
        dbc.CardBody([
            html.Table(component_rows, className='table table-sm')
        ])
    ], className='mb-3'))

    # Section 5 & 6: Performance Metrics - Side by Side
    recent_metrics = [
        ('Lots Sold', 'last3_months_lots_sold'),
        ('Active Days', 'last3_months_active_days'),
        ('Sales Velocity (lots/day)', 'last3_months_sales_velocity'),
        ('Days with Sales', 'last3_months_lots_sold_days'),
        ('Conversion Rate', 'last3_months_conversion_days'),
        ('Net Delivered Buyers', 'last3_months_net_delivered_buyers'),
        ('Net Delivered Lots', 'last3_months_net_delivered_lots'),
    ]

    recent_rows = []
    for label, field in recent_metrics:
        if field in row_data:
            value = row_data[field]
            if pd.notna(value):
                formatted_value = f"{value:.2f}" if isinstance(value, (int, float)) and field not in ['last3_months_lots_sold', 'last3_months_active_days', 'last3_months_lots_sold_days', 'last3_months_net_delivered_buyers', 'last3_months_net_delivered_lots'] else f"{int(value)}" if isinstance(value, (int, float)) else str(value)
                recent_rows.append(html.Tr([
                    html.Td(html.Strong(label), style={'width': '50%'}),
                    html.Td(formatted_value)
                ]))

    recent_card = dbc.Card([
        dbc.CardHeader(html.H5("📈 Last 3 Months Performance", className='mb-0')),
        dbc.CardBody([
            html.Table(recent_rows, className='table table-sm table-hover')
        ])
    ])

    lifetime_metrics = [
        ('Lots Sold', 'lifetime_lots_sold'),
        ('Active Days', 'lifetime_active_days'),
        ('Sales Velocity (lots/day)', 'lifetime_sales_velocity'),
        ('Days with Sales', 'lifetime_lots_sold_days'),
        ('Conversion Rate', 'lifetime_conversion_days'),
        ('Net Delivered Buyers', 'lifetime_net_delivered_buyers'),
        ('Net Delivered Lots', 'lifetime_net_delivered_lots'),
        ('Repeat Buyers', 'lifetime_repeat_buyers'),
        ('Repeat Buyer Ratio', 'repeat_buyer_ratio'),
    ]

    lifetime_rows = []
    for label, field in lifetime_metrics:
        if field in row_data:
            value = row_data[field]
            if pd.notna(value):
                # Fields that should be formatted as integers
                integer_fields = ['lifetime_lots_sold', 'lifetime_active_days', 'lifetime_lots_sold_days',
                                 'lifetime_net_delivered_buyers', 'lifetime_net_delivered_lots', 'lifetime_repeat_buyers']
                if field in integer_fields:
                    formatted_value = f"{int(value)}"
                elif isinstance(value, (int, float)):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                lifetime_rows.append(html.Tr([
                    html.Td(html.Strong(label), style={'width': '50%'}),
                    html.Td(formatted_value)
                ]))

    lifetime_card = dbc.Card([
        dbc.CardHeader(html.H5("📊 Lifetime Performance", className='mb-0')),
        dbc.CardBody([
            html.Table(lifetime_rows, className='table table-sm table-hover')
        ])
    ])

    # Add side-by-side performance metrics
    sections.append(dbc.Row([
        dbc.Col(recent_card, width=6),
        dbc.Col(lifetime_card, width=6)
    ], className='mb-3'))

    return html.Div(sections)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SKU CORE ANALYSIS DASHBOARD")
    print("="*60)
    print("\nDashboard starting at: http://localhost:8050")
    print("\nFeatures:")
    print("  • CSV Upload")
    print("  • Interactive Data Table with Filtering/Sorting")
    print("  • Scoring Definitions & Methodology")
    print("  • Classification System Details")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, port=8050)