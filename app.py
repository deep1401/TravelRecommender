from flask import Flask, request, jsonify
import requests
from apikeys import apikey
from flask_cors import CORS, cross_origin
import pandas as pd
from sklearn.cluster import MiniBatchKMeans

app = Flask(__name__)
CORS(app, support_credentials=True)
app.config["DEBUG"] = True

secret_key = apikey()


def get_location_attributes(location):
    response = requests.get(
        f'https://geocoder.ls.hereapi.com/6.2/geocode.json?searchtext={location}&gen=9&apiKey={secret_key}')
    if response.status_code == 200:
        if len(response.json()['Response']['View']) != 0:
            return response.json()
        else:
            return 'No such location found'
    else:
        return 'Something went wrong'


def fit_and_inference(dataframe, number_of_days):
    if len(dataframe) > number_of_days:
        model = MiniBatchKMeans(n_clusters=number_of_days, random_state=42, init='k-means++')
        df = dataframe[['latitude', 'longitude']]
        df_matrix = df.values
        model.fit(df_matrix)
        predicted_labels=model.predict(df_matrix)

    else:
        predicted_labels= [0]*len(dataframe)

    return predicted_labels + 1




@app.route('/')
def hello_world():
    return 'Houston,we are a go!'


@app.route('/generate', methods=['POST'])
def generate_itinerary():
    response_final = get_location_attributes(request.form.get('location'))
    number_of_days = int(request.form.get('days'))
    if type(response_final) != type(dict({})):
        return jsonify([response_final])
    else:
        coordinate_dict = response_final['Response']['View'][0]['Result'][0]['Location']["NavigationPosition"][0]
        latitude, longitude = coordinate_dict['Latitude'], coordinate_dict['Longitude']
        location_response = requests.get(
            f'https://places.ls.hereapi.com/places/v1/discover/search?at={latitude},{longitude}&r=100000&q=Landmark/Attraction&apiKey={secret_key}')
        if location_response.status_code == 200:
            if len(location_response.json()['results']['items']) > 0:
                tourist_data = location_response.json()
                tourist_dict = {'title': [], 'latitude': [], 'longitude': []}
                for i in range(len(tourist_data['results']['items'])):
                    tourist_dict['title'].append(tourist_data['results']['items'][i]['title'])
                    tourist_dict['latitude'].append(tourist_data['results']['items'][i]['position'][0])
                    tourist_dict['longitude'].append(tourist_data['results']['items'][i]['position'][1])
                tourist_df = pd.DataFrame(tourist_dict)
                day_of_travel= fit_and_inference(tourist_df,number_of_days)
                tourist_df['day_of_travel'] = day_of_travel
                print(tourist_df)
                return {'title': list(tourist_df['title']),'latitude': list(tourist_df['latitude']),
                        'longitude': list(tourist_df['longitude']), 'day_of_travel': list(tourist_df['day_of_travel'])}

            else:
                return jsonify(['Nothing to roam here captain!'])

        else:
            return jsonify(['Error fetching API'])



if __name__ == '__main__':
    app.run()