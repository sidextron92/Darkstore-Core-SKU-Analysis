# SKU Core Analysis Dashboard

A streamlined dashboard for analyzing SKU performance and identifying core products to prevent inventory stockouts.

## 🚀 Quick Start

```bash
./run_simple_dashboard.sh
```

Then open: **http://localhost:8050**

## 📁 Project Structure

```
core_sku_analysis/
├── simple_dashboard.py          # Main dashboard application
├── core_algorithm.py            # Dual-track CORE scoring algorithm
├── run_simple_dashboard.sh      # Startup script
├── requirements.txt             # Python dependencies
├── SIMPLE_GUIDE.md             # Detailed usage guide
├── venv/                        # Virtual environment (auto-created)
└── CORE SKU Analysis - Sheet1.csv  # Your data file
```

## ✨ Features

### 1. CSV Upload
- Drag and drop CSV files
- Automatic analysis on upload
- Supports standard SKU data format

### 2. Interactive Data Table
- ✅ **Filter** any column
- ✅ **Sort** by any metric (multi-column support)
- ✅ **Color-coded** scores and classifications
- ✅ **Export** to CSV
- ✅ **Pagination** for large datasets

### 3. Scoring Definitions
- Complete methodology documentation
- Shows all calculation formulas
- Lists columns used for each score
- Interpretation guides

### 4. Classification System
- 7-tier classification (Platinum → Standard)
- Dual-track approach (Absolute + Category)
- Visual tier distribution
- Criteria for each tier

## 📊 Required CSV Columns

Your CSV should include these columns:

**Identifiers:**
- `variantid` - SKU variant identifier
- `darkstoreid`, `darkstorename` - Store identifiers
- `productid`, `productname` - Product identifiers
- `brandid`, `brandname` - Brand identifiers

**Performance Metrics (Required):**
- `lifetime_lots_sold` - Total units sold (all time)
- `lifetime_active_days` - Days available (all time)
- `lifetime_sales_velocity` - Sales per day (all time)
- `last3_months_lots_sold` - Units sold (last 3 months)
- `last3_months_active_days` - Days available (last 3 months)
- `last3_months_sales_velocity` - Sales per day (last 3 months)
- `lifetime_lots_sold_days` - Days with sales (all time)
- `last3_months_lots_sold_days` - Days with sales (last 3 months)
- `lifetime_conversion_days` - Conversion rate (all time)
- `last3_months_conversion_days` - Conversion rate (last 3 months)
- `lifetime_net_delivered_buyers` - Unique buyers (all time)
- `last3_months_net_delivered_buyers` - Unique buyers (last 3 months)
- `lifetime_net_delivered_lots` - Delivered lots (all time)
- `last3_months_net_delivered_lots` - Delivered lots (last 3 months)

**Category Information:**
- `groupcategory` - Main category grouping
- `subcategory` - Sub-category
- `maincategory` - Main category
- `supercategory` - Super category

**Additional Fields (Optional):**
- `lifecycle` - Product lifecycle stage
- `producttransferprice` - Transfer price
- `color` - Product color
- `productimage` - Image URL

## 🎯 Output Scores

The dashboard calculates:

1. **Velocity Score (30%)** - Sales speed when available
2. **Conversion Score (25%)** - Sales consistency
3. **Availability Score (20%)** - Stock availability
4. **Penetration Score (15%)** - Customer reach
5. **Momentum Score (10%)** - Growth trend

**Final Outputs:**
- Absolute Core Score (0-100)
- Category Core Score (0-100)
- Final Classification (PLATINUM → STANDARD)

## 🏆 Classification Tiers

| Tier | Description | Criteria |
|------|-------------|----------|
| PLATINUM_ABSOLUTE | Top 5% platform-wide | Score ≥75, Velocity ≥1.0 |
| GOLD_ABSOLUTE | Top 15% platform-wide | Score ≥60, Velocity ≥0.5 |
| PLATINUM_CATEGORY | Top 5% in category | Category Score ≥80 |
| SILVER_ABSOLUTE | Top 30% platform-wide | Score ≥45, Velocity ≥0.2 |
| GOLD_CATEGORY | Top 15% in category | Category Score ≥65 |
| SILVER_CATEGORY | Top 30% in category | Category Score ≥50 |
| STANDARD | Below CORE thresholds | - |

## 🔧 Manual Setup (if needed)

If the script doesn't work:

```bash
# Activate virtual environment
source venv/bin/activate

# Run dashboard
python3 simple_dashboard.py
```

## 📖 Detailed Guide

See `SIMPLE_GUIDE.md` for:
- Complete feature walkthrough
- Filtering and sorting examples
- Score interpretation
- Best practices

## 🛠 Troubleshooting

**Dashboard won't start?**
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 simple_dashboard.py
```

**Port already in use?**
- Edit `simple_dashboard.py` line 519
- Change `port=8050` to `port=8051`

**CSV upload fails?**
- Check CSV has required columns
- Verify file is UTF-8 encoded
- Maximum file size: ~50MB

## 💡 Tips

1. **Find top performers:**
   - Filter: `final_classification` contains "PLATINUM"
   - Sort by: `absolute_core_score` (descending)

2. **Compare categories:**
   - Filter by category
   - Compare average scores

3. **Export filtered results:**
   - Apply filters in table
   - Click "Export to CSV"

## 🎨 Color Coding

**In Data Table:**
- 🟡 Yellow = Classification column
- 🔵 Blue = Absolute Score
- 🟠 Orange = Category Score
- 🟢 Green = High scores (≥75)
- 🟨 Yellow = Medium scores (50-75)

## 📞 Support

For detailed usage instructions, see: `SIMPLE_GUIDE.md`

## 🔄 To Restart

Press `Ctrl+C` to stop, then:
```bash
./run_simple_dashboard.sh
```

---

**Built for analyzing SKU performance and preventing stockouts through data-driven inventory management.**