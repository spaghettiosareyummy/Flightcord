import os
import interactions
from src.config import DEV_GUILD
from src import logutil
import requests
from dotenv import load_dotenv
import json
import datetime
import pymongo
from interactions.ext.paginator import Page, Paginator

logger = logutil.init_logger(os.path.basename(__file__))
load_dotenv()

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("DB_URI"))
# get the database
database = pymongo_client.FlightDB
collection = database.FlightSearchHist

# TODO
# Create a page for Aircraft Info
# Create a page for Flight History??? might be unable
# Create a page for DEPARTURE and ARRIVAL information


def get_unix_time(date: str):

    date_example = date.replace("Z", "").replace(" ", ", ")
    date_format = datetime.datetime.strptime(date_example, "%Y-%m-%d, %H:%M")
    unix_time = datetime.datetime.timestamp(date_format)
    return int(unix_time)


class GetFlight(interactions.Extension):
    def __init__(self, client: interactions.Client):

        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    # user = users.find_one({"user_id": int(self.user_id)})

    @interactions.extension_command(
        name="getflight",
        description="search for a flight",
    )
    async def getflight(self, ctx: interactions.CommandContext) -> None:
        """The Base Command for the getflight command"""

    @getflight.subcommand(name="searchwith", description="Search for a flight")
    @interactions.option(
        name="callsign",
        description="Search by callsign",
        type=interactions.OptionType.STRING,
        required=False,
    )
    @interactions.option(
        name="flightnumber",
        description="Search by flight number",
        type=interactions.OptionType.STRING,
        required=False,
    )
    @interactions.option(
        name="reg",
        description="Search by registration (Note: This may lead to being unable to find the flight)",
        type=interactions.OptionType.STRING,
        required=False,
    )
    @interactions.option(
        name="icao24",
        description="Search by ICAO24",
        type=interactions.OptionType.STRING,
        required=False,
    )
    async def searchwith(
        self,
        ctx: interactions.CommandContext,
        callsign: str = None,
        flightnumber: str = None,
        reg: str = None,
        icao24: str = None,
    ) -> None:
        """The Subcommand for the getflight command"""

        if callsign:
            url = f"https://aerodatabox.p.rapidapi.com/flights/callsign/{callsign}"
        elif flightnumber:
            url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flightnumber}"
        elif reg:
            url = f"https://aerodatabox.p.rapidapi.com/flights/reg/{reg}"
        elif icao24:
            url = f"https://aerodatabox.p.rapidapi.com/flights/icao24/{icao24}"

        querystring = {"withAircraftImage": "true", "withLocation": "false"}

        headers = {
            "X-RapidAPI-Key": os.environ.get("KEY"),
            "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
        }

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            api_response = response.json()
        except json.decoder.JSONDecodeError as err:
            logger.error(err)
            await ctx.send(
                "Flight not found, check your input and try again", ephemeral=True
            )
            return

        for flight in range(len(api_response)):
            try:
                if (
                    api_response[flight]["departure"]["airport"]["name"] is not None
                    and api_response[flight]["status"] != "Arrived"
                ):
                    try:
                        image_url = (
                            f"{api_response[flight]['aircraft']['image']['url']}"
                        )
                    except KeyError:
                        image_url = None

                    try:
                        depart_time = f"<t:{get_unix_time(api_response[flight]['departure']['actualTimeUtc'])}:f>"
                    except KeyError:
                        depart_time = f"<t:{get_unix_time(api_response[flight]['departure']['scheduledTimeUtc'])}:f>"

                    try:
                        arrive_time = f"<t:{get_unix_time(api_response[flight]['arrival']['scheduledTimeUtc'])}:f>"
                    except KeyError:
                        arrive_time = f"<t:{get_unix_time(api_response[flight]['arrival']['actualTimeUtc'])}:f>"

                    author_url = f"https://www.flightradar24.com/data/flights/{api_response[flight]['number'].replace(' ', '')}"
                    pages = [
                        Page(
                            embeds=interactions.Embed(
                                title=f"Flight Information for {api_response[flight]['callSign']}",
                                description=f"Operated by: {api_response[flight]['airline']['name']}",
                                color=0x04A9A6,
                                footer=interactions.EmbedFooter(
                                    text="Powered by Aerodatabox and Flightradar24"
                                ),
                                thumbnail=interactions.EmbedImageStruct(
                                    url="https://imgur.com/YqojWNd.png"
                                ),
                                image=interactions.EmbedImageStruct(url=image_url),
                                author=interactions.EmbedAuthor(
                                    name="Click for Flight History",
                                    url=author_url,
                                    icon_url="https://is5-ssl.mzstatic.com/image/thumb/Purple128/v4/79/72/9a/79729a6b-2043-3317-95e9-3e877ed41086/source/512x512bb.jpg",
                                ),
                                fields=[
                                    interactions.EmbedField(
                                        name="Departed From:",
                                        value=f"{api_response[flight]['departure']['airport']['name']}",
                                        inline=False,
                                    ),
                                    interactions.EmbedField(
                                        name="Departed At (UTC):",
                                        value=depart_time,
                                        inline=False,
                                    ),
                                    interactions.EmbedField(
                                        name="Arriving To:",
                                        value=f"{api_response[flight]['arrival']['airport']['name']}",
                                        inline=False,
                                    ),
                                    interactions.EmbedField(
                                        name="Arriving At (UTC):",
                                        value=arrive_time,
                                        inline=True,
                                    ),
                                ],
                            )
                        ),
                        Page(
                            embeds=interactions.Embed(
                                title=f"Aircraft Info for {api_response[flight]['aircraft']['reg']}"
                            )
                        ),  # TODO: Use a different API to get aircraft info
                        Page(
                            embeds=interactions.Embed(
                                title=f"Departure Info for {api_response[flight]['departure']['airport']['name']}"
                            )
                        ),
                        Page(
                            embeds=interactions.Embed(
                                title=f"Arrival Info for {api_response[flight]['arrival']['airport']['name']}"
                            )
                        ),  # Different API for these too
                    ]
                    p = Paginator(
                        client=self.client, ctx=ctx, use_buttons=False, pages=pages
                    )
                    await p.run()

                    previous = collection.find_one({"user_id": int(ctx.author.id)})
                    if previous is None:
                        """If the user does not already have a document in the database, create a new one"""
                        newentry = {
                            "user_id": int(ctx.author.id),
                            "searches": [
                                {
                                    "callsign": api_response[flight]["callSign"],
                                    "flightnumber": api_response[flight]["number"],
                                    "reg": api_response[flight]["aircraft"]["reg"],
                                }
                            ],
                        }
                        collection.insert_one(newentry)
                    else:
                        """If the user already has a document in the database, update it."""
                        collection.update_one(
                            {"user_id": int(ctx.author.id)},
                            {
                                "$push": {
                                    "searches": {
                                        "callsign": api_response[flight]["callSign"],
                                        "flightnumber": api_response[flight]["number"],
                                        "reg": api_response[flight]["aircraft"]["reg"],
                                    }
                                }
                            },
                        )

                else:
                    await ctx.send(
                        "This flight has already occured or is not in the database. Please try again with a different flight",
                        ephemeral=True,
                    )
            except KeyError as err:
                logger.error(err)
                await ctx.send(
                    "There was an issue with collecting the flight data. This is most likely an internal error and not an error with your query",
                    ephemeral=True,
                )
                return


def setup(client: interactions.Client):
    GetFlight(client)
