from flask import Flask, render_template, request, jsonify
from datetime import datetime

import logging
app = Flask(__name__,template_folder='templates')

import aeroapi_key as aeroapi_key
import requests, json

headers = {
    'Accept': 'application/json; charset=UTF-8',
    'x-apikey': aeroapi_key.key,
}

params = (
    ('type', 'Airline'),
    ('max_pages', '1'),
)


@app.route("/")
def main_handler():
    app.logger.info("In MainHandler")
    return render_template('mainpage.html', page_title="Airport Ground Transportation Predictor")

display_return_code = 200

@app.route("/gresponse")
def search_handler():
    airportname = request.args.get('airportname')
    app.logger.info(airportname)

    if airportname:
        print("Airportname: ", airportname)
        #print("Headers: ", headers)

        url = "https://aeroapi.flightaware.com/aeroapi/airports/" + airportname + "/flights/scheduled_arrivals"
        print("URL: ", url)

        arrival_times = []
        arrival_info = {}

        # The API requires us to get results in pages.
        # If the first page returns an error, then we will display to the user an error. However, if at least
        # the first page comes without error then we will proceed on.
        first_try = 1
        datetimeFormat = '%Y-%m-%d %H:%M:%S'

        now = datetime.utcnow()
        cur_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print(cur_time)

        cur_time_display = datetime.now().strftime("%m/%d/%y %I:%M:%S %p")

        # loop over all result pages
        while url:
            resp = requests.get(url, headers=headers, params=params)
            print("Response: ", resp)
            print("URL rep: ", resp.url)
            print("TEXT: ", resp.text)
            return_code = resp.status_code

            if first_try == 1:
                first_try = 0
                display_return_code = resp.status_code


            flight_info = resp.json()

            # Sometimes a page of the results would not include the JSON key or we get 'too many requests'
            if "scheduled_arrivals" not in flight_info or return_code != 200:
                break

            flight_arrivals = flight_info['scheduled_arrivals']

            for fa in flight_arrivals:
                time_Arrival = fa['estimated_in']
                if time_Arrival != None:
                    arrival_times.append(time_Arrival)
                    flightname = fa['ident']
                    arrival_info[flightname] = time_Arrival

            links = flight_info['links']

            print("links:", links)
            if links == None:
                break

            next_url = "https://aeroapi.flightaware.com/aeroapi" + links['next']
            print(next_url)
            url = next_url

        #print(arrival_times)
        #print("done")
        #print(arrival_info)


        flight_timeleft = {}

        # Now loop over all the flight arrivals to figure out how much time till they arrive.
        # I couldn't figure out how to get Google to do a histogram based on clock variable, so will bucketize
        # on minutes to arrival
        for i,j in arrival_info.items():
            str_t = str(j)
            #print("str_t:" , str_t)
            str_t = str_t.strip("Z")
            time = datetime.fromisoformat(str_t)
            #print(time)

            diff = datetime.strptime(str(time), datetimeFormat) \
                   - datetime.strptime(cur_time, datetimeFormat)
            #print(diff)

            # Convert to minute units
            t_min_left = int(diff.seconds / 60)
            #print(t_min_left)

            # Don't need to display flights too far in the future
            if t_min_left < 270:
                flight_timeleft[i] = t_min_left

        #print(flight_timeleft)

        if display_return_code == 200:
            return render_template('mainpage.html',page_title="Airport Ground Transportation Predictor", curtime=cur_time_display, airport=airportname, flightresults=flight_timeleft)
        elif display_return_code == 429:
            return render_template('mainpage.html', page_title="Airport Ground Transportation Predictor - Error",
                                   prompt="FlightAware API returned 'Too Many Requests'. Please wait and retry.")
        else:
            return render_template('mainpage.html', page_title="Airport Ground Transportation Predictor - Error",
                                   prompt="FlightAware API return Error: " + str(display_return_code))
    elif airportname == "":
        return render_template('mainpage.html',
                           page_title="Airport Ground Transportation Predictor - Error",
                           prompt="We need an airport name")
    else:
        return render_template('mainpage.html',page_title="Airport Ground Transportation Predictor")


if __name__ == "__main__":
    # Used when running locally only.
    # When deploying to Google AppEngine, a webserver process will
    # serve your app.
    app.run(host="localhost", port=8080, debug=True)




