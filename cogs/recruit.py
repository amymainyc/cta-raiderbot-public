from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import aiohttp
import asyncio
from utils.utils import *
from datetime import datetime



global config
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



    @commands.command()
    async def setChannels(self, ctx):
        # sets up recruitment channels
        if await isAdmin(ctx):
            channel = ctx.channel.id 
            channelData = config["channels"]
            for c in channelData: 
                channelData[c] = 0

            def whosent(m):
                return m.author == ctx.author

            for c in channelData:
                text = f"```Please reply with the channel id for your {c} channel."
                for ch in channelData:
                    channelID = channelData[ch]
                    if channelID == 0:
                        text += f"\n\n{ch} Channel: "
                        break
                    channelName = self.client.get_channel(channelID).name
                    text += f"\n\n{ch} Channel: #{channelName}"
                text += "```"
                botMessage = await ctx.send(text)
                
                try:
                    channelID = await self.client.wait_for('message', check=whosent, timeout=300)
                    await channelID.delete() 
                    channelID = channelID.content
                    channelData[c] = int(channelID)
                    await botMessage.delete()

                except asyncio.TimeoutError:
                    return await ctx.send('You took too long \:( Please try the command again.')
                except:
                    return await ctx.send('```Invalid channel ID. Please check and try again.```')

            with open("data/config.json", "w") as f:
                config["channels"] = channelData
                json.dump(config, f, indent=4)
            await ctx.send('```Recruitment channels have been set!```')
            await self.sendEmbed()



    async def sendEmbed(self):
        welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
        embed = discord.Embed(
            title="Welcome to the Raiders discord server!", 
            color=0x000000,
            description="Follow the instructions below to gain access to channels."
        )
        embed.add_field(name="** **", value="React with  :green_circle:  to be sent to a recruitment channel. \nReact with  :red_circle:  if you already have a guild or don't want to join Raiders.")
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        embed.set_image(url="data/banner.png")
        welcomeMessage = await welcomeChannel.send(embed=embed)
        await welcomeMessage.add_reaction("🟢")
        await welcomeMessage.add_reaction("🔴")
        with open("data/config.json", "w") as f:
            config["config"]["welcomeMessageID"] = welcomeMessage.id
            json.dump(config, f, indent=4)



    @commands.command()
    async def sendNewEmbed(self, ctx):
        if isAdmin:
            welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
            embed = discord.Embed(
                title="Welcome to the Raiders discord server!", 
                color=0x000000,
                description="Follow the instructions below to gain access to channels."
            )
            embed.add_field(name="** **", value="React with  :green_circle:  to be sent to a recruitment channel. \nReact with  :red_circle:  if you already have a guild or don't want to join Raiders.")
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.set_image(url=config["config"]["bannerUrl"])
            welcomeMessage = await welcomeChannel.send(embed=embed)
            await welcomeMessage.add_reaction("🟢")
            await welcomeMessage.add_reaction("🔴")
            with open("data/config.json", "w") as f:
                config["config"]["welcomeMessageID"] = welcomeMessage.id
                json.dump(config, f, indent=4)



    @commands.command()
    async def setRoles(self, ctx):
        # sets up recruitment roles
        if await isAdmin(ctx):
            channel = ctx.channel.id
            roleData = config["roles"] 
            for r in roleData:
                roleData[r] = 0

            def whosent(m):
                return m.author == ctx.author

            for r in roleData:
                text = f"```Please tag your {r} role below."
                for ro in roleData:
                    roleID = roleData[ro]
                    if roleID == 0:
                        text += f"\n\n{ro} Role: "
                        break
                    role = ctx.guild.get_role(roleID).name
                    text += f"\n\n{ro} Role: @{role}"
                text += "```"
                botMessage = await ctx.send(text)
                
                try:
                    roleID = await self.client.wait_for('message', check=whosent, timeout=300)
                    await roleID.delete()
                    roleID = roleID.content[3:-1]
                    roleData[r] = int(roleID)
                    await botMessage.delete()

                except asyncio.TimeoutError:
                    return await ctx.send('You took too long \:( Please try the command again.')
                except Exception as e:
                    logger.exception(e)
                    return await ctx.send('```Invalid role. Please check and try again.```')

            with open("data/config.json", "w") as f:
                config["roles"] = roleData
                json.dump(config, f, indent=4)
            await ctx.send("```Recruitment roles have been set!```")



    async def checkWelcomeMessage(self):
        # make sure the welcome message has preset reactions
        welcomeMessageID = config["config"]["welcomeMessageID"]
        welcomeChannel = self.client.get_channel(config["channels"]["Welcome"])
        message = await welcomeChannel.fetch_message(welcomeMessageID)
        await message.add_reaction('🟢')
        await message.add_reaction('🔴')


        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check for reactions on the welcome message
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
                if payload.emoji.name == '🟢':
                    await self.sendToNextGuild(payload.member)
                if payload.emoji.name == '🔴':
                    await self.sendToVisitorChannel(payload.member)



    async def sendToNextGuild(self, member):
        # sends user to next channel after reaction
        with open('data/config.json') as d:
            config = json.load(d)
        channels = config["channels"]
        nextChannel = config["config"]["nextChannel"]
        nextChannel = list(channels)[nextChannel]
        channel = self.client.get_channel(channels[nextChannel])
        leaderRole = config["roles"][nextChannel]
        overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
        for role in range(1, len(member.roles)):
            await member.remove_roles(member.roles[role])
        await member.add_roles(channel.guild.get_role(config["roles"]["Recruitee"]))
        await channel.set_permissions(member, overwrite=overwrite)
        await channel.send(f"(・ω・)ノ <@{member.id}> has arrived! <@&{leaderRole}>")

        with open("data/config.json", "w") as f:
            config["config"]["nextChannel"] += 1
            if config["config"]["nextChannel"] >= len(config["channels"]):
                config["config"]["nextChannel"] = 2
            json.dump(config, f, indent=4)
        with open("data/recruitees.json") as f:
            recruitees = json.load(f)
            recruitees[member.id] = [f"[Sent to {nextChannel}]"]
        with open("data/recruitees.json", "w") as f:
            json.dump(recruitees, f, indent=4)



    async def sendToVisitorChannel(self, member):
        # sends user to visitor channel after reaction 
        with open('data/config.json') as d:
            config = json.load(d)
        channels = config["channels"]
        channel = self.client.get_channel(channels["Visitor"])
        await member.add_roles(channel.guild.get_role(config["roles"]["Visitor"]))
        await channel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")


    
    @commands.command()
    async def recruit(self, ctx, member: discord.Member):
        # recruit a user to a guild
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
                embed.add_field(name=f"@{member.name} has been recruited to {channelName} ✅", value="** **")
                with open("data/recruitees.json") as f:
                    recruitees = json.load(f)
                    recruitees.pop(str(member.id))
                with open("data/recruitees.json", "w") as f:
                    json.dump(recruitees, f, indent=4)
            elif str(reaction.emoji) == "❌":
                embed.add_field(name=f"@{member.name}'s recruitment has been aborted ❌", value="** **")
            await message.edit(embed=embed)
            await message.clear_reactions()



    @commands.command() 
    async def transfer(self, ctx, member: discord.Member):
        # send to channel due to unsuccessful recruit
        if await isLeader(ctx) and await isRecruitee(ctx, member):
            with open('data/config.json') as d:
                config = json.load(d)
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
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
                    await targetChannel.set_permissions(member, overwrite=overwrite)
                    leaderRole = config["roles"][targetName]
                    
                    if targetName == "Visitor":
                        await member.remove_roles(ctx.channel.guild.get_role(config["roles"]["Recruitee"]))
                        await member.add_roles(ctx.channel.guild.get_role(config["roles"]["Visitor"]))
                        await targetChannel.send(f"(・ω・)ノ <@{member.id}> has joined the party!")
                        with open("data/recruitees.json") as f:
                            recruitees = json.load(f)
                            recruitees.pop(str(member.id))
                        with open("data/recruitees.json", "w") as f:
                            json.dump(recruitees, f, indent=4)
                    else:
                        await targetChannel.send(f"(・ω・)ノ <@{member.id}> has landed! (Sent over by @{ctx.author.name}) <@&{leaderRole}>")
                        with open("data/recruitees.json") as f:
                            recruitees = json.load(f)
                            recruitees[str(member.id)].append(f"[Transferred to {targetName} by @{ctx.author.name}]")
                        with open("data/recruitees.json", "w") as f:
                            json.dump(recruitees, f, indent=4)
                        chatLog = "\n".join(recruitees[str(member.id)])
                        if len(chatLog) > 2000:
                            chatLog = chatLog[:1900] + "..."

                        embed = discord.Embed()
                        embed.add_field(name=f"{member.name}'s previous chat logs for your convenience:", value=f"** **\n```{chatLog}```")
                        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                        await targetChannel.send(embed=embed)

                    embed = discord.Embed()
                    embed.add_field(name=f"@{member.name} has been sent to {targetName} ✅", value=f"** **")
                    embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
                    await message.edit(embed=embed)
                    await message.clear_reactions()
                    break


    
    @commands.Cog.listener()
    async def on_message(self, message):
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



    @commands.command()
    async def recruitStats(self, ctx):
        # sends the monthly new members
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
        emojis = ["🟠", "🟢", "🔵", "🔴", "🟣", "⚫️", "🟤", "⚪️"]
        for guild in range(len(stats)):
            field += f"{emojis[guild]} {list(stats)[guild]}: {stats[list(stats)[guild]]}\n"
        embed.add_field(name="** **", value=field)
        await ctx.send(embed=embed)



    @tasks.loop(minutes=1)
    async def resetRecruitStats(self):
        with open('data/config.json') as d:
            config = json.load(d)
        # reset the new members counts after each month
        time = str(datetime.utcnow())
        if time[8:10] == "01" and (time[11:16] == "00:00" or time[11:16] == "00:01"):
        # if time[8:10] == "17" and time[11:16] == "00:40":
            for guild in config["newMembers"]:
                config["newMembers"][guild] = 0
            with open("data/config.json", "w") as f:
                json.dump(config, f, indent=4)



    async def deleteInactives(self):
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



    @commands.Cog.listener()
    async def on_command_error(self, ctx : commands.Context, exception):
        if isinstance(exception, commands.MemberNotFound):
            await ctx.send('```Invalid user! Make sure you are tagging the right user.```')



def setup(client):
    client.add_cog(Recruit(client))