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
            value="Returns this command list",
            inline=False
        )
        embed.add_field(
            name="★ **r.modhelp**",
            value="Returns the command list for moderation",
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
            name="★ **r.recruitstats**",
            value="Returns the monthly new members counts for each guild",
            inline=False
        )
        embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
        await ctx.send(embed=embed)
    


    @commands.command()
    async def modHelp(self, ctx):
        # mod help command
        embed = discord.Embed(
            title="Raider Bot's Mod Commands (r.)"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
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
        await ctx.send(embed=embed)



    @commands.command()
    async def gitPush(self, ctx):
        # push files to GitHub
        if ctx.author == self.client.get_user(430079880353546242):
            await ctx.send("Pushing latest files to GitHub.")
            with open('data/config.json') as d:
                config = json.load(d)
            filenames = ["data/config.json", "data/recruitees.json"]
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
                    logger.exception(e)



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



def setup(client):
    client.add_cog(Admin(client))