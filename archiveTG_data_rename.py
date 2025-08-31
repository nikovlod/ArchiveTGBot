import csv
import os

def add_quotes_to_third_column(input_file, output_file=None):
    """
    Add quotes around the content of the third column in a CSV file.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output CSV file (optional)
    """
    
    # If no output file specified, create one with '_modified' suffix
    if output_file is None:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_modified{ext}"
    
    try:
        # Read the CSV file and process it
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            rows = []
            
            for row in reader:
                if len(row) >= 3:  # Make sure there are at least 3 columns
                    # Don't add quotes here - we'll handle it during writing
                    pass
                rows.append(row)
        
        # Write the modified data to the output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            for row in rows:
                # Join the row with commas, but handle the quoted third column specially
                if len(row) >= 3:
                    # Escape any existing quotes in the content
                    escaped_content = row[2].replace('"', '""')
                    # Write the row manually to control quoting
                    line = f'{row[0]},{row[1]},"{escaped_content}"'
                    if len(row) > 3:
                        line += ',' + ','.join(row[3:])
                    outfile.write(line + '\n')
                else:
                    # For rows with less than 3 columns, write normally
                    outfile.write(','.join(row) + '\n')
        
        print(f"Successfully processed {input_file}")
        print(f"Output saved to: {output_file}")
        print(f"Total rows processed: {len(rows)}")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    # Specify the input file
    input_file = "archiveTG_data.csv"
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found in the current directory.")
        print("Please make sure the file exists and try again.")
        return
    
    # Process the file
    add_quotes_to_third_column(input_file)

if __name__ == "__main__":
    main()
