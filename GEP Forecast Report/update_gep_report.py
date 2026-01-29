#!/usr/bin/env python3
"""
GEP Forecast Report - Snowflake Data Fetcher
Fetches GEP performance data from Snowflake using Okta SSO authentication.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import snowflake.connector
from typing import Optional, Dict, Any


# Configuration
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT', 'GUSTO-WAREHOUSE')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', 'jason.chao@gusto.com')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'ANALYTICS_WH')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'ANALYTICS')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA', 'GROWTH')
SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE', 'PUBLIC')


def get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """
    Establish connection to Snowflake using Okta SSO (externalbrowser authentication).
    This will open a browser window for Okta authentication.
    """
    print("Connecting to Snowflake via Okta SSO...")
    print("A browser window will open for authentication.")
    
    conn = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        authenticator='externalbrowser',
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE
    )
    
    print("Successfully connected to Snowflake!")
    return conn


def fetch_gep_performance_data(conn: snowflake.connector.SnowflakeConnection) -> pd.DataFrame:
    """
    Fetch GEP (Growth Efficiency & Performance) metrics from Snowflake.
    """
    # Get date range for the report (last 7 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    query = f"""
    SELECT 
        DATE_TRUNC('day', metric_date) as report_date,
        metric_name,
        metric_value,
        metric_unit,
        channel,
        segment,
        forecast_value,
        variance_pct
    FROM {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.GEP_DAILY_METRICS
    WHERE metric_date >= '{start_date}'
      AND metric_date <= '{end_date}'
    ORDER BY metric_date DESC, metric_name
    """
    
    print(f"Fetching GEP data from {start_date} to {end_date}...")
    
    try:
        df = pd.read_sql(query, conn)
        print(f"Retrieved {len(df)} rows of GEP data.")
        return df
    except Exception as e:
        print(f"Error fetching GEP data: {e}")
        # Return empty DataFrame with expected columns if query fails
        return pd.DataFrame(columns=[
            'report_date', 'metric_name', 'metric_value', 
            'metric_unit', 'channel', 'segment',
            'forecast_value', 'variance_pct'
        ])


def fetch_arr_summary(conn: snowflake.connector.SnowflakeConnection) -> Dict[str, Any]:
    """
    Fetch ARR (Annual Recurring Revenue) summary metrics.
    """
    query = """
    SELECT 
        current_arr,
        arr_growth_mtd,
        arr_growth_ytd,
        arr_forecast_eom,
        arr_vs_forecast_pct
    FROM ANALYTICS.GROWTH.ARR_SUMMARY
    WHERE report_date = CURRENT_DATE()
    LIMIT 1
    """
    
    print("Fetching ARR summary...")
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            return {
                'current_arr': row[0],
                'arr_growth_mtd': row[1],
                'arr_growth_ytd': row[2],
                'arr_forecast_eom': row[3],
                'arr_vs_forecast_pct': row[4]
            }
    except Exception as e:
        print(f"Error fetching ARR summary: {e}")
    
    return {}


def fetch_channel_performance(conn: snowflake.connector.SnowflakeConnection) -> pd.DataFrame:
    """
    Fetch performance breakdown by channel.
    """
    query = """
    SELECT 
        channel_name,
        leads_count,
        conversion_rate,
        arr_contribution,
        cac,
        ltv_cac_ratio,
        performance_vs_target_pct
    FROM ANALYTICS.GROWTH.CHANNEL_PERFORMANCE_DAILY
    WHERE report_date = CURRENT_DATE()
    ORDER BY arr_contribution DESC
    """
    
    print("Fetching channel performance data...")
    
    try:
        df = pd.read_sql(query, conn)
        print(f"Retrieved performance data for {len(df)} channels.")
        return df
    except Exception as e:
        print(f"Error fetching channel performance: {e}")
        return pd.DataFrame()


def get_report_data() -> Dict[str, Any]:
    """
    Main function to fetch all GEP report data from Snowflake.
    Returns a dictionary containing all report components.
    """
    conn = None
    try:
        conn = get_snowflake_connection()
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'gep_metrics': fetch_gep_performance_data(conn),
            'arr_summary': fetch_arr_summary(conn),
            'channel_performance': fetch_channel_performance(conn)
        }
        
        return report_data
        
    except Exception as e:
        print(f"Error generating report: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("Snowflake connection closed.")


if __name__ == "__main__":
    # Test the connection and data fetching
    print("=" * 50)
    print("GEP Forecast Report - Data Fetcher Test")
    print("=" * 50)
    
    data = get_report_data()
    
    print("\n" + "=" * 50)
    print("Report Data Summary:")
    print("=" * 50)
    print(f"Timestamp: {data['timestamp']}")
    print(f"GEP Metrics rows: {len(data['gep_metrics'])}")
    print(f"ARR Summary: {data['arr_summary']}")
    print(f"Channel Performance rows: {len(data['channel_performance'])}")
