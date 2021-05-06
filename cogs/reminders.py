import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
from loguru import logger
import asyncio
from utils.utils import *


with open('data/config.json') as d:
    config = json.load(d)


class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.checkCalendar.start()



    @tasks.loop(seconds=10)
    async def checkCalendar(self):
        try:
            with open("data/calendar.json", "r") as f:
                calendar = json.load(f)

            event = ""
            for e in calendar:
                time = calendar[e]["time"]
                intervals = calendar[e]["intervals"]
                if abs(int(datetime.now().timestamp()) - time) % intervals < 60:
                    event = e
                    break

            if event != "":
                logger.info(f"Event: {event}")
                channel = self.client.get_channel(config["config"]["remindersChannel"])
                color = discord.Color(int(calendar[event]["color"], 16))
                embed = discord.Embed(title=event, color=color)
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                embed.set_image(url=calendar[event]["image"])
                await asyncio.sleep(120)
                if event == "Daily Reset!":
                    days = calendar[event]["days"]
                    day = list(days)[datetime.utcnow().weekday()]
                    chest = days[day][0]
                    runes = days[day][1]
                    text = calendar[event]["description"].replace("[day]", day).replace("[chest]", chest).replace("[runes]", runes)
                    color = discord.Color(int(days[day][3], 16))
                    embed = discord.Embed(title=event, color=color)
                    embed.set_thumbnail(url=days[day][2])
                else:
                    text = calendar[event]["description"]
                    color = discord.Color(int(calendar[event]["color"], 16))
                    embed = discord.Embed(title=event, color=color)
                    embed.set_thumbnail(url=calendar[event]["thumbnail"])

                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                embed.set_image(url=calendar[event]["image"])
                value = f"**{text}**\n\n*To receive notifications for reminders like these, select the exclamation mark emoji at the bottom of <#716720818670927892>.*"
                embed.add_field(name="** **", value=value)
                await channel.send(f"<@&797840056504680468>")
                await channel.send(embed=embed)
                await asyncio.sleep(300)

        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)


    
    @commands.command()
    async def testEmbeds(self, ctx):
        if isDev(ctx):
            with open("data/calendar.json") as f:
                calendar = json.load(f)
            for event in calendar:
                channel = self.client.get_channel(config["config"]["remindersChannel"])

                if event == "Daily Reset!":
                    days = calendar[event]["days"]
                    day = list(days)[datetime.utcnow().weekday()]
                    chest = days[day][0]
                    runes = days[day][1]
                    text = calendar[event]["description"].replace("[day]", day).replace("[chest]", chest).replace("[runes]", runes)
                    color = discord.Color(int(days[day][3], 16))
                    embed = discord.Embed(title=event, color=color)
                    embed.set_thumbnail(url=days[day][2])
                else:
                    text = calendar[event]["description"]
                    color = discord.Color(int(calendar[event]["color"], 16))
                    embed = discord.Embed(title=event, color=color)
                    embed.set_thumbnail(url=calendar[event]["thumbnail"])

                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                embed.set_image(url=calendar[event]["image"])
                value = f"**{text}**\n\n*To receive notifications for reminders like these, select the exclamation mark emoji at the bottom of the #directory channel.*"
                embed.add_field(name="** **", value=value)
                await channel.send(f"<@&797840056504680468>")
                await channel.send(embed=embed)


    
def setup(client):
    client.add_cog(Reminders(client))
