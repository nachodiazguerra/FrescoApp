from flask import Flask, render_template, request, redirect, url_for, session
import requests
import csv
import pandas as pd
import folium
from folium import IFrame
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = '45rf-6Sds-tq7j'  # Replace with a strong, random secret key


class Fresco:
    def __init__(self):
        self.header = ["Medida", "Aparato", "Fecha", "Lugar", "Dirección", "Latitud", "Longitud", "Ocupación"]

        current_directory = os.path.dirname(os.path.realpath(__file__))  # Get the current directory of the Python file
        self.csv_file = os.path.join(current_directory, 'data.csv')
        self.csv_file_sorted = os.path.join(current_directory, 'data_sorted.csv')
        # self.csv_file_sorted ="/home/DrDaveBowman/FrescoApp/data_sorted.csv"

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 10000)

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.header)

    def write_csv(self, data):
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data.values())

    def add_data(self, number, device, date, place, address, occupancy):
        lat, lon = self.get_coordinates(address)
        data = {
            "Medida": number,
            "Aparato": device,
            "Fecha": str(date),
            "Lugar": place,
            "Dirección": address,
            "Latitud": lat,
            "Longitud": lon,
            "Ocupación": occupancy
        }

        self.write_csv(data)

    def get_coordinates(self, address):
        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Dirección'] == address:
                    return row['Latitud'], row['Longitud']
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?proximity=ip&types=place%2Cpostcode%2Caddress&access_token=pk.eyJ1IjoiZnJlc2NvYXBwIiwiYSI6ImNsZHB3b3d0djBiZjYzd256MXQxZmhvY3MifQ.cKt6kwgw3XWBu9-QzjoMHw"
        response = requests.get(url)
        data = response.json()
        features = data.get('features', [])
        if features:
            lat, lon = features[0]['center']
            return lat, lon
        else:
            return None, None

    def add_measurement(self, form_data):
        number = form_data['number']
        device = form_data['device']
        date = form_data['date']
        place = form_data['place']
        address = form_data['address']
        occupancy = form_data['status']

        self.add_data(number, device, date, place, address, occupancy)

        return True

    def view_measurements(self):
        data = []
        with open(self.csv_file_sorted, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        if data:
            df = pd.DataFrame(data)

            return df.to_html(index=False, classes='table table-striped')
        else:
            return '<p>No hay datos disponibles.</p>'

    def generate_locations_map(self):
        locations = []
        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Latitud'] and row['Longitud']:
                    locations.append({
                        'Latitud': float(row['Latitud']),
                        'Longitud': float(row['Longitud']),
                        'Lugar': row['Lugar'],
                        'Fecha': row['Fecha'],
                        'Medida': row['Medida']
                    })

        if locations:
            map = folium.Map(location=[locations[0]['Latitud'], locations[0]['Longitud']], zoom_start=12)

            for location in locations:
                popup_content = f"Lugar: {location['Lugar']}<br>Fecha: {location['Fecha']}<br>Medida: {location['Medida']}"
                iframe = IFrame(html=popup_content, width=300, height=100)
                popup = folium.Popup(iframe, max_width=300)
                folium.Marker(
                    location=[location['Latitud'], location['Longitud']],
                    popup=popup,
                    icon=folium.Icon(color='blue')
                ).add_to(map)

            return map._repr_html_()
        else:
            return '<p>No hay ubicaciones disponibles.</p>'

    def get_c02_level(self, url, element_id):
        try:
            # Send a GET request to the website
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:

                # Parse the HTML content of the page
                soup = BeautifulSoup(response.content, 'html.parser')

                # Use BeautifulSoup's find method to find the div element by class
                div_element = soup.find('div', class_=element_id)

                # Check if the div element is found
                if div_element:
                    # Find the text content between the div and span tags
                    value_text = div_element.find_next('span', class_='error').previous_sibling.strip()

                    return value_text
                else:
                    print(f"Element with class '{element_id}' not found.")
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")


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

            df.to_csv(self.csv_file_sorted, index=False)

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


fresco_app = Fresco()

@app.route('/', methods=['GET', 'POST'])

def home():
    success_message = session.pop('success_message', None)  # Get and clear the success message from the session

    if request.method == 'POST':
        form_data = request.form.to_dict()
        if fresco_app.add_measurement(form_data):

            # Run the Data Cleaning.
            CleanData().remove_low_values()
            CleanData().clean_data()
            CleanData().arrange_displaying_data()

            # Set the success message in the session
            session['success_message'] = 'Medida añadida exitosamente.'
            return redirect(url_for('home'))  # Redirect to the home page

    measurements = fresco_app.view_measurements()
    locations_map = fresco_app.generate_locations_map()

    url = 'https://climate.nasa.gov/vital-signs/carbon-dioxide/'
    element_id = 'value'
    co2_level = fresco_app.get_c02_level(url, element_id)

    return render_template('index.html', data=measurements, co2_level=co2_level, success_message=success_message)

@app.route('/new_measure', methods=['GET', 'POST'])
def new_measure():
    # Add logic for the newMeasure.html page here if needed
    return render_template('newMeasure.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    # Add logic for the newMeasure.html page here if needed
    return render_template('test.html')

@app.route('/previous', methods=['GET', 'POST'])
def previous():
    # Add logic for the newMeasure.html page here if needed
    return render_template('previous.html')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
