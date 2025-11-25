# Column Reference Guide

## Your CSV File Structure

This dashboard is configured to work with your exact column structure.

### 📊 Complete Column List (34 columns)

#### 1. Identifiers (9 columns)
| Column | Description | Usage in Dashboard |
|--------|-------------|-------------------|
| `variantid` | SKU variant ID | Primary identifier, shown in data table |
| `darkstoreid` | Dark store ID | Store identification |
| `darkstorename` | Dark store name | Shown in data table for filtering |
| `dswarehouseid` | Warehouse ID | Internal reference |
| `productid` | Product ID | Product identification |
| `productname` | Product name | Shown in data table |
| `brandid` | Brand ID | Brand identification |
| `brandname` | Brand name | Shown in data table for filtering |
| `productimage` | Image URL | Product image reference |

#### 2. Performance Metrics - Lifetime (7 columns)
| Column | Description | Used in Score Calculation |
|--------|-------------|--------------------------|
| `lifetime_lots_sold` | Total units sold (all time) | ✅ Velocity, Momentum |
| `lifetime_active_days` | Days available (all time) | ✅ Velocity, Availability, Penetration |
| `lifetime_sales_velocity` | Sales per day (all time) | ✅ Velocity (30% weight) |
| `lifetime_lots_sold_days` | Days with at least 1 sale | ✅ Conversion (25% weight) |
| `lifetime_conversion_days` | Conversion rate (all time) | ✅ Conversion (25% weight) |
| `lifetime_net_delivered_buyers` | Unique buyers (all time) | ✅ Penetration (15% weight) |
| `lifetime_net_delivered_lots` | Delivered lots (all time) | Used for validation |

#### 3. Performance Metrics - Last 3 Months (7 columns)
| Column | Description | Used in Score Calculation |
|--------|-------------|--------------------------|
| `last3_months_lots_sold` | Units sold (last 3 months) | ✅ Velocity, Momentum |
| `last3_months_active_days` | Days available (last 3 months) | ✅ Velocity, Availability, Penetration |
| `last3_months_sales_velocity` | Sales per day (last 3 months) | ✅ Velocity (30% weight) - Primary |
| `last3_months_lots_sold_days` | Days with at least 1 sale | ✅ Conversion (25% weight) |
| `last3_months_conversion_days` | Conversion rate (3 months) | ✅ Conversion (25% weight) - Primary |
| `last3_months_net_delivered_buyers` | Unique buyers (3 months) | ✅ Penetration (15% weight) - Primary |
| `last3_months_net_delivered_lots` | Delivered lots (3 months) | Used for validation |

#### 4. Category Hierarchy (8 columns)
| Column | Description | Used in Dashboard |
|--------|-------------|-------------------|
| `supercategoryid` | Super category ID | Category grouping |
| `supercategory` | Super category name | Analysis grouping |
| `maincategoryid` | Main category ID | Category grouping |
| `maincategory` | Main category name | Analysis grouping |
| `groupcategoryid` | Group category ID | Primary for category-specific scoring |
| `groupcategory` | Group category name | ✅ **Primary category for classification** |
| `subcategoryid` | Sub-category ID | Sub-grouping |
| `subcategory` | Sub-category name | Shown in data table |

#### 5. Additional Attributes (3 columns)
| Column | Description | Usage |
|--------|-------------|-------|
| `lifecycle` | Product lifecycle stage | Shown in data table, filtering |
| `producttransferprice` | Transfer price | Cost analysis (optional) |
| `color` | Product color | Product attribute |

---

## 🎯 Key Columns for CORE Scoring

### Most Important (Used in Final Score)
1. **`last3_months_sales_velocity`** - 30% weight in Absolute Score
2. **`last3_months_conversion_days`** - 25% weight in Absolute Score
3. **`last3_months_active_days`** - 20% weight in Availability Score
4. **`last3_months_net_delivered_buyers`** - 15% weight in Penetration Score
5. **`groupcategory`** - Used for Category-specific scoring

### Secondary (Used for Comparison & Momentum)
- All `lifetime_*` columns
- Category hierarchy columns
- Identifiers (product, brand, store)

---

## 📋 What You'll See in Dashboard

### Data Table Columns (Displayed)
- Variant ID
- Darkstore Name
- Product Name
- Brand Name
- Category (groupcategory)
- Sub Category
- **Classification** (PLATINUM_ABSOLUTE, GOLD_ABSOLUTE, etc.)
- **Absolute Score** (0-100)
- **Category Score** (0-100)
- **5 Component Scores** (Velocity, Conversion, Availability, Penetration, Momentum)
- Recent metrics (velocity, conversion, buyers, active days)
- Lifetime velocity
- Lifecycle

### Filterable Fields
- Any text field (product name, brand, category, etc.)
- Any numeric field (scores, metrics)
- Classification tiers

---

## ✅ Data Validation

The dashboard automatically:
- Checks for required columns
- Calculates derived metrics if needed
- Handles missing values
- Validates numeric ranges

**Required columns for analysis:**
- ✅ `lifetime_lots_sold`
- ✅ `lifetime_active_days`
- ✅ `last3_months_lots_sold`
- ✅ `last3_months_active_days`
- ✅ `last3_months_net_delivered_buyers`
- ✅ `lifetime_net_delivered_buyers`

**Auto-calculated if missing:**
- `lifetime_sales_velocity` = `lifetime_lots_sold` / `lifetime_active_days`
- `last3_months_sales_velocity` = `last3_months_lots_sold` / `last3_months_active_days`
- `lifetime_conversion_days` = `lifetime_lots_sold_days` / `lifetime_active_days`
- `last3_months_conversion_days` = `last3_months_lots_sold_days` / `last3_months_active_days`

---

## 🔍 Example CSV Row

```csv
variantid,darkstoreid,darkstorename,dswarehouseid,lifetime_lots_sold,lifetime_active_days,lifetime_sales_velocity,last3_months_lots_sold,last3_months_active_days,last3_months_sales_velocity,lifetime_lots_sold_days,last3_months_lots_sold_days,lifetime_conversion_days,last3_months_conversion_days,lifetime_net_delivered_buyers,last3_months_net_delivered_buyers,lifetime_net_delivered_lots,last3_months_net_delivered_lots,productimage,lifecycle,productid,productname,brandid,brandname,producttransferprice,color,subcategoryid,subcategory,groupcategoryid,groupcategory,maincategoryid,maincategory,supercategoryid,supercategory
V12345,DS001,Store Downtown,WH001,250,180,1.39,85,90,0.94,120,65,0.67,0.72,45,28,240,82,img_url,Active,P789,Premium Cotton T-Shirt,B456,BrandX,299,Blue,SC12,T-Shirts,GC34,Apparel,MC56,Fashion,SP78,Clothing
```

---

## 💡 Tips for Best Results

1. **Ensure data quality:**
   - No negative values in quantity fields
   - Active days should be > 0
   - All required columns present

2. **Category naming:**
   - Use consistent naming in `groupcategory`
   - This field is crucial for category-specific scoring

3. **Time periods:**
   - Lifetime = All-time data
   - Last 3 months = Most recent 90-109 days

4. **File size:**
   - Recommended: < 50MB
   - Rows: Tested with 200-10,000 SKUs
   - Processing time: ~5-30 seconds

---

## 🚀 Ready to Upload?

Your CSV file with these 34 columns is ready to be analyzed!

1. Start dashboard: `./run_simple_dashboard.sh`
2. Open: http://localhost:8050
3. Upload your CSV file
4. Click "Run Analysis"
5. Explore results in data table!