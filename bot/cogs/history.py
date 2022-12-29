import os
import interactions

from src.config import DEV_GUILD
from src import logutil
import pymongo
import asyncio
from interactions.ext.wait_for import setup

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("DB_URI"))
# get the database
database = pymongo_client.FlightDB

collection = database.FlightSearchHist

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
        # ability to search

        # pull the user's searches from DB
        user_searches = collection.find_one({"user_id": int(ctx.author.id)})
        if user_searches is not None:

            # only show 12 searches per page
            searches = user_searches["searches"]

            pages = []
            for i in range(0, len(searches), 12):
                embed = interactions.Embed(
                    title=f"Flight Search History for {ctx.author.name}",
                    description=f"Page {i+1} of {len(searches)//12+1}",
                    color=0x04A9A6,
                )
                embed.set_footer(text=f"")
                for search in searches[i : i + 12]:
                    message_link = f"https://discord.com/channels/{DEV_GUILD}/{search['channel_id']}/{search['message_id']}"
                    time = f"<t:{search['time']}:D>"
                    embed.add_field(
                        name=f"``{i+1}.``Flight {search['flightnumber']} on {time}",
                        value=f"[Go to Message]({message_link})",
                        inline=True,
                    )
                    i += 1

                buttons = [
                    interactions.Button(
                        style=interactions.ButtonStyle.PRIMARY,
                        emoji=interactions.Emoji(name="⏮️"),
                        custom_id="first",
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.PRIMARY,
                        emoji=interactions.Emoji(name="◀️"),
                        custom_id="prev",
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.PRIMARY,
                        emoji=interactions.Emoji(name="▶️"),
                        custom_id="next",
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.PRIMARY,
                        emoji=interactions.Emoji(name="⏭️"),
                        custom_id="last",
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.DANGER,
                        label="Delete History",
                        custom_id="delete",
                    ),
                ]

                pages.append(embed)
            current_index = 0
            await ctx.send(embeds=pages[0], components=buttons)

            async def check(button_ctx):
                if int(button_ctx.author.id) == int(ctx.author.id):
                    return True
                await ctx.send("You can't use this button!", ephemeral=True)
                return False

            while True:
                try:
                    button_ctx: interactions.ComponentContext = (
                        await self.client.wait_for_component(
                            components=buttons, check=check
                        )
                    )

                    if button_ctx.custom_id == "first":
                        current_index = 0
                        await button_ctx.defer(edit_origin=True)
                        await button_ctx.edit(embeds=pages[0])
                    elif button_ctx.custom_id == "prev":
                        if current_index > 0:
                            current_index -= 1
                            await button_ctx.defer(edit_origin=True)
                            await button_ctx.edit(embeds=pages[current_index])
                    elif button_ctx.custom_id == "next":
                        if current_index < len(pages):
                            current_index += 1
                            await button_ctx.defer(edit_origin=True)
                            await button_ctx.edit(embeds=pages[current_index])
                    elif button_ctx.custom_id == "last":
                        current_index = -1
                        await button_ctx.defer(edit_origin=True)
                        await button_ctx.edit(embeds=pages[-1])
                    elif button_ctx.custom_id == "delete":
                        collection.delete_many({"user_id": int(ctx.author.id)})
                        await button_ctx.defer(
                            edit_origin=True,
                            ephemeral=True,
                        )
                        await button_ctx.edit("Your history has been deleted!")

                except asyncio.TimeoutError:
                    await ctx.send("You took too long to respond!", ephemeral=True)

            # @interactions.extension_component("first")
            # async def first(self, ctx: interactions.ComponentContext):
            #     current_index = 0
            #     await ctx.edit_origin(embeds=pages[current_index])

            # @interactions.extension_component("prev")
            # async def prev(self, ctx: interactions.ComponentContext):
            #     if current_index > 0:
            #         print(current_index)
            #         current_index -= 1
            #         await ctx.edit_origin(embeds=pages[current_index])

            # @interactions.extension_component("next")
            # async def next(self, ctx: interactions.ComponentContext):
            #     if current_index < len(pages):
            #         current_index += 1
            #         await ctx.edit_origin(embeds=pages[current_index])

            # @interactions.extension_component("last")
            # async def last(self, ctx: interactions.ComponentContext):
            #     current_index = -1
            #     await ctx.edit_origin(embeds=pages[-1])

            # @interactions.extension_component("delete")
            # async def delete(self, ctx: interactions.ComponentContext):
            #     collection.delete_many({"user_id": int(ctx.author.id)})
            #     await ctx.edit_origin(
            #         "Your flight history has been deleted.", ephemeral=True
            #     )

        else:
            await ctx.send(
                "You have no flight history. Search for a flight to add to your history.",
                ephemeral=True,
            )


def setup(client: interactions.Client):
    FlightHistory(client)
