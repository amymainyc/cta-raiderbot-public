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



class Reactions(commands.Cog):



    def __init__(self, client):
        self.client = client
    


    @commands.command()
    async def addNewReactionRole(self, ctx, emoji, role: discord.Role, *desc):
        try:
            if isDev(ctx):
                config["reactions"]["reactionRoles"][str(emoji)] = [role.id, " ".join(desc)]
                with open("data/config.json", "w") as f:
                    json.dump(config, f, indent=4)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)


    
    
    @commands.command()
    async def sendNewReactionEmbed(self, ctx):
        # send a new reactions message
        try:
            if isDev(ctx):
                channel = self.client.get_channel(config["reactions"]["channelID"])
                embed = discord.Embed(
                    title="Reaction Roles",
                    description="React with one of the following emojis to get the role."
                )
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)

                reactionRoles = config["reactions"]["reactionRoles"]
                for emoji in reactionRoles:
                    title = f"{emoji} __**{ctx.guild.get_role(reactionRoles[emoji][0]).name}**__"
                    text = f"{reactionRoles[emoji][1]}\n"
                    embed.add_field(name=title, value=text, inline=False)
                message = await channel.send(embed=embed)
                for emoji in reactionRoles:
                    await message.add_reaction(emoji)
                with open("data/config.json", "w") as f:
                    config["reactions"]["messageID"] = message.id
                    json.dump(config, f, indent=4)

        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check for reactions on the reactions message
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            reactionRoles = config["reactions"]
            messageID = reactionRoles["messageID"]
            if payload.message_id == messageID and payload.member != self.client.user:
                channel = self.client.get_channel(config["reactions"]["channelID"])
                message = await channel.fetch_message(messageID)
                reactionRoles = reactionRoles["reactionRoles"]
                if str(payload.emoji) in reactionRoles:
                    guild = self.client.get_guild(payload.guild_id)
                    role = guild.get_role(reactionRoles[str(payload.emoji)][0])
                    await payload.member.add_roles(role)
                else:
                    await message.remove_reaction(payload.emoji, payload.member)

        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # check for reaction removals on the reactions message
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            reactionRoles = config["reactions"]
            messageID = reactionRoles["messageID"]
            if payload.message_id == messageID and payload.user_id != self.client.user.id:
                channel = self.client.get_channel(config["reactions"]["channelID"])
                message = await channel.fetch_message(messageID)
                reactionRoles = reactionRoles["reactionRoles"]
                if str(payload.emoji) in reactionRoles:
                    guild = self.client.get_guild(payload.guild_id)
                    role = guild.get_role(reactionRoles[str(payload.emoji)][0])
                    member  = guild.get_member(payload.user_id)
                    if role in member.roles:
                        await member.remove_roles(role)

        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)

    

def setup(client):
    client.add_cog(Reactions(client))