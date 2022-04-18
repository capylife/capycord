import disnake

from disnake.ext import commands
from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient

from .env import (
    CHECK_DELAY, MONGO_HOST, MONGO_PORT, MONGO_DB,
    CAPY_API_LINK, CAPY_LIFE_LINK
)


class CapyCog(commands.Cog):
    def __init__(self, bot: disnake.Client):
        self.bot = bot

    async def cog_load(self) -> None:
        self.__http = ClientSession()
        self.__mongo = AsyncIOMotorClient(
            MONGO_HOST, MONGO_PORT
        )
        self.__collection = self.__mongo[MONGO_DB]

        return await super().cog_load()

    def cog_unload(self) -> None:
        self.bot.loop.create_task(
            self.__http.close()
        )
        return super().cog_unload()

    @commands.slash_command(
        description="Interact with capy bot"
    )
    async def capy(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    @commands.has_permissions(manage_guild=True)
    @capy.sub_command(
        description="Set channel to push Capybara's to daily",
        name="set"
    )
    async def set_channel(self, inter: disnake.ApplicationCommandInteraction,
                          channel: disnake.TextChannel) -> None:
        if not inter.guild_id:
            await inter.response.send_message("Must be set within guild.")
            return

        if inter.guild_id != channel.guild.id:
            await inter.response.send_message(
                "Must be a channel within the guild"
            )
            return

        await self.__collection.channel.update_one({
            "guild_id": inter.guild_id
        }, {"$set": {
            "channel_id": channel.id,
            "last_capy_id": None
        }}, upsert=True)

        await inter.response.send_message((
            f"A new capybara will be pushed to {channel.mention} "
            "daily!"
        ))

        # Add logic to post lastest capy.

    @commands.has_permissions(manage_guild=True)
    @capy.sub_command(
        description="Remove channel from receiving daily capybaras",
        name="remove"
    )
    async def remove_channel(self,
                             inter: disnake.ApplicationCommandInteraction,
                             channel: disnake.TextChannel) -> None:
        if not inter.guild_id:
            await inter.response.send_message("Must be set within guild.")
            return

        if inter.guild_id != channel.guild.id:
            await inter.response.send_message(
                "Must be a channel within the guild"
            )
            return

        if await self.__collection.channel.count_documents({
            "guild_id": inter.guild_id,
            "channel_id": channel.id
        }) == 0:
            await inter.response.send_message((
                f"{channel.mention} isn't set to "
                "receive any capybaras currently."
            ))
            return

        await self.__collection.channel.delete_many({
            "guild_id": inter.guild_id
        })

        await inter.response.send_message((
            f"{channel.mention} will no longer "
            "receive daily capybaras."
        ))
