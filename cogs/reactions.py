from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import asyncio
import aiohttp
import sys
from utils.utils import *



with open('data/server.json') as d:
    server = json.load(d)



class Reactions(commands.Cog):



    def __init__(self, client):
        self.client = client
    


    @commands.command()
    async def addNewReactionRole(self, ctx, emoji, role: discord.Role, *desc):
        try:
            if isDev(ctx):
                server["reactions"]["reactionRoles"][str(emoji)] = [role.id, " ".join(desc)]
                with open("data/server.json", "w") as f:
                    json.dump(server, f, indent=4)
                await logUsage(f"New reaction role added by @{ctx.author.name}.", self.client) 
        except Exception as e:
            await handleException(e, self.client)


    
    
    @commands.command()
    async def sendNewReactionEmbed(self, ctx):
        # send a new reactions message
        try:
            if isDev(ctx):
                channel = self.client.get_channel(server["reactions"]["channelID"])
                try: 
                    message = await channel.fetch_message(server["reactions"]["messageID"])
                    await message.delete()
                except: pass
                embed = discord.Embed(
                    title="Reaction Roles",
                    description="React with one of the following emojis to get the role."
                )
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)

                reactionRoles = server["reactions"]["reactionRoles"]
                for emoji in reactionRoles:
                    guild = self.client.get_guild(server["general"]["guildID"])
                    title = f"{emoji} __**{guild.get_role(reactionRoles[emoji][0]).name}**__"
                    text = f"{reactionRoles[emoji][1]}\n"
                    embed.add_field(name=title, value=text, inline=False)
                message = await channel.send(embed=embed)
                for emoji in reactionRoles:
                    await message.add_reaction(emoji)
                with open("data/server.json", "w") as f:
                    server["reactions"]["messageID"] = message.id
                    json.dump(server, f, indent=4)
                await ctx.reply("```New reaction embed sent! Please make sure no other data has changed in server.json and then gitpush.```")

        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def updateReactionEmbed(self, ctx):
        # updates reactions message
        try:
            if isDev(ctx):
                channel = self.client.get_channel(server["reactions"]["channelID"])
                message = await channel.fetch_message(server["reactions"]["messageID"])
                embed = discord.Embed(
                    title="Reaction Roles",
                    description="React with one of the following emojis to get the role."
                )
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)

                reactionRoles = server["reactions"]["reactionRoles"]
                for emoji in reactionRoles:
                    guild = self.client.get_guild(server["general"]["guildID"])
                    title = f"{emoji} __**{guild.get_role(reactionRoles[emoji][0]).name}**__"
                    text = f"{reactionRoles[emoji][1]}\n"
                    embed.add_field(name=title, value=text, inline=False)
                for emoji in reactionRoles:
                    await message.add_reaction(emoji)
                await message.edit(embed=embed)

        except Exception as e:
            await handleException(e, self.client)



    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check for reactions on the reactions message
        try:
            reactionRoles = server["reactions"]
            messageID = reactionRoles["messageID"]
            if payload.message_id == messageID and payload.member != self.client.user:
                channel = self.client.get_channel(server["reactions"]["channelID"])
                message = await channel.fetch_message(messageID)
                reactionRoles = reactionRoles["reactionRoles"]
                if str(payload.emoji) in reactionRoles:
                    guild = self.client.get_guild(payload.guild_id)
                    role = guild.get_role(reactionRoles[str(payload.emoji)][0])
                    await payload.member.add_roles(role)
                    await logUsage(f"@{payload.member.name} has been given {role.name} role.", self.client)
                else:
                    await message.remove_reaction(payload.emoji, payload.member)

        except Exception as e:
            await handleException(e, self.client)



    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # check for reaction removals on the reactions message
        try:
            reactionRoles = server["reactions"]
            messageID = reactionRoles["messageID"]
            if payload.message_id == messageID and payload.user_id != self.client.user.id:
                channel = self.client.get_channel(server["reactions"]["channelID"])
                message = await channel.fetch_message(messageID)
                reactionRoles = reactionRoles["reactionRoles"]
                if str(payload.emoji) in reactionRoles:
                    guild = self.client.get_guild(payload.guild_id)
                    role = guild.get_role(reactionRoles[str(payload.emoji)][0])
                    member  = guild.get_member(payload.user_id)
                    if role in member.roles:
                        await member.remove_roles(role)
                        await logUsage(f"@{member.name} has been removed of {role.name} role.", self.client)

        except Exception as e:
            await handleException(e, self.client)

    

def setup(client):
    client.add_cog(Reactions(client))