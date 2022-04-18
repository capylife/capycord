import disnake
import logging
import asyncio

from disnake.ext import commands, tasks
from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient
from sys import stdout
from json import JSONDecodeError

from .env import (
    CHECK_DELAY, MONGO_HOST, MONGO_PORT, MONGO_DB,
    CAPY_API_LINK, CAPY_LIFE_LINK, INVITE_LINK
)


logger = logging.getLogger("capycord")
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(stdout)
logger.addHandler(consoleHandler)


class CapyCog(commands.Cog):
    def __init__(self, bot: disnake.Client):
        self.bot = bot

    async def cog_load(self) -> None:
        self.__http = ClientSession()
        self.__mongo = AsyncIOMotorClient(
            MONGO_HOST, MONGO_PORT
        )
        self.__collection = self.__mongo[MONGO_DB]

        self.check_capy.start()
        return await super().cog_load()

    def cog_unload(self) -> None:
        self.check_capy.cancel()

        self.bot.loop.create_task(
            self.__http.close()
        )

        return super().cog_unload()

    async def __send_capy(self, guild_id: int, channel_id: int,
                          name: str, image: str, capy_id: str) -> None:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            await self.__collection.channel.delete_many({
                "guild_id": guild_id
            })
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            await self.__collection.channel.delete_many({
                "guild_id": guild_id
            })
            return

        if not isinstance(channel, disnake.TextChannel):
            return

        embed = disnake.Embed(
            title=f"Meet {name}!",
            url=CAPY_LIFE_LINK,
            color=0x332525
        )
        embed.set_image(image)

        try:
            await channel.send(embed=embed)
        except Exception:
            pass

        await self.__collection.channel.update_one({
            "guild_id": guild_id
        }, {"$set": {"last_capy_id": capy_id}})

    @tasks.loop(seconds=CHECK_DELAY)
    async def check_capy(self) -> None:
        async with self.__http.get(CAPY_API_LINK) as resp:
            if resp.status != 200:
                logger.warn((
                    f"HTTP Request to \"{CAPY_API_LINK}\""
                    f" gave status code {resp.status}"
                ))
                return

            try:
                json = await resp.json()
            except JSONDecodeError as error:
                logger.warn(error)
                return

            query = {"last_capy_id": {
                "$ne": json["_id"]
            }}
            async for record in self.__collection.channel.find(query):
                asyncio.create_task(
                    self.__send_capy(
                        record["guild_id"],
                        record["channel_id"],
                        json["name"],
                        json["image"],
                        json["_id"]
                    )
                )

    @check_capy.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(
        description="Interact with capy bot"
    )
    async def capy(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    @capy.sub_command(
        description="Submit a capybara!",
    )
    async def submit(self,
                     inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            f"You can submit capybaras at <{CAPY_LIFE_LINK}>",
            ephemeral=True
        )

    @capy.sub_command(
        description="Invite Capy.life!",
    )
    async def invite(self,
                     inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            f"You can invite this bot with <{INVITE_LINK}>",
            ephemeral=True
        )

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
                "Must be a channel within the guild",
                ephemeral=True
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
        ), ephemeral=True)

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
                "Must be a channel within the guild",
                ephemeral=True
            )
            return

        if await self.__collection.channel.count_documents({
            "guild_id": inter.guild_id,
            "channel_id": channel.id
        }) == 0:
            await inter.response.send_message((
                f"{channel.mention} isn't set to "
                "receive any capybaras currently."
            ), ephemeral=True)
            return

        await self.__collection.channel.delete_many({
            "guild_id": inter.guild_id
        })

        await inter.response.send_message((
            f"{channel.mention} will no longer "
            "receive daily capybaras."
        ), ephemeral=True)
