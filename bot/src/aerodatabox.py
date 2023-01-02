import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import interactions

from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))


load_dotenv()


def vague_utc_conv(date: str):
    date_example = date.replace("Z", "").replace(" ", ", ")
    date_format = datetime.strptime(date_example, "%Y-%m-%d, %H:%M")
    unix_time = datetime.timestamp(date_format)
    return int(unix_time)


def accurate_utc_conv(date: str):
    date_str = str(date)
    date_format = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    unix_time = datetime.timestamp(date_format)
    return int(unix_time)


class AeroDataBox:
    def get_aircraft(
        reg: str = None,
    ):
        api_key = os.environ.get("KEY")
        base_url = "https://aerodatabox.p.rapidapi.com/aircrafts/reg/"
        url = f"{base_url}{reg}"
        querystring = {"withRegistrations": "true", "withImage": "true"}
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            api_response = response.json()
        except json.decoder.JSONDecodeError as err:
            logger.error(err)
            return None
        try:
            num_seats = {"num_seats": f"{api_response['seats']}"}
        except KeyError:
            num_seats = {"num_seats": "Unknown"}
        try:
            image = {"image": f"{api_response['image']['url']}"}
        except KeyError:
            image = {"image": "None"}
        return (api_response, num_seats, image)

    def get_nearest(
        flight_number: str = None,
        callsign: str = None,
        reg: str = None,
        icao: str = None,
    ):
        api_key = os.environ.get("KEY")
        base_url = "https://aerodatabox.p.rapidapi.com/flights/"
        if callsign:
            type = "callsign"
        elif flight_number:
            type = "number"
        elif reg:
            type = "reg"
        elif icao:
            type = "icao24"
        url = f"{base_url}{type}/{flight_number or callsign or reg or icao}"
        querystring = {"withAircraftImage": "true", "withLocation": "false"}
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            api_response = response.json()
        except json.decoder.JSONDecodeError as err:
            logger.error(err)
            return

        for flight in range(len(api_response)):
            try:
                if (
                    api_response[flight]["departure"]["airport"]["name"] is not None
                    and api_response[flight]["status"] != "Arrived"
                ):
                    try:
                        image_url = {
                            "image_url": f"{api_response[flight]['aircraft']['image']['url']}"
                        }
                    except KeyError as err:
                        logger.error(err)
                        image_url = None
                    try:
                        depart_time = {
                            "depart_time": f"<t:{vague_utc_conv(api_response[flight]['departure']['actualTimeUtc'])}:f>"
                        }
                    except KeyError as err:
                        logger.error(err)
                        depart_time = {
                            "depart_time": f"<t:{vague_utc_conv(api_response[flight]['departure']['scheduledTimeUtc'])}:f>"
                        }
                    try:
                        try:
                            arrive_time = {
                                "arrive_time": f"<t:{vague_utc_conv(api_response[flight]['arrival']['scheduledTimeUtc'])}:f>"
                            }
                        except KeyError as err:
                            logger.error(err)
                            arrive_time = {
                                "arrive_time": f"<t:{vague_utc_conv(api_response[flight]['arrival']['actualTimeUtc'])}:f>"
                            }
                    except KeyError as err:
                        logger.error(err)
                        arrive_time = {"arrive_time": "Unknown"}
                    try:
                        title = {
                            "title": f"Flight Information for {api_response[flight]['callSign']}"
                        }
                    except KeyError as err:
                        logger.error(err)
                        title = {
                            "title": f"Flight Information for {api_response[flight]['number']}"
                        }
                    author_url = {
                        "author_url": f"https://www.flightradar24.com/data/flights/{api_response[flight]['number'].replace(' ', '')}"
                    }

                    return (
                        api_response[flight],
                        image_url,
                        depart_time,
                        arrive_time,
                        title,
                        author_url,
                    )
            except KeyError as err:
                logger.error(err)
                return False
