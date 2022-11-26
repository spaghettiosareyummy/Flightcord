import os
import interactions
from src.config import DEV_GUILD
from src import logutil
import requests
from dotenv import load_dotenv
from pprint import pprint
import json
import datetime

logger = logutil.init_logger(os.path.basename(__file__))
load_dotenv()

def get_unix_time(date: str):
    date_example = date.replace("Z", "").replace(" ", ", ")
    date_format = datetime.datetime.strptime(date_example, "%Y-%m-%d, %H:%M")
    unix_time = datetime.datetime.timestamp(date_format)
    return int(unix_time)


class GetFlight(interactions.Extension):
    def __init__(self, client: interactions.Client):

        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    @interactions.extension_command(
        name="getflight", 
        description="test command", 
        scope=DEV_GUILD,
        options = [
            interactions.Option(
                name="callsign",
                description="The callsign of the flight",
                type=interactions.OptionType.STRING,
                required=True,
            ),
        ],
    )
    async def getflight(self, ctx: interactions.CommandContext, callsign: str):

        url = f"https://aerodatabox.p.rapidapi.com/flights/callsign/{callsign}"

        querystring = {"withAircraftImage":"true","withLocation":"false"}

        headers = {
            "X-RapidAPI-Key": os.environ.get("KEY"),
            "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            api_response = response.json()
        except json.decoder.JSONDecodeError as err:
            logger.error(err)
            await ctx.send("Callsign not found")
            return

        for flight in range(len(api_response)):
            if (api_response[flight]['departure']['airport']['name'] is not None):

                image_url = api_response[flight]['aircraft']['image']['url']
                author_url = f"https://www.flightradar24.com/data/flights/{api_response[flight]['number'].replace(' ', '')}"
                
                embed = interactions.Embed(
                    title=f"Showing info for {api_response[flight]['callSign']}",
                    description=f"Operated by: {api_response[flight]['airline']['name']}", 
                    color=0x04a9a6,
                    footer = interactions.EmbedFooter(text=f"Last Updated: {api_response[flight]['lastUpdatedUtc']}"),
                    thumbnail = interactions.EmbedImageStruct(url="https://imgur.com/YqojWNd.png"),
                    image = interactions.EmbedImageStruct(url=f"{image_url}"),
                    author = interactions.EmbedAuthor(name="Click for Flight History", url=author_url, icon_url="https://is5-ssl.mzstatic.com/image/thumb/Purple128/v4/79/72/9a/79729a6b-2043-3317-95e9-3e877ed41086/source/512x512bb.jpg"),
                    fields = [
                        interactions.EmbedField(name="Departed From:", value=f"{api_response[flight]['departure']['airport']['shortName']}", inline=True),
                        interactions.EmbedField(name="Departed At (UTC):", value=f"<t:{get_unix_time(api_response[flight]['departure']['actualTimeUtc'])}:F>", inline=True),
                        interactions.EmbedField(name="Arriving To:", value=f"{api_response[flight]['arrival']['airport']['shortName']}", inline=False),
                        interactions.EmbedField(name="Arriving At (UTC):", value=f"<t:{get_unix_time(api_response[flight]['arrival']['scheduledTimeUtc'])}:F>", inline=True)
                    ],
                    )
                await ctx.send(embeds=[embed])



def setup(client: interactions.Client):
    GetFlight(client)