from discord.ext import commands, tasks
import discord
import json
from loguru import logger
import asyncio
from bs4 import BeautifulSoup
import aiohttp
import sys
from utils.utils import *



with open('data/config.json') as d:
    config = json.load(d)



class General(commands.Cog):



    def __init__(self, client):
        self.client = client
    


    @commands.Cog.listener()
    async def on_ready(self):
        sys.setrecursionlimit(10000)
        await asyncio.sleep(1800)
        await self.cacheGuildWar.start()


    
    @commands.command(aliases=["gw"])
    async def guildWar(self, ctx, guild):
        # gets guild war stats for guild
        try:
            logger.info(f"Getting guild war stats for {guild}.")
            with open("data/guildwar.json") as f:
                rankings = json.load(f)
            isGuild = False
            for r in rankings:
                if rankings[r][0][1:4] == guild:
                    guild = rankings[r][0]
                    score = rankings[r][1]
                    rank = str(r)
                    isGuild = True
                    break
            if not isGuild:
                return await ctx.send("```Guild not found! Make sure you have the right guild tag and the capitalization is correct.```")
            embed = discord.Embed(title=f"⚔️ Guild War Ranking")
            embed.add_field(name=guild, value=f"Ranking: #{rank}\nScore: {score}")
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.set_image(url=config["config"]["guildWarBannerUrl"])
            await ctx.send(embed=embed)
            await logUsage(f"Guild war stats for {guild} requested by @{ctx.author.name}.", self.client) 
        except Exception as e:
            await handleException(e, self.client)



    @commands.command(aliases=["gwr"])
    async def guildWarRaiders(self, ctx):
        # gets guild war stats for raider guilds
        try:
            logger.info("Getting guild war stats for Raider guilds.")
            with open("data/guildwar.json") as f:
                rankings = json.load(f)
            text = "```"
            for r in rankings:
                if rankings[r][0][1:4].lower() == "rdr":
                    spaces1 = " " * (5 - len(str(r)))
                    text += f"\n# {str(r)}{spaces1}{rankings[r][0]}\n       Score: {rankings[r][1]}"
            text += "```"
            embed = discord.Embed(title="⚔️ Raiders Guild War Rankings")
            embed.add_field(name="** **", value=text)
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.set_image(url=config["config"]["bannerUrl"])
            await ctx.send(embed=embed)
            await logUsage(f"Guild war stats for Raiders requested by @{ctx.author.name}.", self.client) 
        except Exception as e:
            await handleException(e, self.client)



    @tasks.loop(minutes=30)
    async def cacheGuildWar(self):
        # caches all guild war stats
        leaderboard = {}
        data = []
        for offset in range(0, 5):
            URL = config["config"]["guildWar"] + str(offset)
            logger.info(f"Getting guild war stats: {URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as page:
                    html = await page.text()
                    soup = BeautifulSoup(html, 'html.parser')
            soup = soup.find("tbody")
            guilds = soup.findAll("td")
            
            for g in range(len(guilds)):
                content = guilds[g].contents
                for c in range(len(content)):
                    content[c] = str(content[c])
                content = "".join(content).strip()
                content = "".join(content.split("\n"))
                content = "".join(content.split("\t"))
                soup = BeautifulSoup(content, "html.parser")
                guilds[g] = str(soup.get_text())
            data = data + guilds

        leaderboard[1] = [data[1], data[2]]
        leaderboard[2] = [data[4], data[5]]
        leaderboard[3] = [data[7], data[8]]
        i = 9
        while (i < len(data)):
            leaderboard[int(data[i])] = [data[i + 1], data[i + 2]]
            i += 3

        with open("data/guildwar.json", "w") as f:
            json.dump(leaderboard, f, indent=4)



    @commands.command(aliases=["h"])
    async def hero(self, ctx, *params):
        try:
            if len(params) == 0:
                return await ctx.send("```You are missing required arguments! Check r.help for usage instructions.```")
            starCount = [-1, -1]
            hero = []
            for p in params:
                try:
                    num = int(p)
                    if num < 1 and starCount[0] == -1:
                        return await ctx.send("```Star counts must be greater than 0.```")
                    if num > 7:
                        return await ctx.send("```Star counts must be less than 7.```")
                    if starCount[0] == -1:
                        starCount[0] = num
                    else:
                        starCount[1] = num
                except ValueError:
                    hero.append(p)
            if starCount[0] == -1:
                starCount[0] = 1
            if starCount[1] == -1:
                starCount[1] = 0
            if starCount[0] < starCount[1]:
                return await ctx.send("```Awakened stars cannot be greater than regular stars.```")
            hero = self.getHero(" ".join(hero))
            if hero == -1:
                return await ctx.send("```Invalid hero!```")
            await logUsage(f"Hero data for {hero} requested by @{ctx.author.name}.", self.client)

            with open("data/encyclopedia.json") as f:
                heroes = json.load(f)
                heroData = heroes[hero]
            with open("data/emojis.json") as f:
                emojis = json.load(f)

            attack = float(heroData['Base Stats']['ATK'])
            health = float(heroData['Base Stats']['HP'])
            defense = float(heroData['Base Stats']['DEF'])
            for i in range(starCount[0] - 1):
                attack *= 2
                health *= 2
                defense *= 2
            for i in range(starCount[1]):
                attack *= 1.5
                health *= 1.5
                defense *= 1.5
            attack = formatNum(attack)
            health = formatNum(health)
            defense = formatNum(defense)
            aps = heroData["Base Stats"]["APS"]
            speed = heroData["Base Stats"]["SPEED"]
            arange = heroData["Base Stats"]["RANGE"]
            ctkrate = heroData["Base Stats"]["CTK RATE"]
            ctkdmg = heroData["Base Stats"]["CTK DMG"]

            colors = {
                "earth": "0x64B361",
                "water": "0x3E90BF",
                "fire": "0xE0291D",
                "light": "0xF5DB43",
                "dark": "0xAB57C1"
            }
            color = discord.Color(int(colors[heroData["Type"]], 16))
            desc = f"**Rarity:** {heroData['Rarity']}\n**Attributes: {emojis[heroData['Type']]} {emojis[heroData['Job']]} {emojis[heroData['Gender']]}**"
            if heroData["Special Ability"] != "":
                desc += f"\n**Special:** {heroData['Special Ability']}"
            embed = discord.Embed(
                title=f"**{hero}**\n{emojis['awaken'] * starCount[1]}{emojis['star'] * (starCount[0] - starCount[1])}{emojis['blackStar'] * (7 - starCount[0])}",
                color=color,
                description=desc
            )
            embed.set_thumbnail(url=heroData['Image'])
            embed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            embed.add_field(name=f"**{emojis['attack']} Attack**", value=f"{attack}")
            embed.add_field(name=f"**{emojis['health']} Health**", value=f"{health}")
            embed.add_field(name=f"**{emojis['defense']} Defense**", value=f"{defense}")
            embed.add_field(name=f"**{emojis['aps']} APS**", value=f"{aps}")
            embed.add_field(name=f"**{emojis['speed']} Speed**", value=f"{speed}")
            embed.add_field(name=f"**{emojis['range']} Range**", value=f"{arange}")
            embed.add_field(name=f"**{emojis['ctk rate']} Ctk Rate**", value=f"{ctkrate}")
            embed.add_field(name=f"**{emojis['ctk dmg']} Ctk Dmg**", value=f"{ctkdmg}")
            embed.add_field(name=f"** **", value=f"** **")

            if heroData["SP2"] != "":
                embed.add_field(name=f"**Ability**", value=f"```{heroData['SP2']}```", inline=False)
            if heroData["SP3"] != "":
                embed.add_field(name=f"**Ultimate**", value=f"```{heroData['SP3']}```", inline=False)
            if heroData["SP4"] != "":
                embed.add_field(name=f"**Passive**", value=f"```{heroData['SP4']}```", inline=False)
            
            embed.add_field(name=f"** **", value=f"**Runes** ⏩", inline=False)

            runeEmbed = discord.Embed(
                title=f"{hero}\n{emojis['awaken'] * starCount[1]}{emojis['star'] * (starCount[0] - starCount[1])}{emojis['blackStar'] * (7 - starCount[0])}",
                color=color
            )
            runeEmbed.set_thumbnail(url=heroData['Image'])
            runeEmbed.set_footer(text=config["config"]["footer"], icon_url=self.client.user.avatar_url)
            for runeSet in heroData["Target Rune Set"]:
                runeEmbed.add_field(name=f"**{runeSet}**", value=f"```{heroData['Target Rune Set'][runeSet]}```", inline=False)
            for runeSet in heroData["Target Rune Stats"]:
                desc = '\n'.join(heroData['Target Rune Stats'][runeSet])
                runeEmbed.add_field(name=f"**{runeSet}**", value=f"```{desc}```", inline=False)
            runeEmbed.add_field(name=f"** **", value=f"⏪ **General**", inline=False)

            left = '⏪'
            right = '⏩'
            pages = [embed, runeEmbed]
            message = await ctx.send(embed=pages[0])
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
                except asyncio.TimeoutError:
                    break 
            await message.clear_reactions()

        except Exception as e:
            await handleException(e, self.client)
        


    def getHero(self, h):
        with open("data/encyclopedia.json") as f:
            heroes = json.load(f)
        h = h.lower()
        shortVersions = {
            "mm": "Monki Mortar",
            "glad": "Gladiator",
            "furi": "Furiosa"
        }
        for hero in heroes:
            if h in shortVersions:
                return shortVersions[h]
            if h == hero.lower():
                return hero
            hero = hero.split(" ")
            initials = ""
            if len(hero) > 1:
                for s in hero:
                    initials += s[0]
                if h == initials.lower():
                    return " ".join(hero)
        return -1

    

    @commands.command(aliases=["cpr"])
    async def compare(self, ctx, *params):
        try:
            if len(params) == 0:
                return await ctx.send("```You are missing required arguments! Check r.help for usage instructions.```")
            starCount = [-1, -1]
            heroes = []
            hero = []
            params = " ".join(params).split(",")
            for p in params:
                p = p.strip().split(" ")
                for part in p:
                    try:
                        num = int(part)
                        if num < 1 and starCount[0] == -1:
                            return await ctx.send("```Star counts must be greater than 0.```")
                        if num > 7:
                            return await ctx.send("```Star counts must be less than 7.```")
                        if starCount[0] == -1:
                            starCount[0] = num
                        else:
                            starCount[1] = num
                    except ValueError:
                        hero.append(part)
                
                if starCount[0] == -1:
                    starCount[0] = 1
                if starCount[1] == -1:
                    starCount[1] = 0
                if starCount[0] < starCount[1]:
                    return await ctx.send("```Awakened stars cannot be greater than regular stars.```")
                
                hero = " ".join(hero)

                if self.getHero(hero) == -1:
                    typeHeroes = self.getType(hero, starCount) 
                    if typeHeroes == []:
                        return await ctx.send("```Invalid hero or type!```")
                    heroes += typeHeroes 
                else:
                    heroes.append([self.getHero(hero), starCount])
                hero = []
                starCount = [-1, -1]
                        
            if len(heroes) < 1:
                return await ctx.send("```Please include one or more heroes separated by commas (,) or a valid type.```")
            
            heroList = []
            for l in heroes:
                heroList.append(l[0])

            await logUsage(f"Comparing {', '.join(list(heroList))} requested by @{ctx.author.name}.", self.client)

            with open("data/encyclopedia.json") as f:
                encyclopedia = json.load(f)
            with open("data/emojis.json") as f:
                emojis = json.load(f)

            text = f""

            for l in heroes:
                hero = l[0]
                starCount = l[1]
                heroData = encyclopedia[hero]
                attack = float(heroData['Base Stats']['ATK'])
                health = float(heroData['Base Stats']['HP'])
                defense = float(heroData['Base Stats']['DEF'])
                for i in range(starCount[0] - 1):
                    attack *= 2
                    health *= 2
                    defense *= 2
                for i in range(starCount[1]):
                    attack *= 1.5
                    health *= 1.5
                    defense *= 1.5
                attack = formatNum(attack)
                health = formatNum(health)
                defense = formatNum(defense)
                aps = heroData["Base Stats"]["APS"]
                speed = heroData["Base Stats"]["SPEED"]
                arange = heroData["Base Stats"]["RANGE"]
                ctkrate = heroData["Base Stats"]["CTK RATE"]
                ctkdmg = heroData["Base Stats"]["CTK DMG"]

                text += \
                    f"{heroData['Emoji']} **{hero}** \n {starCount[0]}{emojis['star']}{starCount[1]}{emojis['awaken']} {emojis[heroData['Type']]}{emojis[heroData['Job']]}{emojis[heroData['Gender']]}" \
                    f"\n" \
                    f"{emojis['attack']} `{attack}` " \
                    f"{emojis['health']} `{health}` " \
                    f"{emojis['defense']} `{defense}` " \
                    f"{emojis['aps']} `{aps}` " \
                    f"{emojis['speed']} `{speed}` " \
                    f"{emojis['range']} `{arange}` " \
                    f"{emojis['ctk rate']} `{ctkrate}` " \
                    f"{emojis['ctk dmg']} `{ctkdmg}`\n" 

            text = text.split("\n")
            t = 0
            while t < len(text) - 1:
                await ctx.send(text[t] + "\n" + text[t + 1] + "\n" + text[t + 2])
                t += 3
                if t != 0 and t % 24 == 0:
                    message = await ctx.send("React with ⏩ for more heroes.")
                    await message.add_reaction("⏩")
                    def check(reaction, user):
                        return user == ctx.author
                    try: 
                        reaction, user = await self.client.wait_for('reaction_add', timeout=300, check=check)
                        if reaction == "⏩":
                            pass
                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break

        except Exception as e:
            await handleException(e, self.client)



    def getType(self, type, starCount):
        type = type.split(" ")
        heroes = []
        with open("data/herotypes.json") as f:
            heroTypes = json.load(f)
        with open("data/encyclopedia.json") as f:
            encyclopedia = json.load(f)
        isValid = heroes
        for category in heroTypes:
            for t in range(len(type)):
                if type[t] in heroTypes[category]:
                    type[t] == True
        for i in isValid:
            if i != True:
                return heroes
        for hero in encyclopedia:
            heroData = encyclopedia[hero]
            attributes = [heroData["Job"], heroData["Type"], heroData["Gender"], heroData["Rarity"].lower()]
            match = True
            for t in type:
                if not t in attributes:
                    match = False
            if match == True:
                inHeroes = False
                for h in heroes:
                    if h[0] == hero:
                        inHeroes = True
                        break
                if not inHeroes:
                    heroes.append([hero, starCount])
        return heroes
                    
        



def setup(client):
    client.add_cog(General(client))