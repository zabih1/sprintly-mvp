"""Script to validate and preview LinkedIn connections CSV file."""
import sys
import pandas as pd

def validate_csv(file_path: str):
    """Validate a CSV file for LinkedIn connections format."""
    print("🔍 Validating CSV file...\n")
    
    try:
        # Try different encodings
        df = None
        encoding_used = None
        
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                encoding_used = encoding
                print(f"✓ Successfully read with encoding: {encoding}\n")
                break
            except:
                continue
        
        if df is None:
            print("❌ Failed to read CSV with any common encoding")
            return
        
        # Show basic info
        print(f"📊 CSV Info:")
        print(f"   - Total rows: {len(df)}")
        print(f"   - Total columns: {len(df.columns)}")
        print(f"   - Encoding: {encoding_used}\n")
        
        # Show columns
        print("📋 Columns found:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. '{col}'")
        print()
        
        # Expected columns
        expected = {
            'First Name', 'Last Name', 'URL', 'Email Address',
            'Company', 'Position', 'Connected On'
        }
        
        actual = set(df.columns)
        missing = expected - actual
        extra = actual - expected
        
        if missing:
            print(f"⚠️  Missing required columns:")
            for col in missing:
                print(f"   - {col}")
            print()
        
        if extra:
            print(f"ℹ️  Extra columns (will be ignored):")
            for col in extra:
                print(f"   - {col}")
            print()
        
        if not missing:
            print("✅ All required columns present!\n")
            
            # Show sample data
            print("📝 Sample data (first 3 rows):\n")
            for i, row in df.head(3).iterrows():
                print(f"Row {i+1}:")
                print(f"   Name: {row.get('First Name', '')} {row.get('Last Name', '')}")
                print(f"   Company: {row.get('Company', 'N/A')}")
                print(f"   Position: {row.get('Position', 'N/A')}")
                print(f"   Email: {row.get('Email Address', 'N/A')}")
                print(f"   URL: {row.get('URL', 'N/A')}")
                print(f"   Connected On: {row.get('Connected On', 'N/A')}")
                print()
        else:
            print("❌ CSV is missing required columns\n")
            print("📥 To get the correct format:")
            print("   1. Go to LinkedIn Settings & Privacy")
            print("   2. Data Privacy → Get a copy of your data")
            print("   3. Select 'Connections' only")
            print("   4. Download the CSV file")
            print()
            print("Or create a CSV with these exact column headers:")
            print("   First Name,Last Name,URL,Email Address,Company,Position,Connected On")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_csv.py <path_to_csv_file>")
        print("\nExample:")
        print("  python validate_csv.py connections.csv")
        print("  python validate_csv.py sample_connections.csv")
    else:
        validate_csv(sys.argv[1])

