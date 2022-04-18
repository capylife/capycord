from disnake.ext import commands
from disnake import Intents

from capycord import CapyCog


bot = commands.Bot(
    intents=Intents(
        messages=True, guilds=True,
        typing=False, presences=False
    )
)
bot.add_cog(CapyCog(bot))


if __name__ == "__main__":
    import os
    bot.run(
        os.environ["BOT_TOKEN"],
    )
