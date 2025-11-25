# Simple Dashboard - Quick Guide

## ✅ Your Dashboard is Ready!

Access it now at: **http://localhost:8050**

## 🎯 What You'll See

### 1. **CSV Upload Page**
- Drag and drop your CSV file
- Or click to browse and select
- Click "Run Analysis" button
- Analysis runs automatically

### 2. **Data Table Tab** 📊
**Complete interactive table with:**
- ✅ **📋 Actions Column** - Click any row to view detailed metrics in a modal popup
- ✅ All SKU data with scores and classifications
- ✅ **Filter by any column** - Click filter icon in column header
- ✅ **Sort any column** - Click column header to sort (multi-sort supported)
- ✅ **Color-coded highlights:**
  - 🟡 Yellow: Classification column
  - 🔵 Blue: Absolute Score
  - 🟠 Orange: Category Score
  - 🟢 Green: High scores (≥75)
  - 🟡 Yellow: Medium scores (50-75)
  - 🟦 Gold: Platinum classifications
  - 🟨 Light gold: Gold classifications

- ✅ **Export to CSV** button at bottom
- ✅ **20 rows per page** with pagination

**🔍 Detailed View Modal:**
Click on ANY cell in a row to open a popup modal showing:
- 📦 **Product Information** - Full product details, lifecycle, color, price
- 📁 **Category Hierarchy** - Super → Main → Group → Sub category
- 🏆 **Classification & Scores** - Badge with color-coding + core scores
- 📊 **Component Scores** - All 5 scores with visual progress bars
- 📈 **Last 3 Months Performance** - All recent metrics in detail
- 📊 **Lifetime Performance** - All historical metrics in detail

**Columns shown:**
- Variant ID, Product Name, Brand, Category
- **🏆 Classification** (PLATINUM_ABSOLUTE, GOLD_ABSOLUTE, etc.)
- **⭐ Absolute Score** (0-100)
- **📊 Category Score** (0-100)
- **🚀 Velocity Score** (how fast it sells)
- **✅ Conversion Score** (how consistently it sells)
- **📦 Availability Score** (how often in stock)
- **👥 Penetration Score** (customer reach)
- **📈 Momentum Score** (growth trend)
- Recent Velocity, Conversion, Buyers, Active Days

### 3. **Scoring Definitions Tab** 📖
**For each score component, you'll see:**
- ✅ **Description**: What it measures
- ✅ **Calculation Logic**: How it's computed
- ✅ **Formula**: Exact calculation formula
- ✅ **Columns Used**: All input columns (highlighted as badges)
- ✅ **Interpretation**: What high/low scores mean
- ✅ **Weight**: Contribution to overall CORE score

**5 Components Explained:**
1. **🚀 Velocity Score (30%)** - Measures sales speed
   - Uses: last3_months_sales_velocity, lifetime_sales_velocity, lots_sold, active_days

2. **✅ Conversion Score (25%)** - Measures sales consistency
   - Uses: last3_months_conversion_days, lifetime_conversion_days, lots_sold_days

3. **📦 Availability Score (20%)** - Measures stock availability
   - Uses: last3_months_active_days, lifetime_active_days

4. **👥 Penetration Score (15%)** - Measures customer reach
   - Uses: last3_months_net_delivered_buyers, lifetime_net_delivered_buyers

5. **📈 Momentum Score (10%)** - Measures growth trend
   - Uses: Recent vs lifetime performance comparison

### 4. **Classifications Tab** 🎯
**Shows all classification tiers with:**
- ✅ **Color-coded card** for each tier
- ✅ **SKU count and percentage** in your dataset
- ✅ **Description** of what the tier represents
- ✅ **Specific criteria** to achieve that tier

**7 Classification Tiers:**
1. **PLATINUM_ABSOLUTE** (Gold color) - Top 5% platform-wide
2. **GOLD_ABSOLUTE** (Gold yellow) - Top 15% platform-wide
3. **PLATINUM_CATEGORY** (Silver) - Top 5% in category
4. **SILVER_ABSOLUTE** (Light silver) - Top 30% platform-wide
5. **GOLD_CATEGORY** (Light gold) - Top 15% in category
6. **SILVER_CATEGORY** (Gray) - Top 30% in category
7. **STANDARD** (Dark gray) - Below CORE thresholds

## 📤 How to Use

### Step 1: Upload Your CSV
```bash
# Your CSV should have these columns:
- lifetime_lots_sold
- lifetime_active_days
- last3_months_lots_sold
- last3_months_active_days
- last3_months_net_delivered_buyers
- lifetime_net_delivered_buyers
(+ optional: lots_sold_days, product names, categories)
```

### Step 2: Click "Run Analysis"
- Processing takes 5-30 seconds depending on file size
- Summary cards appear showing: Total SKUs, CORE SKUs, Average Scores

### Step 3: Explore the Tabs
- **Data Table**: Filter and sort your results
- **Definitions**: Understand the scoring methodology
- **Classifications**: See the tier system

### Step 4: Export Results
- Click "Export to CSV" in the Data Table tab
- Downloads complete analysis with all scores

## 🔍 Key Features

### **Advanced Filtering**
Click the filter icon in any column header:
- Text columns: Type to search (e.g., "slipper")
- Number columns: Use operators:
  - `> 75` (greater than 75)
  - `< 50` (less than 50)
  - `>= 60` (greater than or equal to 60)
  - `= PLATINUM_ABSOLUTE` (exact match)

### **Multi-Column Sorting**
- Click column header to sort ascending
- Click again to sort descending
- Hold Shift + Click to sort by multiple columns

### **Score Highlighting**
- Green cells = High performance (≥75)
- Yellow cells = Medium performance (50-75)
- Gold highlights = Platinum/Gold classifications

## 🎨 Understanding the Colors

**In Data Table:**
- 🟡 Yellow background = Classification column
- 🔵 Blue background = Absolute Core Score
- 🟠 Orange background = Category Core Score
- 🟢 Green = Score ≥75 (Excellent)
- 🟡 Yellow = Score 50-75 (Good)
- ⚪ White = Score <50 (Needs improvement)

**In Classifications:**
- Each tier has its unique color matching the classification system

## 🚀 Quick Tips

1. **Find your top performers:**
   - Filter `final_classification` contains "PLATINUM"
   - Sort by `absolute_core_score` descending

2. **Find underperforming CORE SKUs:**
   - Filter `final_classification` not contains "STANDARD"
   - Filter `abs_velocity_score < 60`

3. **Compare categories:**
   - Filter by `groupcategory = "Innerwear"`
   - Compare average scores with other categories

4. **Export filtered data:**
   - Apply filters
   - Click "Export to CSV"
   - Only filtered rows export!

## 🔄 To Restart Dashboard

```bash
./run_simple_dashboard.sh
```

Or manually:
```bash
source venv/bin/activate
python simple_dashboard.py
```

## ❓ Troubleshooting

**Dashboard not loading?**
- Check http://localhost:8050 in browser
- Restart: Press Ctrl+C, then run script again

**CSV upload fails?**
- Check file has required columns
- Ensure CSV is properly formatted
- File size limit: 50MB

**Scores showing 0 or NaN?**
- Missing required columns in your CSV
- Check Definitions tab for required columns

## 📊 Example Workflow

1. Upload "CORE SKU Analysis - Sheet1.csv"
2. Click "Run Analysis"
3. Go to Data Table tab
4. Filter: `abs_velocity_score > 70`
5. Sort by: `last3_months_net_delivered_buyers` (descending)
6. Review top velocity + high buyer reach SKUs
7. Export filtered results

Perfect for identifying your platform's star performers! 🌟