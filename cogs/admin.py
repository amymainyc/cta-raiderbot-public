from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import asyncio
from utils.utils import *
from utils.data import Data
from datetime import datetime



with open('data/server.json') as d:
    server = json.load(d)



class Admin(commands.Cog):



    def __init__(self, client):
        self.client = client
        self.data = Data()



    @commands.Cog.listener()
    async def on_ready(self):
        # bot startup tasks
        await logEvent("Bot has finished rebooting.", self.client)
        activity = discord.Game(name=f"Crush Them All! | r.help")
        await self.client.change_presence(activity=activity)
        await self.resetCookieStats.start()
        await asyncio.sleep(43200)
        await gitPush()



    @commands.command()
    async def help(self, ctx):
        # help command
        await logUsage(f"Help command requested by @{ctx.author.name}.", self.client) 
        left = '⏪'
        right = '⏩'
        pages = [self.makeGeneralHelpEmbed(), self.makeRecruitHelpEmbed(), self.makeModHelpEmbed()]
        message = await ctx.send(embed = pages[0])
        await message.add_reaction(left)
        await message.add_reaction(right)

        def check(reaction, user):
            return user == ctx.message.author and reaction.message.id == message.id

        i = 0
        reaction = None

        while True:
            if str(reaction) == left:
                i -= 1
                if i < 0:
                    i = len(pages) - 1
                await message.edit(embed=pages[i])
            elif str(reaction) == right:
                i += 1
                if i > len(pages) - 1:
                    i = 0
                await message.edit(embed=pages[i])
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=300, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
        await message.clear_reactions()
    


    def makeGeneralHelpEmbed(self):
        # make the general help embed
        embed = discord.Embed(
            title="Raider Bot's Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(
            name="★ **r.help**",
            value="Returns this command list",
            inline=False
        )
        embed.add_field(
            name="★ **r.guildwar (guild tag)**",
            value="Returns the guild war rankings for the given guild. `(Aliases: r.gw (guild tag))`",
            inline=False
        )
        embed.add_field(
            name="★ **r.guildwarraiders**",
            value="Returns the guild war rankings for all of the Raider guilds. `(Aliases: r.gwr)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.hero (hero)**",
            value="Returns general hero info and rune recommendations. `(Aliases: r.h)`\n`Ex: r.hero frost queen 7 4`",
            inline=False
        )
        embed.add_field(
            name="★ **r.compare (hero1) <stars> <awakened>, (hero2) ...**",
            value="Compares the stats of those heros. `(Aliases: r.cpr)`\n`Ex: r.compare sg 4 2, xak 5 3`",
            inline=False
        )
        embed.add_field(
            name="★ **r.compare (type1) <subtype> <stars> <awakened>, (type2) ...**",
            value="Compares the stats of the hero types given. `(Aliases: r.cpr)`\n`Ex: r.compare epic dark, legendary dark`",
            inline=False
        )
        embed.add_field(
            name="★ **r.blitzcalc star1 medals star2**",
            value="Calculates how many blitz chests and flooz you need to reach a certain star. `(Aliases: r.bc)`\n`Ex: r.bc 6 2200 7`",
            inline=False
        )
        embed.add_field(
            name="★ **r.crushercalc star1 medals star2**",
            value="Calculates how many blitz chests and flooz you need to reach a certain star. `(Aliases: r.bc)`\n`Ex: r.cc 6 2200 7`",
            inline=False
        )
        embed.add_field(
            name="★ **r.cat, r.dog, r.car**",
            value="Returns a random picture of that thing.",
            inline=False
        )
        embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    def makeRecruitHelpEmbed(self):
        # make the recruit help embed
        embed = discord.Embed(
            title="Raider Bot's Recruitment Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(
            name="★ **r.recruit @user**",
            value="Recruits a user to a guild. `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.transfer @user**",
            value="Sends the user to another channel due to unsuccessful recruitment. `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.closeguild**",
            value="Closes guild to new recruits. `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.openguild**",
            value="Opens guild to new recruits. `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.rotation**",
            value="Returns the guild rotation for new recruits.",
            inline=False
        )
        embed.add_field(
            name="★ **r.recruitstats**",
            value="Returns the monthly new members counts for each guild.",
            inline=False
        )
        embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    def makeModHelpEmbed(self):
        # make the mod help embed
        embed = discord.Embed(
            title="Raider Bot's Mod Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(
            name="★ **r.purge (n)**",
            value="Purges n messages from current channel excluding pinned messages. `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.purgeuser @user (n)**",
            value="Purges n messages from user in current channel excluding pinned messages. `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.purgeall**",
            value="Purges all messages is current channel excluding pinned messages. `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.setuprr, r.disablerr**",
            value="Sets up/disables roster reminders in the channel the command is sent in. `(guild leader only)`",
            inline=False
        )
        embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    @commands.command()
    async def viewJson(self, ctx):
        try:
            if isDev(ctx):
                await ctx.send(file=discord.File(fp="data/server.json", filename="server.json"))
        except Exception as e: 
            await handleException(e, self.client)



    @commands.command()
    async def gitPush(self, ctx):
        # push files to GitHub
        if ctx.author == self.client.get_user(430079880353546242):
            await ctx.send("Pushing latest files to GitHub.")
            await gitPush()



    @commands.Cog.listener()
    async def on_command_error(self, ctx : commands.Context, exception):
        # error handling
        if isinstance(exception, commands.CommandNotFound):
            return await ctx.send("```Command not found! Check r.help for usage instructions.```")
        if isinstance(exception, commands.MemberNotFound):
            return await ctx.send('```Invalid user! Make sure you are tagging the right user.```')
        if isinstance(exception, commands.MissingRequiredArgument):
            return await ctx.send("```You are missing required arguments! Check r.help for usage instructions.```")
        if isinstance(exception, commands.BadArgument):
            return await ctx.send("```Invalid arguments! Check r.help for usage instructions.```")
        if isinstance(exception, commands.TooManyArguments):
            return await ctx.send("```Too many arguments! Check r.help for usage instructions.```")
        else:
            await handleException(exception, self.client)
            return await ctx.send("```There was an error executing this command. The developers have been notified.```")



    @commands.command()
    async def purge(self, ctx, num_messages: int):
        # purge n messages from current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return not msg.pinned

            try:
                await ctx.message.delete()
                await channel.purge(limit=num_messages, check=check, before=None)
            except:
                pass
            await logUsage(f"Purged {num_messages} messages in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



    @commands.command()
    async def purgeUser(self, ctx, user: discord.User, num_messages: int):
        # purges n messages from a user in current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return msg.author.id == user.id and not msg.pinned

            try:
                await ctx.message.delete()
                await channel.purge(limit=num_messages, check=check, before=None)
            except:
                pass
            await logUsage(f"Purged {num_messages} messages by @{user.name} in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



    @commands.command()
    async def purgeAll(self, ctx):
        # purge all messages from current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return not msg.pinned

            try:
                await ctx.message.delete()
                await channel.purge(check=check, before=None)
            except:
                pass
            await logUsage(f"Purged all messages in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



    @commands.command()
    async def giveCookie(self, ctx, member: discord.Member):
        # gives a cookie to a user
        try:
            if isLeader(ctx):
                cookieData = self.data.getCookies()
                if not str(member.id) in cookieData:
                    cookieData[str(member.id)] = 1
                else:
                    cookieData[str(member.id)] += 1
                self.data.updateCookies(cookieData)
                cookie = await self.data.getCookiePicture()
                embed = discord.Embed(
                    description=f"{ctx.author.mention} gave a cookie to {member.mention}!" \
                        f"\n{member.mention} now has {cookieData[str(member.id)]} cookies. " \
                        f"Check your cookie count with `r.cookiestats`."
                )
                embed.set_image(url=cookie["link"])
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                await ctx.send(embed=embed)
                await logUsage(f"@{ctx.author.name} gave a cookie to @{member.name}.", self.client) 
        except Exception as e:
            await handleException(e, self.client)



    @commands.command(aliases=["cookietop"])
    async def cookieStats(self, ctx):
        # shows top cookie holders this month
        try:
            cookieData = self.data.getCookies()
            if not str(ctx.author.id) in cookieData:
                cookieCount = 0
            else:
                cookieCount = cookieData[str(ctx.author.id)]
            leaderboard = []
            for c in cookieData:
                if leaderboard == []:
                    leaderboard.append([c, cookieData[c]])
                    continue
                for l in range(len(leaderboard)):
                    if leaderboard[l][1] <= cookieData[c]:
                        leaderboard.insert(l, [c, cookieData[c]])
                        if len(leaderboard) > 10:
                            leaderboard.pop(-1)
                        break

            embed = discord.Embed(title="Monthly Cookie Stats :cookie:", description=f"Your cookies: {cookieCount}")
            guild = self.client.get_guild(server["general"]["guildID"]) 
            body = ""
            for l in range(len(leaderboard)):
                try:
                    body += f"#{str(l + 1)} {(await guild.fetch_member(int(leaderboard[l][0]))).mention} ({str(leaderboard[l][1])} cookies)\n"
                except:
                    body += f"#{str(l + 1)} <@{leaderboard[l][0]}> ({str(leaderboard[l][1])} cookies)\n"
            embed.add_field(name="** **", value=body)
            embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
            await ctx.send(embed=embed)

        except Exception as e:
            await handleException(e, self.client)



    @tasks.loop(minutes=1)
    async def resetCookieStats(self):
        # resets cookie stats after each month
        try:            
            time = str(datetime.utcnow())
            if time[8:10] == "01" and (time[11:16] == "00:00" or time[11:16] == "00:01"):
                cookieStats = {"430079880353546242": 1}
                self.data.updateCookies(cookieStats)
                await logEvent("Cookie stats have been reset.", self.client)
        except Exception as e:
            await handleException(e, self.client)



def setup(client):
    client.add_cog(Admin(client))