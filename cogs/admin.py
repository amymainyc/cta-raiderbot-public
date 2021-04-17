from discord.ext import commands
import discord
import json
from loguru import logger
import asyncio
from utils.utils import *



with open('data/config.json') as d:
    config = json.load(d)



class Admin(commands.Cog):



    def __init__(self, client):
        self.client = client



    @commands.Cog.listener()
    async def on_ready(self):
        # bot startup tasks
        logger.info("Bot is ready.")
        activity = discord.Game(name=f"Crush Them All!")
        await self.client.change_presence(activity=activity)
        await asyncio.sleep(43200)
        await gitPush()



    @commands.command()
    async def help(self, ctx):
        # help command
        embed = discord.Embed(
            title="Raider Bot's Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(
            name="★ **r.help**",
            value="Returns this help message",
            inline=False
        )
        embed.add_field(
            name="★ **r.setchannels**",
            value="Sets up recruitment channels `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.setroles**",
            value="Sets up recruitment roles `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.recruit @user**",
            value="Recruits a user to a guild `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.transfer @user**",
            value="Sends the user to another channel due to unsuccessful recruitment `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.recruitstats**",
            value="Returns the monthly new members counts for each guild",
            inline=False
        )
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        await ctx.send(embed=embed)
    


def setup(client):
    client.add_cog(Admin(client))