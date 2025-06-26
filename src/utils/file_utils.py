import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from .date_utils import DateUtils

class FileUtils:
    @staticmethod
    def save_to_excel(data: List[Dict[str, Any]], query: str, result_dir: Path) -> str:
        """Save crawled data to Excel file"""
        if not data:
            raise ValueError("No data to save")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Ensure result directory exists
        result_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = DateUtils.get_current_timestamp()
        filename = f"{timestamp} {query}.xlsx"
        filepath = result_dir / filename
        
        # Save to Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return str(filepath)
    
    @staticmethod
    def load_from_excel(filepath: str) -> pd.DataFrame:
        """Load data from Excel file"""
        return pd.read_excel(filepath)
    
    @staticmethod
    def merge_excel_files(filepaths: List[str], output_path: str) -> str:
        """Merge multiple Excel files into one"""
        all_data = []
        
        for filepath in filepaths:
            try:
                df = pd.read_excel(filepath)
                all_data.append(df)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
        
        if not all_data:
            raise ValueError("No valid files to merge")
        
        # Merge all DataFrames
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates based on link
        merged_df = merged_df.drop_duplicates(subset=['link'], keep='first')
        
        # Save merged file
        merged_df.to_excel(output_path, index=False, engine='openpyxl')
        
        return output_path
    
    @staticmethod
    def validate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean crawled data"""
        validated_data = []
        
        for item in data:
            # Skip items without required fields
            if not item.get('title') or not item.get('link'):
                continue
            
            # Clean and validate fields
            cleaned_item = {
                'title': str(item.get('title', '')).strip(),
                'link': str(item.get('link', '')).strip(),
                'source': str(item.get('source', '')).strip(),
                'date': str(item.get('date', '')).strip(),
                'content': str(item.get('content', '')).strip()
            }
            
            # Skip if title or link is empty after cleaning
            if not cleaned_item['title'] or not cleaned_item['link']:
                continue
            
            validated_data.append(cleaned_item)
        
        return validated_data