import os
import interactions
from src.config import DEV_GUILD
from src import logutil
import requests
from dotenv import load_dotenv

logger = logutil.init_logger(os.path.basename(__file__))
load_dotenv()


class GetFlight(interactions.Extension):
    def __init__(self, client: interactions.Client):

        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    @interactions.extension_command(
        name="test", description="test command", scope=DEV_GUILD
    )
    async def test_cmd(self, ctx: interactions.CommandContext):
        params = {
            'access_key': os.environ.get("API_ACCESS")
        }

        api_result = requests.get('http://api.aviationstack.com/v1/flights', params)

        api_response = api_result.json()

        for flight in api_response['results']:
            if (flight['live']['is_ground'] is False):
                print(u'%s flight %s from %s (%s) to %s (%s) is in the air.' % (
                    flight['airline']['name'],
                    flight['flight']['iata'],
                    flight['departure']['airport'],
                    flight['departure']['iata'],
                    flight['arrival']['airport'],
                    flight['arrival']['iata']))


def setup(client: interactions.Client):
    GetFlight(client)