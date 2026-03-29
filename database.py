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
import time

# ===== BIGQUERY CONNECTION WITH TIMEOUT =====
@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client with timeout and retry"""
    try:
        service_account_info = get_service_account_info()
        
        if service_account_info:
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            project_id = get_project_id()
            # Add query config with byte limit
            client = bigquery.Client(
                credentials=credentials, 
                project=project_id,
                default_query_job_config=bigquery.QueryJobConfig(
                    maximum_bytes_billed=10**10  # 10GB limit
                )
            )
            return client
        else:
            project_id = get_project_id()
            client = bigquery.Client(project=project_id)
            return client
            
    except Exception as e:
        st.error(f"BigQuery connection failed: {e}")
        return None

# ===== PHONE NORMALIZATION =====
def normalize_phone(phone):
    """Normalize phone number to international format with +"""
    if pd.isna(phone) or phone == '' or str(phone).strip() == '':
        return None
    
    phone_str = str(phone).strip()
    cleaned = ''.join(ch for ch in phone_str if ch.isdigit() or ch == '+')
    
    if not any(ch.isdigit() for ch in cleaned):
        return None
    
    digits = ''.join(filter(str.isdigit, cleaned))
    
    if cleaned.startswith('+'):
        return f"+{digits}"
    else:
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
    """Auto-detect date column from available columns"""
    if date_type == 'sent':
        date_variants = ['sent_date', 'date_sent', 'sent_at', 'sent_on', 'date_sent',
                        'sent_time', 'sent_datetime', 'email_sent_date']
    else:
        date_variants = ['date', 'created_date', 'created_at', 'submitted_at', 
                        'submitted_date', 'record_date', 'event_date', 'registration_date',
                        'signup_date', 'entry_date', 'date_created', 'date_entered']
    
    for col in date_variants:
        if col in actual_columns:
            return col
    return None

# ===== TABLE UTILITIES WITH CACHING =====
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

@st.cache_data(ttl=300)
def table_exists(_client, table_name):
    """Check if a table exists in BigQuery with caching"""
    if not _client:
        return False
    try:
        _client.get_table(table_name)
        return True
    except NotFound:
        return False
    except Exception:
        return False

# ===== SENT DATA FUNCTIONS WITH CACHING =====
@st.cache_data(ttl=600)
def get_sent_phones(_client, sent_table, phone_column=None, date_column=None):
    """Get sent phones from sent table - with caching"""
    if not _client or not sent_table:
        return {}
    
    try:
        if not table_exists(_client, sent_table):
            return {}
        
        actual_columns = get_table_columns(_client, sent_table)
        
        if not phone_column:
            phone_column = detect_phone_column(actual_columns)
            if not phone_column:
                return {}
        
        if phone_column not in actual_columns:
            return {}
        
        if not date_column:
            date_column = detect_date_column(actual_columns, date_type='sent')
        
        if date_column and date_column not in actual_columns:
            date_column = None
        
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
        
        query_job = _client.query(query)
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
    """Get sent phones from sent tables in campaigns"""
    client = init_bigquery_client()
    if not client:
        return {}
    
    all_sent_data = {}
    
    for campaign in campaigns:
        sent_table = campaign.get('sent_table')
        if sent_table:
            phone_column = campaign.get('sent_phone_column')
            date_column = campaign.get('sent_date_column')
            
            sent_data = get_sent_phones(client, sent_table, phone_column, date_column)
            if sent_data:
                all_sent_data.update(sent_data)
    
    return all_sent_data

# ===== EXCLUDED PHONES FUNCTIONS WITH CACHING =====
@st.cache_data(ttl=600)
def get_excluded_phones_from_campaigns(previous_campaigns):
    """Get all excluded phones from previous campaigns with caching"""
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

# ===== FETCH LEADS FUNCTIONS WITH OPTIMIZATION =====
@st.cache_data(ttl=300, show_spinner=False)
def fetch_leads_from_campaign_with_dates(_client, source, requested_columns, start_date, end_date, max_records=10000):
    """Fetch leads from a source table with date range - OPTIMIZED with caching"""
    if not _client:
        return pd.DataFrame()
    
    table = source['table']
    phone_col = source.get('phone_column')
    date_col = source.get('date_column')
    
    if not table_exists(_client, table):
        return pd.DataFrame()
    
    actual_columns = get_table_columns(_client, table)
    
    if not phone_col:
        phone_col = detect_phone_column(actual_columns)
        if not phone_col:
            return pd.DataFrame()
    
    if not date_col:
        date_col = detect_date_column(actual_columns, date_type='source')
    
    valid_columns = []
    for col in requested_columns:
        if col == 'source_type':
            valid_columns.append(col)
        elif col in actual_columns:
            valid_columns.append(col)
    
    if not valid_columns:
        default_cols = ['name', 'phone_number', 'email', 'created_at']
        valid_columns = [col for col in default_cols if col in actual_columns]
    
    select_parts = []
    for col in valid_columns:
        if col == 'source_type':
            select_parts.append(f"'{source['type']}' as source_type")
        else:
            select_parts.append(f"`{col}`")
    
    select_clause = ', '.join(select_parts)
    
    where_conditions = [f"{phone_col} IS NOT NULL", f"{phone_col} != ''"]
    
    if date_col and date_col in actual_columns:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        where_conditions.append(f"{date_col} >= '{start_date_str}'")
        where_conditions.append(f"{date_col} <= '{end_date_str}'")
    
    where_clause = ' AND '.join(where_conditions)
    order_by = date_col if date_col in actual_columns else phone_col
    
    query = f"""
        SELECT {select_clause}
        FROM `{table}`
        WHERE {where_clause}
        ORDER BY {order_by} DESC
        LIMIT {max_records}
    """
    
    try:
        query_job = _client.query(query)
        results = query_job.result()
        df = pd.DataFrame([dict(row) for row in results])
        
        if phone_col in df.columns:
            df['phone_number_normalized'] = df[phone_col].apply(normalize_phone)
            if 'phone_number' not in df.columns and phone_col != 'phone_number':
                df['phone_number'] = df[phone_col]
        
        for col in requested_columns:
            if col not in df.columns and col != 'source_type':
                df[col] = None
        
        return df
    except Exception as e:
        return pd.DataFrame()

def fetch_all_sources_leads_with_dates(sources, requested_columns, start_date, end_date, max_records=10000):
    """Fetch leads from all active sources with date range"""
    client = init_bigquery_client()
    if not client:
        return pd.DataFrame()
    
    all_dfs = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, source in enumerate(sources):
        if source.get('active', True):
            status_text.text(f"Loading {source['name']}...")
            df = fetch_leads_from_campaign_with_dates(
                client, source, requested_columns, start_date, end_date, max_records
            )
            if not df.empty:
                df['source_name'] = source['name']
                all_dfs.append(df)
            progress_bar.progress((idx + 1) / len(sources))
    
    status_text.text("✅ Loading complete!")
    progress_bar.empty()
    
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

# ===== DATA VALIDATION FUNCTIONS =====
def validate_phone(phone):
    if pd.isna(phone) or phone == '' or str(phone).strip() == '':
        return False
    return True

def validate_email(email):
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
    if pd.isna(name) or name == '':
        return False
    name_str = str(name).lower()
    test_keywords = ['test', 'abc', 'xyz', 'demo', 'sample']
    if any(kw in name_str for kw in test_keywords):
        return False
    return True

# ===== UTILITY FUNCTIONS =====
def clear_all_cache():
    """Clear all cached data"""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ All cache cleared!")

def get_query_limit_from_session():
    """Get max records limit from session state"""
    return st.session_state.get('query_limit', 10000)