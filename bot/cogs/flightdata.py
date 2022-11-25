import os
import interactions
from src.config import DEV_GUILD
from src import logutil
import requests
from dotenv import load_dotenv
from pprint import pprint

logger = logutil.init_logger(os.path.basename(__file__))
load_dotenv()


class GetFlight(interactions.Extension):
    def __init__(self, client: interactions.Client):

        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    @interactions.extension_command(
        name="getflight", description="test command", scope=DEV_GUILD
    )
    async def getflight(self, ctx: interactions.CommandContext):

        url = "https://aerodatabox.p.rapidapi.com/flights/callsign/CLX44K"

        querystring = {"withAircraftImage":"false","withLocation":"false"}

        headers = {
            "X-RapidAPI-Key": os.environ.get("KEY"),
            "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        api_response = response.json()
        # print(api_response['departure']['airport']['name'])

        for flight in range(len(api_response)):
            if (api_response[flight]['departure']['airport']['name'] is not None):
                print(u'%s flight %s from %s (%s) to %s (%s) is in the air.' % (
                    api_response[flight]['airline']['name'],
                    api_response[flight]['number'],
                    api_response[flight]['departure']['airport']['name'],
                    api_response[flight]['departure']['airport']['iata'],
                    api_response[flight]['arrival']['airport']['name'],
                    api_response[flight]['arrival']['airport']['iata']))


def setup(client: interactions.Client):
    GetFlight(client)