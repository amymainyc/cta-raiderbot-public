from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import aiohttp
import asyncio
from utils.utils import *
from datetime import datetime



with open('data/config.json') as d:
    config = json.load(d)



class Recruit(commands.Cog):



    def __init__(self, client):
        self.client = client


    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.checkWelcomeMessage()
        await self.deleteInactives()
        await self.resetRecruitStats.start()



    async def checkWelcomeMessage(self):
        # make sure the welcome message has preset reactions
        try:
            welcomeMessageID = config["config"]["welcomeMessageID"]
            welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
            message = await welcomeChannel.fetch_message(welcomeMessageID)
            await message.clear_reactions()
            await message.add_reaction('✅')
            await message.add_reaction('❌')
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command()
    async def sendNewEmbed(self, ctx):
        # send a new welcome message
        try:
            if isDev(ctx):
                welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
                embed = discord.Embed(
                    title="Welcome to the Raiders discord server!", 
                    color=0x000000,
                    description="Follow the instructions below to gain access to channels."
                )
                embed.add_field(name="** **", value="React with ✅ to be sent to a recruitment channel. \nReact with ❌ if you already have a guild or don't want to join Raiders.")
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                embed.set_image(url=config["config"]["bannerUrl"])
                welcomeMessage = await welcomeChannel.send(embed=embed)
                await welcomeMessage.add_reaction("✅")
                await welcomeMessage.add_reaction("❌")
                with open("data/config.json", "w") as f:
                    config["config"]["welcomeMessageID"] = welcomeMessage.id
                    json.dump(config, f, indent=4)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)


        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check for reactions on the welcome message
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            welcomeMessageID = config["config"]["welcomeMessageID"]
            if payload.message_id == welcomeMessageID and payload.member != self.client.user:
                welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
                message = await welcomeChannel.fetch_message(welcomeMessageID)
                await message.remove_reaction(payload.emoji, payload.member)
                roles = config["roles"]
                memberRoles = payload.member.roles
                hasRole = False
                for r in roles:
                    guild = self.client.get_guild(payload.guild_id)
                    if guild.get_role(roles[r]) in memberRoles:
                        hasRole = True
                if not hasRole:
                    if payload.emoji.name == '✅':
                        await self.sendToNextGuild(payload.member)
                    if payload.emoji.name == '❌':
                        await self.sendToGeneralChannel(payload.member)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    async def sendToNextGuild(self, member):
        # sends user to next channel after reaction
        try:
            channels = config["channels"]
            index = config["config"]["nextChannel"]
            hasOpening = False
            for guild in config["isOpen"]:
                if config["isOpen"][guild] == "open":
                    hasOpening = True
                    break
            if not hasOpening:
                welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
                return await welcomeChannel.send(f"<@{member.id}> There are no guilds open for recruitment currently! Please check back later.", delete_after=20)
            while True:
                nextChannel = list(channels)[index]
                if config["isOpen"][nextChannel] == "open":
                    break
                else:
                    index += 1
                    if index >= len(config["channels"]):
                        index = 2

            channel = self.client.get_channel(channels[nextChannel])
            leaderRole = config["roles"][nextChannel]
            overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(config["roles"]["Recruitee"]))
            await channel.set_permissions(member, overwrite=overwrite)
            await channel.send(f"(・ω・)ノ <@{member.id}> has arrived! <@&{leaderRole}>\nGuild leaders have 10m to respond or <@{member.id}> will be redirected to a new channel.")

            with open("data/config.json", "w") as f:
                config["config"]["nextChannel"] = index + 1
                if config["config"]["nextChannel"] >= len(config["channels"]):
                    config["config"]["nextChannel"] = 2
                json.dump(config, f, indent=4)
            with open("data/recruitees.json") as f:
                recruitees = json.load(f)
                recruitees[member.id] = [f"[Sent to {nextChannel}]"]
            with open("data/recruitees.json", "w") as f:
                json.dump(recruitees, f, indent=4)
            await self.guildTimeout(channel, member)


        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    async def guildTimeout(self, ogChannel, member):
        try:
            def whosent(m):
                return isGuildLeader(m.author) and m.channel == ogChannel
            message = await self.client.wait_for('message', check=whosent, timeout=600)
        except asyncio.TimeoutError:
            openGuilds = 0
            for guild in config["isOpen"]:
                if config["isOpen"][guild] == "open":
                    openGuilds += 1
            if openGuilds < 2:
                return await ogChannel.send("All other guilds are closed! Unable to redirect.")
            channels = config["channels"]
            for i in range(len(channels)):
                if channels[list(channels)[i]] == ogChannel.id:
                    index = i + 1
                    if index >= len(config["channels"]):
                        index = 2
                    break
            while True:
                nextChannel = list(channels)[index]
                if config["isOpen"][nextChannel] == "open":
                    break
                else:
                    index += 1
                    if index >= len(config["channels"]):
                        index = 2

            channel = self.client.get_channel(channels[nextChannel])
            leaderRole = config["roles"][nextChannel]
            overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(config["roles"]["Recruitee"]))
            await ogChannel.set_permissions(member, overwrite=None)
            await ogChannel.send(f"`User has been sent to another guild due to timeout.`")
            await channel.set_permissions(member, overwrite=overwrite)
            await channel.send(f"(・ω・)ノ <@{member.id}> has arrived! (Redirected due to timeout) <@&{leaderRole}>\nGuild leaders have 10m to respond or <@{member.id}> will be redirected to a new channel.")

            with open("data/config.json", "w") as f:
                config["config"]["nextChannel"] = index + 1
                if config["config"]["nextChannel"] >= len(config["channels"]):
                    config["config"]["nextChannel"] = 2
                json.dump(config, f, indent=4)
            with open("data/recruitees.json") as f:
                recruitees = json.load(f)
                try:
                    recruitees[str(member.id)].append(f"[Sent to {nextChannel} due to timeout]")
                except:
                    pass
            with open("data/recruitees.json", "w") as f:
                json.dump(recruitees, f, indent=4)

            chatLog = "\n".join(recruitees[str(member.id)])
            if len(chatLog) > 2000:
                chatLog = chatLog[:1900] + "..."

            embed = discord.Embed()
            embed.add_field(name=f"{member.name}'s previous chat logs for your convenience:", value=f"** **\n```{chatLog}```")
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            await channel.send(embed=embed)

            await self.guildTimeout(channel, member)





    async def sendToGeneralChannel(self, member):
        # sends user to general channel after reaction 
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            channels = config["channels"]
            channel = self.client.get_channel(channels["General"])
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(config["roles"]["General"]))
            await channel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)


    
    @commands.command()
    async def recruit(self, ctx, member: discord.Member):
        # recruit a user to a guild
        try:
            if await isLeader(ctx) and await isRecruitee(ctx, member):
                with open('data/config.json') as d:
                    config = json.load(d)
                channels = config["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to recruit @{member.name} to {channelName}?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌")
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                embed = discord.Embed()
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    await ctx.channel.set_permissions(member, overwrite=None)
                    overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
                    await member.remove_roles(ctx.channel.guild.get_role(config["roles"]["Recruitee"]))
                    await member.add_roles(ctx.channel.guild.get_role(config["roles"][channelName]))
                    with open("data/config.json", "w") as f:
                        config["newMembers"][channelName] += 1
                        json.dump(config, f, indent=4)
                    emoji = config["emojis"][channelName]
                    embed.add_field(name=f"@{member.name} has been recruited to {channelName} {emoji}✅", value="** **")
                    guildChannel = self.client.get_channel(config["guildChannels"][channelName])
                    await guildChannel.send(f"<@{member.id}> has arrived! `(Recruited to {channelName} by {ctx.author.name})`{emoji}")
                    with open("data/recruitees.json") as f:
                        recruitees = json.load(f)
                        try:
                            recruitees.pop(str(member.id))
                        except:
                            pass
                    with open("data/recruitees.json", "w") as f:
                        json.dump(recruitees, f, indent=4)
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"@{member.name}'s recruitment has been aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command() 
    async def transfer(self, ctx, member: discord.Member):
        # send to channel due to unsuccessful recruit
        try:
            if await isLeader(ctx) and await isRecruitee(ctx, member):
                with open('data/config.json') as d:
                    config = json.load(d)
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
                channels = config["channels"]
                field = "Please react with the corresponding number: \n"
                for i in range(len(channels) - 1):
                    field += f"\n{emojis[i]} `#{self.client.get_channel(channels[list(channels)[i+1]]).name}`"

                embed = discord.Embed()
                embed.add_field(name="Where would you like to send this user?", value=field)
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                for e in emojis:
                    await message.add_reaction(e)

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in emojis
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                for e in range(len(emojis)):
                    if str(reaction.emoji) == emojis[e]:
                        targetName = list(channels)[e+1]
                        targetChannel = self.client.get_channel(channels[targetName])
                        await ctx.channel.set_permissions(member, overwrite=None)
                        overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
                        
                        if targetName == "General":
                            await member.remove_roles(ctx.channel.guild.get_role(config["roles"]["Recruitee"]))
                            await member.add_roles(ctx.channel.guild.get_role(config["roles"]["General"]))
                            await targetChannel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")
                            emoji = ""
                            with open("data/recruitees.json") as f:
                                recruitees = json.load(f)
                                try: 
                                    recruitees.pop(str(member.id))
                                except:
                                    pass
                            with open("data/recruitees.json", "w") as f:
                                json.dump(recruitees, f, indent=4)
                        else:
                            if config["isOpen"][targetName] == "closed":
                                embed = discord.Embed()
                                embed.add_field(name=f"{targetName} is currently closed to new recruits! Please try a different guild ❌", value=f"** **")
                                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                                await message.edit(embed=embed)
                                return await message.clear_reactions()
                            await targetChannel.set_permissions(member, overwrite=overwrite)
                            leaderRole = config["roles"][targetName]
                            await targetChannel.send(f"(・ω・)ノ <@{member.id}> has landed! (Sent over by @{ctx.author.name}) <@&{leaderRole}>")
                            with open("data/recruitees.json") as f:
                                recruitees = json.load(f)
                                try: 
                                    recruitees[str(member.id)].append(f"[Transferred to {targetName} by @{ctx.author.name}]")
                                except:
                                    pass
                            with open("data/recruitees.json", "w") as f:
                                json.dump(recruitees, f, indent=4)
                            chatLog = "\n".join(recruitees[str(member.id)])
                            if len(chatLog) > 2000:
                                chatLog = chatLog[:1900] + "..."

                            embed = discord.Embed()
                            embed.add_field(name=f"{member.name}'s previous chat logs for your convenience:", value=f"** **\n```{chatLog}```")
                            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                            await targetChannel.send(embed=embed)
                            emoji = config["emojis"][targetName]

                        embed = discord.Embed()
                        embed.add_field(name=f"@{member.name} has been sent to {targetName} {emoji}✅", value=f"** **")
                        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                        await message.edit(embed=embed)
                        await message.clear_reactions()
                        break

        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command()
    async def openGuild(self, ctx):
        # opens guild for recruitees
        try:
            if await isLeader(ctx):
                with open('data/config.json') as d:
                    config = json.load(d)
                channels = config["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                if config["isOpen"][channelName] == "open":
                    return await ctx.send("```This guild is already open to new members.```")
                
                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to open {channelName} to new recruits?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌")
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                embed = discord.Embed()
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    with open("data/config.json", "w") as f:
                        config["isOpen"][channelName] = "open"
                        json.dump(config, f, indent=4)
                    embed.add_field(name=f"{channelName} has been opened to new recruits ✅", value="** **")
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"Command aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command()
    async def closeGuild(self, ctx):
        # closes guild for recruitees
        try:
            if await isLeader(ctx):
                with open('data/config.json') as d:
                    config = json.load(d)
                channels = config["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                if config["isOpen"][channelName] == "closed":
                    return await ctx.send("```This guild is already closed to new members.```")
                
                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to closed {channelName} to new recruits?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌")
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                embed = discord.Embed()
                embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    with open("data/config.json", "w") as f:
                        config["isOpen"][channelName] = "closed"
                        json.dump(config, f, indent=4)
                    embed.add_field(name=f"{channelName} has been closed to new recruits ✅", value="** **")
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"Command aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)


    
    @commands.Cog.listener()
    async def on_message(self, message):
        # check and log messages for recruitees
        try:
            whoSent = str(message.author.id)
            with open("data/recruitees.json") as f:
                recruitees = json.load(f)
            if whoSent in recruitees:
                if len(recruitees[whoSent]) < 30: 
                    if len(message.attachments) == 0:
                        recruitees[whoSent].append(message.content)
                    else:
                        recruitees[whoSent].append(message.attachments[0].url)
                    with open("data/recruitees.json", "w") as f:
                            json.dump(recruitees, f, indent=4)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command()
    async def recruitStats(self, ctx):
        # sends the monthly new members
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            stats = config["newMembers"]
            most = 0
            mostGuild = []
            least = -1
            leastGuild = []
            for guild in stats:
                if stats[guild] >= most:
                    if stats[guild] == most:
                        mostGuild.append(guild)
                    else:
                        most = stats[guild]
                        mostGuild = [guild]
                if stats[guild] <= least or least == -1:
                    if stats[guild] == least:
                        leastGuild.append(guild)
                    else:
                        least = stats[guild]
                        leastGuild = [guild]
            desc = "**Most new members**:\n`"
            for g in range(len(mostGuild)):
                if g == 0:
                    desc += f"{mostGuild[g]}"
                else:
                    desc += f", {mostGuild[g]}"
            desc += "`\n\n**Least new members**:\n`"
            for g in range(len(leastGuild)):
                if g == 0:
                    desc += f"{leastGuild[g]}"
                else:
                    desc += f", {leastGuild[g]}"
            desc += "`"
            embed = discord.Embed(title="Monthly New Members", description=desc)
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)

            field = ""
            for guild in range(len(stats)):
                field += f"{config['colorEmojis'][list(stats)[guild]]} `{list(stats)[guild]}`: {stats[list(stats)[guild]]}\n"
            embed.add_field(name="** **", value=field)
            await ctx.send(embed=embed)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.command()
    async def rotation(self, ctx):
        index = config["config"]["nextChannel"]
        order = []
        i = index
        while True:
            nextChannel = list(config["channels"])[i]
            if config["isOpen"][nextChannel] == "open":
                order.append(config["colorEmojis"][nextChannel] + f" `{nextChannel}`")
            i += 1
            if i >= len(config["channels"]):
                i = 2
            if i == index: break

        embed = discord.Embed(title="Guilds Rotation")
        embed.add_field(name="Next recruit goes to:", value=order[0], inline=False)
        embed.add_field(name="Followed by:", value="\n".join(order[1:]), inline=False)
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        await ctx.send(embed=embed)



    @tasks.loop(minutes=1)
    async def resetRecruitStats(self):
        # resets monthly new members after each month
        try:
            with open('data/config.json') as d:
                config = json.load(d)
            
            time = str(datetime.utcnow())
            if time[8:10] == "01" and (time[11:16] == "00:00" or time[11:16] == "00:01"):
                for guild in config["newMembers"]:
                    config["newMembers"][guild] = 0
                with open("data/config.json", "w") as f:
                    json.dump(config, f, indent=4)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    async def deleteInactives(self):
        # remove inactive users from recruitees.json
        try:
            channel = self.client.get_channel(config["channels"]["Welcome"])
            guild = channel.guild
            with open("data/recruitees.json") as f:
                recruitees = json.load(f)
            for r in recruitees:
                member = await guild.fetch_member(int(r))
                if member == None:
                    recruitees.pop(r)
                    break
                elif guild.get_role(config["roles"]["Recruitee"]) not in member.roles:
                    recruitees.pop(r)
                    break
            with open("data/recruitees.json", "w") as f:
                json.dump(recruitees, f, indent=4)
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.client.get_channel(config["channels"]["Welcome"])
        await member.add_roles(channel.guild.get_role(config["config"]["newMemberRole"]))
        await asyncio.sleep(1)
        await channel.send(f"<@{member.id}>", delete_after=1)
        await asyncio.sleep(300)
        try:
            if channel.guild.get_role(config["config"]["newMemberRole"]) in member.roles:
                await member.send(f"```Hey! I noticed you haven't reacted to the welcome message yet! Check #{channel.name} and react to gain access to the server.```")
        except Exception as e:
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(e, channel)



    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.client.get_channel(config["channels"]["General"])
        await channel.send(f"{member.mention} has left the server... Farewell on your journeys!")



def setup(client):
    client.add_cog(Recruit(client))