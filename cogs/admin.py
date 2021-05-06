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
        with open("data/exceptions.json", "w") as f:
            exceptions = {"exceptions":[]}
            json.dump(exceptions, f, indent=4)
        activity = discord.Game(name=f"Crush Them All! | r.help")
        await self.client.change_presence(activity=activity)
        await asyncio.sleep(43200)
        await gitPush()



    @commands.command()
    async def help(self, ctx):
        # help command
        left = '⏪'
        right = '⏩'
        pages = [self.makeGeneralHelpEmbed(), self.makeRecruitHelpEmbed(), self.makeModHelpEmbed()]
        message = await ctx.send(embed = pages[0])
        await message.add_reaction(left)
        await message.add_reaction(right)

        def check(reaction, user):
            return user == ctx.author

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
            except Exception as e:
                print(str(e))
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
            value="Returns the guild war rankings for the given guild `(Aliases: r.gw (guild tag))`",
            inline=False
        )
        embed.add_field(
            name="★ **r.guildwarraiders**",
            value="Returns the guild war rankings for all of the Raider guilds `(Aliases: r.gwr)`",
            inline=False
        )
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    def makeRecruitHelpEmbed(self):
        # make the recruit help embed
        embed = discord.Embed(
            title="Raider Bot's Recruitment Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
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
            name="★ **r.closeguild**",
            value="Closes guild to new recruits `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.openguild**",
            value="Opens guild to new recruits `(guild leader only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.rotation**",
            value="Returns the guild rotation for new recruits",
            inline=False
        )
        embed.add_field(
            name="★ **r.recruitstats**",
            value="Returns the monthly new members counts for each guild",
            inline=False
        )
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    def makeModHelpEmbed(self):
        # make the mod help embed
        embed = discord.Embed(
            title="Raider Bot's Mod Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(
            name="★ **r.purge (n)**",
            value="Purges n messages from current channel excluding pinned messages `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.purgeuser @user (n)**",
            value="Purges n messages from user in current channel excluding pinned messages `(server admin only)`",
            inline=False
        )
        embed.add_field(
            name="★ **r.purgeall**",
            value="Purges all messages is current channel excluding pinned messages `(server admin only)`",
            inline=False
        )
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        return embed



    @commands.command()
    async def gitPush(self, ctx):
        # push files to GitHub
        if ctx.author == self.client.get_user(430079880353546242):
            await ctx.send("Pushing latest files to GitHub.")
            with open('data/config.json') as d:
                config = json.load(d)
            filenames = ["data/config.json", "data/recruitees.json", "data/guildwar.json"]
            for filename in filenames: 
                try:
                    token = config["config"]["githubOath"]
                    repo = "amymainyc/cta-raiderbot"
                    branch = "main"
                    url = "https://api.github.com/repos/" + repo + "/contents/" + filename

                    base64content = base64.b64encode(open(filename, "rb").read())

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url + '?ref=' + branch, headers={"Authorization": "token " + token}) as data:
                            data = await data.json()
                    sha = data['sha']

                    if base64content.decode('utf-8') + "\n" != data['content']:
                        message = json.dumps(
                            {"message": "Automatic data update.",
                                "branch": branch,
                                "content": base64content.decode("utf-8"),
                                "sha": sha}
                        )

                        async with aiohttp.ClientSession() as session:
                            async with session.put(
                                url, data=message, headers={"Content-Type": "application/json", "Authorization": "token " + token}
                            ) as resp:
                                print(resp)

                except Exception as e:
                    channel = self.client.get_channel(config["config"]["errorLogs"])
                    await handleException(e, channel)



    @commands.Cog.listener()
    async def on_command_error(self, ctx : commands.Context, exception):
        # error handling
        logger.exception(exception)
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
            channel = self.client.get_channel(config["config"]["errorLogs"])
            await handleException(exception, channel)



def setup(client):
    client.add_cog(Admin(client))