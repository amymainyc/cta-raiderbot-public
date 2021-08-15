import discord
from discord.ext import commands, tasks
from utils.utils import *
from utils.data import Data
import asyncio



with open('data/server.json') as d:
    server = json.load(d)


class General(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.rateLimited = False
        self.data = Data()



    @commands.command()
    async def cat(self, ctx):
        try:
            if not self.rateLimited:
                item = await self.data.getCatPicture()
                embed = discord.Embed(description=f"Photo by [{item['user']}]({item['userLink']}) on [Unsplash]({item['unsplashLink']})")
                embed.set_image(url=item["link"])
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                await ctx.send(embed=embed)
                self.rateLimited = True
                await asyncio.sleep(2)
                self.rateLimited = False
            else:
                await ctx.send("```This command has been rate-limited due to Unsplash API restrictions. Please try again in a few seconds.```")
        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def dog(self, ctx):
        try:
            if not self.rateLimited:
                item = await self.data.getDogPicture()
                embed = discord.Embed(description=f"Photo by [{item['user']}]({item['userLink']}) on [Unsplash]({item['unsplashLink']})")
                embed.set_image(url=item["link"])
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                await ctx.send(embed=embed)
                self.rateLimited = True
                await asyncio.sleep(2)
                self.rateLimited = False
            else:
                await ctx.send("```This command has been rate-limited due to Unsplash API restrictions. Please try again in a few seconds.```")
        except Exception as e:
            await handleException(e, self.client)



    @commands.command()
    async def car(self, ctx):
        try:
            if not self.rateLimited:
                item = await self.data.getCarPicture()
                embed = discord.Embed(description=f"Photo by [{item['user']}]({item['userLink']}) on [Unsplash]({item['unsplashLink']})")
                embed.set_image(url=item["link"])
                embed.set_footer(text=server["general"]["footer"], icon_url=self.client.user.avatar_url)
                await ctx.send(embed=embed)
                self.rateLimited = True
                await asyncio.sleep(2)
                self.rateLimited = False
            else:
                await ctx.send("```This command has been rate-limited due to Unsplash API restrictions. Please try again in a few seconds.```")
        except Exception as e:
            await handleException(e, self.client)


    
def setup(client):
    client.add_cog(General(client))
