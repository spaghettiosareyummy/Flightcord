import os
import interactions
from src.config import DEBUG
from src import logutil
import requests
from dotenv import load_dotenv
import json
from datetime import datetime
import pymongo
import asyncio
from interactions.ext.wait_for import setup
from src.aerodatabox import AeroDataBox as adb, accurate_utc_conv, vague_utc_conv

logger = logutil.init_logger(os.path.basename(__file__))
load_dotenv()

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("DB_URI"))
# get the database
database = pymongo_client.FlightDB
collection = database.FlightSearchHist

# TODO:
# Create a page for Aircraft Info
# Create a page for Flight History??? might be unable
# Create a page for DEPARTURE and ARRIVAL information


class GetFlight(interactions.Extension):
    def __init__(self, client: interactions.Client):

        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    # user = users.find_one({"user_id": int(self.user_id)})

    @interactions.extension_command(
        name="getflight",
        description="search for a live flight",
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

        flight = adb.get_nearest(
            flight_number=flightnumber,
            callsign=callsign,
            reg=reg,
            icao=icao24,
        )
        try:
            aircraft = adb.get_aircraft(reg=f"{flight[0]['aircraft']['reg']}")
        except TypeError as err:
            logger.error(err)
            aircraft = False
        # else:
        #     aircraft = False
        if flight is None:
            await ctx.send(
                "This flight has already occured or is not in the database. Please try again with a different flight",
                ephemeral=True,
            )
        elif flight is False:
            await ctx.send(
                "There was an issue with collecting the flight data. This is most likely an internal error and not an error with your query",
                ephemeral=True,
            )
        elif aircraft is False:
            await ctx.send(
                "There was an issue with collecting the aircraft data. This is most likely an internal error and not an error with your query",
                ephemeral=True,
            )

        else:
            pages = [
                interactions.Embed(
                    title=flight[4]["title"],
                    description=f"Operated by: {flight[0]['airline']['name']}",
                    color=0x04A9A6,
                    footer=interactions.EmbedFooter(
                        text="Note: Image may not represent actual flight. This message will explode in 3 minutes"
                    ),
                    thumbnail=interactions.EmbedImageStruct(
                        url="https://imgur.com/YqojWNd.png"
                    ),
                    image=interactions.EmbedImageStruct(url=flight[1]["image_url"]),
                    author=interactions.EmbedAuthor(
                        name="Click for Flight History",
                        url=flight[5]["author_url"],
                    ),
                    fields=[
                        interactions.EmbedField(
                            name="Status",
                            value=flight[0]["status"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Codeshare Status",
                            value=flight[0]["codeshareStatus"].replace("Is", ""),
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Departure Airport",
                            value=flight[0]["departure"]["airport"]["name"],
                            inline=False,
                        ),
                        interactions.EmbedField(
                            name="Departure Time(UTC)",
                            value=flight[2]["depart_time"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Arrival Airport",
                            value=flight[0]["arrival"]["airport"]["name"],
                            inline=False,
                        ),
                        interactions.EmbedField(
                            name="Arrival Time(UTC)",
                            value=flight[3]["arrive_time"],
                            inline=True,
                        ),
                    ],
                ),
                interactions.Embed(
                    title="Aircraft Information",
                    description=f"Registration: {flight[0]['aircraft']['reg']}",
                    color=0x04A9A6,
                    footer=interactions.EmbedFooter(
                        text="Note: Image may not represent exact aircraft. This message will explode in 3 minutes"
                    ),
                    image=interactions.EmbedImageStruct(url=aircraft[2]["image"]),
                    author=interactions.EmbedAuthor(
                        name="Click for Flight History",
                        url=flight[5]["author_url"],
                    ),
                    fields=[
                        interactions.EmbedField(
                            name="Aircraft Type",
                            value=aircraft[0]["typeName"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Aircraft ICAO",
                            value=aircraft[0]["icaoCode"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Aircraft IATA",
                            value=aircraft[0]["iataCodeShort"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Rollout Date",
                            value=f"<t:{int(datetime.timestamp(datetime.fromisoformat(aircraft[0]['rolloutDate'])))}:d>",
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="First Flight",
                            value=f"<t:{int(datetime.timestamp(datetime.fromisoformat(aircraft[0]['firstFlightDate'])))}:d>",
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Aircraft Age",
                            value=f"{aircraft[0]['ageYears']} Years",
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="# of Seats",
                            value=aircraft[1]["num_seats"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="# of Engines",
                            value=aircraft[0]["numEngines"],
                            inline=True,
                        ),
                        interactions.EmbedField(
                            name="Engine Type",
                            value=aircraft[0]["engineType"],
                            inline=True,
                        ),
                    ],
                ),
            ]

            buttons = [
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Flight Info",
                    custom_id="flight_info",
                    emoji=interactions.Emoji(name="🎫"),
                    disabled=True,
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Aircraft Info",
                    custom_id="aircraft_info",
                    emoji=interactions.Emoji(name="✈️"),
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Departure Info",
                    custom_id="departure_info",
                    emoji=interactions.Emoji(name="🛫"),
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="Arrival Info",
                    custom_id="arrival_info",
                    emoji=interactions.Emoji(name="🛬"),
                ),
            ]

            flightem = await ctx.send(embeds=pages[0], components=buttons)
            page = "flight_info"

            async def check(button_ctx):
                if int(button_ctx.author.id) == int(ctx.author.id):
                    return True
                await ctx.send("You are not the author of this message!", hidden=True)
                return False

            while True:
                try:
                    button_ctx: interactions.ComponentContext = (
                        await self.client.wait_for_component(
                            components=buttons, check=check, timeout=180
                        )
                    )
                    await button_ctx.defer(edit_origin=True)

                    if button_ctx.custom_id == "flight_info":
                        if page == "aircraft_info":
                            page = "flight_info"
                            buttons[0].disabled = True
                            buttons[1].disabled = False

                            await button_ctx.edit(embeds=pages[0], components=buttons)

                    elif button_ctx.custom_id == "aircraft_info":
                        if page == "flight_info":
                            page = "aircraft_info"
                            buttons[0].disabled = False
                            buttons[1].disabled = True

                            await button_ctx.edit(embeds=pages[1], components=buttons)
                    elif button_ctx.custom_id == "departure_info":
                        if page == "flight_info":
                            page = "departure_info"
                            buttons[0].disabled = False
                            buttons[2].disabled = True

                            await button_ctx.edit(embeds=pages[2], components=buttons)
                    elif button_ctx.custom_id == "arrival_info":
                        if page == "flight_info":
                            page = "arrival_info"
                            buttons[0].disabled = False
                            buttons[3].disabled = True

                            await button_ctx.edit(embeds=pages[3], components=buttons)

                except asyncio.TimeoutError:
                    buttons[0].disabled = True
                    buttons[1].disabled = True
                    await flightem.edit(components=buttons)
                    break
                except interactions.api.error.LibraryException:
                    break

            previous = collection.find_one({"user_id": int(ctx.author.id)})
            if previous is None:
                """If the user does not already have a document in the database, create a new one"""
                newentry = {
                    "user_id": int(ctx.author.id),
                    "searches": [
                        {
                            "flightnumber": flight[0]["number"],
                            "reg": flight[0]["aircraft"]["reg"],
                            "time": str(accurate_utc_conv(datetime.now())),
                            "message_id": int(ctx.message.id),
                            "channel_id": int(ctx.channel.id),
                            "guild_id": int(ctx.guild.id),
                        }
                    ],
                }
                collection.insert_one(newentry)
                if DEBUG == True:
                    print("Updated Document")
            else:
                """If the user already has a document in the database, update it."""
                collection.update_one(
                    {"user_id": int(ctx.author.id)},
                    {
                        "$push": {
                            "searches": {
                                "flightnumber": flight[0]["number"],
                                "reg": flight[0]["aircraft"]["reg"],
                                "time": str(accurate_utc_conv(datetime.now())),
                                "message_id": int(ctx.message.id),
                                "channel_id": int(ctx.channel.id),
                                "guild_id": int(ctx.guild.id),
                            }
                        }
                    },
                )
                if DEBUG == True:
                    print("Updated Document")


def setup(client: interactions.Client):
    GetFlight(client)
