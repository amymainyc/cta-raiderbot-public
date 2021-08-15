import aiohttp
import json
import base64
from loguru import logger
import discord
import traceback



with open('data/server.json') as d:
    server = json.load(d)
with open('data/config.json') as d:
    config = json.load(d)



async def isAdmin(ctx):
    # check if user is server administrator
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send('```You must me a server administrator to use this command.```')
        return False
    return True



async def isRecruiter(ctx):
    # check if user is guild leader
    role = ctx.guild.get_role(server["roles"]["Recruitee"])
    userRoles = ctx.message.author.roles
    if role in userRoles:
        await ctx.send('```Recruitees cannot use this command.```')
        return False
    channels = server["channels"]
    for c in channels:
        if channels[c] == ctx.channel.id and c != "General" and c != "Welcome":
            return True
    await ctx.send('```This command can only be used in recruitment channels.```')
    return False



def isRecruiterMessage(user):
    # check if user is guild leader
    guild = user.guild
    role = guild.get_role(server["roles"]["Recruitee"])
    userRoles = user.roles
    if role in userRoles:
        return False
    return True



def isLeader(ctx):
    userRoles = ctx.message.author.roles
    leaderRoles = []
    for role in server["leaderRoles"]:
        leaderRoles.append(server["leaderRoles"][role])
    for role in userRoles:
        if role.id in leaderRoles:
            return True
    return False



def isDev(ctx):
    if ctx.author.id == 430079880353546242 or ctx.author.id == 267813665296744450:
        return True
    return False



async def isRecruitee(ctx, user):
    # add a try statement to check for validity
    userRoles = user.roles
    role = ctx.guild.get_role(server["roles"]["Recruitee"])
    if role not in userRoles:
        await ctx.send('```You can only user this command on recruitees.```')
        return False

    if ctx.channel.overwrites_for(user).is_empty():
        await ctx.send("```This user isn't a recruitee in this channel.```")
        return False
    return True



async def handleException(e, client):
    logger.exception(e)
    for channelID in server["general"]["logs"]:
        channel = client.get_channel(channelID)
        tb = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
        embed = discord.Embed(title="⛔️ ERROR ⛔️", color=0xff1100, description=f"```{tb}```")
        await channel.send(embed=embed)



async def logUsage(str, client):
    for channelID in server["general"]["logs"]:
        channel = client.get_channel(channelID)
        embed = discord.Embed(title="✅ USAGE ✅", color=0x1aff00, description=f"```{str}```")
        await channel.send(embed=embed)



async def logEvent(str, client):
    for channelID in server["general"]["logs"]:
        channel = client.get_channel(channelID)
        embed = discord.Embed(title="⚠️ EVENT ⚠️", color=0xfff700, description=f"```{str}```")
        await channel.send(embed=embed)



async def gitPush():
    # push files to GitHub
    logger.info("Pushing latest files to GitHub.")
    filenames = ["data/server.json"]
    for filename in filenames: 
        try:
            token = config["config"]["githubOath"]
            repo = "amymainyc/raider-bot"
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



def formatNum(num1):
    num1 = str(round(float(num1)))
    num2 = ""
    for i in range(len(num1)):
        if len(num1[len(num1) - i:]) % 3 == 0 and num2 != "":
            num2 = "," + num2
        num2 = num1[len(num1) - i - 1] + num2
    return num2
