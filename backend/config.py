import os
from pathlib import Path

def get_data_dir():
    """Get the standard directory for application data on Windows"""
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        data_dir = Path(local_app_data) / "WFMoney"
    else:
        # Fallback for non-Windows or if LOCALAPPDATA is missing
        data_dir = Path.home() / ".wfmoney"
    
    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_data_path(filename):
    """Get the full path for a data file"""
    return get_data_dir() / filename
