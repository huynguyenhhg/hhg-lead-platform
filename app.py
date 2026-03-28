# app.py - Lead Explorer với UI Hello Health Group Style
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from database import get_sent_phones_from_campaigns

from config import (
    load_campaigns, get_active_campaigns, get_campaign_by_id,
    EXCLUDED_FILE, STANDARD_COLUMNS, DISPLAY_COLUMNS,
    add_campaign, update_campaign, delete_campaign,
    add_source_to_campaign, delete_source_from_campaign, toggle_source_active,
    add_previous_campaign_to_campaign, delete_previous_campaign_from_campaign,
    toggle_previous_campaign_exclude, get_source_types, generate_source_id
)
from database import (
    init_bigquery_client, fetch_all_sources_leads_with_dates,
    get_excluded_phones_from_campaigns, get_table_columns,normalize_phone  
)

# Page config
st.set_page_config(
    page_title="Hello Health Group - Lead Management Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, #0b2b5c 0%, #1e4a7a 50%, #2a6a9a 100%);
        padding: 1.8rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('https://www.hellohealthgroup.com/wp-content/uploads/2021/03/logo.png') no-repeat center;
        opacity: 0.05;
        pointer-events: none;
    }
    .main-header h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .main-header p {
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #2a6a9a;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    .metric-card h3 {
        color: #1e3c72;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card h2 {
        color: #2a6a9a;
        font-size: 2rem;
        font-weight: bold;
        margin: 0.3rem 0;
    }
    .metric-card p {
        color: #6c757d;
        font-size: 0.75rem;
        margin: 0;
    }
    
    /* Campaign Cards */
    .campaign-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        border-left: 4px solid #2a6a9a;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .campaign-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Source Badges */
    .source-badge {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdef5 100%);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.2rem;
        color: #1e3c72;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #2a6a9a 0%, #1e4a7a 100%);
        color: white;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(42,106,154,0.3);
    }
    
    /* Form Elements */
    .form-section {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 2rem;
        border-top: 1px solid #e9ecef;
        color: #6c757d;
        font-size: 0.75rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 16px;
    }
    
    /* Selection Panel */
    .selection-panel {
        background: linear-gradient(135deg, #e8f0fe 0%, #d4e4fc 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #c4d4f0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2a6a9a 0%, #1e4a7a 100%);
        color: white;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 10px;
        font-weight: 500;
    }
    
    /* Data Review Styles */
    .badge-pass {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-fail {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
        color: #856404;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize
client = init_bigquery_client()

# Session state
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = load_campaigns()
if 'selected_leads' not in st.session_state:
    st.session_state.selected_leads = pd.DataFrame()
if 'select_all' not in st.session_state:
    st.session_state.select_all = False
if 'show_add_source' not in st.session_state:
    st.session_state.show_add_source = False
if 'show_add_prev' not in st.session_state:
    st.session_state.show_add_prev = False
if 'selected_campaign_for_source' not in st.session_state:
    st.session_state.selected_campaign_for_source = None
if 'config_sent_table' not in st.session_state:
    st.session_state.config_sent_table = None
if 'editing_campaign' not in st.session_state:
    st.session_state.editing_campaign = None
if 'selected_campaign_for_prev' not in st.session_state:
    st.session_state.selected_campaign_for_prev = None

# ===== THÊM CÁC SESSION STATE MỚI =====
if 'require_previous' not in st.session_state:
    st.session_state.require_previous = True
if 'require_duplicate' not in st.session_state:
    st.session_state.require_duplicate = True
if 'require_phone' not in st.session_state:
    st.session_state.require_phone = True
if 'require_sent' not in st.session_state:
    st.session_state.require_sent = True
if 'require_child_dob' not in st.session_state:
    st.session_state.require_child_dob = True
if 'require_email' not in st.session_state:
    st.session_state.require_email = True
if 'require_name' not in st.session_state:
    st.session_state.require_name = True

# ===== FUNCTIONS =====
def check_email_valid(email):
    if pd.isna(email) or email == '':
        return 1
    email_lower = str(email).lower()
    test_keywords = ['test', 'abc', 'xyz', 'demo', 'sample']
    if any(kw in email_lower for kw in test_keywords):
        return 1
    if '@' not in email:
        return 1
    return 0

def check_name_valid(name):
    if pd.isna(name) or name == '':
        return 1
    name_lower = str(name).lower()
    test_keywords = ['test', 'abc', 'xyz', 'demo', 'sample']
    if any(kw in name_lower for kw in test_keywords):
        return 1
    return 0

def check_phone_valid(phone):
    if pd.isna(phone) or phone == '' or str(phone).strip() == '':
        return 0
    return 1

def calculate_mom_stage(child_dob, sent_date):
    if pd.isna(child_dob) or pd.isna(sent_date):
        return "Unknown"
    try:
        child_dob = pd.to_datetime(child_dob)
        sent_date = pd.to_datetime(sent_date)
        age_months = (sent_date - child_dob).days / 30.44
        
        if age_months < 0:
            return "🤰 Pregnant"
        elif age_months < 1:
            return "👶 0-1 month"
        elif age_months < 2:
            return "👶 1-2 months"
        elif age_months < 3:
            return "👶 2-3 months"
        elif age_months < 4:
            return "👶 3-4 months"
        elif age_months < 5:
            return "👶 4-5 months"
        elif age_months < 6:
            return "👶 5-6 months"
        elif age_months < 7:
            return "👶 6-7 months"
        elif age_months < 8:
            return "👶 7-8 months"
        elif age_months < 9:
            return "👶 8-9 months"
        elif age_months < 10:
            return "👶 9-10 months"
        elif age_months < 11:
            return "👶 10-11 months"
        elif age_months < 12:
            return "👶 11-12 months"
        else:
            return "🧒 Child's Age > 1"
    except:
        return "Unknown"

def add_all_conditions(df, previous_phones=None, sent_data=None, sent_date=None, 
                       require_previous=True, require_duplicate=True, require_phone=True, require_sent=True,
                       require_child_dob=True, require_email=True, require_name=True):
    """Add all condition columns to dataframe with flexible requirements"""
    if df.empty:
        return df
    
    if sent_date is None:
        sent_date = datetime.now()
    
    # Tạo cột phone_normalized
    if 'phone_number_normalized' in df.columns:
        df['phone_normalized'] = df['phone_number_normalized']
    else:
        # Normalize phone numbers
        df['phone_normalized'] = df['phone_number'].apply(normalize_phone)
    
    # 1. Previous campaign flag
    if previous_phones:
        df['previous_campaign'] = df['phone_normalized'].isin(previous_phones).astype(int)
    else:
        df['previous_campaign'] = 0
    
    # 2. Xác định duplicate (sắp xếp theo ngày)
    date_col = 'created_at' if 'created_at' in df.columns else 'date'
    if date_col in df.columns:
        df = df.sort_values([date_col, 'phone_normalized'])
    else:
        df = df.sort_values('phone_normalized')
    
    # Đánh dấu duplicate (giữ bản ghi đầu tiên)
    df['duplicate_flag'] = df.groupby('phone_normalized').cumcount().apply(lambda x: 1 if x > 0 else 0)
    
    # 3. Xử lý sent flag - CHỈ đánh dấu sent cho bản ghi KHÔNG duplicate
    if sent_data:
        df['sent_flag'] = df.apply(
            lambda row: 1 if (row['phone_normalized'] in sent_data and row['duplicate_flag'] == 0) else 0,
            axis=1
        )
        df['sent_date'] = df.apply(
            lambda row: sent_data.get(row['phone_normalized']) if (row['sent_flag'] == 1) else None,
            axis=1
        )
    else:
        df['sent_flag'] = 0
        df['sent_date'] = None
    
    # 4. Email validation
    df['check_email'] = df['email'].apply(check_email_valid)
    
    # 5. Name validation
    df['check_name'] = df['name'].apply(check_name_valid)
    
    # 6. Phone validation
    df['check_phone'] = df['phone_number'].apply(check_phone_valid)
    
    # 7. Mom stage calculation
    df['mom_stage'] = df.apply(
        lambda row: calculate_mom_stage(row.get('child_dob'), sent_date), 
        axis=1
    )
    
    # 8. Data Review flag - Build conditions based on user selection
    conditions = []
    
    if require_previous:
        conditions.append(df['previous_campaign'] == 0)
    if require_duplicate:
        conditions.append(df['duplicate_flag'] == 0)
    if require_phone:
        conditions.append(df['check_phone'] == 1)
    if require_sent:
        conditions.append(df['sent_flag'] == 0)
    if require_email:
        conditions.append(df['check_email'] == 0)
    if require_name:
        conditions.append(df['check_name'] == 0)
    if require_child_dob:
        conditions.append(df['mom_stage'] != "Unknown")
    
    # If no conditions selected, all leads pass
    if conditions:
        df['data_review'] = pd.concat(conditions, axis=1).all(axis=1).astype(int)
    else:
        df['data_review'] = 1
    
    # Drop temporary column
    df = df.drop(columns=['phone_normalized'], errors='ignore')
    
    return df

# ===== CAMPAIGN MANAGER PAGE =====
def render_campaign_manager():
    st.markdown("""
        <div class="main-header">
            <h1>📁 Campaign Manager</h1>
            <p>Create, edit and manage campaigns, sources, and previous campaigns</p>
        </div>
    """, unsafe_allow_html=True)
    
    campaigns = load_campaigns()
    
    tab1, tab2 = st.tabs(["📋 View & Manage Campaigns", "➕ Create New Campaign"])
    
    with tab1:
        if campaigns:
            for idx, campaign in enumerate(campaigns):
                with st.expander(f"📌 {campaign['name']} - {campaign['country']}/{campaign['brand']}", expanded=False):
                    # Campaign info
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**ID:** `{campaign['id']}`")
                        st.markdown(f"**Description:** {campaign.get('description', 'No description')}")
                        status = "🟢 Active" if campaign.get('active', True) else "🔴 Inactive"
                        st.markdown(f"**Status:** {status}")
                    
                    with col2:
                        if st.button(f"✏️ Edit", key=f"edit_{campaign['id']}_{idx}"):
                            st.session_state.editing_campaign = campaign
                            st.rerun()
                        if st.button(f"🔄 Toggle", key=f"toggle_{campaign['id']}_{idx}"):
                            new_status = not campaign.get('active', True)
                            update_campaign(campaign['id'], {'active': new_status})
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{campaign['id']}_{idx}"):
                            delete_campaign(campaign['id'])
                            st.success(f"Deleted campaign: {campaign['name']}")
                            st.rerun()
                    
                    # ===== THÊM SECTION SENT TABLE =====
                    st.markdown("---")
                    st.markdown("#### 📧 Sent Table Configuration")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        current_sent_table = campaign.get('sent_table', 'Not configured')
                        st.markdown(f"**Current Sent Table:** `{current_sent_table}`")
                        
                        if st.button(f"✏️ Configure Sent Table", key=f"config_sent_{campaign['id']}_{idx}"):
                            st.session_state.config_sent_table = campaign['id']
                            st.rerun()
                    
                    # Sent table configuration modal
                    if st.session_state.get('config_sent_table') == campaign['id']:
                        st.markdown("---")
                        st.markdown("#### ⚙️ Configure Sent Table")
                        
                        with st.form(f"sent_table_form_{campaign['id']}"):
                            sent_table = st.text_input(
                                "Sent Table Path", 
                                value=campaign.get('sent_table', ''),
                                placeholder="project.dataset.table",
                                help="BigQuery table containing sent leads"
                            )
                            sent_phone_col = st.text_input(
                                "Phone Column",
                                value=campaign.get('sent_phone_column', 'phone_number'),
                                help="Column name for phone numbers in sent table"
                            )
                            sent_date_col = st.text_input(
                                "Sent Date Column",
                                value=campaign.get('sent_date_column', 'sent_date'),
                                help="Column name for sent date"
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                save_sent = st.form_submit_button("💾 Save Configuration", type="primary")
                            with col2:
                                cancel_sent = st.form_submit_button("❌ Cancel")
                            
                            if save_sent:
                                update_campaign(campaign['id'], {
                                    'sent_table': sent_table if sent_table else None,
                                    'sent_phone_column': sent_phone_col,
                                    'sent_date_column': sent_date_col
                                })
                                st.success("✅ Sent table configuration saved!")
                                st.session_state.config_sent_table = None
                                st.rerun()
                            
                            if cancel_sent:
                                st.session_state.config_sent_table = None
                                st.rerun()
                    
                    # ===== SOURCES SECTION =====
                    st.markdown("---")
                    st.markdown("#### 📥 Sources")
                    
                    if campaign.get('sources'):
                        for src_idx, src in enumerate(campaign['sources']):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                status = "🟢 Active" if src.get('active', True) else "🔴 Inactive"
                                st.markdown(f"**{src['name']}** ({src['type']}) - {status}")
                                st.caption(f"Table: `{src['table']}`")
                            with col2:
                                if st.button(f"Toggle", key=f"toggle_src_{src['id']}_{src_idx}"):
                                    toggle_source_active(campaign['id'], src['id'])
                                    st.rerun()
                            with col3:
                                if st.button(f"Delete", key=f"del_src_{src['id']}_{src_idx}"):
                                    delete_source_from_campaign(campaign['id'], src['id'])
                                    st.rerun()
                    else:
                        st.info("No sources configured")
                    
                    # Add Source button
                    if st.button(f"➕ Add Source", key=f"add_src_{campaign['id']}_{idx}", use_container_width=True):
                        st.session_state.show_add_source = True
                        st.session_state.selected_campaign_for_source = campaign['id']
                        st.rerun()
                    
                    # ===== PREVIOUS CAMPAIGNS SECTION =====
                    st.markdown("#### 🚫 Previous Campaigns (Excluded)")
                    
                    if campaign.get('previous_campaigns'):
                        for prev_idx, prev in enumerate(campaign['previous_campaigns']):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                exclude_status = "🔴 Exclude" if prev.get('exclude', True) else "🟢 Include"
                                st.markdown(f"**{prev['name']}** - {exclude_status}")
                                st.caption(f"Table: `{prev['table']}`")
                            with col2:
                                if st.button(f"Toggle", key=f"toggle_prev_{prev['id']}_{prev_idx}"):
                                    toggle_previous_campaign_exclude(campaign['id'], prev['id'])
                                    st.rerun()
                            with col3:
                                if st.button(f"Delete", key=f"del_prev_{prev['id']}_{prev_idx}"):
                                    delete_previous_campaign_from_campaign(campaign['id'], prev['id'])
                                    st.rerun()
                    else:
                        st.info("No previous campaigns configured")
                    
                    # Add Previous Campaign button
                    if st.button(f"➕ Add Previous Campaign", key=f"add_prev_{campaign['id']}_{idx}", use_container_width=True):
                        st.session_state.show_add_prev = True
                        st.session_state.selected_campaign_for_prev = campaign['id']
                        st.rerun()
        else:
            st.info("No campaigns found. Add your first campaign below.")
    
    with tab2:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("➕ Create New Campaign")
        
        with st.form("new_campaign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                campaign_id = st.text_input("Campaign ID (unique)", placeholder="e.g., glucerna_my_2025")
                campaign_name = st.text_input("Campaign Name", placeholder="e.g., Glucerna MY 2025")
                country = st.selectbox("Country", ["KH", "MY", "TH", "VN"])
            
            with col2:
                brand = st.text_input("Brand", placeholder="e.g., Glucerna")
                description = st.text_area("Description", placeholder="Campaign description")
                active = st.checkbox("Active", value=True)
            
            # ===== THÊM SENT TABLE CONFIGURATION =====
            st.markdown("---")
            st.markdown("#### 📧 Sent Table Configuration (Optional)")
            
            col3, col4 = st.columns(2)
            with col3:
                sent_table = st.text_input("Sent Table Path", placeholder="project.dataset.sent_table")
                sent_phone_col = st.text_input("Phone Column", value="phone_number")
            with col4:
                sent_date_col = st.text_input("Sent Date Column", value="sent_date")
            
            submitted = st.form_submit_button("🚀 Create Campaign", type="primary", use_container_width=True)
            
            if submitted:
                if not campaign_id or not campaign_name:
                    st.error("Campaign ID and Name are required")
                else:
                    new_campaign = {
                        "id": campaign_id,
                        "name": campaign_name,
                        "country": country,
                        "brand": brand,
                        "description": description,
                        "sources": [],
                        "previous_campaigns": [],
                        "display_columns": DISPLAY_COLUMNS,
                        "active": active,
                        # Thêm sent table config
                        "sent_table": sent_table if sent_table else None,
                        "sent_phone_column": sent_phone_col,
                        "sent_date_column": sent_date_col
                    }
                    add_campaign(new_campaign)
                    st.success(f"✅ Campaign '{campaign_name}' created successfully!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add Source Modal
    if st.session_state.show_add_source and st.session_state.selected_campaign_for_source:
        st.markdown("---")
        st.markdown("### ➕ Add New Source")
        
        campaign = get_campaign_by_id(st.session_state.selected_campaign_for_source)
        st.info(f"Adding source to: **{campaign['name']}**")
        
        with st.form("add_source_form_modal"):
            col1, col2 = st.columns(2)
            
            with col1:
                source_name = st.text_input("Source Name", placeholder="e.g., Facebook, Ladipage")
                source_type = st.selectbox("Source Type", get_source_types())
                source_table = st.text_input("Table Path", placeholder="project.dataset.table")
            
            with col2:
                phone_column = st.text_input("Phone Column", value="phone_number")
                date_column = st.text_input("Date Column", value="date")
                active = st.checkbox("Active", value=True)
            
            col3, col4 = st.columns(2)
            with col3:
                submitted = st.form_submit_button("✅ Add Source", type="primary", use_container_width=True)
            with col4:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submitted:
                if source_name and source_table:
                    source_id = generate_source_id(campaign['id'], source_name)
                    new_source = {
                        "id": source_id,
                        "name": source_name,
                        "type": source_type,
                        "table": source_table,
                        "phone_column": phone_column,
                        "date_column": date_column,
                        "active": active
                    }
                    add_source_to_campaign(campaign['id'], new_source)
                    st.success(f"✅ Added source: {source_name}")
                    st.session_state.show_add_source = False
                    st.session_state.selected_campaign_for_source = None
                    st.rerun()
                else:
                    st.error("Source Name and Table Path are required")
            
            if cancelled:
                st.session_state.show_add_source = False
                st.session_state.selected_campaign_for_source = None
                st.rerun()
    
    # Add Previous Campaign Modal
    if st.session_state.show_add_prev and 'selected_campaign_for_prev' in st.session_state:
        st.markdown("---")
        st.markdown("### ➕ Add Previous Campaign to Exclude")
        
        campaign = get_campaign_by_id(st.session_state.selected_campaign_for_prev)
        st.info(f"Adding previous campaign to: **{campaign['name']}**")
        
        with st.form("add_prev_form_modal"):
            col1, col2 = st.columns(2)
            
            with col1:
                prev_name = st.text_input("Campaign Name", placeholder="e.g., Dugro KH 2024")
                prev_table = st.text_input("Table Path", placeholder="project.dataset.table")
            
            with col2:
                phone_column = st.text_input("Phone Column", value="phone_number")
                exclude = st.checkbox("Exclude", value=True)
            
            col3, col4 = st.columns(2)
            with col3:
                submitted = st.form_submit_button("✅ Add Previous Campaign", type="primary", use_container_width=True)
            with col4:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submitted:
                if prev_name and prev_table:
                    prev_id = f"{campaign['id']}_prev_{prev_name.lower().replace(' ', '_')}"
                    new_prev = {
                        "id": prev_id,
                        "name": prev_name,
                        "table": prev_table,
                        "phone_column": phone_column,
                        "exclude": exclude
                    }
                    add_previous_campaign_to_campaign(campaign['id'], new_prev)
                    st.success(f"✅ Added previous campaign: {prev_name}")
                    st.session_state.show_add_prev = False
                    st.session_state.selected_campaign_for_prev = None
                    st.rerun()
                else:
                    st.error("Campaign Name and Table Path are required")
            
            if cancelled:
                st.session_state.show_add_prev = False
                st.session_state.selected_campaign_for_prev = None
                st.rerun()

# ===== LEAD EXPLORER PAGE =====
def render_lead_explorer():
    st.markdown("""
        <div class="main-header">
            <h1>🔍 Lead Explorer</h1>
            <p>Explore, filter, and select leads with smart qualification</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Logo và tên
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 3rem;">🏥</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #1e3c72;">Hello Health Group</div>
                <div style="font-size: 0.75rem; color: #6c757d;">Lead Management Platform</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Campaign Selection
        st.markdown("### 🎯 Campaign")
        campaigns = get_active_campaigns()
        if not campaigns:
            st.warning("No active campaigns. Please create a campaign first.")
            st.stop()
        
        campaign_names = [c['name'] for c in campaigns]
        selected_campaign_name = st.selectbox("Select Campaign", campaign_names)
        selected_campaign = next(c for c in campaigns if c['name'] == selected_campaign_name)
        
        st.markdown("---")
        
        # Date Range
        st.markdown("### 📅 Date Range")
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=7)
        date_range = st.date_input("Select date range", value=(default_start, default_end))
        
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            start_date = default_start
            end_date = default_end
        
        st.caption(f"📅 {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")
        
        st.markdown("---")
        
        # Sent Date for Mom Stage
        st.markdown("### 📅 Sent Date")
        sent_date = st.date_input("For Mom Stage", value=datetime.now().date())
        
        st.markdown("---")
        
        # Data Review Options
        st.markdown("### ✅ Data Review Options")

        with st.expander("📋 Data Review Conditions", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                require_previous = st.checkbox("📁 Not in Previous Campaign", 
                                                value=st.session_state.require_previous,
                                                key="require_previous",
                                                help="Exclude leads from previous campaigns")
                require_duplicate = st.checkbox("🔄 Not Duplicate", 
                                                value=st.session_state.require_duplicate,
                                                key="require_duplicate",
                                                help="Keep only first occurrence of each phone number")
                require_phone = st.checkbox("📱 Valid Phone", 
                                            value=st.session_state.require_phone,
                                            key="require_phone",
                                            help="Phone number must not be empty")
                require_sent = st.checkbox("📧 Not Already Sent", 
                                            value=st.session_state.require_sent,
                                            key="require_sent",
                                            help="Exclude leads that were already sent")
            
            with col2:
                require_child_dob = st.checkbox("📅 Has Child DOB", 
                                                value=st.session_state.require_child_dob,
                                                key="require_child_dob",
                                                help="Lead must have valid Child Date of Birth")
                require_email = st.checkbox("📧 Valid Email", 
                                            value=st.session_state.require_email,
                                            key="require_email",
                                            help="Email must not contain test keywords and must have @")
                require_name = st.checkbox("👤 Valid Name", 
                                            value=st.session_state.require_name,
                                            key="require_name",
                                            help="Name must not contain test keywords")

        st.markdown("---")
        
        st.markdown("### 🔍 Filter Logic")
        filter_logic = st.radio(
            "Logic",
            ["AND (All must match)", "OR (Any can match)"],
            index=0
        )
        
        # ===== TIẾP TỤC VỚI CÁC FILTER KHÁC =====
        st.markdown("---")
        
        # Filter Options
        st.markdown("### 🚩 Filters")

        with st.expander("📋 Basic Filters", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                show_previous = st.checkbox("📁 Previous Campaign", value=False, key="show_previous")
                show_duplicate = st.checkbox("🔄 Duplicate", value=False, key="show_duplicate")
                show_invalid_email = st.checkbox("📧 Invalid Email", value=False, key="show_invalid_email")
            with col2:
                show_invalid_name = st.checkbox("👤 Invalid Name", value=False, key="show_invalid_name")
                show_invalid_phone = st.checkbox("📱 Invalid Phone", value=False, key="show_invalid_phone")
                show_valid_only = st.checkbox("✅ Hold Leads", value=True, key="show_valid_only")
        
        st.markdown("---")
    
        
        with st.expander("👶 Mom Stage Filter"):
            mom_stages = [
                "🤰 Pregnant", "👶 0-1 month", "👶 1-2 months", "👶 2-3 months", 
                "👶 3-4 months", "👶 4-5 months", "👶 5-6 months", "👶 6-7 months",
                "👶 7-8 months", "👶 8-9 months", "👶 9-10 months", "👶 10-11 months",
                "👶 11-12 months", "🧒 Child's Age > 1", "Unknown"
            ]
            selected_stages = st.multiselect("Select stages", mom_stages, default=[], key="selected_stages")
        
        with st.expander("📂 Source Filter"):
            sources = [s['name'] for s in selected_campaign.get('sources', []) if s.get('active', True)]
            source_filter = st.multiselect("Sources", options=sources, default=sources)
        
        st.markdown("---")
        
        # Search
        st.markdown("### 🔎 Search")
        search_term = st.text_input("Search by name, email, or phone", placeholder="Type to search...")
        
        st.markdown("---")
        
        # Load Previous Campaign Data
        with st.spinner("Loading previous campaign data..."):
            previous_phones = get_excluded_phones_from_campaigns(selected_campaign.get('previous_campaigns', []))
        
        st.info(f"📁 Excluded: **{len(previous_phones)}** phones")
        
        # Load Sent Data
        with st.spinner("Loading sent campaign data..."):
            sent_data = get_sent_phones_from_campaigns([selected_campaign])
            
            if sent_data and len(sent_data) > 0:
                # Metric card style
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                                padding: 1rem;
                                border-radius: 12px;
                                margin: 0.8rem 0;
                                text-align: center;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 2rem;">📧</div>
                        <div style="font-size: 1.8rem; font-weight: bold; color: #2e7d32;">{len(sent_data):,}</div>
                        <div style="font-size: 0.8rem; color: #2e7d32; font-weight: 500;">Phones Already Sent</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No sent data loaded")
    
    # Main content
    st.markdown(f"### 📋 {selected_campaign['name']}")
    
    # Get leads
    with st.spinner(f"🔄 Loading leads from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}..."):
        all_leads = fetch_all_sources_leads_with_dates(
            selected_campaign.get('sources', []),
            selected_campaign.get('display_columns', DISPLAY_COLUMNS),
            start_date,
            end_date
        )
    
    if not all_leads.empty:
        # Add source name
        all_leads['source'] = all_leads['source_name']
        if 'source_name' in all_leads.columns:
            all_leads = all_leads.drop(columns=['source_name'])
        
        # Add conditions
        all_leads = add_all_conditions(
            all_leads, 
            previous_phones, 
            sent_data, 
            pd.to_datetime(sent_date),
            require_previous=require_previous,
            require_duplicate=require_duplicate,
            require_phone=require_phone,
            require_sent=require_sent,
            require_child_dob=require_child_dob,
            require_email=require_email,
            require_name=require_name
        )
        
        # Apply filters
        filtered_df = all_leads.copy()
        
        masks = []
        if show_previous:
            masks.append(filtered_df['previous_campaign'] == 1)
        if show_duplicate:
            masks.append(filtered_df['duplicate_flag'] == 1)
        if show_invalid_email:
            masks.append(filtered_df['check_email'] == 1)
        if show_invalid_name:
            masks.append(filtered_df['check_name'] == 1)
        if show_invalid_phone:
            masks.append(filtered_df['check_phone'] == 0)
        if show_valid_only:
            masks.append(filtered_df['data_review'] == 1)
        if selected_stages:
            masks.append(filtered_df['mom_stage'].isin(selected_stages))
        if source_filter:
            masks.append(filtered_df['source'].isin(source_filter))
        
        if masks:
            if filter_logic == "AND (All must match)":
                final_mask = pd.Series([True] * len(filtered_df))
                for mask in masks:
                    final_mask = final_mask & mask
            else:
                final_mask = pd.Series([False] * len(filtered_df))
                for mask in masks:
                    final_mask = final_mask | mask
            filtered_df = filtered_df[final_mask]
        
        # Search filter
        if search_term and search_term.strip():
            search_term_lower = search_term.strip().lower()
            mask = pd.Series([False] * len(filtered_df))
            if 'name' in filtered_df.columns:
                mask = mask | filtered_df['name'].astype(str).str.lower().str.contains(search_term_lower, na=False)
            if 'email' in filtered_df.columns:
                mask = mask | filtered_df['email'].astype(str).str.lower().str.contains(search_term_lower, na=False)
            if 'phone_number' in filtered_df.columns:
                mask = mask | filtered_df['phone_number'].astype(str).str.contains(search_term, na=False)
            filtered_df = filtered_df[mask]
        
        # ===== STATISTICS =====
        st.markdown("### 📊 Performance Overview")
        
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📊 Total</h3>
                    <h2>{len(filtered_df):,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            valid_count = filtered_df['data_review'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>✅ Hold</h3>
                    <h2>{valid_count:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            sent_count = filtered_df['sent_flag'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📧 Sent</h3>
                    <h2>{sent_count:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            prev_count = filtered_df['previous_campaign'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📁 Previous</h3>
                    <h2>{prev_count:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col5:
            duplicate_count = filtered_df['duplicate_flag'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>🔄 Duplicate</h3>
                    <h2>{duplicate_count:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col6:
            invalid_email = filtered_df['check_email'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📧 Invalid Email</h3>
                    <h2>{invalid_email:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col7:
            invalid_name = filtered_df['check_name'].sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>👤 Invalid Name</h3>
                    <h2>{invalid_name:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col8:
            invalid_phone = (filtered_df['check_phone'] == 0).sum()
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📱 Invalid Phone</h3>
                    <h2>{invalid_phone:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # ===== CHARTS =====
        st.markdown("---")
        st.markdown("### 📊 Source Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_counts = filtered_df['source'].value_counts().reset_index()
            source_counts.columns = ['Source', 'Count']
            fig_source = px.bar(source_counts, x='Source', y='Count', title="Leads by Source",
                                color='Count', color_continuous_scale='Blues', text='Count')
            fig_source.update_traces(textposition='outside')
            fig_source.update_layout(height=400, showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_source, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(source_counts, values='Count', names='Source', 
                            title="Distribution by Source", 
                            color_discrete_sequence=px.colors.qualitative.Set2)
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # ===== MOM STAGE DISTRIBUTION =====
        st.markdown("---")
        st.markdown("### 👶 Mom Stage Distribution")
        
        stage_counts = filtered_df['mom_stage'].value_counts()
        
        if len(stage_counts) > 0:
            stage_df = stage_counts.reset_index()
            stage_df.columns = ['Stage', 'Count']
            stage_df = stage_df.sort_values('Count', ascending=True)
            
            fig = px.bar(stage_df, x='Count', y='Stage', orientation='h',
                        title="Lead Distribution by Stage", color='Count',
                        color_continuous_scale='Blues', text='Count')
            fig.update_traces(textposition='outside', texttemplate='%{text}')
            fig.update_layout(height=max(400, len(stage_df) * 35), showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mom stage data available")
        
        # ===== DATA REVIEW BREAKDOWN =====
        st.markdown("---")
        st.markdown("### 📋 Data Review Breakdown")

        # Tạo dataframe cho breakdown
        breakdown_data = {
            'Condition': [],
            'Pass Count': [],
            'Fail Count': [],
            'Required': []
        }

        # Thêm từng condition
        conditions_list = [
            ('📁 Not in Previous Campaign', 'previous_campaign', 0, require_previous),
            ('🔄 Not Duplicate', 'duplicate_flag', 0, require_duplicate),
            ('📱 Valid Phone', 'check_phone', 1, require_phone),
            ('📧 Not Sent', 'sent_flag', 0, require_sent),
            ('📧 Valid Email', 'check_email', 0, require_email),
            ('👤 Valid Name', 'check_name', 0, require_name),
            ('📅 Has Child DOB', 'mom_stage', 'not_unknown', require_child_dob)
        ]

        for label, col, expected, is_required in conditions_list:
            if col == 'mom_stage' and expected == 'not_unknown':
                pass_count = (filtered_df[col] != "Unknown").sum()
                fail_count = (filtered_df[col] == "Unknown").sum()
            else:
                pass_count = (filtered_df[col] == expected).sum()
                fail_count = (filtered_df[col] != expected).sum()
            
            breakdown_data['Condition'].append(label)
            breakdown_data['Pass Count'].append(pass_count)
            breakdown_data['Fail Count'].append(fail_count)
            breakdown_data['Required'].append('✓' if is_required else '✗')

        breakdown_df = pd.DataFrame(breakdown_data)

        # Thêm percentage
        breakdown_df['Pass %'] = (breakdown_df['Pass Count'] / len(filtered_df) * 100).round(1).astype(str) + '%'
        breakdown_df['Fail %'] = (breakdown_df['Fail Count'] / len(filtered_df) * 100).round(1).astype(str) + '%'

        st.dataframe(
            breakdown_df[['Condition', 'Pass Count', 'Pass %', 'Fail Count', 'Fail %', 'Required']],
            use_container_width=True,
            hide_index=True
        )

        st.caption("💡 **Note:** ✓ = Required (must pass), ✗ = Optional (not required)")
        # ===== CONDITIONS SUMMARY =====
        st.markdown("---")
        st.markdown("### 📋 Quality Conditions Summary")
        
        conditions_data = {
            'Condition': ['✅ Data Review Pass', '📧 Already Sent', '📁 Previous Campaign', 
                         '🔄 Duplicate', '📧 Invalid Email', '👤 Invalid Name', '📱 Invalid Phone'],
            'Count': [
                filtered_df['data_review'].sum(),
                filtered_df['sent_flag'].sum(),
                filtered_df['previous_campaign'].sum(),
                filtered_df['duplicate_flag'].sum(),
                filtered_df['check_email'].sum(),
                filtered_df['check_name'].sum(),
                (filtered_df['check_phone'] == 0).sum()
            ]
        }
        st.dataframe(pd.DataFrame(conditions_data), use_container_width=True, hide_index=True)
        
        # ===== LEADS TABLE =====
        st.markdown("---")
        st.markdown(f"### 📋 Leads List ({len(filtered_df)} records)")
        
        # Selection Panel
        st.markdown("""
            <div class="selection-panel">
                <p><strong>📌 Selection Tools</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state.select_all = True
                st.rerun()
        with col2:
            if st.button("❌ Clear All", use_container_width=True):
                st.session_state.select_all = False
                st.rerun()
        with col3:
            if st.button("📋 Select Filtered", use_container_width=True):
                st.session_state.select_all = "filtered"
                st.rerun()
        
        # Create display dataframe
        display_df = filtered_df.copy()
        
        # Set select column based on session state
        if st.session_state.select_all is True:
            display_df.insert(0, 'Select', True)
        elif st.session_state.select_all == "filtered":
            display_df.insert(0, 'Select', True)
        else:
            display_df.insert(0, 'Select', False)
        
        # Tạo cột lý do fail
        def get_fail_reason(row):
            reasons = []
            if row.get('previous_campaign', 0) == 1:
                reasons.append("Prev Campaign")
            if row.get('duplicate_flag', 0) == 1:
                reasons.append("Duplicate")
            if row.get('check_phone', 0) == 0:
                reasons.append("Invalid Phone")
            if row.get('sent_flag', 0) == 1:
                reasons.append("Already Sent")
            if require_email and row.get('check_email', 0) == 1:
                reasons.append("Invalid Email")
            if require_name and row.get('check_name', 0) == 1:
                reasons.append("Invalid Name")
            if require_child_dob and row.get('mom_stage', '') == "Unknown":
                reasons.append("Missing DOB")
            
            return ", ".join(reasons) if reasons else "Pass"
        
        filtered_df['fail_reason'] = filtered_df.apply(get_fail_reason, axis=1)
        display_df['fail_reason'] = filtered_df['fail_reason']
        
        # Format sent_date
        if 'sent_date' in display_df.columns:
            display_df['sent_date'] = display_df['sent_date'].fillna('')
            
            def safe_format_date(x):
                """Safely format date to YYYY-MM-DD"""
                if x == '' or pd.isna(x):
                    return ''
                try:
                    if hasattr(x, 'strftime'):
                        return x.strftime('%Y-%m-%d')
                    if isinstance(x, str):
                        if len(x) >= 10 and x[4] == '-' and x[7] == '-':
                            return x[:10]
                        try:
                            dt = pd.to_datetime(x)
                            return dt.strftime('%Y-%m-%d')
                        except:
                            return x[:10] if len(x) >= 10 else x
                    return str(x)[:10] if len(str(x)) >= 10 else str(x)
                except:
                    return str(x)[:10] if len(str(x)) >= 10 else str(x)
            
            display_df['sent_date'] = display_df['sent_date'].apply(safe_format_date)
        
        # Format boolean columns
        format_map = {
            'previous_campaign': {1: '❌ Yes', 0: '✅ No'},
            'duplicate_flag': {1: '❌ Yes', 0: '✅ No'},
            'check_email': {1: '❌ Invalid', 0: '✅ Valid'},
            'check_name': {1: '❌ Invalid', 0: '✅ Valid'},
            'check_phone': {1: '✅ Valid', 0: '❌ Invalid'},
            'data_review': {1: '✅ Pass', 0: '❌ Fail'}
        }
        
        for col, mapping in format_map.items():
            if col in display_df.columns:
                display_df[col] = display_df[col].map(mapping)
        
        # Rename columns
        rename_map = {
            'name': 'Name',
            'phone_number': 'Phone',
            'email': 'Email',
            'source': 'Source',
            'sent_flag': 'Sent',
            'sent_date': 'Sent Date',
            'previous_campaign': 'Prev Campaign',
            'duplicate_flag': 'Duplicate',
            'check_email': 'Email Check',
            'check_name': 'Name Check',
            'check_phone': 'Phone Check',
            'mom_stage': 'Mom Stage',
            'data_review': 'Data Review',
            'fail_reason': 'Status / Reason',
            'child_dob': 'Child DOB',
            'address': 'Address',
            'created_at': 'Created At',
            'date': 'Date'
        }
        
        display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})
        display_df = display_df.loc[:, ~display_df.columns.duplicated()]
        
        # Reorder columns for better display
        priority_cols = ['Select', 'Name', 'Phone', 'Email', 'Source', 'Mom Stage', 'Data Review', 
                         'Status / Reason', 'Sent', 'Sent Date', 'Prev Campaign', 'Duplicate']
        existing_priority = [col for col in priority_cols if col in display_df.columns]
        other_cols = [col for col in display_df.columns if col not in priority_cols]
        display_df = display_df[existing_priority + other_cols]
        
        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
        
        # Get selected leads
        selected = edited_df[edited_df['Select'] == True].copy()
        selected = selected.drop(columns=['Select'], errors='ignore')
        
        # Reset select all after use
        if st.session_state.select_all is not False:
            st.session_state.select_all = False
        
        if not selected.empty:
            st.success(f"✅ Selected {len(selected)} leads")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export Selected to Excel", use_container_width=True):
                    filename = f"leads_{selected_campaign['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    selected.to_excel(filename, index=False)
                    with open(filename, "rb") as f:
                        st.download_button("📥 Download Excel", data=f, file_name=filename)
            
            with col2:
                if st.button("🚫 Mark as Sent", use_container_width=True):
                    phone_col = 'Phone' if 'Phone' in selected.columns else 'phone_number'
                    new_phones = selected[phone_col].astype(str).tolist()
                    
                    excluded = set()
                    if os.path.exists(EXCLUDED_FILE):
                        with open(EXCLUDED_FILE, 'r') as f:
                            try:
                                excluded = set(json.load(f))
                            except:
                                excluded = set()
                    
                    excluded.update(new_phones)
                    with open(EXCLUDED_FILE, 'w') as f:
                        json.dump(list(excluded), f)
                    
                    st.success(f"✅ Marked {len(new_phones)} leads as sent")
                    st.rerun()
        else:
            st.info("💡 Select leads using the checkboxes above")
    else:
        st.info(f"ℹ️ No leads found from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
# ===== MAIN APP =====
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Lead Explorer", "Campaign Manager"],
        icons=["search", "folder-plus"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa", "border-radius": "12px"},
            "icon": {"color": "#2a6a9a", "font-size": "20px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "0px", "padding": "12px", "border-radius": "10px"},
            "nav-link-selected": {"background": "linear-gradient(135deg, #2a6a9a 0%, #1e4a7a 100%)", "color": "white"},
        }
    )

if selected == "Lead Explorer":
    render_lead_explorer()
else:
    render_campaign_manager()

# Footer
st.markdown("""
    <div class="footer">
        <p>🏥 <strong>Hello Health Group</strong> - Lead Management Platform</p>
        <p style="font-size: 0.7rem;">© 2024 All Rights Reserved | Powered by BigQuery | Smart Lead Qualification System</p>
    </div>
""", unsafe_allow_html=True)