import os
import pandas as pd

def combine_csv_files(folder_path, output_file):
    # List to hold dataframes
    dataframes = []

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            # Read the CSV file into a dataframe
            df = pd.read_csv(file_path)
            # Filter rows where 'time' column is greater than 0.5
            df_filtered = df[df['time'] > 0.5]
            dataframes.append(df_filtered)

    # Concatenate all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Write the combined dataframe to a new CSV file
    combined_df.to_csv(output_file, index=False)
    print(f"Combined CSV file saved as {output_file}")

# Example usage
folder_path = '/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/betterData_150_PSI/calibration_20250420'
output_file = '/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/betterData_150_PSI/daily_combined_csv/combined_output_20250420.csv'
combine_csv_files(folder_path, output_file)