import os
import interactions

from src.config import DEV_GUILD
from src import logutil
import pymongo

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("DB_URI"))
# get the database
database = pymongo_client.FlightDB

collection = database.FlightSearchHist

# post = {"_id": 0, "user_id": 123456789, "searches": []}
# collection.insert_one(post)

# TODO
# Connect up the DB

logger = logutil.init_logger(os.path.basename(__file__))


class FlightHistory(interactions.Extension):
    def __init__(self, client: interactions.Client):
        self.client: interactions.Client = client
        logger.info(f"{__class__.__name__} cog registered")

    @interactions.extension_command(
        name="history",
        description="Get your flight history",
    )
    async def history(self, ctx: interactions.CommandContext):

        # TODO
        # ability to delete history
        # ability to filter history

        # pull the user's searches from DB
        user_searches = collection.find_one({"user_id": int(ctx.author.id)})
        searches = user_searches["searches"]

        embed = interactions.Embed(
            title=f"Flight Search History for {ctx.author.name}",
            description="Your flight history",
            color=0x04A9A6,
        )
        for search in searches:
            time = f"<t:{search['time']}:f>"
            embed.add_field(
                name=f"Flight {search['callsign']}",
                value=time,
                inline=False,
            )
        embed.set_footer(
            text="Flights take 10-30 seconds to register in flight history."
        )
        await ctx.send(embeds=embed)


def setup(client: interactions.Client):
    FlightHistory(client)
