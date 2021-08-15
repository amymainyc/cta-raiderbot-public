from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import aiohttp
import asyncio
from utils.utils import *
from utils.data import *
from datetime import datetime



class Recruit(commands.Cog):



    def __init__(self, client):
        self.client = client
        self.data = Data()
        with open('data/server.json') as d:
            self.server = json.load(d)


    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.deleteInactives()
        await self.resetRecruitStats.start()



    @commands.command()
    async def sendNewEmbed(self, ctx):
        # send a new welcome message
        try:
            if isDev(ctx):
                welcomeChannel = self.client.get_channel(self.server["channels"]["Welcome"])
                try:
                    message = await welcomeChannel.fetch_message(self.server["general"]["welcomeMessageID"]) 
                    await message.delete()
                except: 
                    pass
                embed = discord.Embed(
                    title="Welcome to the Raiders discord server!", 
                    color=0x000000,
                    description="Follow the instructions below to gain access to channels."
                )
                embed.add_field(name="** **", value="React with ✅ to be sent to a recruitment channel. \nReact with ❌ if you already have a guild or don't want to join Raiders.")
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                embed.set_image(url=self.server["general"]["bannerUrl"])
                welcomeMessage = await welcomeChannel.send(embed=embed)
                await welcomeMessage.add_reaction("✅")
                await welcomeMessage.add_reaction("❌")
                with open("data/server.json", "w") as f:
                    self.server["general"]["welcomeMessageID"] = welcomeMessage.id
                    json.dump(self.server, f, indent=4)
        except Exception as e:
            await handleException(e, self.client)


        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check for reactions on the welcome message
        try:
            welcomeMessageID = self.server["general"]["welcomeMessageID"]
            if payload.message_id == welcomeMessageID and payload.member != self.client.user:
                welcomeChannel = self.client.get_channel(self.server["channels"]["Welcome"])
                message = await welcomeChannel.fetch_message(welcomeMessageID)
                await message.remove_reaction(payload.emoji, payload.member)
                roles = self.server["roles"]
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
            await handleException(e, self.client)



    async def sendToNextGuild(self, member):
        # sends user to next channel after reaction
        try:
            channels = self.server["channels"]
            index = self.server["general"]["nextChannel"]
            hasOpening = False
            for guild in self.server["isOpen"]:
                if self.server["isOpen"][guild] == "open":
                    hasOpening = True
                    break
            if not hasOpening:
                welcomeChannel = self.client.get_channel(self.server["channels"]["Welcome"])
                return await welcomeChannel.send(f"<@{member.id}> There are no guilds open for recruitment currently! Please check back later.", delete_after=20)
            while True:
                nextChannel = list(channels)[index]
                if self.server["isOpen"][nextChannel] == "open":
                    break
                else:
                    index += 1
                    if index >= len(self.server["channels"]):
                        index = 2

            channel = self.client.get_channel(channels[nextChannel])
            leaderRole = self.server["roles"][nextChannel]
            overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(self.server["roles"]["Recruitee"]))
            await channel.set_permissions(member, overwrite=overwrite)
            await channel.send(f"(・ω・)ノ <@{member.id}> has arrived! <@&{leaderRole}>\nGuild leaders have 10m to respond or <@{member.id}> will be redirected to a new channel.")

            with open("data/server.json", "w") as f:
                self.server["general"]["nextChannel"] = index + 1
                if self.server["general"]["nextChannel"] >= len(self.server["channels"]):
                    self.server["general"]["nextChannel"] = 2
                json.dump(self.server, f, indent=4)
            recruitees = self.data.getRecruitees()
            recruitees[member.id] = [f"[Sent to {nextChannel}]"]
            self.data.updateRecruitees(recruitees)

            await logUsage(f"@{member.name} has been sent to #{channel.name} by @Raider Bot.", self.client)
            await self.guildTimeout(channel, member)

        except Exception as e:
            await handleException(e, self.client)



    async def guildTimeout(self, ogChannel, member):
        try:
            def whosent(m):
                return isRecruiterMessage(m.author) and m.channel == ogChannel
            message = await self.client.wait_for('message', check=whosent, timeout=600)
        except asyncio.TimeoutError:
            openGuilds = 0
            for guild in self.server["isOpen"]:
                if self.server["isOpen"][guild] == "open":
                    openGuilds += 1
            if openGuilds < 2:
                return await ogChannel.send("All other guilds are closed! Unable to redirect.")
            channels = self.server["channels"]
            for i in range(len(channels)):
                if channels[list(channels)[i]] == ogChannel.id:
                    index = i + 1
                    if index >= len(self.server["channels"]):
                        index = 2
                    break
            while True:
                nextChannel = list(channels)[index]
                if self.server["isOpen"][nextChannel] == "open":
                    break
                else:
                    index += 1
                    if index >= len(self.server["channels"]):
                        index = 2

            channel = self.client.get_channel(channels[nextChannel])
            leaderRole = self.server["roles"][nextChannel]
            overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(self.server["roles"]["Recruitee"]))
            await ogChannel.set_permissions(member, overwrite=None)
            await ogChannel.send(f"`User has been sent to another guild due to timeout.`")
            await channel.set_permissions(member, overwrite=overwrite)
            await channel.send(f"(・ω・)ノ <@{member.id}> has arrived! (Redirected due to timeout) <@&{leaderRole}>\nGuild leaders have 10m to respond or <@{member.id}> will be redirected to a new channel.")

            recruitees = self.data.getRecruitees()
            try:
                recruitees[str(member.id)].append(f"[Sent to {nextChannel} due to timeout]")
            except:
                pass
            self.data.updateRecruitees(recruitees)

            chatLog = "\n".join(recruitees[str(member.id)])
            if len(chatLog) > 2000:
                chatLog = chatLog[:1900] + "..."

            embed = discord.Embed()
            embed.add_field(name=f"{member.name}'s previous chat logs for your convenience:", value=f"** **\n```{chatLog}```")
            embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
            await channel.send(embed=embed)

            await logUsage(f"@{member.name} has been sent to #{channel.name} by @Raider Bot due to timeout.", self.client)
            await self.guildTimeout(channel, member)





    async def sendToGeneralChannel(self, member):
        # sends user to general channel after reaction 
        try:
            channels = self.server["channels"]
            channel = self.client.get_channel(channels["General"])
            for role in range(1, len(member.roles)):
                await member.remove_roles(member.roles[role])
            await member.add_roles(channel.guild.get_role(self.server["roles"]["General"]))
            await channel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")
            await logUsage(f"@{member.name} has been sent to #{channel.name} by @Raider Bot.", self.client)
        except Exception as e:
            await handleException(e, self.client)


    
    @commands.command()
    async def recruit(self, ctx, member: discord.Member):
        # recruit a user to a guild
        try:
            if await isRecruiter(ctx) and await isRecruitee(ctx, member):
                channels = self.server["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to recruit @{member.name} to {channelName}?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌") and reaction.message.id == message.id
                try: 
                    reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=300)
                except asyncio.TimeoutError:
                    return await message.clear_reactions()
                
                embed = discord.Embed()
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    await ctx.channel.set_permissions(member, overwrite=None)
                    overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
                    await member.remove_roles(ctx.channel.guild.get_role(self.server["roles"]["Recruitee"]))
                    await member.add_roles(ctx.channel.guild.get_role(self.server["roles"][channelName]))
                    with open("data/server.json", "w") as f:
                        self.server["newMembers"][channelName] += 1
                        json.dump(self.server, f, indent=4)
                    emoji = self.server["emojis"][channelName]
                    embed.add_field(name=f"@{member.name} has been recruited to {channelName} {emoji}✅", value="** **")
                    guildChannel = self.client.get_channel(self.server["guildChannels"][channelName])
                    await guildChannel.send(f"<@{member.id}> has arrived! `(Recruited to {channelName} by {ctx.author.name})`{emoji}")
                    recruitees = self.data.getRecruitees()
                    try:
                        recruitees.pop(str(member.id))
                    except:
                        pass
                    self.data.updateRecruitees(recruitees)
                    await logUsage(f"@{member.name} has been recruited to {channelName} by @{ctx.author.name}.", self.client)
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"@{member.name}'s recruitment has been aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as e:
            await handleException(e, self.client)



    @commands.command() 
    async def transfer(self, ctx, member: discord.Member):
        # send to channel due to unsuccessful recruit
        try:
            if await isRecruiter(ctx) and await isRecruitee(ctx, member):
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
                channels = self.server["channels"]
                field = "Please react with the corresponding number: \n"
                for i in range(len(channels) - 1):
                    field += f"\n{emojis[i]} `#{self.client.get_channel(channels[list(channels)[i+1]]).name}`"

                embed = discord.Embed()
                embed.add_field(name="Where would you like to send this user?", value=field)
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                for e in emojis:
                    await message.add_reaction(e)

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in emojis and reaction.message.id == message.id
                try: 
                    reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=300)
                except asyncio.TimeoutError:
                    return await message.clear_reactions()

                for e in range(len(emojis)):
                    if str(reaction.emoji) == emojis[e]:
                        targetName = list(channels)[e+1]
                        targetChannel = self.client.get_channel(channels[targetName])
                        await ctx.channel.set_permissions(member, overwrite=None)
                        overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
                        
                        if targetName == "General":
                            await member.remove_roles(ctx.channel.guild.get_role(self.server["roles"]["Recruitee"]))
                            await member.add_roles(ctx.channel.guild.get_role(self.server["roles"]["General"]))
                            await targetChannel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")
                            emoji = ""
                            recruitees = self.data.getRecruitees()
                            try:
                                recruitees.pop(str(member.id))
                            except:
                                pass
                            self.data.updateRecruitees(recruitees)
                        else:
                            if self.server["isOpen"][targetName] == "closed":
                                embed = discord.Embed()
                                embed.add_field(name=f"{targetName} is currently closed to new recruits! Please try a different guild ❌", value=f"** **")
                                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                                await message.edit(embed=embed)
                                return await message.clear_reactions()
                            await targetChannel.set_permissions(member, overwrite=overwrite)
                            leaderRole = self.server["roles"][targetName]
                            await targetChannel.send(f"(・ω・)ノ <@{member.id}> has landed! (Sent over by @{ctx.author.name}) <@&{leaderRole}>")
                            recruitees = self.data.getRecruitees()
                            try:
                                recruitees[str(member.id)].append(f"[Transferred to {targetName} by @{ctx.author.name}]")
                            except:
                                pass
                            self.data.updateRecruitees(recruitees)
                            chatLog = "\n".join(recruitees[str(member.id)])
                            if len(chatLog) > 2000:
                                chatLog = chatLog[:1900] + "..."

                            embed = discord.Embed()
                            embed.add_field(name=f"{member.name}'s previous chat logs for your convenience:", value=f"** **\n```{chatLog}```")
                            embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                            await targetChannel.send(embed=embed)
                            emoji = self.server["emojis"][targetName]

                        embed = discord.Embed()
                        embed.add_field(name=f"@{member.name} has been transferred to {targetName} {emoji}✅", value=f"** **")
                        embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                        await message.edit(embed=embed)
                        await message.clear_reactions()
                        await logUsage(f"@{member.name} has been transferred to {targetName} by @{ctx.author.name}.", self.client)
                        break

        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def openGuild(self, ctx):
        # opens guild for recruitees
        try:
            if await isRecruiter(ctx):
                channels = self.server["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                if self.server["isOpen"][channelName] == "open":
                    return await ctx.send("```This guild is already open to new members.```")
                
                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to open {channelName} to new recruits?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌") and reaction.message.id == message.id
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                embed = discord.Embed()
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    with open("data/server.json", "w") as f:
                        self.server["isOpen"][channelName] = "open"
                        json.dump(self.server, f, indent=4)
                    embed.add_field(name=f"{channelName} has been opened to new recruits ✅", value="** **")
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"Command aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
                await logUsage(f"{channelName} has been opened to new recruits by @{ctx.author.name}.", self.client)
                
        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def closeGuild(self, ctx):
        # closes guild for recruitees
        try:
            if await isRecruiter(ctx):
                channels = self.server["channels"]
                for c in channels:
                    if channels[c] == ctx.channel.id:
                        channelName = c

                if self.server["isOpen"][channelName] == "closed":
                    return await ctx.send("```This guild is already closed to new members.```")
                
                embed = discord.Embed()
                embed.add_field(
                    name=f"Do you want to close {channelName} to new recruits?", 
                    value=f"Please react with the corresponding emoji:\n\n✅`Yes`\n❌`No`\n"
                )
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                message = await ctx.send(embed=embed)
                await message.add_reaction("✅")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❌") and reaction.message.id == message.id
                reaction, user = await self.client.wait_for('reaction_add', check=check)
                
                embed = discord.Embed()
                embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
                if str(reaction.emoji) == "✅":
                    with open("data/server.json", "w") as f:
                        self.server["isOpen"][channelName] = "closed"
                        json.dump(self.server, f, indent=4)
                    embed.add_field(name=f"{channelName} has been closed to new recruits ✅", value="** **")
                elif str(reaction.emoji) == "❌":
                    embed.add_field(name=f"Command aborted ❌", value="** **")
                await message.edit(embed=embed)
                await message.clear_reactions()
                await logUsage(f"{channelName} has been closed to new recruits by @{ctx.author.name}.", self.client)

        except Exception as e:
            await handleException(e, self.client)


    
    @commands.Cog.listener()
    async def on_message(self, message):
        # check and log messages for recruitees
        try:
            whoSent = str(message.author.id)
            recruitees = self.data.getRecruitees()
            if whoSent in recruitees:
                if len(recruitees[whoSent]) < 30: 
                    if len(message.attachments) == 0:
                        recruitees[whoSent].append(message.content)
                    else:
                        recruitees[whoSent].append(message.attachments[0].url)
                    self.data.updateRecruitees(recruitees)
        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def recruitStats(self, ctx):
        # sends the monthly new members
        try:
            stats = self.server["newMembers"]
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
            embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)

            field = ""
            for guild in range(len(stats)):
                field += f"{self.server['colorEmojis'][list(stats)[guild]]} `{list(stats)[guild]}`: {stats[list(stats)[guild]]}\n"
            embed.add_field(name="** **", value=field)
            await ctx.send(embed=embed)
            await logUsage(f"Recruit stats requested by @{ctx.author.name}.", self.client)

        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def rotation(self, ctx):
        # returns the rotation of guilds
        try: 
            index = self.server["general"]["nextChannel"]
            order = []
            i = index
            while True:
                nextChannel = list(self.server["channels"])[i]
                if self.server["isOpen"][nextChannel] == "open":
                    order.append(self.server["colorEmojis"][nextChannel] + f" `{nextChannel}`")
                i += 1
                if i >= len(self.server["channels"]):
                    i = 2
                if i == index: break

            embed = discord.Embed(title="Guilds Rotation")
            embed.add_field(name="Next recruit goes to:", value=order[0], inline=False)
            embed.add_field(name="Followed by:", value="\n".join(order[1:]), inline=False)
            embed.set_footer(text=self.server["general"]["footer"], icon_url=self.client.user.avatar_url)
            await ctx.send(embed=embed)
            await logUsage(f"Rotation requested by @{ctx.author.name}.", self.client)

        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def forward(self, ctx):
        # changes the rotation
        if isDev(ctx):
            index = self.server["general"]["nextChannel"]
            while True:
                nextChannel = list(self.server["channels"])[index]
                index += 1
                if index >= len(self.server["channels"]):
                    index = 2
                if self.server["isOpen"][nextChannel] == "open":
                    break
            with open("data/server.json", "w") as f:
                self.server["general"]["nextChannel"] = index
                json.dump(self.server, f, index=4)
            await logUsage(f"Rotation forwarded by @{ctx.author.name}.", self.client)




    @tasks.loop(minutes=1)
    async def resetRecruitStats(self):
        # resets monthly new members after each month
        try:            
            time = str(datetime.utcnow())
            if time[8:10] == "01" and (time[11:16] == "00:00" or time[11:16] == "00:01"):
                for guild in self.server["newMembers"]:
                    self.server["newMembers"][guild] = 0
                with open("data/server.json", "w") as f:
                    json.dump(self.server, f, indent=4)
                await logEvent("Recruit stats have been reset.", self.client)
        except Exception as e:
            await handleException(e, self.client)



    async def deleteInactives(self):
        # remove inactive users from recruitees.json
        try:
            channel = self.client.get_channel(self.server["channels"]["Welcome"])
            guild = channel.guild
            recruitees = self.data.getRecruitees()
            newRecruitees = recruitees
            for r in recruitees:
                try:
                    member = await guild.fetch_member(int(r))
                    if member == None:
                        newRecruitees.pop(r)
                    elif guild.get_role(self.server["roles"]["Recruitee"]) not in member.roles:
                        newRecruitees.pop(r)
                except:
                    newRecruitees.pop(r)
            self.data.updateRecruitees(newRecruitees)
        except Exception as e:
            await handleException(e, self.client)



    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == self.server["general"]["guildID"]:
            channel = self.client.get_channel(self.server["channels"]["Welcome"])
            await member.add_roles(channel.guild.get_role(self.server["general"]["newMemberRole"]))
            await asyncio.sleep(1)
            await channel.send(f"<@{member.id}>", delete_after=1)
            await logEvent(f"@{member.name} has joined the server.", self.client)
            await asyncio.sleep(300)
            try:
                if channel.guild.get_role(self.server["general"]["newMemberRole"]) in member.roles:
                    await member.send(f"```Hey! I noticed you haven't reacted to the welcome message yet! Check #{channel.name} and react to gain access to the server.```")
            except Exception as e:
                await handleException(e, self.client)



    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == self.server["general"]["guildID"]:
            channel = self.client.get_channel(828439372923404328)
            await channel.send(f"@{member.name} has left the server... smh!")
            await logEvent(f"@{member.name} has left the server.", self.client)



def setup(client):
    client.add_cog(Recruit(client))
