from discord.ext import commands
#import sys, traceback
from io import BytesIO
import discord
from PIL import Image
#import asyncio
#import aiohttp
#import re
from discord.ext.commands import DefaultHelpCommand
import itertools
import concurrent.futures
from datetime import datetime, timezone
#from collections import Counter
import json
#import typing
#import copy
import glob
import random

class HelpCommandWithSubcommands(DefaultHelpCommand):

    def __init__(self):
        attrs = {'aliases': ['admin_help']}
        super().__init__(command_attrs=attrs)

    async def prepare_help_command(self, ctx, command):
        await super().prepare_help_command(ctx, command)
        if ctx.invoked_with == 'admin_help' and ctx.message.author.id == ctx.bot.owner_id: 
            self.show_hidden = True
            self.verify_checks = False
        else:
            self.show_hidden = False
            self.verify_checks = True

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Indents a list of commands after the specified heading.
        The formatting is added to the :attr:`paginator`.
        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.
        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        heading: :class:`str`
            The heading to add to the output. This is only added
            if the list of commands is greater than 0.
        max_size: Optional[:class:`int`]
            The max size to use for the gap between indents.
            If unspecified, calls :meth:`get_max_size` on the
            commands parameter.
        """

        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.qualified_name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(self.indent * ' ', name, command.short_doc, width=width)
            self.paginator.add_line(self.shorten_text(entry))

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category}:'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(set(bot.walk_commands()), sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.qualified_name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

class MiscCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = HelpCommandWithSubcommands()
        bot.help_command.cog = self
        #self.bot.thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        try:
            with open('emoji_counter.json','r') as fp:
                self.bot.all_emoji_counter = json.load(fp)
        except:
            self.bot.all_emoji_counter = dict()
        #self.bot.apscheduler.add_job(self.emoji_counter_all_channel_update, trigger="cron",minute="0",hour="1",replace_existing=True,id="emoji_counter_all_channel_update", jobstore="default")
        self.bot.apscheduler.add_job(self.idol_change_update, trigger="cron",minute="0",hour="*",replace_existing=True,id="idol_change_update", jobstore="default")

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.Cog.listener()
    async def on_message(self, message):
       if message.channel.id == 579657195780571137:
           await self.bot.get_channel(326116971504467969).send(message.content)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
       if before.author.bot:
           return
       if before.guild.id != 326048564965015552:
           return
       if before.content == after.content:
           return
       logging_channel = self.bot.get_channel(457750402448752650)
       embed = discord.Embed(title="Edited Message")
       embed.set_author(name=str(before.author),icon_url=str(before.author.avatar_url))
       embed.timestamp = datetime.now(timezone.utc)
       if before.content :
           embed.add_field(name="Before", value=before.content, inline=False)
       if after.content :
           embed.add_field(name="After", value=after.content, inline=False)
       embed.add_field(name="Message Information", value="User " + before.author.mention + " in " + before.channel.mention, inline=False)
       embed.add_field(name="Message URL", value=before.jump_url, inline=False)
       message = await logging_channel.send(embed=embed)
       await message.delete(delay=36000)

    @commands.command()
    async def image_echo(self, ctx):
        if len(ctx.message.attachments) > 0 :
            for attachment in ctx.message.attachments  : 
                file_object = BytesIO()
                await attachment.save(file_object)
                filename = attachment.filename
                discord_file = discord.File(file_object, filename)
                await ctx.send(file=discord_file)

    @commands.command()
    async def image_echo_resize(self, ctx):
        if len(ctx.message.attachments) > 0 :
            for attachment in ctx.message.attachments  :
                file_object = BytesIO()
                await attachment.save(file_object)
                size = attachment.size 
                filename = attachment.filename
                if filename.casefold().endswith("jpg") or filename.casefold().endswith("jpeg"):
                    format = "JPEG"
                elif filename.casefold().endswith("png"):
                    format = "PNG"
                elif filename.casefold().endswith("gif"):
                    format = "GIF"
                image = Image.open(file_object)
                width, height = image.size
                resized_image = image.resize((int(width*2),int(height*2)), Image.LANCZOS)
                new_width, new_height = resized_image.size
                file_object2 = BytesIO()
                resized_image.save(file_object2, format, optimize=True)
                new_size = file_object2.tell()
                file_object2.seek(0)
                discord_file = discord.File(file_object2, filename)
                embed = discord.Embed(title="Image Info")
                embed.add_field(name="Filename", value=filename, inline=False)
                embed.add_field(name="Original Size", value=str(size))
                embed.add_field(name="Image Dimensions", value=f"{str(width)}x{str(height)}")
                embed.add_field(name="New Size", value=str(new_size))
                embed.add_field(name="New Image Dimensions", value=f"{str(new_width)}x{str(new_height)}")
                await ctx.send(embed=embed)
                await ctx.send(file=discord_file)

    @commands.command()
    async def bigemoji(self, ctx, emoji : discord.PartialEmoji ):
        file_object = BytesIO()
        await emoji.save(file_object)
        image = Image.open(file_object)
        width, height = image.size
        resized_image = image.resize((int(width*4),int(height*4)), Image.LANCZOS)
        file_object2 = BytesIO()
        resized_image.save(file_object2, "PNG", optimize=True)
        file_object2.seek(0)
        discord_file = discord.File(file_object2, emoji.name+".png")
        await ctx.send(file=discord_file)

    @bigemoji.error 
    async def bigemoji_error_handler(self, ctx, error):
        await ctx.send("Need valid Discord Custom Emoji")

    @commands.command()
    async def bigemoji_orig(self, ctx, emoji : discord.PartialEmoji ):
        embed = discord.Embed(title="Click for image link", url=str(emoji.url))
        embed.set_image(url=str(emoji.url))
        await ctx.send(embed=embed)

    @bigemoji_orig.error
    async def bigemoji_orig_error_handler(self, ctx, error):
        await ctx.send("Need valid Discord Custom Emoji")

    """

    @commands.command(hidden=True)
    @commands.is_owner()
    async def read_message(self, ctx, channel : discord.TextChannel ):
        start_time = datetime.now()
        emoji_counter = Counter()
        async for message in channel.history(limit=None, oldest_first=False):
            message_content=message.content
            emoji_list = list(set(re.findall(r'<:.*?:.*?>', message_content)))
            emoji_counter += Counter(emoji_list)
        end_time = datetime.now()
        await ctx.send(f"{channel.mention} processed in {str(end_time-start_time)}")
        await ctx.send(str(emoji_counter.most_common(30)))

    async def emoji_counter_all_channel_update(self):
        await self.emoji_counter_function(None)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_all_channel(self, ctx):
        await self.emoji_counter_function(ctx)

    async def emoji_counter_function(self, ctx):
        if ctx is None:
            guild_id = "326048564965015552"
        else:
            guild_id = str(ctx.guild.id)
        guild = self.bot.get_guild(int(guild_id))
        channel_list = [ channel for channel in guild.text_channels if channel.category_id not in [360581693549182986,406241715712950272]]
        server_emoji_list = [ str(emoji.id) for emoji in guild.emojis ]
        all_start_time = datetime.now()
        all_emoji_counter = Counter()
        local_timezone = datetime.now().astimezone().tzinfo
        for channel in channel_list:
            channel_id = str(channel.id)
            self.emoji_counter_channel = channel
            start_time = datetime.now()
            if guild_id not in self.bot.all_emoji_counter :
                self.bot.all_emoji_counter[guild_id] = dict()
            if guild_id in self.bot.all_emoji_counter :
                if channel_id not in self.bot.all_emoji_counter[guild_id]:
                    self.bot.all_emoji_counter[guild_id][channel_id] = dict()
                    self.bot.all_emoji_counter[guild_id][channel_id]["count"] = Counter()
                if "user" not in self.bot.all_emoji_counter[guild_id]:
                    self.bot.all_emoji_counter[guild_id]["user"] = dict()
            if "after_timestamp" in self.bot.all_emoji_counter[guild_id][channel_id]:
                after = datetime.fromtimestamp(self.bot.all_emoji_counter[guild_id][channel_id]["after_timestamp"], tz=timezone.utc).replace(tzinfo=None)
            else:
                after = None
            emoji_counter = Counter()
            user_emoji_counter = dict()
            to_be_saved_after = None
            single_latest_message = await channel.history(limit=1).flatten()
            if len(single_latest_message) > 0:
                to_be_saved_after = single_latest_message[0].created_at.replace(tzinfo=timezone.utc).timestamp()
            async for message in channel.history(limit=None, oldest_first=False, after=after):
                message_content=message.content
                message_user_id=str(message.author.id)
                self.emoji_counter_message = message
                if message.author.bot :
                    continue
                emoji_list = [ emoji for emoji in set(re.findall(r'<.*?:.*?:(.*?)>', message_content)) if emoji in server_emoji_list ]
                if message_user_id not in user_emoji_counter :
                    user_emoji_counter[message_user_id] = Counter()
                emoji_counter += Counter(emoji_list)
                user_emoji_counter[message_user_id] += Counter(emoji_list)
            end_time = datetime.now()
            if to_be_saved_after:
                self.bot.all_emoji_counter[guild_id][channel_id]["after_timestamp"] = to_be_saved_after
            self.bot.all_emoji_counter[guild_id][channel_id]["count"] = Counter(self.bot.all_emoji_counter[guild_id][channel_id]["count"]) + emoji_counter
            for key, value in user_emoji_counter.items():
                if key not in self.bot.all_emoji_counter[guild_id]["user"]:
                    self.bot.all_emoji_counter[guild_id]["user"][key] = Counter()
                self.bot.all_emoji_counter[guild_id]["user"][key] = Counter(self.bot.all_emoji_counter[guild_id]["user"][key]) + value
            if ctx is not None:
                await ctx.author.send(f"{ctx.author.mention} {channel.mention} processed in {str(end_time-start_time)}")
                await ctx.author.send(str(emoji_counter.most_common(30)))
        all_end_time = datetime.now()
        self.bot.all_emoji_counter[guild_id]["all_channel"] = dict()
        self.bot.all_emoji_counter[guild_id]["all_channel"]["count"] = Counter()
        self.bot.all_emoji_counter[guild_id]["all_channel"]["updated_time"] = all_start_time.timestamp()
        for channel in channel_list:
            self.bot.all_emoji_counter[guild_id]["all_channel"]["count"] += self.bot.all_emoji_counter[guild_id][str(channel.id)]["count"]
        if ctx is not None:
            await ctx.send(f"{ctx.author.mention} All channels processed in {str(all_end_time-all_start_time)}")
            await ctx.send(str(self.bot.all_emoji_counter[guild_id]["all_channel"]["count"].most_common(30)))
        with open('emoji_counter.json','w+') as fp:
            json.dump(self.bot.all_emoji_counter, fp)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_all_channel_status(self, ctx):
        await ctx.send(f"{self.emoji_counter_channel.mention} {str(self.emoji_counter_message.created_at)}")

    @commands.command()
    async def emoji_counter_show(self, ctx, input : typing.Union[discord.TextChannel,discord.Member,discord.Emoji] = None):
        channel = None 
        member = None
        emoji = None
        if isinstance (input, discord.TextChannel):
            channel = input
        elif isinstance (input, discord.Member):
            member = input 
        elif isinstance (input, discord.Emoji):
            emoji = input
        guild_id = str(ctx.guild.id)
        local_timezone = datetime.now().astimezone().tzinfo
        emoji_counter_updated_time = datetime.fromtimestamp(self.bot.all_emoji_counter[guild_id]["all_channel"]["updated_time"], tz=local_timezone)
        embed = discord.Embed(title="Emoji counter", timestamp=emoji_counter_updated_time)
        embed.set_footer(text="Last updated")
        if channel is None and member is None and emoji is None:
            emoji_counter_sorted = Counter(self.bot.all_emoji_counter[guild_id]["all_channel"]["count"]).most_common()
            embed.add_field(name="Channel",value="All channels", inline=False)
        elif channel is not None:
            if channel.category_id in [360581693549182986,406241715712950272]:
                return
            emoji_counter_sorted = Counter(self.bot.all_emoji_counter[guild_id][str(channel.id)]["count"]).most_common()
            embed.add_field(name="Channel",value=channel.mention, inline=False)
        elif member is not None:
            emoji_counter_sorted = Counter(self.bot.all_emoji_counter[guild_id]["user"][str(member.id)]).most_common()
            embed.add_field(name="User",value=member.mention, inline=False)
        elif emoji is not None :
            emoji_id = str(emoji.id)
            emoji_counter_for_this_emoji = Counter()
            for key, value in self.bot.all_emoji_counter[guild_id]["user"].items() : 
                user = self.bot.get_user(int(key))
                if user is None:
                    continue
                try:
                    if value[emoji_id] == 0:
                        continue
                    emoji_counter_for_this_emoji[str(user)] = value[emoji_id]
                except:
                    pass
            emoji_counter_sorted = emoji_counter_for_this_emoji.most_common(40)
            embed.add_field(name="Emoji",value=str(emoji), inline=False)
        if emoji is None :
            emoji_counter_sorted_2 = copy.deepcopy(emoji_counter_sorted)
            for count, item in reversed(list(enumerate(emoji_counter_sorted_2))):
                emoji_to_be_deleted = self.bot.get_emoji(int(item[0]))
                if emoji_to_be_deleted is None:
                    emoji_counter_sorted.pop(count)
            embed.add_field(name="Total Count", value=str(sum(emoji_tuple[1] for emoji_tuple in emoji_counter_sorted)), inline=False)
            
        emoji_counter_chunks = list(self.chunks(emoji_counter_sorted, 21))
        #Embed might get too long, splitting the embed
        emoji_counter_chunks_split = self.chunks(emoji_counter_chunks, 6)
        embed_list = list()
        for emoji_counter_chunks in emoji_counter_chunks_split:
            embed_copy = copy.deepcopy(embed)
            for chunk in emoji_counter_chunks:
                try:
                    if emoji is None:
                        emoji_counter_string = "\n".join([ str(self.bot.get_emoji(int(emoji_tuple[0]))) +" "+str(emoji_tuple[1]) for emoji_tuple in chunk ])
                    else:
                        emoji_counter_string = "\n".join([ str(emoji_tuple[0])+" **"+str(emoji_tuple[1])+"**" for emoji_tuple in chunk ])
                    embed_copy.add_field(name="Count",value=emoji_counter_string)
                except:
                    pass
            embed_list.append(embed_copy)
        for embed_send in embed_list:
            await ctx.send(embed=embed_send)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def emoji_counter_dump(self, ctx):
        with open('emoji_counter.json','w+') as fp:
            json.dump(self.bot.all_emoji_counter, fp)  

    """

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i : i + n] 

    @commands.hybrid_command(hidden=True)
    @commands.is_owner()
    async def list_channel(self, ctx):
        channel_list = [ channel for channel in ctx.guild.text_channels if channel.category_id not in [360581693549182986,406241715712950272]]
        channel_mentions = [ channel.mention for channel in channel_list ]
        channel_mentions_string = ' '.join(channel_mentions)
        await ctx.send(channel_mentions_string)

    @commands.hybrid_command(hidden=True)
    @commands.is_owner()
    async def list_emoji(self, ctx):
        emoji_list = [ str(emoji) for emoji in ctx.guild.emojis ] 
        emoji_list_chunks = self.chunks(emoji_list, 30)
        for emoji_list in emoji_list_chunks:
            await ctx.send(" ".join(emoji_list))

    async def idol_change_update(self):
        await self.idol_change_function(None, None)

    @commands.hybrid_command(hidden=True)
    @commands.is_owner()
    @commands.cooldown(1,3600)
    async def idol_change(self, ctx, idol:str=None):
        await self.idol_change_function(ctx, idol)

    async def idol_change_function(self, ctx, idol):
        if ctx is None:
            guild_id = "326048564965015552"
            ctx = self.bot.get_channel(457801818144243716)
        else:
            guild_id = str(ctx.guild.id)
        guild = self.bot.get_guild(int(guild_id))
        idol_dict = {
            "aoi":"Aoi-Chan ⭐",
            "ako":"Ako-Nyan 😹",
            "yume":"Yume-Chan 🌈",
            "yurika":"Yurika-Sama 🦇",
            "mirai":"Mirai-Chan ⭐",
            "ema":"Ema-Chan ⭐",
            "mio":"Mio-Chan ⭐",
            "akari":"Akari-Chan ⭐",
            "rei":"Rei-Chan ⚔"
        } 
        if idol:
            if idol not in idol_dict:
                await ctx.send("Idol not found")
                return
        else:
            idol = random.choice(list(idol_dict.keys()))
        file_list = glob.glob("pfp/"+idol+"*")
        if len(file_list) == 0:
            await ctx.send("Idol not found")
            return
        else:
            filename = random.choice(file_list)
            with open(filename, "rb") as file:
                binarybytes = file.read()
            await ctx.send(f"Trying to change idol username and pfp to {idol}")
            await self.bot.user.edit(username=idol_dict[idol], avatar=binarybytes)
            await guild.me.edit(nick=idol_dict[idol])
            await ctx.send(filename)
            await ctx.send("Change complete")

async def setup(bot):
    #bot.remove_command("help")
    await bot.add_cog(MiscCog(bot))
