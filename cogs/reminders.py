import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
from loguru import logger
import asyncio
from utils.utils import *
from utils.data import *


with open('data/server.json') as d:
    server = json.load(d)


class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.data = Data()



    @commands.Cog.listener()
    async def on_ready(self):
        self.checkCalendar.start()
        self.rosterReminder.start()



    @tasks.loop(seconds=30)
    async def checkCalendar(self):
        # check for events on the calendar and sends a reminder 
        try:
            calendar = self.data.getReminders()

            nextEvents = []
            for e in calendar:
                time = calendar[e]["time"]
                intervals = calendar[e]["intervals"]
                if abs(int(datetime.now().timestamp()) - time) % intervals < 60:
                    nextEvents.append(e)

            if nextEvents != []:
                await asyncio.sleep(120)
                channel = self.client.get_channel(server["general"]["remindersChannel"])
                await channel.send(f"<@&797840056504680468>", delete_after=3)
                for event in nextEvents:
                    logger.info(f"Event: {event}")
                    color = discord.Color(int(calendar[event]["color"], 16))
                    embed = discord.Embed(title=event, color=color)
                    embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                    embed.set_image(url=calendar[event]["image"])
                    if event == "One hour until daily reset!":
                        days = calendar[event]["days"]
                        index = datetime.utcnow().weekday() + 1
                        if index == 7: index = 0
                        daysOfTheWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        day = daysOfTheWeek[index]
                        chest = days[day][0]
                        runes = days[day][1]
                        text = calendar[event]["description"].replace("[chest]", chest).replace("[runes]", runes)
                        color = discord.Color(int(days[day][3], 16))
                        embed = discord.Embed(title=event, color=color)
                        embed.set_thumbnail(url=days[day][2])
                    else:
                        text = calendar[event]["description"]
                        color = discord.Color(int(calendar[event]["color"], 16))
                        embed = discord.Embed(title=event, color=color)
                        embed.set_thumbnail(url=calendar[event]["thumbnail"])

                    embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                    embed.set_image(url=calendar[event]["image"])
                    value = f"**{text}**\n\n*To receive notifications for reminders like these, select the exclamation mark emoji at the bottom of <#716720818670927892>.*"
                    embed.add_field(name="** **", value=value)
                    await channel.send(embed=embed)
                    await logEvent(f"{event}", self.client)
                await asyncio.sleep(300)

        except Exception as e:
            await handleException(e, self.client)



    @commands.command(aliases=["setuprr"])
    async def setupRosterReminders(self, ctx):
        try:            
            if isLeader(ctx):
                rosterReminders = self.data.getRR()
                if not str(ctx.channel.id) in rosterReminders:
                    try:
                        def whosent(m):
                            return m.author == ctx.author

                        await ctx.send("```Please @ the role to tag when roster reminders get sent.```")
                        role = await self.client.wait_for('message', check=whosent, timeout=300)
                        roleID = role.content[3:-1]
                        role = ctx.guild.get_role(int(roleID))
                        if role is None:
                            return await ctx.send("```Invalid role. Please check and try again.```")
                        else:
                            rosterReminders[ctx.channel.id] = roleID
                            self.data.updateRR(rosterReminders)
                            await logUsage(f"Roster reminders set up for @{role.name} in #{ctx.channel.name}.", self.client)
                            return await ctx.send("```Roster reminders have been set up in this channel. I will send a reminder at the beginning of every month to post rosters! If you want to change something, do r.disablerr and try this command again.```")
                    except asyncio.TimeoutError:
                        return await ctx.send("```You took too long \:( Please try the command again.```")
                else:
                    return await ctx.send("```Roster reminders already set up in this channel. If you want to change something, do r.disablerr and try this command again.```")
            else:
                return await ctx.send("```You must have a leader role to use this command.```")
        except Exception as e:
            await handleException(e, self.client)



    @commands.command(aliases=["disablerr"])
    async def disableRosterReminders(self, ctx):
        try:            
            if isLeader(ctx):
                rosterReminders = self.data.getRR()
                if not str(ctx.channel.id) in rosterReminders:
                    return await ctx.send("```Roster reminders are not set up in this channel. Do r.setuprr to set them up.```")
                else:
                    rosterReminders.pop(str(ctx.channel.id))
                    self.data.updateRR(rosterReminders)
                    await logUsage(f"Roster reminders disabled in #{ctx.channel.name}.", self.client)
                    return await ctx.send("```Roster reminders have been disabled in this channel.```")
            else:
                return await ctx.send("```You must have a leader role to use this command.```")
        except Exception as e:
            await handleException(e, self.client)



    @tasks.loop(minutes=1)
    async def rosterReminder(self):
        # reminds people to post their rosters every month
        try:            
            time = str(datetime.utcnow())
            if time[8:10] == "01" and (time[11:16] == "00:00" or time[11:16] == "00:01"):
                rosterReminders = self.data.getRR()
                guild = self.client.get_guild(server["general"]["guildID"])
                for channelID in rosterReminders:
                    try:
                        channel = guild.get_channel(int(channelID))
                        role = guild.get_role(int(rosterReminders[channelID]))
                        await channel.send(f"{role.mention} It's the beginning of the month! Please post your CTA rosters.")
                    except:
                        await handleException(e, self.client)
                await logEvent("Roster reminders have been sent.", self.client)
                await asyncio.sleep(1200)
        except Exception as e:
            await handleException(e, self.client)



    
def setup(client):
    client.add_cog(Reminders(client))
