from flask import Flask, request, jsonify,render_template
import requests
from apikeys import apikey
from flask_cors import CORS, cross_origin
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from telegram.bot import Bot
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
from telebot.mastermind import get_response

app = Flask(__name__)
CORS(app, support_credentials=True)
app.config["DEBUG"] = True
secret_key = apikey()

global bot
global TOKEN
TOKEN = bot_token
bot = Bot(token=TOKEN)


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
        predicted_labels = model.predict(df_matrix)

    else:
        predicted_labels = [0] * len(dataframe)

    return predicted_labels + 1


@app.route('/')
def hello_world():
    
    return render_template("index.html")


@app.route('/generate', methods=['POST'])
def generate_itinerary():
    response_final = get_location_attributes(request.form.get('location'))
    print(request.form.get("location"))
    number_of_days = int(request.form.get('days'))
    if type(response_final) != type(dict({})):
        return jsonify([response_final])
    else:
        coordinate_dict = response_final['Response']['View'][0]['Result'][0]['Location']["NavigationPosition"][0]
        latitude, longitude = coordinate_dict['Latitude'], coordinate_dict['Longitude']
        location_response = requests.get(
            f'https://places.ls.hereapi.com/places/v1/discover/search?at={latitude},{longitude}&r=10000&q=Landmark/Attractions&apiKey={secret_key}')
        if location_response.status_code == 200:
            if len(location_response.json()['results']['items']) > 0:
                tourist_data = location_response.json()
                tourist_dict = {'title': [], 'latitude': [], 'longitude': []}
                for i in range(len(tourist_data['results']['items'])):
                    tourist_dict['title'].append(tourist_data['results']['items'][i]['title'])
                    tourist_dict['latitude'].append(tourist_data['results']['items'][i]['position'][0])
                    tourist_dict['longitude'].append(tourist_data['results']['items'][i]['position'][1])
                tourist_df = pd.DataFrame(tourist_dict)
                day_of_travel = fit_and_inference(tourist_df, number_of_days)
                tourist_df['day_of_travel'] = day_of_travel
                print(tourist_df)
                return {'title': list(tourist_df['title']), 'latitude': list(tourist_df['latitude']),
                        'longitude': list(tourist_df['longitude']), 'day_of_travel': list(tourist_df['day_of_travel'])}

            else:
                return jsonify(['Nothing to roam here captain!'])

        else:
            return jsonify(['Error fetching API'])


@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    # get the chat_id to be able to respond to the same user
    chat_id = update.message.chat.id
    # get the message id to be able to reply to this specific message
    msg_id = update.message.message_id
    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    print("got text message :", text)
    # here we call our super AI
    response = get_response(text)
    if type(response) != type(dict({})):
        bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
        return 'OK'
    else:
        response_final = get_location_attributes(response['location'])
        number_of_days = int(response['days'])
        if type(response_final) != type(dict({})):
            bot.sendMessage(chat_id=chat_id, text=str(response_final), reply_to_message_id=msg_id)
            return 'OK'
        else:
            coordinate_dict = response_final['Response']['View'][0]['Result'][0]['Location']["NavigationPosition"][0]
            latitude, longitude = coordinate_dict['Latitude'], coordinate_dict['Longitude']
            location_response = requests.get(
                f'https://places.ls.hereapi.com/places/v1/discover/search?at={latitude},{longitude}&r=100000&q'
                f'=Landmark/Attraction&apiKey={secret_key}')
            if location_response.status_code == 200:
                if len(location_response.json()['results']['items']) > 0:
                    tourist_data = location_response.json()
                    tourist_dict = {'title': [], 'latitude': [], 'longitude': []}
                    for i in range(len(tourist_data['results']['items'])):
                        tourist_dict['title'].append(tourist_data['results']['items'][i]['title'])
                        tourist_dict['latitude'].append(tourist_data['results']['items'][i]['position'][0])
                        tourist_dict['longitude'].append(tourist_data['results']['items'][i]['position'][1])
                    tourist_df = pd.DataFrame(tourist_dict)
                    day_of_travel = fit_and_inference(tourist_df, number_of_days)
                    tourist_df['day_of_travel'] = day_of_travel
                    # print(tourist_df)
                    #response = str({'title': list(tourist_df['title']), 'latitude': list(tourist_df['latitude']),
                    #               'longitude': list(tourist_df['longitude']),
                    #                'day_of_travel': list(tourist_df['day_of_travel'])})
                    tourist_df.sort_values(by='day_of_travel', inplace=True, axis=0)
                    response = ''.join(f"Place:{tourist_df['title'].iloc[i]} \t Day: {tourist_df['day_of_travel'].iloc[i]}\n"
                                       for i in range(len(tourist_df)))

                    bot.sendMessage(chat_id=chat_id, text=str(response), reply_to_message_id=msg_id)
                    return 'OK'

                else:
                    bot.sendMessage(chat_id=chat_id, text='Nothing to roam here captain!', reply_to_message_id=msg_id)
                    return 'OK'

            else:
                bot.sendMessage(chat_id=chat_id, text='Sorry we faced an error in API', reply_to_message_id=msg_id)
                return 'OK'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    # something to let us know things work
    if s:
        return "Webhook setup ok"
    else:
        return "Webhook setup failed"


if __name__ == '__main__':
    app.run(threaded=True)
