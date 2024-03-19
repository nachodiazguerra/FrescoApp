import pandas as pd
import csv
import os

class CleanData:
    def __init__(self):
        self.header = ["Medida", "Aparato", "Fecha", "Lugar", "Dirección", "Latitud", "Longitud"]

        current_directory = os.path.dirname(os.path.realpath(__file__))  # Get the current directory of the Python file
        self.csv_file = os.path.join(current_directory, 'data.csv')
        self.csv_file_sorted = os.path.join(current_directory, 'data_sorted.csv')

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 10000)

    def clean_data(self):

        data = []

        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        if data:
            df = pd.DataFrame(data)
            df = self.merge_locations_data(df)

            # Reset the index of the DataFrame
            df.reset_index(drop=True, inplace=True)

            df.to_csv("data_sorted.csv", index=False)

        else:
            return 'No hay datos disponibles.'

    def merge_locations_data(self, df):
        # Group rows by "Latitud" and "Longitud"
        grouped = df.groupby(['Latitud', 'Longitud'])

        # Initialize empty lists to store the new data
        new_rows = []

        for group_name, group_df in grouped:

            # Calculate the most frequent values in "Lugar" and "Dirección"
            most_common_lugar = group_df['Lugar'].mode().values[0]
            most_common_direccion = group_df['Dirección'].mode().values[0]

            # Combine data from "Medida", "Aparato", and "Fecha" into a list
            medidas_aparato_fecha = list(map(list, zip(group_df['Medida'], group_df['Aparato'], group_df['Fecha'], group_df['Ocupación'])))

            # Create a new row based on the group
            new_row = {
                'Latitud': group_name[0],
                'Longitud': group_name[1],
                'Lugar': most_common_lugar,
                'Dirección': most_common_direccion,
                'Datos de mediciones': medidas_aparato_fecha,
                'Mediciones': len(group_df)
            }

            new_rows.append(new_row)

        # Create a new DataFrame from the merged data
        merged_df = pd.DataFrame(new_rows)

        return merged_df

    def remove_low_values(self):
        # Create a temporary list to store rows to keep
        rows_to_keep = []

        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                # Check the value in the "Medidas" column
                if int(row['Medida']) >= 400:
                    rows_to_keep.append(row)

        # Check if any rows need to be kept
        if rows_to_keep:
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write the header row
                writer.writeheader()

                # Write the rows to keep
                writer.writerows(rows_to_keep)

            print(f"Rows with 'Medidas' >= 400 have been saved to {self.csv_file}")
        else:
            print("No rows with 'Medidas' >= 400 found in the CSV file.")

    def arrange_displaying_data(self):
        data = []

        with open(self.csv_file_sorted, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        if data:
            df = pd.DataFrame(data)

            # Define a custom function to extract the highest and lowest "Medida" from each row
            def get_highest_lowest(row):
                # Access the "Datos de mediciones" cell and parse it as a list of lists
                data_list = eval(row['Datos de mediciones'])

                # Extract the "Medida" values from each inner list and convert to integers
                medidas = [int(item[0]) for item in data_list]

                # Calculate the highest and lowest "Medida" values
                highest_medida = max(medidas)
                lowest_medida = min(medidas)

                return highest_medida, lowest_medida

            # Apply the custom function to each row and assign the results to new columns
            df[['Mayor Valor', 'Menor Valor']] = df.apply(get_highest_lowest, axis=1, result_type='expand')

            # Write the updated DataFrame to self.csv_file_sorted
            df.to_csv(self.csv_file_sorted, index=False)
            print(f"Data has been written to {self.csv_file_sorted}")

            # Print the updated DataFrame
            print(df)


CleanData().remove_low_values()
CleanData().clean_data()
CleanData().arrange_displaying_data()
