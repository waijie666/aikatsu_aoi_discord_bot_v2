import discord
from discord.ext import commands
import random
import csv
from datetime import date, datetime, timedelta
import pytz
from collections import Counter
import asyncio
from os import listdir
from os.path import isfile, join
import concurrent.futures
import operator
import typing
from collections import defaultdict
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import boto3

class LString:
    def __init__(self):
        self._total = 0
        self._successors = defaultdict(int)

    def put(self, word):
        self._successors[word] += 1
        self._total += 1

    def get_random(self):
        ran = random.randint(0, self._total - 1)
        for key, value in self._successors.items():
            if ran < value:
                return key
            else:
                ran -= value

class AikatsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.airtime_datetime = None
        self.singing_already = False
        self.init_aikatsup()
        self.init_photokatsu()
        self.init_songs()
        self.init_aikatsu_idol()
        self.init_aikatsu_markov()
        try:
            self.init_boto3()
            self.init_aikatsu_screenshots_s3()
            #self.init_aikatsu_stars_screenshots()
            #self.init_aikatsu_screenshots()
            #self.init_aikatsu_friends_screenshots()
        except Exception as e:
            self.bot.logger.exception(e)
            self.bot.logger.error("Screenshot initialization failed. Screenshots may not work in this environment")
        self.bot.process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=3)

    def init_boto3(self):
        s3_endpoint_url = os.environ.get("s3_endpoint_url")
        s3_access_key = os.environ.get("s3_access_key")
        s3_secret_key = os.environ.get("s3_secret_key")

        self.s3_client = boto3.client(service_name="s3", endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)

    def init_aikatsu_screenshots_s3(self):
        self.aikatsu_screenshot_dict = {"multiplier":5, "title":"Aikatsu Screenshot"}
        self.aistars_screenshot_dict = {"multiplier":5, "title":"Aikatsu Stars Screenshot"}
        self.aifure_screenshot_dict = {"multiplier":5, "title":"Aikatsu Friends Screenshot"}
        
        with open("data/s3_aikatsu_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                filename_split = line.split("/")
                if len(filename_split) < 2:
                    continue
                episode_and_framenumber = filename_split[1].split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = line
                filename = filename_split[1]
                if filename_split[0] == "aikatsu_screenshot":
                    screenshot_dict = self.aikatsu_screenshot_dict
                elif filename_split[0] == "aikatsu_stars_screenshot":
                    screenshot_dict = self.aistars_screenshot_dict
                elif filename_split[0] == "aikatsu_friends_screenshot":
                    screenshot_dict = self.aifure_screenshot_dict
                if episode not in screenshot_dict:
                    screenshot_dict[episode] = list()
                screenshot_dict[episode].append({"full_filename":full_filename, "filename":filename, "frame_number": frame_number, "web_url": "https://images.dream-wonderland.com/" + full_filename})

        #self.bot.logger.info(str(self.aikatsu_screenshot_dict))
        #self.bot.logger.info(str(self.aistars_screenshot_dict))
        #self.bot.logger.info(str(self.aifure_screenshot_dict))

    def get_aikatsu_screenshot_from_s3(self, filename):
        file_object = BytesIO()
        self.s3_client.download_fileobj("images.dream-wonderland.com", filename, file_object)
        file_object.seek(0)
        return file_object    
 
    def init_aikatsu_stars_screenshots(self):
        self.aistars_screenshot_dict = {"multiplier":1, "title":"Aikatsu Stars Screenshot"}
        
        with open("aistars_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                episode_and_framenumber = line.split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = "/screenshots/aistars/" + line
                if episode not in self.aistars_screenshot_dict:
                    self.aistars_screenshot_dict[episode] = list()
                self.aistars_screenshot_dict[episode].append({"full_filename":full_filename, "filename":line, "frame_number": frame_number, "web_url": "https://dream-wonderland.com/images/aikatsu_stars/" + line})

    def init_aikatsu_screenshots(self):
        self.aikatsu_screenshot_dict = {"multiplier":5, "title":"Aikatsu Screenshot"}

        with open("aikatsu_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                episode_and_framenumber = line.split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = "/backup/aikatsu_screenshot/" + line
                if episode not in self.aikatsu_screenshot_dict:
                    self.aikatsu_screenshot_dict[episode] = list()
                self.aikatsu_screenshot_dict[episode].append({"full_filename":full_filename, "filename":line, "frame_number": frame_number, "web_url": "https://dream-wonderland.com/images/aikatsu/" + line})
    
    def init_aikatsu_friends_screenshots(self):
        self.aifure_screenshot_dict = {"multiplier":5, "title":"Aikatsu Friends Screenshot"}

        with open("aikatsu_friends_screenshot.txt","r") as f:
            fullstring = f.read()
            lines = fullstring.split("\n")
            for line in lines:
                episode_and_framenumber = line.split("screenshot")
                if len(episode_and_framenumber) < 2:
                    continue
                episode = str(int(episode_and_framenumber[0]))
                frame_number = int(episode_and_framenumber[1].split(".")[0])
                full_filename = "/backup/aifure_screenshot/" + line
                if episode not in self.aifure_screenshot_dict:
                    self.aifure_screenshot_dict[episode] = list()
                self.aifure_screenshot_dict[episode].append({"full_filename":full_filename, "filename":line, "frame_number": frame_number, "web_url": "https://dream-wonderland.com/images/aikatsu_friends/" + line})

    def init_aikatsu_markov(self):
        self.couple_words = defaultdict(LString)
        self.uppercase_words_set = set()
        for file in [ "data/aikatsu_og_subs.txt", "data/aikatsu_stars_subs.txt" , "data/aikatsu_friends_subs.txt" ] :
            with open(file, 'r') as f:
                contents = f.read()
                contents_list = contents.splitlines()
                for line in contents_list:
                    self.add_message(line)

    def add_message(self, message):
        #message = re.sub(r'\s[-\"]', '', message).strip()
        words_prefiltered = message.strip().split()
        #words = words_prefiltered
        words = list()
        for word in words_prefiltered:
            try:
                float(word)
            except:
                words.append(word)
        if len(words) < 2:
            return
        for i in range(2, len(words)):
            self.couple_words[(words[i - 2], words[i - 1])].put(words[i])
            if words[i - 2][0].isupper():
                self.uppercase_words_set.add((words[i - 2], words[i - 1]))
        self.couple_words[(words[-2], words[-1])].put("")
        if words[-2][0].isupper():
            self.uppercase_words_set.add((words[-2], words[-1]))

    def init_aikatsu_idol(self):
        with open("data/aikatsu_idol.csv", "r") as csvfile:
            csvfile.readline()
            fieldnames = ["birthday","name","blood","height","school","type","series"]
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            self.idol_dict_list = list(reader)
        self.bot.apscheduler.add_job(self.send_birthday_message, trigger="cron",minute="0",hour="0",replace_existing=True,id="birthday_post", jobstore="default")
        self.bot.apscheduler.add_job(self.change_client_presence, trigger="cron", minute="*/5", replace_existing=True,id="change_client_presence",jobstore="default")

    def init_songs(self):
        self.songs_dict = dict()
        songs_dir = "songs"
        for f in listdir(songs_dir):
            if isfile(join(songs_dir, f)) and "txt" in f:
                with open(join(songs_dir, f)) as songfile:
                    song_title = songfile.readline()
                    song_lyrics = songfile.read()
                    self.songs_dict[song_title] = song_lyrics

    def init_aikatsup(self):
        self.aikatsup_item_id = list()
        self.aikatsup_tags = list()
        self.cached_datetime = None

    def init_photokatsu(self):
        with open("data/photokatsu.csv", "r") as csvfile:
            fieldnames = [
                "rarity",
                "id",
                "name",
                "image_url",
                "appeal",
                "skill",
                "preawakened",
            ]
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            self.card_dict_list = list(reader)

        self.PR_dict_list = list()
        self.PRplus_dict_list = list()
        self.PRplus_preawakened_dict_list = list()
        self.SR_dict_list = list()
        self.SRplus_dict_list = list()
        self.SRplus_preawakened_dict_list = list()
        self.R_dict_list = list()
        self.Rplus_dict_list = list()
        self.N_dict_list = list()
        self.Nplus_dict_list = list()

        for card_dict in self.card_dict_list:
            if card_dict["rarity"] == "PR":
                self.PR_dict_list.append(card_dict)
            elif card_dict["rarity"] == "PR+" and card_dict["preawakened"] == "yes":
                self.PRplus_preawakened_dict_list.append(card_dict)
            elif card_dict["rarity"] == "PR+":
                self.PRplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR":
                self.SR_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR+" and card_dict["preawakened"] == "yes":
                self.SRplus_preawakened_dict_list.append(card_dict)
            elif card_dict["rarity"] == "SR+":
                self.SRplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "R":
                self.R_dict_list.append(card_dict)
            elif card_dict["rarity"] == "R+":
                self.Rplus_dict_list.append(card_dict)
            elif card_dict["rarity"] == "N":
                self.N_dict_list.append(card_dict)
            elif card_dict["rarity"] == "N+":
                self.Nplus_dict_list.append(card_dict)

    async def change_client_presence(self):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        today = current_time.date()
        current_year = today.year
        idol_dict_list = list(self.idol_dict_list)
        for idol_dict in idol_dict_list:
            birthday_current_year = datetime.strptime(str(current_year) + idol_dict["birthday"],"%Y%B %d").date()
            if birthday_current_year < today :
                idol_dict["next_birthday"] = birthday_current_year.replace(year=current_year+1)
            else:
                idol_dict["next_birthday"] = birthday_current_year

        sorted_idol_dict_list = sorted(idol_dict_list, key=operator.itemgetter("next_birthday"))
        filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if idol_dict["next_birthday"] == today ]

        if len(filtered_idol_dict_list) > 0:
            client_presence_choice = random.choice(filtered_idol_dict_list)['name'] +"'s birthday"
        else:
            client_presence_list = ["Aikatsu Friends", "Aikatsu Stars", "Aikatsu"]
            client_presence_choice = random.choice(client_presence_list)
        await self.bot.change_presence(activity=discord.Game(name=client_presence_choice))

    async def send_birthday_message(self):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        today = current_time.date()
        current_year = today.year

        for idol_dict in self.idol_dict_list:
            birthday_current_year = datetime.strptime(str(current_year) + idol_dict["birthday"],"%Y%B %d").date()
            if birthday_current_year < today :
                idol_dict["next_birthday"] = birthday_current_year.replace(year=current_year+1)
            else:
                idol_dict["next_birthday"] = birthday_current_year

        sorted_idol_dict_list = sorted(self.idol_dict_list, key=operator.itemgetter("next_birthday"))
        filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if idol_dict["next_birthday"] == today ]
        send_channel = self.bot.get_channel(326048564965015552)
        for idol_dict in filtered_idol_dict_list:
           await send_channel.send(f"Today **{idol_dict['birthday']}** is **{idol_dict['name']}**'s birthday :birthday: :birthday: :birthday:" )

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i : i + n]

    async def aikatsup_info_cache(self):
        if (
            self.cached_datetime is None
            or (self.cached_datetime + timedelta(hours=1)) < datetime.now()
        ):
            async with self.bot.clientsession.get(
                "http://aikatsup.com/api/v1/info"
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if "item_id" in data:
                        self.aikatsup_item_id = data["item_id"]
                    if "tags" in data:
                        self.aikatsup_tags = data["tags"]
                    if "all_items" in data:
                        self.aikatsup_all_items = data["all_items"]
                    if ("item_id" in data) and ("tags" in data):
                        self.cached_datetime = datetime.now()

    async def aikatsup_image_embed(self, ctx, dict, type="Image"):
        embed = discord.Embed(title=type)
        embed.set_image(url=dict["image"]["url"])
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        if "words" in dict:
            embed.add_field(name="Subs", value=dict["words"])
        if "tags" in dict:
            embed.add_field(name="Tags", value=dict["tags"])
        embed.set_footer(text="Provider: aikatsup.com")
        await ctx.send(embed=embed)

    @commands.hybrid_group(case_insensitive=True, fallback='get')
    async def aikatsup(self, ctx):
        if ctx.invoked_subcommand is None:
            subcommands_str_list = [ f"`{subcommands.name}`" for subcommands in ctx.command.walk_commands() ]
            await ctx.send("Invalid subcommands. Subcommands are " + " ".join(subcommands_str_list) )

    @aikatsup.command()
    async def info(self, ctx):
        await self.aikatsup_info_cache()
        embed = discord.Embed(title="Info")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Image Count", value=self.aikatsup_all_items, inline=False)
        long_tag_chunk = list()
        for index, tag in enumerate(self.aikatsup_tags):
            if len(tag) > 16:
                long_tag = self.aikatsup_tags.pop(index)
                long_tag_chunk.append(long_tag)
        tag_chunks = self.chunks(self.aikatsup_tags, 50)
        tag_chunks = list(tag_chunks)
        tag_chunks.append(long_tag_chunk)
        for chunk in tag_chunks:
            chunkstring = "\n".join(chunk)
            embed.add_field(name="Available Tags", value=chunkstring)
        embed.set_footer(text="Provider: aikatsup.com")
        await ctx.send(embed=embed)

    @aikatsup.command()
    async def subs(self, ctx, *, subtitle: str = ""):
        if subtitle == "":
            await ctx.send("No parameters entered")
            return
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"words": subtitle}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    total = len(data["item"])
                    post_no = random.randint(0, total - 1)
                    await self.aikatsup_image_embed(ctx, data["item"][post_no])
                else:
                    await ctx.send("見つからないよー＞＜")

    @aikatsup.command()
    async def tag(self, ctx, *, tagstr: str = ""):
        if tagstr == "":
            await ctx.send("No parameters entered")
            return
        await self.aikatsup_info_cache()
        if tagstr not in self.aikatsup_tags:
            await ctx.send("Tag does not exist")
            return
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"tags": tagstr}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    total = len(data["item"])
                    post_no = random.randint(0, total - 1)
                    await self.aikatsup_image_embed(ctx, data["item"][post_no])
                else:
                    await ctx.send("見つからないよー＞＜")

    @aikatsup.command()
    async def random(self, ctx):
        await self.aikatsup_info_cache()
        total = len(self.aikatsup_item_id)
        post_no = random.randint(0, total - 1)
        id = self.aikatsup_item_id[post_no]
        async with self.bot.clientsession.get(
            "http://aikatsup.com/api/v1/search?", params={"id": id}
        ) as r:
            if r.status == 200:
                data = await r.json()
                if "item" in data:
                    await self.aikatsup_image_embed(ctx, data["item"])
                else:
                    await ctx.channel.send("見つからないよー＞＜")

    async def photokatsu_image_embed(self, ctx, dict, total=None, title="Photokatsu"):
        embed = discord.Embed(title=title)
        embed.set_image(url=dict["image_url"])
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="ID", value=dict["id"])
        embed.add_field(name="Name", value=dict["name"])
        embed.add_field(name="Rarity", value=dict["rarity"])
        embed.add_field(name="Special Appeal", value=dict["appeal"])
        embed.add_field(name="Skill", value=dict["skill"])
        if total is not None:
            embed.add_field(name="Total search results", value=str(total))
        embed.set_footer(text="Provider: Aikatsu Wikia")
        await ctx.send(embed=embed)

    def pick_cards(self, gacha_rarity_list):
        card_list = list()
        for rarity in gacha_rarity_list:
            if rarity == "R":
                card_list.append(random.choice(self.R_dict_list))
            elif rarity == "SR":
                card_list.append(
                    random.choice(self.SR_dict_list + self.SRplus_preawakened_dict_list)
                )
            elif rarity == "PR":
                card_list.append(
                    random.choice(self.PR_dict_list + self.PRplus_preawakened_dict_list)
                )
        return card_list

    @commands.hybrid_group(case_insensitive=True, fallback='get')
    async def photokatsu(self, ctx):
        if ctx.invoked_subcommand is None:
            subcommands_str_list = [ f"`{subcommands.name}`" for subcommands in ctx.command.walk_commands() ]
            await ctx.send("Invalid subcommands. Subcommands are " + " ".join(subcommands_str_list) )

    @photokatsu.command(
        name="random",
        description="Search examples: !!!photokatsu random ichigo, !!!photokatsu random pr, !!!photokatsu random pr+",
    )
    async def photokatsu_random(self, ctx, *, search_string=None):
        if search_string == None:
            result_dict_list = self.card_dict_list[1:]
        else:
            rarity = None
            search_string_1 = None
            tokens = search_string.split(maxsplit=1)
            for rarity_test in ["PR", "PR+", "SR", "SR+", "R", "R+", "N", "N+"]:
                if tokens[0].casefold() == rarity_test.casefold():
                    rarity = rarity_test
                    break
            if rarity is not None and len(tokens) > 1:
                search_string_1 = tokens[1]
            elif rarity is None:
                search_string_1 = search_string

            if rarity is not None:
                if rarity == "PR":
                    search_dict_list = self.PR_dict_list
                elif rarity == "PR+":
                    search_dict_list = (
                        self.PRplus_dict_list + self.PRplus_preawakened_dict_list
                    )
                elif rarity == "SR":
                    search_dict_list = self.SR_dict_list
                elif rarity == "SR+":
                    search_dict_list = (
                        self.SRplus_dict_list + self.SRplus_preawakened_dict_list
                    )
                elif rarity == "R":
                    search_dict_list = self.R_dict_list
                elif rarity == "R+":
                    search_dict_list = self.Rplus_dict_list
                elif rarity == "N":
                    search_dict_list = self.N_dict_list
                elif rarity == "N+":
                    search_dict_list = self.Nplus_dict_list
                if search_string_1 is None:
                    result_dict_list = search_dict_list
                else:
                    result_dict_list = list()
                    for search_dict in search_dict_list:
                        if search_string_1.casefold() in search_dict["name"].casefold():
                            result_dict_list.append(search_dict)
            else:
                result_dict_list = list()
                for search_dict in self.card_dict_list[1:]:
                    if search_string_1.casefold() in search_dict["name"].casefold():
                        result_dict_list.append(search_dict)

        total = len(result_dict_list)
        if total == 0:
            await ctx.send("Results do not exist")
            return
        post_no = random.randint(0, total - 1)
        await self.photokatsu_image_embed(ctx, result_dict_list[post_no], total)

    @photokatsu.command(name="id")
    async def photokatsu_id(self, ctx, id: int):
        if id < 1 or id > len(self.card_dict_list) - 1:
            await ctx.send(
                f"ID Out of range. Please input 1-{str(len(self.card_dict_list)-1)}"
            )
        else:
            await self.photokatsu_image_embed(ctx, self.card_dict_list[id])

    @photokatsu.command(
        name="gacha",
        description="Default is eleven rolls. !!!photokatsu gacha one for single rolls.",
    )
    async def photokatsu_gacha(self, ctx, number: str = "eleven"):
        if number == "one" or number == "1":
            gacha_rarity_list = random.choices(["R", "SR", "PR"], [78, 20, 2])
        elif number == "eleven" or number == "11":
            gacha_rarity_list = random.choices(["R", "SR", "PR"], [78, 20, 2], k=10)
            gacha_rarity_list += random.choices(["SR", "PR"], [98, 2])
        else:
            return
        card_list = self.pick_cards(gacha_rarity_list)
        rarity_counter = Counter(gacha_rarity_list)
        embed = discord.Embed(
            title="Photokatsu Gacha Results", description="Rates: PR 2%, SR 20%, R 78%"
        )
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Counter", value=dict(rarity_counter))
        card_string_list = list()
        for card in card_list:
            if card["rarity"].startswith("PR"):
                card_string_list.append(
                    f'**{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}**'
                )
            else:
                card_string_list.append(
                    f'{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}'
                )
        embed.add_field(name="Card List", value="\n".join(card_string_list))
        if number == "one" or number == "1":
            embed.set_image(url=card_list[0]["image_url"])
            embed.add_field(name="ID", value=card_list[0]["id"])
            embed.add_field(name="Name", value=card_list[0]["name"])
            embed.add_field(name="Rarity", value=card_list[0]["rarity"])
            embed.add_field(name="Special Appeal", value=card_list[0]["appeal"])
            embed.add_field(name="Skill", value=card_list[0]["skill"])
        embed.set_footer(text="")
        await ctx.send(embed=embed)

    @staticmethod
    def gacha_until_PR_worker(N_rate, PR_rate):
        gacha_rarity_list_try = list()
        gacha_rarity_dict = {"PR":0,"SR":0,"R":0}
        while "PR" not in gacha_rarity_list_try:
            gacha_rarity_list_try = random.choices(
                ["R", "SR", "PR"], [N_rate, 20, PR_rate]
            )
            gacha_rarity_dict[gacha_rarity_list_try[0]] += 1
        return gacha_rarity_dict
    
    @photokatsu.command()
    async def gacha_until_pr(self, ctx, rates: float = 2.0):
        if rates > 78:
            rates = 78
        elif rates < 0.00001:
            rates = 0.00001
        N_rate = 80 - rates
        PR_rate = rates
        async with ctx.typing():
            gacha_rarity_dict = await self.bot.loop.run_in_executor(self.bot.process_executor, self.gacha_until_PR_worker , N_rate, PR_rate)
        card_list = self.pick_cards(["PR"])
        rarity_counter = gacha_rarity_dict
        star_used = 25
        if "SR" in gacha_rarity_dict:
            star_used = star_used + gacha_rarity_dict["SR"]*25
        if "R" in gacha_rarity_dict:
            star_used = star_used + gacha_rarity_dict["R"]*25

        embed = discord.Embed(
            title="Photokatsu Gacha Results",
            description=f"Rates: PR {PR_rate}%, SR 20%, R {N_rate}%",
        )
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Counter", value=dict(rarity_counter))
        embed.add_field(name="Stars Used", value=str(star_used)+":star:")
        card_string_list = list()
        for card in card_list:
            if card["rarity"].startswith("PR"):
                card_string_list.append(
                    f'**{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}**'
                )
            else:
                card_string_list.append(
                    f'{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}'
                )
        embed.add_field(name="Card List", value="\n".join(card_string_list))
        embed.set_image(url=card_list[0]["image_url"])
        embed.add_field(name="ID", value=card_list[0]["id"])
        embed.add_field(name="Name", value=card_list[0]["name"])
        embed.add_field(name="Rarity", value=card_list[0]["rarity"])
        embed.add_field(name="Special Appeal", value=card_list[0]["appeal"])
        embed.add_field(name="Skill", value=card_list[0]["skill"])
        embed.set_footer(text="")
        await ctx.send(embed=embed)

    @photokatsu.command()
    async def gacha_until(self, ctx, *, search_string):
        gacha_rarity_list_try = list()
        card_list = list()
        found = False
        gacha_rarity_dict = {"PR":0,"SR":0,"R":0} 
        search_count = 0
        while found is False:
            search_count += 1 
            gacha_rarity_list_try = random.choices(
                ["R", "SR", "PR"], [78, 20, 2]
            )
            gacha_rarity_dict[gacha_rarity_list_try[0]] += 1
            card_list = self.pick_cards(gacha_rarity_list_try)
            if search_string.casefold() in card_list[0]["name"].casefold() :
                found = True
            if search_count > 200000:
                await ctx.send(search_string + " not found")
                return
        rarity_counter = gacha_rarity_dict
        embed = discord.Embed(
            title="Photokatsu Gacha Results", description="Rates: PR 2%, SR 20%, R 78%"
        )
        embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/980686341498290176/WSTxLywV_400x400.jpg"
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Requester", value=ctx.author.mention)
        embed.add_field(name="Counter", value=dict(rarity_counter))
        card_string_list = list()
        for card in card_list:
            if card["rarity"].startswith("PR"):
                card_string_list.append(
                    f'**{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}**'
                )
            else:
                card_string_list.append(
                    f'{int(card["id"]):04}. {card["rarity"]:<4} {card["name"]}'
                )
        embed.add_field(name="Card List", value="\n".join(card_string_list))
        embed.set_image(url=card_list[0]["image_url"])
        embed.add_field(name="ID", value=card_list[0]["id"])
        embed.add_field(name="Name", value=card_list[0]["name"])
        embed.add_field(name="Rarity", value=card_list[0]["rarity"])
        embed.add_field(name="Special Appeal", value=card_list[0]["appeal"])
        embed.add_field(name="Skill", value=card_list[0]["skill"])
        embed.set_footer(text="")
        await ctx.send(embed=embed)

    """
    @commands.command()
    async def next_episode(self, ctx, anime : str = "aikatsu"):
        anime_dict = dict()
        anime_dict["aikatsu"] = {"day":6, "hour":7, "minute":00}
        anime_dict["prichan"] = {"day":6, "hour":10, "minute":00}
        anime_dict["precure"] = {"day":6, "hour":8, "minute":30}
        anime = anime.casefold()
        if anime == "help":
            await ctx.send("List of valid animes: " + " ".join([*anime_dict]))
            return
        elif anime not in anime_dict:
            anime = "aikatsu"
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        weekday_today = current_time.weekday()
        weekday_delta = timedelta(days=(anime_dict[anime]["day"] - weekday_today))
        next_aikatsu_datetime = (current_time + weekday_delta).replace(hour=anime_dict[anime]["hour"],minute=anime_dict[anime]["minute"],second=0)
        airing = False

        if self.airtime_datetime is not None and anime == "aikatsu":
            if self.airtime_datetime > current_time:
                next_aikatsu_datetime = self.airtime_datetime

        while next_aikatsu_datetime < current_time:
            if self.airtime_datetime is not None and (
                current_time - self.airtime_datetime
            ) < timedelta(minutes=30):
                current_aikatsu_datetime = self.airtime_datetime
            else:
                current_aikatsu_datetime = next_aikatsu_datetime
            next_aikatsu_datetime += timedelta(weeks=1)
            if (current_time - current_aikatsu_datetime) < timedelta(minutes=30):
                airing = True

        embed = discord.Embed(
            title=anime+" Next Episode", timestamp=next_aikatsu_datetime
        )
        fmt = "%Y-%m-%d %H:%M:%S %Z%z"
        embed.add_field(
            name="Next episode time",
            value=next_aikatsu_datetime.strftime(fmt),
            inline=False,
        )
        embed.add_field(
            name="Time til next episode", value=next_aikatsu_datetime - current_time
        )
        embed.add_field(name="Airing now", value=airing)
        embed.set_footer(text="Local time")
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def set_airtime(self, ctx, airtime: str):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        self.airtime_datetime = datetime.fromisoformat(airtime + "+09:00").astimezone(
            jp_timezone
        )
    """

    @commands.command()
    async def next_birthday(self, ctx, days_or_string : typing.Union[int,str] = 30):
        jp_timezone = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jp_timezone)
        today = current_time.date()
        current_year = today.year

        for idol_dict in self.idol_dict_list:
            birthday_current_year = datetime.strptime(str(current_year) + idol_dict["birthday"],"%Y%B %d").date()
            if birthday_current_year < today :
                idol_dict["next_birthday"] = birthday_current_year.replace(year=current_year+1)
            else:
                idol_dict["next_birthday"] = birthday_current_year

        sorted_idol_dict_list = sorted(self.idol_dict_list, key=operator.itemgetter("next_birthday"))
        if isinstance(days_or_string, int):
            filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if idol_dict["next_birthday"] < today + timedelta(days=days_or_string) ]
            embed = discord.Embed(title="Aikatsu Next Birthdays", description=f"Displaying next birthdays for the next {str(days_or_string)} days (max 25 idols)")
        elif isinstance(days_or_string, str):
            filtered_idol_dict_list  = [ idol_dict for idol_dict in sorted_idol_dict_list if days_or_string.casefold() in idol_dict["name"].casefold() ]
            embed = discord.Embed(title="Aikatsu Next Birthdays", description=f"Displaying next birthdays for search string: {str(days_or_string)} (max 25 idols)")
        for idol_dict in filtered_idol_dict_list:
            embed.add_field(name=idol_dict["name"], value=idol_dict["next_birthday"], inline=False)
        await ctx.send(embed=embed)


    @commands.hybrid_command()
    async def aikatsu_quote_generate(self, ctx, word_length : int = 15):
        if word_length > 200:
            word_length = 200
        if word_length < 5:
            word_length = 5
        final_result = []
        while len(final_result) < word_length :
            max_sentence_length = word_length - len(final_result)
            if max_sentence_length < 2 :
                max_sentence_length = 2
            if max_sentence_length > 15 :
                max_sentence_length = 15
            sentence_length = random.randint(2, max_sentence_length) 
            result = []
            while len(result) < sentence_length or len(result) > 30 or not ( result[-2].endswith(".") or result[-2].endswith("!") or result[-2].endswith("?") or result[-2].endswith("~")):
                result = []			
                s = random.choice(list(self.uppercase_words_set))
                result.extend(s)
                while result[-1] and len(result) < max_sentence_length + 20:
                    w = self.couple_words[(result[-2], result[-1])].get_random()
                    result.append(w)
            final_result.extend(result)
        await ctx.send(" ".join(final_result))

    async def detect_fall(self, message):
        if message.content.strip().casefold().startswith("!!!fall"):
           if self.falling is False:
               self.falling = True
               self.lastfallmessage = message
               
    @commands.command(
        description="Sings a random song. Use !!!fall to interrupt her singing"
    )
    async def singing(self, ctx):
        if self.singing_already is True:
            return
        else:
            self.singing_already = True
            self.falling = False
        song_name = random.choice([key for key, value in self.songs_dict.items()])
        full_song_string = self.songs_dict[song_name]
        song_string_list = full_song_string.splitlines()
        message = await ctx.send("Singing **" + song_name + "** \n")
        self.bot.add_listener(self.detect_fall, 'on_message')
        await asyncio.sleep(1)
        message_content = message.content
        for song_string in song_string_list:
            if self.falling is True:
                embed = discord.Embed()
                embed.set_image(url="https://i.imgur.com/sNqvjaE.png")
                await message.edit(content=message_content, embed=embed)
                await self.lastfallmessage.add_reaction(
                        self.bot.get_emoji(537234052080467968)
                )
                if random.choice([True, False]):
                    await asyncio.sleep(3)
                    await message.edit(content=message_content, embed=discord.Embed(description="I will keep singing!!!"))
                    await self.lastfallmessage.add_reaction(
                        self.bot.get_emoji(485997782344138772)
                    )
                    self.falling = False
                else:
                    self.singing_already = False
                    return
            message_append_string = song_string.strip()
            if message_append_string == "":
                emoji = str(self.bot.get_emoji(537242527070158858))
                message_append_string = "\n" + (emoji + " ") * 5 + "\n"
            message_content = message_content + "\n" + message_append_string
            await message.edit(content=message_content)
            await asyncio.sleep(1)
        self.bot.remove_listener(self.detect_fall, 'on_message')
        embed = discord.Embed()
        embed.set_image(
            url="https://vignette.wikia.nocookie.net/aikatsu/images/f/f7/Dc161b80.jpg"
        )
        await message.edit(content=message_content, embed=embed)
        self.singing_already = False

    @singing.error
    async def singing_handler(self, ctx, error):
        self.singing_already = False
        print(error)
   
    @commands.command()
    async def aikatsu_stars_screenshot(self, ctx, episode: int=0):
        if episode == 0 or episode > 100:
            episode = str(random.randint(1,100))
        else:
            episode = str(episode)
        frame_number_index = random.randint(0, len(self.aistars_screenshot_dict[episode])-1)
        full_filename = self.aistars_screenshot_dict[episode][frame_number_index]["full_filename"] 
        filename = self.aistars_screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title="Aikatsu Stars Screenshots")
        minutes, seconds = divmod(frame_number_index, 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        jpg_data = self.get_aikatsu_screenshot_from_s3(full_filename)
        discord_file = discord.File(jpg_data,filename)
        await ctx.send(file=discord_file)
        await ctx.send(embed=embed)

    @commands.command()
    async def aikatsu_screenshot(self, ctx, episode: int=0):
        if episode == 0 or episode > 178:
            episode = str(random.randint(1,178))
        else:
            episode = str(episode)
        frame_number_index = random.randint(0, len(self.aikatsu_screenshot_dict[episode])-1)
        full_filename = self.aikatsu_screenshot_dict[episode][frame_number_index]["full_filename"]
        filename = self.aikatsu_screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title="Aikatsu Screenshots")
        minutes, seconds = divmod(frame_number_index*5, 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        jpg_data = self.get_aikatsu_screenshot_from_s3(full_filename)
        discord_file = discord.File(jpg_data,filename)
        await ctx.send(file=discord_file)
        await ctx.send(embed=embed)

    @commands.command()
    async def aikatsu_friends_screenshot(self, ctx, episode: int=0):
        if episode == 0 or episode > 70:
            episode = str(random.randint(1,70))
        else:
            episode = str(episode)
        frame_number_index = random.randint(0, len(self.aifure_screenshot_dict[episode])-1)
        full_filename = self.aifure_screenshot_dict[episode][frame_number_index]["full_filename"]
        filename = self.aifure_screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title="Aikatsu Friends Screenshots")
        minutes, seconds = divmod(frame_number_index*5, 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        jpg_data = self.get_aikatsu_screenshot_from_s3(full_filename)
        discord_file = discord.File(jpg_data,filename)
        await ctx.send(file=discord_file)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def aikatsu_meme_generate(self, ctx, word_length : int = 15, choice=None):
        if word_length > 15:
            word_length = 15
        if word_length < 2:
            word_length = 2
        final_result = []
        while len(final_result) < word_length :
            max_sentence_length = word_length - len(final_result)
            if max_sentence_length < 2 :
                max_sentence_length = 2
            if max_sentence_length > 10 :
                max_sentence_length = 10
            sentence_length = random.randint(2, max_sentence_length)
            result = []
            while len(result) < sentence_length or len(result) > 15 or not ( result[-2].endswith(".") or result[-2].endswith("!") or result[-2].endswith("?") or result[-2].endswith("~")) :
                result = []
                s = random.choice(list(self.uppercase_words_set))
                result.extend(s)
                while result[-1] and len(result) < max_sentence_length + 20 :
                    w = self.couple_words[(result[-2], result[-1])].get_random()
                    result.append(w)
            final_result.extend(result)
        meme_text = " ".join(final_result)        
        para = textwrap.wrap(meme_text, width=50)
        """
        aikatsu_choice = random.choices(["aikatsu", "aikatsu_stars"], [178, 100])
        if aikatsu_choice[0] == "aikatsu" :
            episode = str(random.randint(1,178)) 
            screenshot_dict = self.aikatsu_screenshot_dict
            title = "Aikatsu Screenshot"
            multiplier = 5
        elif aikatsu_choice[0] == "aikatsu_stars" :
            episode = str(random.randint(1,100))
            screenshot_dict = self.aistars_screenshot_dict
            title = "Aikatsu Stars Screenshot"
            multiplier = 1
        """
        screenshot_dict, episode, frame_number_index = self.get_screenshot_dict(True, choice=choice)
        full_filename = screenshot_dict[episode][frame_number_index]["full_filename"]
        filename = screenshot_dict[episode][frame_number_index]["filename"]
        embed = discord.Embed(title= screenshot_dict["title"] + " (Click to get original image)", url = screenshot_dict[episode][frame_number_index]["web_url"])
        minutes, seconds = divmod(frame_number_index* screenshot_dict["multiplier"], 60)
        embed.add_field(name="Episode", value=episode)
        embed.add_field(name="Time", value=f"{minutes:02d}:{seconds:02d}")
        embed.add_field(name="Meme Text", value=meme_text, inline=False)

        fillcolor = "white"
        shadowcolor = "black"
        with self.get_aikatsu_screenshot_from_s3(full_filename) as f:
            #jpg_data = f.read()
            #file_object = BytesIO(jpg_data)
            #image = Image.open(file_object)
            image = Image.open(f)
            width, height = image.size
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype('/usr/share/fonts/truetype/NotoSansCJKjp-Black.otf', 21)
            w, h = draw.textsize(para[0], font=font)
            pad = 5
            current_h = height - 10 - len(para)*(h+pad)
            outline = 2
            for line in para:
                w, h = draw.textsize(line, font=font)
                draw.text(((width - w) / 2-outline, current_h-outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2+outline, current_h-outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2-outline, current_h+outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2+outline, current_h+outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2-outline, current_h), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2, current_h-outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2, current_h+outline), line, font=font, fill=shadowcolor)
                draw.text(((width - w) / 2+outline, current_h), line, font=font, fill=shadowcolor)
        
                draw.text(((width - w) / 2, current_h), line, font=font, fill=fillcolor)
                current_h += h + pad
            file_object2 = BytesIO()
            image.save(file_object2, "JPEG", optimize=True)
            file_object2.seek(0)
            discord_file = discord.File(file_object2, filename)
            await ctx.send(file=discord_file)
            await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def aikatsu_screenshot_collage(self, ctx, horizontal_count : int = 5, vertical_count : int = 5, choice=None):
        if horizontal_count > 10 :
            horizontal_count = 10 
        elif horizontal_count < 1 :
            horizontal_count = 1
        if vertical_count > 10 :
            vertical_count = 10 
        elif vertical_count < 1 :
            vertical_count = 1  
        total_count = horizontal_count*vertical_count
        screenshots = list()
        for i in range(total_count):
           screenshots.append(self.get_screenshot_dict(choice=choice))

        total_width=640*horizontal_count
        total_height=360*vertical_count

        result = Image.new('RGB', (total_width, total_height))
        count = 0 
        current_horizontal_position = 0
        current_vertical_position = 0
        for screenshot in screenshots:
            count += 1
            if count > horizontal_count:
                count = 1
                current_horizontal_position = 0 
                current_vertical_position += 360
            with Image.open(self.get_aikatsu_screenshot_from_s3(screenshot["full_filename"])) as image:
                result.paste(im=image, box=(current_horizontal_position, current_vertical_position))
            current_horizontal_position += 640
          
        file_object2 = BytesIO()
        result.save(file_object2, "JPEG", optimize=True)
        file_object2.seek(0)
        discord_file = discord.File(file_object2, "test.jpg")
        await ctx.send(file=discord_file)

    def get_screenshot_dict(self, get_frame_number_index=False, choice=None):
        if choice not in ["aikatsu","aikatsu_stars","aikatsu_friends"]:
            aikatsu_choice = random.choices(["aikatsu", "aikatsu_stars","aikatsu_friends"], [178, 100, 70])
        else:
            aikatsu_choice = [choice] 
        if aikatsu_choice[0] == "aikatsu" :
            episode = str(random.randint(1,178))
            screenshot_dict = self.aikatsu_screenshot_dict
        elif aikatsu_choice[0] == "aikatsu_stars" :
            episode = str(random.randint(1,100))
            screenshot_dict = self.aistars_screenshot_dict
        elif aikatsu_choice[0] == "aikatsu_friends" :
            episode = str(random.randint(1,70))
            screenshot_dict = self.aifure_screenshot_dict
        frame_number_index = random.randint(0, len(screenshot_dict[episode])-1)
        if get_frame_number_index:
            return screenshot_dict, episode, frame_number_index
        else:
            return screenshot_dict[episode][frame_number_index]


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case AikatsuCog.
# When we load the cog, we use the name of the file.
async def setup(bot):
    await bot.add_cog(AikatsuCog(bot))

async def teardown(bot):
    bot.process_executor.shutdown()