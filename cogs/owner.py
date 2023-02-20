from discord.ext import commands
import discord
import sys, traceback


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hidden means it won't show up on the default help.
    @commands.hybrid_command(name="load", hidden=True)
    @commands.is_owner()
    async def load_extension(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    @commands.hybrid_command(name="unload", hidden=True)
    @commands.is_owner()
    async def unload_extension(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    @commands.hybrid_command(name="reload", hidden=True)
    @commands.is_owner()
    async def reload_extension(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            #self.bot.unload_extension(cog)
            #self.bot.load_extension(cog)
            await self.bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
            traceback.print_exc(file=sys.stdout)
        else:
            await ctx.send("**`ODAYAKAJANAI`**")

    def cog_unload(self):
        pass

    #bans a user with a reason
    @commands.hybrid_command(hidden=True)
    @commands.has_any_role("S4","Class Admin")
    async def ban (self, ctx, member:discord.User=None, reason=None):
        if member == None or member == ctx.message.author:
            await ctx.channel.send("You cannot ban yourself")
            return
        if reason == None:
            reason = "For being a jerk!"
        #message = f"You have been banned from {ctx.guild.name} for {reason}"
        #await member.send(message)
        await ctx.guild.ban(member, reason=reason)
        await ctx.channel.send(f"{member} is banned!")

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))