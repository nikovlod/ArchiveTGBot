import csv

def convert_csv_for_cloudflare(input_file, output_file):
    """Convert existing CSV to Cloudflare-compatible format"""
    
    data = []
    
    # Read existing CSV
    try:
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            reader = csv.reader(infile)
            
            # Check if first row is header
            first_row = next(reader, None)
            if first_row and 'numerical_file_id' not in first_row[0].lower():
                # First row is data, not header
                data.append(first_row)
            
            # Read all remaining rows
            for row in reader:
                if len(row) >= 4:  # Ensure row has all required columns
                    data.append(row)
    
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return False
    
    # Write in clean format
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write header
            writer.writerow(['numerical_file_id', 'file_id', 'file_name', 'file_type'])
            
            # Write data
            for row in data:
                # Clean each field
                cleaned_row = []
                for i, field in enumerate(row):
                    # Remove extra quotes and whitespace
                    cleaned_field = str(field).strip().strip('"').strip("'")
                    cleaned_row.append(cleaned_field)
                
                # Ensure we have exactly 4 columns
                while len(cleaned_row) < 4:
                    cleaned_row.append('Unknown')
                
                writer.writerow(cleaned_row[:4])  # Only take first 4 columns
        
        print(f"Successfully converted {len(data)} rows to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        return False

def validate_csv(file_path):
    """Validate the CSV format"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            
            if not rows:
                print("CSV is empty")
                return False
            
            # Check header
            header = rows[0]
            expected_header = ['numerical_file_id', 'file_id', 'file_name', 'file_type']
            
            print(f"Header: {header}")
            print(f"Expected: {expected_header}")
            
            if len(rows) > 1:
                print(f"Sample data row: {rows[1]}")
                print(f"Total rows (including header): {len(rows)}")
            
            return True
            
    except Exception as e:
        print(f"Error validating CSV: {e}")
        return False

if __name__ == "__main__":
    input_file = "archiveTG_data.csv"  # Your current CSV file
    output_file = "archiveTG_data_fixed.csv"  # New clean CSV file
    
    print("Converting CSV file...")
    if convert_csv_for_cloudflare(input_file, output_file):
        print("\nValidating converted file...")
        validate_csv(output_file)
        print(f"\nDone! Upload {output_file} to your GitHub repository.")
        print("Then rename it to 'archiveTG_data.csv' in GitHub to replace the old one.")
    else:
        print("Conversion failed!")
