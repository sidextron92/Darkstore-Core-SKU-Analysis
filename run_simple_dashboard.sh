#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run the simplified dashboard
echo "Starting Simple SKU Core Analysis Dashboard..."
echo "Opening at: http://localhost:8050"
echo ""
echo "Features:"
echo "  • Upload CSV and run analysis"
echo "  • Interactive data table with filters and sorting"
echo "  • Scoring definitions and methodology"
echo "  • Classification system details"
echo ""
python simple_dashboard.py