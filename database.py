# database.py
import pandas as pd
import os
import json
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import streamlit as st
from datetime import datetime, timedelta
from config import get_service_account_info, get_project_id

# ===== BIGQUERY CONNECTION =====
@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client using service account from secrets or file"""
    try:
        # Lấy service account info từ config
        service_account_info = get_service_account_info()
        
        if service_account_info:
            # Trên Cloud: Tạo credentials từ dictionary
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            project_id = get_project_id()
            client = bigquery.Client(credentials=credentials, project=project_id)
            return client
        else:
            # Local: Thử dùng default credentials
            project_id = get_project_id()
            client = bigquery.Client(project=project_id)
            return client
            
    except Exception as e:
        st.error(f"BigQuery connection failed: {e}")
        return None

# ===== PHONE NORMALIZATION =====
def normalize_phone(phone):
    """
    Normalize phone number to international format with +
    Examples:
    0123456789 -> +84123456789
    84123456789 -> +84123456789
    +84123456789 -> +84123456789
    123456789 -> +123456789
    """
    if pd.isna(phone) or phone == '' or str(phone).strip() == '':
        return None
    
    # Convert to string and remove all spaces and special characters except '+'
    phone_str = str(phone).strip()
    
    # Keep only digits and plus sign
    cleaned = ''.join(ch for ch in phone_str if ch.isdigit() or ch == '+')
    
    # If no digits, return None
    if not any(ch.isdigit() for ch in cleaned):
        return None
    
    # Extract digits
    digits = ''.join(filter(str.isdigit, cleaned))
    
    # Check if already has +
    if cleaned.startswith('+'):
        # Already has +, just return with + and digits
        return f"+{digits}"
    else:
        # No +, add it
        return f"+{digits}"

# ===== COLUMN DETECTION FUNCTIONS =====
def detect_phone_column(actual_columns):
    """Auto-detect phone column from available columns"""
    phone_variants = ['phone_number', 'phone', 'Phone', 'PhoneNumber', 'phonenumber', 
                      'phone_no', 'contact_phone', 'mobile', 'mobile_number', 'contact_no',
                      'telephone', 'tel', 'cell', 'cellphone']
    for col in phone_variants:
        if col in actual_columns:
            return col
    return None

def detect_date_column(actual_columns, date_type='sent'):
    """
    Auto-detect date column from available columns
    date_type: 'sent' for sent_date, 'source' for source date
    """
    if date_type == 'sent':
        date_variants = ['sent_date', 'date_sent', 'sent_at', 'sent_on', 'date_sent',
                        'sent_time', 'sent_datetime', 'email_sent_date']
    else:  # source date
        date_variants = ['date', 'created_date', 'created_at', 'submitted_at', 
                        'submitted_date', 'record_date', 'event_date', 'registration_date',
                        'signup_date', 'entry_date', 'date_created', 'date_entered']
    
    for col in date_variants:
        if col in actual_columns:
            return col
    return None

# ===== TABLE UTILITIES =====
@st.cache_data(ttl=3600)
def get_table_columns(_client, table_name):
    """Get list of columns in a BigQuery table with caching"""
    if not _client:
        return []
    try:
        table = _client.get_table(table_name)
        return [schema.name for schema in table.schema]
    except Exception as e:
        return []

def table_exists(client, table_name):
    """Check if a table exists in BigQuery"""
    if not client:
        return False
    try:
        client.get_table(table_name)
        return True
    except NotFound:
        return False
    except Exception:
        return False

# ===== SENT DATA FUNCTIONS =====
def get_sent_phones(client, sent_table, phone_column=None, date_column=None):
    """
    Get sent phones from sent table - auto-detect columns if not specified
    Returns dict of normalized_phone -> sent_date
    """
    if not client or not sent_table:
        return {}
    
    try:
        # Check if table exists
        if not table_exists(client, sent_table):
            return {}
        
        # Get actual columns
        actual_columns = get_table_columns(client, sent_table)
        
        # Auto-detect phone column if not specified
        if not phone_column:
            phone_column = detect_phone_column(actual_columns)
            if not phone_column:
                return {}
        
        # Check if phone column exists
        if phone_column not in actual_columns:
            return {}
        
        # Auto-detect date column if not specified
        if not date_column:
            date_column = detect_date_column(actual_columns, date_type='sent')
        
        # Check if date column exists
        if date_column and date_column not in actual_columns:
            date_column = None
        
        # Build query
        if date_column:
            query = f"""
                SELECT DISTINCT 
                    {phone_column} as phone,
                    {date_column} as sent_date
                FROM `{sent_table}`
                WHERE {phone_column} IS NOT NULL
                AND {phone_column} != ''
                AND TRIM({phone_column}) != ''
            """
        else:
            query = f"""
                SELECT DISTINCT 
                    {phone_column} as phone
                FROM `{sent_table}`
                WHERE {phone_column} IS NOT NULL
                AND {phone_column} != ''
                AND TRIM({phone_column}) != ''
            """
        
        query_job = client.query(query)
        results = query_job.result()
        
        sent_data = {}
        for row in results:
            if row.phone:
                normalized_phone = normalize_phone(row.phone)
                if normalized_phone:
                    if date_column and hasattr(row, 'sent_date') and row.sent_date:
                        sent_data[normalized_phone] = row.sent_date
                    else:
                        sent_data[normalized_phone] = None
        
        return sent_data
        
    except Exception as e:
        return {}

def get_sent_phones_from_campaigns(campaigns):
    """Get sent phones from sent tables in campaigns with auto-detection"""
    client = init_bigquery_client()
    if not client:
        return {}
    
    all_sent_data = {}
    
    for campaign in campaigns:
        sent_table = campaign.get('sent_table')
        if sent_table:
            # Get column config from campaign (may be None for auto-detect)
            phone_column = campaign.get('sent_phone_column')
            date_column = campaign.get('sent_date_column')
            
            sent_data = get_sent_phones(client, sent_table, phone_column, date_column)
            if sent_data:
                all_sent_data.update(sent_data)
    
    return all_sent_data

# ===== EXCLUDED PHONES FUNCTIONS =====
def get_excluded_phones_from_campaigns(previous_campaigns):
    """Get all excluded phones from previous campaigns with auto-detection"""
    client = init_bigquery_client()
    if not client:
        return set()
    
    all_phones = set()
    
    for prev in previous_campaigns:
        if prev.get('exclude', True):
            try:
                table = prev['table']
                phone_col = prev.get('phone_column')
                
                if not table_exists(client, table):
                    continue
                
                actual_columns = get_table_columns(client, table)
                
                # Auto-detect phone column if not specified
                if not phone_col:
                    phone_col = detect_phone_column(actual_columns)
                    if not phone_col:
                        continue
                
                if phone_col not in actual_columns:
                    continue
                
                query = f"""
                    SELECT DISTINCT {phone_col} as phone
                    FROM `{table}`
                    WHERE {phone_col} IS NOT NULL
                    AND {phone_col} != ''
                """
                
                query_job = client.query(query)
                results = query_job.result()
                
                for row in results:
                    if row.phone:
                        normalized = normalize_phone(row.phone)
                        if normalized:
                            all_phones.add(normalized)
                
            except Exception as e:
                continue
    
    return all_phones

def get_excluded_phones_from_file(file_path):
    """Get excluded phones from local file"""
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r') as f:
            phones = set(json.load(f))
            # Normalize phones from file
            return {normalize_phone(p) for p in phones if normalize_phone(p)}
    except:
        return set()

def add_to_excluded_phones(file_path, phones):
    """Add phones to excluded file"""
    excluded = get_excluded_phones_from_file(file_path)
    for phone in phones:
        normalized = normalize_phone(phone)
        if normalized:
            excluded.add(normalized)
    with open(file_path, 'w') as f:
        json.dump(list(excluded), f)

# ===== FETCH LEADS FUNCTIONS =====
def fetch_leads_from_campaign_with_dates(source, requested_columns, start_date, end_date):
    """Fetch leads from a source table with date range and auto-detect columns"""
    client = init_bigquery_client()
    if not client:
        return pd.DataFrame()
    
    table = source['table']
    phone_col = source.get('phone_column')
    date_col = source.get('date_column')
    
    if not table_exists(client, table):
        return pd.DataFrame()
    
    actual_columns = get_table_columns(client, table)
    
    # Auto-detect phone column if not specified
    if not phone_col:
        phone_col = detect_phone_column(actual_columns)
        if not phone_col:
            return pd.DataFrame()
    
    # Auto-detect date column if not specified
    if not date_col:
        date_col = detect_date_column(actual_columns, date_type='source')
    
    # Get valid columns for display
    valid_columns = []
    for col in requested_columns:
        if col == 'source_type':
            valid_columns.append(col)
        elif col in actual_columns:
            valid_columns.append(col)
    
    if not valid_columns:
        default_cols = ['name', 'phone_number', 'email', 'created_at']
        valid_columns = [col for col in default_cols if col in actual_columns]
    
    # Build SELECT clause
    select_parts = []
    for col in valid_columns:
        if col == 'source_type':
            select_parts.append(f"'{source['type']}' as source_type")
        else:
            select_parts.append(f"`{col}`")
    
    select_clause = ', '.join(select_parts)
    
    # Build WHERE clause
    where_conditions = [f"{phone_col} IS NOT NULL", f"{phone_col} != ''"]
    
    if date_col and date_col in actual_columns:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        where_conditions.append(f"{date_col} >= '{start_date_str}'")
        where_conditions.append(f"{date_col} <= '{end_date_str}'")
    
    where_clause = ' AND '.join(where_conditions)
    
    # Build ORDER BY clause
    order_by = date_col if date_col in actual_columns else phone_col
    
    query = f"""
        SELECT {select_clause}
        FROM `{table}`
        WHERE {where_clause}
        ORDER BY {order_by} DESC
        LIMIT 50000
    """
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        df = pd.DataFrame([dict(row) for row in results])
        
        # Normalize phone numbers
        if phone_col in df.columns:
            df['phone_number_normalized'] = df[phone_col].apply(normalize_phone)
            # Also keep original phone column for display
            if 'phone_number' not in df.columns and phone_col != 'phone_number':
                df['phone_number'] = df[phone_col]
        
        # Add missing columns as None
        for col in requested_columns:
            if col not in df.columns and col != 'source_type':
                df[col] = None
        
        return df
    except Exception as e:
        return pd.DataFrame()

def fetch_all_sources_leads_with_dates(sources, requested_columns, start_date, end_date):
    """Fetch leads from all active sources with date range and auto-detect columns"""
    all_dfs = []
    
    for source in sources:
        if source.get('active', True):
            df = fetch_leads_from_campaign_with_dates(source, requested_columns, start_date, end_date)
            if not df.empty:
                df['source_name'] = source['name']
                all_dfs.append(df)
    
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

# ===== DATA VALIDATION FUNCTIONS =====
def validate_phone(phone):
    """Validate phone number - only check if not empty"""
    if pd.isna(phone) or phone == '' or str(phone).strip() == '':
        return False
    return True

def validate_email(email):
    """Validate email format"""
    if pd.isna(email) or email == '':
        return False
    email_str = str(email).lower()
    test_keywords = ['test', 'abc', 'xyz', 'demo', 'sample']
    if any(kw in email_str for kw in test_keywords):
        return False
    if '@' not in email_str:
        return False
    return True

def validate_name(name):
    """Validate name - check for test keywords"""
    if pd.isna(name) or name == '':
        return False
    name_str = str(name).lower()
    test_keywords = ['test', 'abc', 'xyz', 'demo', 'sample']
    if any(kw in name_str for kw in test_keywords):
        return False
    return True
