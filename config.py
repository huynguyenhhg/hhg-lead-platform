# config.py
import os
import json
import copy
from datetime import datetime, timedelta
import streamlit as st

# ===== GOOGLE CLOUD CONFIGURATION - HỖ TRỢ CLOUD =====
def get_service_account_info():
    """
    Lấy service account info từ:
    1. Streamlit secrets (khi deploy trên cloud)
    2. File JSON (khi chạy local)
    """
    # Ưu tiên 1: Dùng Streamlit secrets (cho Cloud)
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        return st.secrets['gcp_service_account']
    
    # Ưu tiên 2: Dùng environment variable (cho local)
    service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if service_account_file and os.path.exists(service_account_file):
        with open(service_account_file, 'r') as f:
            return json.load(f)
    
    # Ưu tiên 3: Dùng file mặc định (cho local development)
    # ✅ CÁCH ĐÚNG - dùng os.path.join
    # default_file = os.path.join(BASE_DIR, "hhg-ads-0fecebcf627f.json")
    # if os.path.exists(default_file):
    #     with open(default_file, 'r') as f:
    #         return json.load(f)
    
    return None
    

def get_project_id():
    """Lấy project ID từ secrets hoặc environment variable"""
    if hasattr(st, 'secrets') and 'gcp_project_id' in st.secrets:
        return st.secrets['gcp_project_id']
    return os.getenv('GCP_PROJECT_ID', 'hhg-client')

# ===== DIRECTORY CONFIGURATION - HỖ TRỢ CLOUD =====
def get_base_dir():
    """
    Lấy thư mục gốc của ứng dụng
    - Trên Cloud: thư mục hiện tại
    - Local: D:\HHG\UI
    """
    # Nếu đang chạy trên Streamlit Cloud
    if hasattr(st, 'secrets'):
        return os.path.dirname(os.path.abspath(__file__))
    
    # Nếu chạy local
    return r"D:\HHG\UI"

BASE_DIR = get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
CAMPAIGNS_FILE = os.path.join(DATA_DIR, "campaigns.json")
EXCLUDED_FILE = os.path.join(DATA_DIR, "excluded_phones.json")

# Tạo thư mục nếu chưa có
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ===== SERVICE ACCOUNT FILE PATH (giữ cho tương thích ngược) =====
# Lưu ý: Trên Cloud, file này sẽ không được sử dụng, thay vào đó dùng secrets
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "hhg-ads-0fecebcf627f.json") if not hasattr(st, 'secrets') else None
PROJECT_ID = get_project_id()

# ===== STANDARD COLUMNS (Các cột có thể có trong bảng) =====
STANDARD_COLUMNS = [
    "date",
    "name",
    "email",
    "phone_number",
    "child_dob",
    "address",
    "city",
    "state",
    "created_at"
]

# ===== DEFAULT DISPLAY COLUMNS (EXPORT CHO APP.PY) =====
DISPLAY_COLUMNS = [
    "name",
    "phone_number",
    "email",
    "child_dob",
    "address",
    "created_at",
    "source_type"
]

# ===== COLUMN NAME VARIANTS (cho auto-detect) =====
PHONE_COLUMN_VARIANTS = [
    'phone_number', 'phone', 'Phone', 'PhoneNumber', 'phonenumber',
    'phone_no', 'contact_phone', 'mobile', 'mobile_number', 'contact_no',
    'telephone', 'tel', 'cell', 'cellphone'
]

SENT_DATE_COLUMN_VARIANTS = [
    'sent_date', 'date_sent', 'sent_at', 'sent_on', 'date_sent',
    'sent_time', 'sent_datetime', 'email_sent_date'
]

SOURCE_DATE_COLUMN_VARIANTS = [
    'date', 'created_date', 'created_at', 'submitted_at', 'submitted_date',
    'record_date', 'event_date', 'registration_date', 'signup_date',
    'entry_date', 'date_created', 'date_entered'
]

# ===== DEFAULT CAMPAIGN CONFIGURATION =====
# Lưu ý: Có thể bỏ qua phone_column và date_column để auto-detect
DEFAULT_CAMPAIGNS = [
    {
        "id": "dugro_kh_2026",
        "name": "Dugro KH 2026",
        "country": "KH",
        "brand": "Dugro",
        "description": "Dugro Campaign Cambodia 2026",
        "sources": [
            {
                "id": "dugro_kh_2026_ladipage",
                "name": "Ladipage",
                "type": "Ladipage",
                "table": "hhg-client.hhg_kh_danone_dugro_2026.hhg_kh_danone_dugro_2026_ladipage_di",
                "phone_column": "phone_number",  
                "date_column": "date",           
                "active": True
            },
            {
                "id": "dugro_kh_2026_facebook",
                "name": "Facebook",
                "type": "Facebook",
                "table": "hhg-client.hhg_kh_danone_dugro_2026.hhg_kh_danone_dugro_2026_facebook_di",
                "phone_column": "phone_number",
                "date_column": "date",
                "active": True
            }
        ],
        "sent_table": "hhg-client.hhg_kh_danone_dugro_2026.hhg_kh_danone_dugro_2026_sent_di",
        "sent_phone_column": "phone_number",
        "sent_date_column": "sent_date",
        "previous_campaigns": [
            {
                "id": "dugro_kh_2025",
                "name": "Dugro KH 2025",
                "table": "hhg-client.hhg_kh_danone_dugro_2025.hhg_kh_danone_dugro_2025_all_di",
                "phone_column": "phone_number",
                "exclude": True
            }
        ],
        "display_columns": DISPLAY_COLUMNS,
        "active": True
    },
    {
        "id": "glucerna_my_2025",
        "name": "Glucerna MY 2025",
        "country": "MY",
        "brand": "Glucerna",
        "description": "Glucerna Campaign Malaysia 2025",
        "sources": [
            {
                "id": "glucerna_my_2025_facebook",
                "name": "Facebook",
                "type": "Facebook",
                "table": "hhg-client.hhg_my_abbott_glucerna.hhg_my_abbott_glucerna_2025_sent_di",
                "phone_column": "phone_number",
                "date_column": "date_sent",
                "active": True
            }
        ],
        "sent_table": "hhg-client.hhg_my_abbott_glucerna.hhg_my_abbott_glucerna_2025_sent_di",
        "sent_phone_column": "phone_number",
        "sent_date_column": "date_sent",
        "previous_campaigns": [
            {
                "id": "glucerna_my_2024",
                "name": "Glucerna MY 2024",
                "table": "hhg-client.hhg_my_abbott_glucerna.hhg_my_abbott_glucerna_2024_all_di",
                "phone_column": "phone_number",
                "exclude": True
            }
        ],
        "display_columns": ["name", "phone_number", "email", "source_type"],
        "active": True
    }
]

# ===== CAMPAIGN MANAGEMENT FUNCTIONS =====
def load_campaigns():
    """Load campaigns from file or create default"""
    if os.path.exists(CAMPAIGNS_FILE):
        try:
            with open(CAMPAIGNS_FILE, 'r', encoding='utf-8') as f:
                campaigns = json.load(f)
                # Ensure each campaign has required fields
                for campaign in campaigns:
                    if 'display_columns' not in campaign:
                        campaign['display_columns'] = DISPLAY_COLUMNS
                    if 'previous_campaigns' not in campaign:
                        campaign['previous_campaigns'] = []
                    if 'sources' not in campaign:
                        campaign['sources'] = []
                    # Add sent table fields if missing
                    if 'sent_table' not in campaign:
                        campaign['sent_table'] = None
                    if 'sent_phone_column' not in campaign:
                        campaign['sent_phone_column'] = None  # None = auto-detect
                    if 'sent_date_column' not in campaign:
                        campaign['sent_date_column'] = None  # None = auto-detect
                    # Ensure sources have column config
                    for source in campaign.get('sources', []):
                        if 'phone_column' not in source:
                            source['phone_column'] = None  # None = auto-detect
                        if 'date_column' not in source:
                            source['date_column'] = None  # None = auto-detect
                return campaigns
        except Exception as e:
            st.warning(f"Error loading campaigns, using defaults: {e}")
            return copy.deepcopy(DEFAULT_CAMPAIGNS)
    return copy.deepcopy(DEFAULT_CAMPAIGNS)

def save_campaigns(campaigns):
    """Save campaigns to file"""
    with open(CAMPAIGNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(campaigns, f, indent=2, ensure_ascii=False)

def get_active_campaigns():
    """Get only active campaigns"""
    campaigns = load_campaigns()
    return [c for c in campaigns if c.get('active', True)]

def get_campaign_by_id(campaign_id):
    """Get campaign by ID"""
    campaigns = load_campaigns()
    for c in campaigns:
        if c['id'] == campaign_id:
            return c
    return None

def add_campaign(campaign):
    """Add new campaign"""
    campaigns = load_campaigns()
    # Ensure sent table fields exist
    if 'sent_table' not in campaign:
        campaign['sent_table'] = None
    if 'sent_phone_column' not in campaign:
        campaign['sent_phone_column'] = None  # None = auto-detect
    if 'sent_date_column' not in campaign:
        campaign['sent_date_column'] = None  # None = auto-detect
    # Ensure sources have column config
    for source in campaign.get('sources', []):
        if 'phone_column' not in source:
            source['phone_column'] = None
        if 'date_column' not in source:
            source['date_column'] = None
    campaigns.append(campaign)
    save_campaigns(campaigns)

def update_campaign(campaign_id, updates):
    """Update existing campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            campaigns[i].update(updates)
            break
    save_campaigns(campaigns)

def delete_campaign(campaign_id):
    """Delete campaign"""
    campaigns = load_campaigns()
    campaigns = [c for c in campaigns if c['id'] != campaign_id]
    save_campaigns(campaigns)

def duplicate_campaign(campaign_id, new_id, new_name):
    """Duplicate an existing campaign with new ID and name"""
    campaigns = load_campaigns()
    original = get_campaign_by_id(campaign_id)
    if original:
        new_campaign = copy.deepcopy(original)
        new_campaign['id'] = new_id
        new_campaign['name'] = new_name
        # Update source IDs
        for source in new_campaign.get('sources', []):
            source['id'] = generate_source_id(new_id, source['name'])
        campaigns.append(new_campaign)
        save_campaigns(campaigns)
        return True
    return False

# ===== SOURCE MANAGEMENT FUNCTIONS =====
def add_source_to_campaign(campaign_id, source):
    """Add a new source to campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            if 'sources' not in campaigns[i]:
                campaigns[i]['sources'] = []
            # Ensure column config
            if 'phone_column' not in source:
                source['phone_column'] = None
            if 'date_column' not in source:
                source['date_column'] = None
            campaigns[i]['sources'].append(source)
            break
    save_campaigns(campaigns)

def delete_source_from_campaign(campaign_id, source_id):
    """Delete a source from campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            campaigns[i]['sources'] = [s for s in campaigns[i].get('sources', []) if s['id'] != source_id]
            break
    save_campaigns(campaigns)

def toggle_source_active(campaign_id, source_id):
    """Toggle source active status"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            for j, s in enumerate(campaigns[i].get('sources', [])):
                if s['id'] == source_id:
                    campaigns[i]['sources'][j]['active'] = not campaigns[i]['sources'][j].get('active', True)
                    break
            break
    save_campaigns(campaigns)

def update_source_in_campaign(campaign_id, source_id, updates):
    """Update an existing source in campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            for j, s in enumerate(campaigns[i].get('sources', [])):
                if s['id'] == source_id:
                    campaigns[i]['sources'][j].update(updates)
                    break
            break
    save_campaigns(campaigns)

def get_sources_by_campaign(campaign_id):
    """Get all sources for a campaign"""
    campaign = get_campaign_by_id(campaign_id)
    return campaign.get('sources', []) if campaign else []

# ===== PREVIOUS CAMPAIGN MANAGEMENT FUNCTIONS =====
def add_previous_campaign_to_campaign(campaign_id, prev_campaign):
    """Add a previous campaign to exclude"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            if 'previous_campaigns' not in campaigns[i]:
                campaigns[i]['previous_campaigns'] = []
            # Ensure column config
            if 'phone_column' not in prev_campaign:
                prev_campaign['phone_column'] = None
            campaigns[i]['previous_campaigns'].append(prev_campaign)
            break
    save_campaigns(campaigns)

def delete_previous_campaign_from_campaign(campaign_id, prev_id):
    """Delete previous campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            campaigns[i]['previous_campaigns'] = [
                p for p in campaigns[i].get('previous_campaigns', []) 
                if p['id'] != prev_id
            ]
            break
    save_campaigns(campaigns)

def toggle_previous_campaign_exclude(campaign_id, prev_id):
    """Toggle previous campaign exclude status"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            for j, p in enumerate(campaigns[i].get('previous_campaigns', [])):
                if p['id'] == prev_id:
                    campaigns[i]['previous_campaigns'][j]['exclude'] = not campaigns[i]['previous_campaigns'][j].get('exclude', True)
                    break
            break
    save_campaigns(campaigns)

def update_previous_campaign_in_campaign(campaign_id, prev_id, updates):
    """Update previous campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            for j, p in enumerate(campaigns[i].get('previous_campaigns', [])):
                if p['id'] == prev_id:
                    campaigns[i]['previous_campaigns'][j].update(updates)
                    break
            break
    save_campaigns(campaigns)

def get_previous_campaigns_by_campaign(campaign_id):
    """Get all previous campaigns for a campaign"""
    campaign = get_campaign_by_id(campaign_id)
    return campaign.get('previous_campaigns', []) if campaign else []

# ===== SENT TABLE MANAGEMENT FUNCTIONS =====
def update_sent_table_config(campaign_id, sent_table, sent_phone_column=None, sent_date_column=None):
    """Update sent table configuration for a campaign (None = auto-detect)"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            campaigns[i]['sent_table'] = sent_table
            campaigns[i]['sent_phone_column'] = sent_phone_column
            campaigns[i]['sent_date_column'] = sent_date_column
            break
    save_campaigns(campaigns)

def get_sent_table_config(campaign_id):
    """Get sent table configuration for a campaign"""
    campaign = get_campaign_by_id(campaign_id)
    if campaign:
        return {
            'sent_table': campaign.get('sent_table'),
            'sent_phone_column': campaign.get('sent_phone_column'),
            'sent_date_column': campaign.get('sent_date_column')
        }
    return None

def clear_sent_table(campaign_id):
    """Clear sent table configuration"""
    update_sent_table_config(campaign_id, None, None, None)

# ===== COLUMN MANAGEMENT FUNCTIONS =====
def update_campaign_columns(campaign_id, columns):
    """Update display columns for campaign"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            campaigns[i]['display_columns'] = columns
            break
    save_campaigns(campaigns)

def add_column_to_campaign(campaign_id, column):
    """Add a column to display"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            if column not in campaigns[i].get('display_columns', []):
                campaigns[i]['display_columns'].append(column)
            break
    save_campaigns(campaigns)

def remove_column_from_campaign(campaign_id, column):
    """Remove a column from display"""
    campaigns = load_campaigns()
    for i, c in enumerate(campaigns):
        if c['id'] == campaign_id:
            if column in campaigns[i].get('display_columns', []):
                campaigns[i]['display_columns'].remove(column)
            break
    save_campaigns(campaigns)

def get_campaign_columns(campaign_id):
    """Get display columns for a campaign"""
    campaign = get_campaign_by_id(campaign_id)
    return campaign.get('display_columns', DISPLAY_COLUMNS) if campaign else DISPLAY_COLUMNS

def reset_campaign_columns(campaign_id):
    """Reset display columns to default"""
    update_campaign_columns(campaign_id, DISPLAY_COLUMNS)

# ===== HELPER FUNCTIONS =====
def get_all_available_columns():
    """Get all available columns"""
    return STANDARD_COLUMNS

def get_source_types():
    """Get available source types"""
    return ["Ladipage", "Facebook", "Website", "Google Ads", "TikTok", "Other"]

def generate_source_id(campaign_id, source_name):
    """Generate unique source ID"""
    import re
    base_id = f"{campaign_id}_{re.sub(r'[^a-zA-Z0-9]', '_', source_name.lower())}"
    return base_id

def get_all_campaign_names():
    """Get list of all campaign names"""
    campaigns = load_campaigns()
    return [c['name'] for c in campaigns]

def get_campaign_stats():
    """Get statistics about campaigns"""
    campaigns = load_campaigns()
    total = len(campaigns)
    active = len([c for c in campaigns if c.get('active', True)])
    inactive = total - active
    total_sources = sum(len(c.get('sources', [])) for c in campaigns)
    total_prev = sum(len(c.get('previous_campaigns', [])) for c in campaigns)
    
    return {
        'total_campaigns': total,
        'active_campaigns': active,
        'inactive_campaigns': inactive,
        'total_sources': total_sources,
        'total_previous_campaigns': total_prev
    }

# ===== COLUMN DETECTION HELPER (cho các function khác) =====
def get_phone_column_variants():
    """Get list of phone column name variants"""
    return PHONE_COLUMN_VARIANTS

def get_sent_date_variants():
    """Get list of sent date column name variants"""
    return SENT_DATE_COLUMN_VARIANTS

def get_source_date_variants():
    """Get list of source date column name variants"""
    return SOURCE_DATE_COLUMN_VARIANTS
__all__ = [
    'EXCLUDED_FILE',
    'CAMPAIGNS_FILE',
    'DISPLAY_COLUMNS',
    'get_service_account_info',
    'get_project_id',
    'load_campaigns',
    'save_campaigns',
    'get_active_campaigns',
    'get_campaign_by_id',
    'add_campaign',
    'update_campaign',
    'delete_campaign',
    'add_source_to_campaign',
    'delete_source_from_campaign',
    'toggle_source_active',
    'add_previous_campaign_to_campaign',
    'delete_previous_campaign_from_campaign',
    'toggle_previous_campaign_exclude',
    'get_source_types',
    'generate_source_id'
]
