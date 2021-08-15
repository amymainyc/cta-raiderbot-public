import json
import pyrebase
import aiohttp 
import random
from loguru import logger



with open('data/config.json') as d:
    config = json.load(d)
with open("data/server.json") as f:
    server = json.load(f)
    
firebase = pyrebase.initialize_app(config["firebase"])
db = firebase.database()



class Data:

    def __init__(self):
        self.cats = []
        self.dogs = []
        self.cars = []
        self.cookies = []


    def getEmojis(self):
        return db.child("emojis").get().val()


    def getImages(self):
        return db.child("images").get().val()

        

    def getHeroTypes(self):
        return db.child("herotypes").get().val()



    def getGuildWar(self):
        with open("data/guildwar.json") as f:
            return json.load(f)



    def updateGuildWar(self, data):
        with open("data/guildwar.json", "w") as f:
            json.dump(data, f, indent=4)



    def getRecruitees(self):
        recruitees = db.child("recruitees").get().val()
        if recruitees != "placeholder":
            return recruitees
        return {}



    def updateRecruitees(self, data):
        if data != {}:
            db.child("recruitees").set(data)
        else:
            db.child("recruitees").set("placeholder")



    def getReminders(self):
        return db.child("reminders").get().val()



    def updateReminders(self, data):
        db.child("reminders").set(data)



    def getRR(self):
        data = db.child("rosterreminders").get().val()
        if data == "placeholder":
            return {}
        return data



    def updateRR(self, data):
        if data == {}:
            return db.child("rosterreminders").set("placeholder")
        db.child("rosterreminders").set(data)



    def updateReminders(self, data):
        db.child("rosterreminders").set(data)


    
    def getFortuneChest(self, data):
        return db.child("fortunechest").get().val()



    def updateFortuneChest(self, data):
        db.child("fortunechest").set(data)



    async def __getPictures(self, query, pages):
        link = server["general"]["links"]["photoAPI"].replace("[query]", query) + str(random.randint(0, pages))
        logger.info(f"Getting photos of {query}: {link}")
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as data:
                data = await data.json()
        return data["results"]



    def __parseItemData(self, item):
        return {
            "link": item["urls"]["regular"],
            "user": item["user"]["name"],
            "userLink": item["user"]["links"]["html"] + "?utm_source=RaiderBot&utm_medium=referral",
            "userPfp": item["user"]["profile_image"]["small"],
            "unsplashLink": "https://unsplash.com/" + "?utm_source=RaiderBot&utm_medium=referral"
        }



    async def getCatPicture(self):
        if self.cats == []:
            self.cats = await self.__getPictures("cat", 1000)
        item = self.cats[0]
        self.cats.remove(item)
        item = self.__parseItemData(item)
        return item
        

    
    async def getDogPicture(self):
        if self.dogs == []:
            self.dogs = await self.__getPictures("dog", 1000)
        item = self.dogs[0]
        self.dogs.remove(item)
        item = self.__parseItemData(item)
        return item



    async def getCarPicture(self):
        if self.cars == []:
            self.cars = await self.__getPictures("car", 1000)
        item = self.cars[0]
        self.cars.remove(item)
        item = self.__parseItemData(item)
        return item



    async def getCookiePicture(self):
        if self.cookies == []:
            self.cookies = await self.__getPictures("cookie", 222)
        item = self.cookies[0]
        self.cookies.remove(item)
        item = self.__parseItemData(item)
        return item



    def getCookies(self):
        return db.child("cookies").get().val()



    def updateCookies(self, data):
        db.child("cookies").set(data)