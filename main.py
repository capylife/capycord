from disnake.ext import commands
from disnake import Intents

from capycord import CapyCog


bot = commands.Bot(
    test_guilds=[956885666334113822],
    sync_commands_debug=True,
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
