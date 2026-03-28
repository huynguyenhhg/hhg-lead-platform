# lead_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    fetch_leads_from_source, get_all_leads_with_status, 
    add_to_excluded, get_excluded_phones_from_bigquery
)
from config import SOURCE_TABLES, FILTER_CONDITIONS, AGE_GROUPS

class LeadManager:
    """Class to manage leads with filtering and selection"""
    
    def __init__(self):
        self.selected_leads = []
        self.filters = {}
    
    def apply_filters(self, df, filters):
        """Apply filters to dataframe"""
        filtered_df = df.copy()
        
        if filters.get('exclude_sent'):
            excluded_phones = get_excluded_phones_from_bigquery()
            filtered_df = filtered_df[~filtered_df['phone_number'].astype(str).isin(excluded_phones)]
        
        if filters.get('has_email'):
            filtered_df = filtered_df[filtered_df['email'].notna() & (filtered_df['email'] != '')]
        
        if filters.get('missing_email'):
            filtered_df = filtered_df[filtered_df['email'].isna() | (filtered_df['email'] == '')]
        
        if filters.get('has_phone'):
            filtered_df = filtered_df[filtered_df['phone_number'].notna() & (filtered_df['phone_number'] != '')]
        
        if filters.get('missing_phone'):
            filtered_df = filtered_df[filtered_df['phone_number'].isna() | (filtered_df['phone_number'] == '')]
        
        if filters.get('has_name'):
            filtered_df = filtered_df[filtered_df['name'].notna() & (filtered_df['name'] != '')]
        
        if filters.get('missing_name'):
            filtered_df = filtered_df[filtered_df['name'].isna() | (filtered_df['name'] == '')]
        
        if filters.get('age_group') and filters['age_group'] != "All":
            age_min, age_max = AGE_GROUPS.get(filters['age_group'], (0, 999))
            if 'child_age' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['child_age'] >= age_min) & 
                    (filtered_df['child_age'] < age_max)
                ]
        
        if filters.get('sources'):
            filtered_df = filtered_df[filtered_df['source'].isin(filters['sources'])]
        
        return filtered_df
    
    def get_leads_display(self, filters=None):
        """Get leads for display with applied filters"""
        all_leads = get_all_leads_with_status(filters)
        if not all_leads.empty:
            return self.apply_filters(all_leads, filters or {})
        return pd.DataFrame()
    
    def export_selected_leads(self, leads_df, filename=None):
        """Export selected leads to Excel"""
        if filename is None:
            filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        leads_df.to_excel(filename, index=False)
        return filename
    
    def mark_as_sent(self, phone_numbers):
        """Mark leads as sent"""
        add_to_excluded(phone_numbers)
        return len(phone_numbers)

# UI Components
def render_filter_section():
    """Render filter UI section"""
    st.sidebar.markdown("### 🔍 Filter Conditions")
    
    filters = {}
    
    # Source selection
    st.sidebar.markdown("#### 📂 Sources")
    sources = st.sidebar.multiselect(
        "Select sources",
        options=[s['name'] for s in SOURCE_TABLES],
        default=[s['name'] for s in SOURCE_TABLES]
    )
    filters['sources'] = sources
    
    # Basic filters
    st.sidebar.markdown("#### 📋 Basic Filters")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        filters['has_email'] = st.checkbox("Has Email", value=False)
        filters['has_phone'] = st.checkbox("Has Phone", value=False)
        filters['has_name'] = st.checkbox("Has Name", value=False)
    
    with col2:
        filters['missing_email'] = st.checkbox("Missing Email", value=False)
        filters['missing_phone'] = st.checkbox("Missing Phone", value=False)
        filters['missing_name'] = st.checkbox("Missing Name", value=False)
    
    # Age group filter
    st.sidebar.markdown("#### 👶 Age Group")
    age_options = ["All"] + list(AGE_GROUPS.keys())
    filters['age_group'] = st.sidebar.selectbox("Select age group", age_options)
    
    # Exclude sent
    st.sidebar.markdown("#### 🚫 Exclude Options")
    filters['exclude_sent'] = st.sidebar.checkbox(
        "Exclude already sent leads", 
        value=True,
        help="Exclude phone numbers that have been sent in previous campaigns"
    )
    
    # Search
    st.sidebar.markdown("#### 🔎 Search")
    search_term = st.sidebar.text_input("Search by name, email, or phone")
    
    return filters, search_term

def render_leads_table(df, search_term=""):
    """Render leads table with styling"""
    if df.empty:
        st.info("No leads found with current filters")
        return pd.DataFrame()
    
    # Apply search
    if search_term:
        mask = (
            df['name'].astype(str).str.contains(search_term, case=False, na=False) |
            df['email'].astype(str).str.contains(search_term, case=False, na=False) |
            df['phone_number'].astype(str).str.contains(search_term, case=False, na=False)
        )
        df = df[mask]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Leads", len(df))
    with col2:
        sent_count = df['already_sent'].sum() if 'already_sent' in df.columns else 0
        st.metric("Already Sent", sent_count)
    with col3:
        new_count = len(df) - sent_count
        st.metric("New Leads", new_count)
    with col4:
        email_count = df['has_email'].sum() if 'has_email' in df.columns else 0
        st.metric("Has Email", email_count)
    
    # Display table with selection
    st.markdown("### 📊 Leads List")
    
    # Add selection column
    display_df = df.copy()
    display_df['Select'] = False
    
    # Use st.data_editor for selection
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", default=False),
            "already_sent": st.column_config.CheckboxColumn("Sent", disabled=True),
            "has_email": st.column_config.CheckboxColumn("Has Email", disabled=True),
            "has_phone": st.column_config.CheckboxColumn("Has Phone", disabled=True),
            "has_name": st.column_config.CheckboxColumn("Has Name", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )
    
    # Get selected leads
    selected = edited_df[edited_df['Select'] == True]
    
    return selected

def render_statistics(df):
    """Render statistics cards"""
    if df.empty:
        return
    
    st.markdown("### 📈 Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Source distribution
        source_counts = df['source'].value_counts()
        st.markdown("**By Source**")
        for source, count in source_counts.items():
            st.write(f"- {source}: {count}")
    
    with col2:
        # Age group distribution
        if 'age_group' in df.columns:
            age_counts = df['age_group'].value_counts()
            st.markdown("**By Age Group**")
            for age, count in age_counts.items():
                st.write(f"- {age}: {count}")
    
    with col3:
        # Quality metrics
        st.markdown("**Data Quality**")
        if 'has_email' in df.columns:
            email_pct = (df['has_email'].sum() / len(df)) * 100
            st.write(f"- Has Email: {email_pct:.1f}%")
        if 'has_phone' in df.columns:
            phone_pct = (df['has_phone'].sum() / len(df)) * 100
            st.write(f"- Has Phone: {phone_pct:.1f}%")
        if 'has_name' in df.columns:
            name_pct = (df['has_name'].sum() / len(df)) * 100
            st.write(f"- Has Name: {name_pct:.1f}%")