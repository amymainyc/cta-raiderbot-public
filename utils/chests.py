import random

#   120 10 80
#   240 30 100 20
#   450 50 100 80
#   900 80 100 100 70
#   1800 120 100 100 100 100 10

heroes = [0, 0, 0, 0, 0, 0]
for i in range(100000):
    heroes[0] = heroes[0] + 10
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 80

for h in range(len(heroes)):
    heroes[h] = heroes[h] / 100000

print("Tier 1 Crusher:")
print(heroes)

heroes = [0, 0, 0, 0, 0, 0]
for i in range(100000):
    heroes[0] = heroes[0] + 30
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 20

for h in range(len(heroes)):
    heroes[h] = heroes[h] / 100000

print("Tier 2 Crusher:")
print(heroes)

heroes = [0, 0, 0, 0, 0, 0]
for i in range(100000):
    heroes[0] = heroes[0] + 50
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 80

for h in range(len(heroes)):
    heroes[h] = heroes[h] / 100000

print("Tier 3 Crusher:")
print(heroes)

heroes = [0, 0, 0, 0, 0, 0]
for i in range(100000):
    heroes[0] = heroes[0] + 80
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 80

for h in range(len(heroes)):
    heroes[h] = heroes[h] / 100000

print("Tier 4 Crusher:")
print(heroes)

heroes = [0, 0, 0, 0, 0, 0]
for i in range(100000):
    heroes[0] = heroes[0] + 120
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 100
    j = random.randint(0, 5)
    heroes[j] = heroes[j] + 10

for h in range(len(heroes)):
    heroes[h] = heroes[h] / 100000

print("Tier 5 Crusher:")
print(heroes)

#   120 50 30 10 
heroes = 0
for i in range(100000):
    heroes += 10
    j = random.randint(0, 36)
    if j == 0:
        heroes += 50
    j = random.randint(0, 36)
    if j == 0:
        heroes += 30

heroes = heroes / 100000

print("Blitz:")
print(heroes)



#   200 50 50 30
heroes = 0
for i in range(100000):
    heroes += 10
    j = random.randint(0, 36)
    if j == 0:
        heroes += 50
    j = random.randint(0, 36)
    if j == 0:
        heroes += 30

heroes = heroes / 100000

print("Fortune:")
print(heroes)