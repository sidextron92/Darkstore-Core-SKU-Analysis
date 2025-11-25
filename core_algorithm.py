"""
Dual-Track CORE System for SKU Classification
Implements both Absolute (Platform-wide) and Category-specific benchmarking
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class DualTrackCORESystem:
    """
    Dual-Track CORE System for SKU Classification
    - Track 1: ABSOLUTE CORE (Platform-wide benchmarks)
    - Track 2: CATEGORY CORE (Category-specific benchmarks)
    """

    def __init__(self):
        # Availability removed - it creates perverse incentives:
        # - Penalizes high-demand SKUs with frequent stockouts
        # - Rewards overstocked items with low demand
        # Weights redistributed to demand-focused metrics
        # Repeatability is highest - strong indicator of CORE products (buyer loyalty)
        self.absolute_weights = {
            'velocity': 0.25,      # primary demand signal
            'repeatability': 0.30, # buyer loyalty/repeat purchases (highest weight)
            'conversion': 0.20,    # sales consistency
            'penetration': 0.15,   # customer reach
            'momentum': 0.10       # growth trend
        }

        self.category_weights = {
            'velocity': 0.25,      # primary demand signal within category
            'repeatability': 0.30, # buyer loyalty/repeat purchases (highest weight)
            'conversion': 0.20,    # sales consistency
            'penetration': 0.15,   # customer reach
            'momentum': 0.10       # growth trend
        }

    def calculate_absolute_core(self, df, darkstore_column='darkstoreid'):
        """Calculate ABSOLUTE CORE scores using darkstore-specific benchmarks"""
        df = df.copy()

        # Initialize columns
        percentile_columns = ['abs_velocity_recent_pct', 'abs_velocity_lifetime_pct',
                             'abs_conversion_recent_pct', 'abs_conversion_lifetime_pct',
                             'abs_buyers_recent_pct', 'abs_buyers_lifetime_pct',
                             'abs_repeat_buyers_pct', 'abs_repeat_ratio_pct']
        for col in percentile_columns:
            df[col] = 0.0

        # Calculate buyers per active day (needed for percentiles)
        df['buyers_per_day_recent'] = df['last3_months_net_delivered_buyers'] / df['last3_months_active_days'].replace(0, np.nan)
        df['buyers_per_day_lifetime'] = df['lifetime_net_delivered_buyers'] / df['lifetime_active_days'].replace(0, np.nan)

        # Calculate repeat buyer ratio if column exists
        if 'lifetime_repeat_buyers' in df.columns:
            df['repeat_buyer_ratio'] = df['lifetime_repeat_buyers'] / df['lifetime_net_delivered_buyers'].replace(0, np.nan)
            df['repeat_buyer_ratio'] = df['repeat_buyer_ratio'].fillna(0)
        else:
            df['repeat_buyer_ratio'] = 0

        # Process each darkstore separately to calculate percentile ranks
        if darkstore_column in df.columns:
            for darkstore in df[darkstore_column].unique():
                ds_mask = df[darkstore_column] == darkstore
                ds_df = df[ds_mask].copy()

                # Darkstore-specific percentile ranks
                ds_df['abs_velocity_recent_pct'] = ds_df['last3_months_sales_velocity'].rank(pct=True) * 100
                ds_df['abs_velocity_lifetime_pct'] = ds_df['lifetime_sales_velocity'].rank(pct=True) * 100
                ds_df['abs_conversion_recent_pct'] = ds_df['last3_months_conversion_days'].rank(pct=True) * 100
                ds_df['abs_conversion_lifetime_pct'] = ds_df['lifetime_conversion_days'].rank(pct=True) * 100
                ds_df['abs_buyers_recent_pct'] = ds_df['buyers_per_day_recent'].rank(pct=True) * 100
                ds_df['abs_buyers_lifetime_pct'] = ds_df['buyers_per_day_lifetime'].rank(pct=True) * 100

                # Repeatability percentiles per darkstore
                if 'lifetime_repeat_buyers' in ds_df.columns:
                    ds_df['abs_repeat_buyers_pct'] = ds_df['lifetime_repeat_buyers'].rank(pct=True) * 100
                    ds_df['abs_repeat_ratio_pct'] = ds_df['repeat_buyer_ratio'].rank(pct=True) * 100

                # Update main dataframe with darkstore-specific percentiles
                df.loc[ds_mask, percentile_columns] = ds_df[percentile_columns]
        else:
            # Fallback: calculate globally if no darkstore column
            df['abs_velocity_recent_pct'] = df['last3_months_sales_velocity'].rank(pct=True) * 100
            df['abs_velocity_lifetime_pct'] = df['lifetime_sales_velocity'].rank(pct=True) * 100
            df['abs_conversion_recent_pct'] = df['last3_months_conversion_days'].rank(pct=True) * 100
            df['abs_conversion_lifetime_pct'] = df['lifetime_conversion_days'].rank(pct=True) * 100
            df['abs_buyers_recent_pct'] = df['buyers_per_day_recent'].rank(pct=True) * 100
            df['abs_buyers_lifetime_pct'] = df['buyers_per_day_lifetime'].rank(pct=True) * 100
            if 'lifetime_repeat_buyers' in df.columns:
                df['abs_repeat_buyers_pct'] = df['lifetime_repeat_buyers'].rank(pct=True) * 100
                df['abs_repeat_ratio_pct'] = df['repeat_buyer_ratio'].rank(pct=True) * 100

        # Component scores
        velocity_stability = np.minimum(1.0, df['last3_months_sales_velocity'] / (df['lifetime_sales_velocity'] + 0.001))
        df['abs_velocity_score'] = (
            0.6 * df['abs_velocity_recent_pct'] +
            0.3 * df['abs_velocity_lifetime_pct'] +
            0.1 * np.minimum(100, velocity_stability * 100)
        )

        # Conversion score
        recent_conversion = df['last3_months_conversion_days'] * 100
        lifetime_conversion = df['lifetime_conversion_days'] * 100
        conversion_trend = recent_conversion / (lifetime_conversion + 0.001)
        trend_bonus = np.minimum(20, np.maximum(0, (conversion_trend - 1) * 50))
        df['abs_conversion_score'] = np.minimum(100,
            0.7 * recent_conversion + 0.3 * lifetime_conversion + trend_bonus
        )

        # Availability score removed - creates perverse incentives
        # High availability often indicates overstocking, not importance
        # Low availability with high velocity indicates understocked winners
        df['abs_availability_score'] = 0  # Kept for backward compatibility but not used

        # Penetration score
        buyer_growth_rate = df['buyers_per_day_recent'] / (df['buyers_per_day_lifetime'] + 0.001)
        growth_bonus = np.minimum(20, np.maximum(0, (buyer_growth_rate - 1) * 40))
        df['abs_penetration_score'] = np.minimum(100,
            0.6 * df['abs_buyers_recent_pct'] +
            0.4 * df['abs_buyers_lifetime_pct'] +
            growth_bonus
        )

        # Momentum score
        velocity_momentum = df['last3_months_sales_velocity'] / (df['lifetime_sales_velocity'] + 0.001)
        conversion_momentum = df['last3_months_conversion_days'] / (df['lifetime_conversion_days'] + 0.001)
        buyer_momentum = df['buyers_per_day_recent'] / (df['buyers_per_day_lifetime'] + 0.001)
        df['abs_momentum_score'] = np.minimum(100, (
            0.5 * velocity_momentum +
            0.3 * conversion_momentum +
            0.2 * buyer_momentum
        ) * 50)

        # Repeatability score - based on lifetime_repeat_buyers
        # Measures buyer loyalty: higher repeat buyers = more essential product
        if 'lifetime_repeat_buyers' in df.columns:
            # Repeatability score combines absolute count and ratio
            # Higher weight on ratio (loyalty proportion) over absolute count
            df['abs_repeatability_score'] = np.minimum(100, (
                0.4 * df['abs_repeat_buyers_pct'] +  # Absolute repeat buyer count
                0.6 * df['abs_repeat_ratio_pct']     # Repeat buyer ratio
            ))
        else:
            df['abs_repeatability_score'] = 0

        # Final ABSOLUTE score (availability removed, repeatability added)
        df['absolute_core_score'] = (
            self.absolute_weights['velocity'] * df['abs_velocity_score'] +
            self.absolute_weights['conversion'] * df['abs_conversion_score'] +
            self.absolute_weights['penetration'] * df['abs_penetration_score'] +
            self.absolute_weights['momentum'] * df['abs_momentum_score'] +
            self.absolute_weights['repeatability'] * df['abs_repeatability_score']
        )

        # Classify ABSOLUTE
        df['absolute_classification'] = df.apply(self._classify_absolute, axis=1)

        return df

    def calculate_category_core(self, df, category_column='groupcategory', darkstore_column='darkstoreid'):
        """Calculate CATEGORY CORE scores using darkstore+category-specific benchmarks"""
        df = df.copy()

        # Initialize columns
        score_columns = ['cat_velocity_score', 'cat_conversion_score', 'cat_availability_score',
                        'cat_penetration_score', 'cat_momentum_score', 'cat_repeatability_score', 'category_core_score']
        for col in score_columns:
            df[col] = 0.0

        df['category_classification'] = 'STANDARD'

        # Process each darkstore separately, then each category within darkstore
        if darkstore_column in df.columns:
            for darkstore in df[darkstore_column].unique():
                ds_mask = df[darkstore_column] == darkstore
                ds_df = df[ds_mask].copy()

                # Process each category within this darkstore
                for category in ds_df[category_column].unique():
                    cat_mask = ds_df[category_column] == category
                    combined_mask = ds_mask & (df[category_column] == category)
                    self._process_category(df, combined_mask, category)
        else:
            # Fallback: process categories globally if no darkstore column
            for category in df[category_column].unique():
                cat_mask = df[category_column] == category
                self._process_category(df, cat_mask, category)

        return df

    def _process_category(self, df, mask, category):
        """Helper method to process a single category (within a darkstore)"""
        cat_df = df[mask].copy()

        if len(cat_df) < 5:  # Skip categories with too few SKUs
            return

        # Category-specific percentile ranks
        cat_df['cat_velocity_recent_pct'] = cat_df['last3_months_sales_velocity'].rank(pct=True) * 100
        cat_df['cat_velocity_lifetime_pct'] = cat_df['lifetime_sales_velocity'].rank(pct=True) * 100
        cat_df['cat_conversion_recent_pct'] = cat_df['last3_months_conversion_days'].rank(pct=True) * 100
        cat_df['cat_conversion_lifetime_pct'] = cat_df['lifetime_conversion_days'].rank(pct=True) * 100

        # Buyers per active day within category
        cat_df['buyers_per_day_recent'] = cat_df['last3_months_net_delivered_buyers'] / \
                                          cat_df['last3_months_active_days'].replace(0, np.nan)
        cat_df['buyers_per_day_lifetime'] = cat_df['lifetime_net_delivered_buyers'] / \
                                            cat_df['lifetime_active_days'].replace(0, np.nan)
        cat_df['cat_buyers_recent_pct'] = cat_df['buyers_per_day_recent'].rank(pct=True) * 100
        cat_df['cat_buyers_lifetime_pct'] = cat_df['buyers_per_day_lifetime'].rank(pct=True) * 100

        # Component scores for category
        velocity_stability = np.minimum(1.0, cat_df['last3_months_sales_velocity'] /
                                      (cat_df['lifetime_sales_velocity'] + 0.001))
        cat_df['cat_velocity_score'] = (
            0.6 * cat_df['cat_velocity_recent_pct'] +
            0.3 * cat_df['cat_velocity_lifetime_pct'] +
            0.1 * np.minimum(100, velocity_stability * 100)
        )

        # Conversion score
        recent_conversion = cat_df['last3_months_conversion_days'] * 100
        lifetime_conversion = cat_df['lifetime_conversion_days'] * 100
        conversion_trend = recent_conversion / (lifetime_conversion + 0.001)
        trend_bonus = np.minimum(20, np.maximum(0, (conversion_trend - 1) * 50))
        cat_df['cat_conversion_score'] = np.minimum(100,
            0.7 * recent_conversion + 0.3 * lifetime_conversion + trend_bonus
        )

        # Availability score removed - creates perverse incentives
        cat_df['cat_availability_score'] = 0  # Kept for backward compatibility but not used

        # Penetration score within category
        buyer_growth_rate = cat_df['buyers_per_day_recent'] / (cat_df['buyers_per_day_lifetime'] + 0.001)
        growth_bonus = np.minimum(20, np.maximum(0, (buyer_growth_rate - 1) * 40))
        cat_df['cat_penetration_score'] = np.minimum(100,
            0.6 * cat_df['cat_buyers_recent_pct'] +
            0.4 * cat_df['cat_buyers_lifetime_pct'] +
            growth_bonus
        )

        # Momentum score
        velocity_momentum = cat_df['last3_months_sales_velocity'] / (cat_df['lifetime_sales_velocity'] + 0.001)
        conversion_momentum = cat_df['last3_months_conversion_days'] / (cat_df['lifetime_conversion_days'] + 0.001)
        buyer_momentum = cat_df['buyers_per_day_recent'] / (cat_df['buyers_per_day_lifetime'] + 0.001)
        cat_df['cat_momentum_score'] = np.minimum(100, (
            0.5 * velocity_momentum +
            0.3 * conversion_momentum +
            0.2 * buyer_momentum
        ) * 50)

        # Repeatability score within category
        if 'lifetime_repeat_buyers' in cat_df.columns:
            # Calculate repeat buyer ratio within category
            cat_df['repeat_buyer_ratio'] = cat_df['lifetime_repeat_buyers'] / cat_df['lifetime_net_delivered_buyers'].replace(0, np.nan)
            cat_df['repeat_buyer_ratio'] = cat_df['repeat_buyer_ratio'].fillna(0)

            # Category-specific percentile ranks
            cat_df['cat_repeat_buyers_pct'] = cat_df['lifetime_repeat_buyers'].rank(pct=True) * 100
            cat_df['cat_repeat_ratio_pct'] = cat_df['repeat_buyer_ratio'].rank(pct=True) * 100

            # Repeatability score within category
            cat_df['cat_repeatability_score'] = np.minimum(100, (
                0.4 * cat_df['cat_repeat_buyers_pct'] +
                0.6 * cat_df['cat_repeat_ratio_pct']
            ))
        else:
            cat_df['cat_repeatability_score'] = 0

        # Final CATEGORY score (availability removed, repeatability added)
        cat_df['category_core_score'] = (
            self.category_weights['velocity'] * cat_df['cat_velocity_score'] +
            self.category_weights['conversion'] * cat_df['cat_conversion_score'] +
            self.category_weights['penetration'] * cat_df['cat_penetration_score'] +
            self.category_weights['momentum'] * cat_df['cat_momentum_score'] +
            self.category_weights['repeatability'] * cat_df['cat_repeatability_score']
        )

        # Get category-specific thresholds
        velocity_p75 = cat_df['last3_months_sales_velocity'].quantile(0.75)
        velocity_p90 = cat_df['last3_months_sales_velocity'].quantile(0.90)

        conversion_p75 = cat_df['last3_months_conversion_days'].quantile(0.75)

        buyers_p75 = cat_df['last3_months_net_delivered_buyers'].quantile(0.75)

        active_p50 = cat_df['last3_months_active_days'].quantile(0.50)

        # Classify within category
        for idx, row in cat_df.iterrows():
            classification = self._classify_category(row, velocity_p75, velocity_p90,
                                                    conversion_p75, buyers_p75, active_p50)
            cat_df.loc[idx, 'category_classification'] = classification

        # Update main dataframe
        score_columns = ['cat_velocity_score', 'cat_conversion_score', 'cat_availability_score',
                        'cat_penetration_score', 'cat_momentum_score', 'cat_repeatability_score', 'category_core_score']
        df.loc[mask, score_columns] = cat_df[score_columns]
        df.loc[mask, 'category_classification'] = cat_df['category_classification']

    def _classify_absolute(self, row):
        """Classify SKU based on absolute performance (availability removed from criteria)"""
        score = row['absolute_core_score']

        # Availability requirement removed - high-velocity SKUs with stockouts
        # should still qualify as CORE (they're understocked winners, not low-demand)
        if (score >= 75 and
            row['last3_months_sales_velocity'] >= 1.0 and
            row['last3_months_conversion_days'] >= 0.4 and
            row['last3_months_net_delivered_buyers'] >= 25):
            return 'PLATINUM_ABSOLUTE'
        elif (score >= 60 and
              row['last3_months_sales_velocity'] >= 0.5 and
              row['last3_months_conversion_days'] >= 0.25 and
              row['last3_months_net_delivered_buyers'] >= 15):
            return 'GOLD_ABSOLUTE'
        elif (score >= 45 and
              row['last3_months_sales_velocity'] >= 0.2 and
              row['last3_months_conversion_days'] >= 0.15 and
              row['last3_months_net_delivered_buyers'] >= 5):
            return 'SILVER_ABSOLUTE'
        else:
            return 'STANDARD'

    def _classify_category(self, row, v_p75, v_p90, c_p75, b_p75, a_p50):
        """Classify SKU based on category-specific performance (availability removed)"""
        score = row['category_core_score']

        # Availability requirement removed from all tier criteria
        if (score >= 80 and
            row['last3_months_sales_velocity'] >= v_p90 and
            row['last3_months_conversion_days'] >= c_p75 and
            row['last3_months_net_delivered_buyers'] >= b_p75):
            return 'PLATINUM_CATEGORY'
        elif (score >= 65 and
              row['last3_months_sales_velocity'] >= v_p75 and
              row['last3_months_conversion_days'] >= c_p75 * 0.7 and
              row['last3_months_net_delivered_buyers'] >= b_p75 * 0.7):
            return 'GOLD_CATEGORY'
        elif (score >= 50 and
              row['last3_months_sales_velocity'] >= v_p75 * 0.5 and
              row['last3_months_conversion_days'] >= c_p75 * 0.5 and
              row['last3_months_net_delivered_buyers'] >= b_p75 * 0.5):
            return 'SILVER_CATEGORY'
        else:
            return 'STANDARD'

    def create_final_classification(self, df):
        """Create final dual-track classification and recommendations"""
        df = df.copy()

        # Create unified label combining both tracks
        def get_final_label(row):
            abs_class = row['absolute_classification']
            cat_class = row['category_classification']

            # Highest priority wins - Revised hierarchy
            # Priority: Platinum tiers > Gold tiers > Silver tiers
            # Within each tier level: Absolute slightly > Category
            if 'PLATINUM_ABSOLUTE' in abs_class:
                return 'PLATINUM_ABSOLUTE'
            elif 'PLATINUM_CATEGORY' in cat_class:
                return 'PLATINUM_CATEGORY'
            elif 'GOLD_ABSOLUTE' in abs_class:
                return 'GOLD_ABSOLUTE'
            elif 'GOLD_CATEGORY' in cat_class:
                return 'GOLD_CATEGORY'
            elif 'SILVER_ABSOLUTE' in abs_class:
                return 'SILVER_ABSOLUTE'
            elif 'SILVER_CATEGORY' in cat_class:
                return 'SILVER_CATEGORY'
            else:
                return 'STANDARD'

        df['final_classification'] = df.apply(get_final_label, axis=1)

        # Inventory recommendations
        def get_inventory_strategy(row):
            final_class = row['final_classification']

            if 'PLATINUM_ABSOLUTE' in final_class:
                return {
                    'safety_stock_days': 20,
                    'reorder_point_days': 10,
                    'max_stockout_hours': 0,
                    'priority': 'CRITICAL',
                    'investment_allocation': 'MAXIMUM'
                }
            elif 'GOLD_ABSOLUTE' in final_class:
                return {
                    'safety_stock_days': 15,
                    'reorder_point_days': 7,
                    'max_stockout_hours': 24,
                    'priority': 'HIGH',
                    'investment_allocation': 'HIGH'
                }
            elif 'PLATINUM_CATEGORY' in final_class:
                return {
                    'safety_stock_days': 12,
                    'reorder_point_days': 6,
                    'max_stockout_hours': 48,
                    'priority': 'HIGH',
                    'investment_allocation': 'MODERATE-HIGH'
                }
            elif 'SILVER_ABSOLUTE' in final_class:
                return {
                    'safety_stock_days': 10,
                    'reorder_point_days': 5,
                    'max_stockout_hours': 72,
                    'priority': 'MEDIUM',
                    'investment_allocation': 'MODERATE'
                }
            elif 'GOLD_CATEGORY' in final_class:
                return {
                    'safety_stock_days': 8,
                    'reorder_point_days': 4,
                    'max_stockout_hours': 96,
                    'priority': 'MEDIUM',
                    'investment_allocation': 'MODERATE'
                }
            elif 'SILVER_CATEGORY' in final_class:
                return {
                    'safety_stock_days': 5,
                    'reorder_point_days': 3,
                    'max_stockout_hours': 120,
                    'priority': 'LOW-MEDIUM',
                    'investment_allocation': 'LOW-MODERATE'
                }
            else:
                return {
                    'safety_stock_days': 3,
                    'reorder_point_days': 2,
                    'max_stockout_hours': 168,
                    'priority': 'LOW',
                    'investment_allocation': 'MINIMAL'
                }

        # Apply inventory strategy
        inventory_strategies = df.apply(get_inventory_strategy, axis=1, result_type='expand')
        for col in inventory_strategies.columns:
            df[f'strategy_{col}'] = inventory_strategies[col]

        return df

    def generate_summary_report(self, df):
        """Generate summary statistics for the dual-track system"""
        report = {}

        # Overall statistics
        report['total_skus'] = len(df)
        report['categories'] = df['groupcategory'].nunique() if 'groupcategory' in df.columns else 0

        # Absolute track statistics
        abs_classifications = df['absolute_classification'].value_counts()
        report['absolute_track'] = {
            'platinum': abs_classifications.get('PLATINUM_ABSOLUTE', 0),
            'gold': abs_classifications.get('GOLD_ABSOLUTE', 0),
            'silver': abs_classifications.get('SILVER_ABSOLUTE', 0),
            'standard': abs_classifications.get('STANDARD', 0)
        }

        # Category track statistics
        cat_classifications = df['category_classification'].value_counts()
        report['category_track'] = {
            'platinum': cat_classifications.get('PLATINUM_CATEGORY', 0),
            'gold': cat_classifications.get('GOLD_CATEGORY', 0),
            'silver': cat_classifications.get('SILVER_CATEGORY', 0),
            'standard': cat_classifications.get('STANDARD', 0)
        }

        # Final classification statistics
        final_classifications = df['final_classification'].value_counts()
        report['final_classification'] = final_classifications.to_dict()

        # Category representation
        if 'groupcategory' in df.columns:
            category_core = df[df['final_classification'] != 'STANDARD'].groupby('groupcategory').size()
            report['category_representation'] = category_core.to_dict()
        else:
            report['category_representation'] = {}

        # Performance metrics
        core_skus = df[df['final_classification'] != 'STANDARD']
        report['performance'] = {
            'total_core_skus': len(core_skus),
            'core_velocity_sum': core_skus['last3_months_sales_velocity'].sum() if len(core_skus) > 0 else 0,
            'avg_core_conversion': core_skus['last3_months_conversion_days'].mean() if len(core_skus) > 0 else 0,
            'avg_core_buyers': core_skus['last3_months_net_delivered_buyers'].mean() if len(core_skus) > 0 else 0
        }

        return report