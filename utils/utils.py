import aiohttp
import json
import base64
from loguru import logger
import discord



async def isAdmin(ctx):
    # check if user is server administrator
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send('```You must me a server administrator to use this command.```')
        return False
    return True



async def isLeader(ctx):
    # check if user is guild leader
    with open('data/config.json') as d:
        config = json.load(d)
    role = ctx.guild.get_role(config["roles"]["Recruitee"])
    userRoles = ctx.message.author.roles
    if role in userRoles:
        await ctx.send('```Recruitees cannot use this command.```')
        return False
    channels = config["channels"]
    for c in channels:
        if channels[c] == ctx.channel.id and c != "General" and c != "Welcome":
            return True
    await ctx.send('```This command can only be used in recruitment channels.```')
    return False



def isGuildLeader(user):
    # check if user is guild leader
    with open('data/config.json') as d:
        config = json.load(d)
    guild = user.guild
    role = guild.get_role(config["roles"]["Recruitee"])
    userRoles = user.roles
    if role in userRoles:
        return False
    return True



async def isRecruitee(ctx, user):
    # add a try statement to check for validity
    userRoles = user.roles
    with open('data/config.json') as d:
        role = ctx.guild.get_role(json.load(d)["roles"]["Recruitee"])
    if role not in userRoles:
        await ctx.send('```You can only user this command on recruitees.```')
        return False

    if ctx.channel.overwrites_for(user).is_empty():
        await ctx.send("```This user isn't a recruitee in this channel.```")
        return False
    return True



async def handleException(e, channel):
    logger.exception(e)
    await channel.send(f"```{str(e)}```")



async def gitPush():
    # push files to GitHub
    logger.info("Pushing latest files to GitHub.")
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