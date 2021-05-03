from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import asyncio
from bs4 import BeautifulSoup
import aiohttp
import sys
from utils.utils import *



with open('data/config.json') as d:
    config = json.load(d)



class General(commands.Cog):



    def __init__(self, client):
        self.client = client
    


    @commands.Cog.listener()
    async def on_ready(self):
        sys.setrecursionlimit(10000)
        await asyncio.sleep(1800)
        await self.cacheGuildWar.start()


    
    @commands.command(aliases=["gw"])
    async def guildWar(self, ctx, guild):
        # gets guild war stats for guild
        try:
            logger.info(f"Getting guild war stats for {guild}.")
            with open("data/guildwar.json") as f:
                rankings = json.load(f)
            isGuild = False
            for r in rankings:
                if rankings[r][0][1:4] == guild:
                    guild = rankings[r][0]
                    score = rankings[r][1]
                    rank = str(r)
                    isGuild = True
                    break
            if not isGuild:
                return await ctx.send("```Guild not found! Make sure you have the right guild tag and the capitalization is correct.```")
            embed = discord.Embed(title=f"⚔️ Guild War Ranking")
            embed.add_field(name=guild, value=f"Ranking: #{rank}\nScore: {score}")
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.set_image(url=config["config"]["guildWarBannerUrl"])
            await ctx.send(embed=embed)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command(aliases=["gwr"])
    async def guildWarRaiders(self, ctx):
        # gets guild war stats for raider guilds
        try:
            logger.info("Getting guild war stats for Raider guilds.")
            with open("data/guildwar.json") as f:
                rankings = json.load(f)
            text = "```"
            for r in rankings:
                if rankings[r][0][1:4].lower() == "rdr":
                    spaces1 = " " * (5 - len(str(r)))
                    text += f"\n# {str(r)}{spaces1}{rankings[r][0]}\n       Score: {rankings[r][1]}"
            text += "```"
            embed = discord.Embed(title="⚔️ Raiders Guild War Rankings")
            embed.add_field(name="** **", value=text)
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.set_image(url=config["config"]["bannerUrl"])
            await ctx.send(embed=embed)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @tasks.loop(minutes=30)
    async def cacheGuildWar(self):
        # caches all guild war stats
        leaderboard = {}
        data = []
        for offset in range(0, 5):
            URL = config["config"]["guildWar"] + str(offset)
            logger.info(f"Getting guild war stats: {URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as page:
                    html = await page.text()
                    soup = BeautifulSoup(html, 'html.parser')
            soup = soup.find("tbody")
            guilds = soup.findAll("td")
            
            for g in range(len(guilds)):
                content = guilds[g].contents
                for c in range(len(content)):
                    content[c] = str(content[c])
                content = "".join(content).strip()
                content = "".join(content.split("\n"))
                content = "".join(content.split("\t"))
                soup = BeautifulSoup(content, "html.parser")
                guilds[g] = str(soup.get_text())
            data = data + guilds

        leaderboard[1] = [data[1], data[2]]
        leaderboard[2] = [data[4], data[5]]
        leaderboard[3] = [data[7], data[8]]
        i = 9
        while (i < len(data)):
            leaderboard[int(data[i])] = [data[i + 1], data[i + 2]]
            i += 3

        with open("data/guildwar.json", "w") as f:
            json.dump(leaderboard, f, indent=4)

    

def setup(client):
    client.add_cog(General(client))