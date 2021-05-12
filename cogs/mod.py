from discord.ext import commands
from discord import User, errors
from utils.utils import *


class Mod(commands.Cog):



    def __init__(self, client):
        self.client = client



    @commands.command()
    async def purge(self, ctx, num_messages: int):
        # purge n messages from current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return not msg.pinned

            await ctx.message.delete()
            await channel.purge(limit=num_messages, check=check, before=None)
            await logUsage(f"Purged {num_messages} messages in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



    @commands.command()
    async def purgeUser(self, ctx, user: User, num_messages: int):
        # purges n messages from a user in current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return msg.author.id == user.id and not msg.pinned

            await ctx.message.delete()
            await channel.purge(limit=num_messages, check=check, before=None)
            await logUsage(f"Purged {num_messages} messages by @{user.name} in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



    @commands.command()
    async def purgeAll(self, ctx):
        # purge all messages from current channel
        if await isAdmin(ctx):
            channel = ctx.message.channel

            def check(msg):
                return not msg.pinned

            await ctx.message.delete()
            await channel.purge(check=check, before=None)
            await logUsage(f"Purged all messages in #{ctx.message.channel.name}, requested by @{ctx.author.name}.", self.client) 



def setup(client):
    client.add_cog(Mod(client))