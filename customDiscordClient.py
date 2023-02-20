import discord
from discord import app_commands
from discord.ext import commands

import traceback
from os import listdir
from os.path import isfile, join

import aiohttp
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

MY_GUILD = discord.Object(id=344405367595466755)

class baseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.apscheduler = AsyncIOScheduler(event_loop=bot.loop, timezone=pytz.timezone("Asia/Tokyo"))
        bot.apscheduler.add_jobstore("sqlalchemy", alias="sqlite", url="sqlite:///scheduler.sqlite")
    
    @commands.hybrid_command(name="list_extension", hidden=True)
    @commands.is_owner()
    async def list_extension(self, ctx):
        await ctx.send([*self.bot.extensions])

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.bot.logger.error(f"Failed command: {ctx.message}")
        self.bot.logger.error(f"{ctx.message.content}")
        tb_str = "".join(traceback.format_exception(error, value=error, tb=error.__traceback__))
        self.bot.logger.error(tb_str)   

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Logged in as")
        self.bot.logger.info(self.bot.user.name)
        self.bot.logger.info(self.bot.user.id)
        if self.bot.first_startup is False:
            self.bot.clientsession = aiohttp.ClientSession()
            self.bot.apscheduler.start()
            self.bot.first_startup = True 

class customDiscordClient(commands.Bot):
    def __init__(self, logger, cogs_dir, **kwargs):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents, **kwargs)
        self.logger = logger
        self.cogs_dir = cogs_dir
        self.first_startup = False

        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
    
    async def on_message(self, message):
        if self.user in message.mentions:
            await message.channel.send(self.command_prefix + "help for help")
            return
        await self.process_commands(message)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        await self.add_cog(baseCog(self))
        for extension in [
            f.replace(".py", "") for f in listdir(self.cogs_dir) if isfile(join(self.cogs_dir, f))
        ]:
            try:
                await self.load_extension(self.cogs_dir + "." + extension)
                self.logger.info(f"Loaded cogs {self.cogs_dir}.{extension}")
            except (discord.ClientException, ModuleNotFoundError) as e:
                self.logger.exception(f"Failed to load extension {extension}.")
            self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
