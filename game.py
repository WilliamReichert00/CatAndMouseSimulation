# Notes ---------------------------------------------------------------------------------------------------------------- Notes
# pygame screen: positive x is to the right, left edge is 0. positive y is down, top edge is 0.


# Imports -------------------------------------------------------------------------------------------------------------- Imports
# imports pygame for visuals and input, math for advanced math, random for randomization, clock for frame control, and numpy is used to create the sigmoid function
from copy import deepcopy

import pygame, math, time, numpy, random
from pygame.locals import (
    KEYDOWN,
    MOUSEBUTTONDOWN,
    K_ESCAPE,
    K_SPACE,
    K_LEFT,
    K_RIGHT
)

# Program Constants ---------------------------------------------------------------------------------------------------- Program Constants
# width height of pygame window
WIDTH = 2500
HEIGHT = 1400
# distance from one corner to its opposite, used to turn input distance into a percentage
DISTANCESCALE = math.sqrt(WIDTH * WIDTH + HEIGHT * HEIGHT)
# pi used in rotation and sphere calculations
PI = math.pi
# number of simulated items
NUMMICE = 8
NUMFOOD = 10
NUMCATS = 4
# lists for all entities
mice = []
food = []
cats = []
miceBrains = []
bestMice = []
catBrains = []
bestCats = []
# preset color rgb tuples
WHITE = (255, 255, 255)
LIGHTGRAY = (190, 190, 190)
GRAY = (127, 127, 127)
DARKGRAY = (100, 100, 100)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255,123,100)
# additional parameters
# body to head radius ratio |1/2 : 1/HEADSCALE|
HEADSCALE = 3
# parameters determining the lifespan of entities
MOUSEBELLY = 10000
CATBELLY = 20000


# Sprite classes ------------------------------------------------------------------------------------------------------- Sprite classes
class Mouse(pygame.sprite.Sprite):

    # x,y starting body coordinates (screen center is WIDTH/2, HEIGHT/2), width is size of body and head, color is body head color
    def __init__(self, x=0, y=0, width=25, bodyColor=LIGHTGRAY, headColor=WHITE, brain=0):
        super(Mouse, self).__init__()
        self.score = 0
        self.bColor = bodyColor
        self.hColor = headColor
        self.width = width
        self.neck = width / 2
        self.angle = 0
        self.bodySurf = pygame.Surface((self.width, self.width), pygame.SRCALPHA, 32)
        self.bodySurf = self.bodySurf.convert_alpha()
        pygame.draw.circle(self.bodySurf, self.bColor, (self.width / 2, self.width / 2), self.width / 2)
        self.headSurf = pygame.Surface((self.width, self.width), pygame.SRCALPHA, 32)
        self.headSurf = self.headSurf.convert_alpha()
        pygame.draw.circle(self.headSurf, self.hColor, (self.width / 2, self.width / 2), self.width / HEADSCALE)
        self.x = WIDTH / 2 + x
        self.y = HEIGHT / 2 - y
        self.hx = self.x + math.cos(self.angle) * self.neck
        self.hy = self.y - math.sin(self.angle) * self.neck
        self.bodyRect = self.bodySurf.get_rect(center=(self.x, self.y))
        self.headRect = self.headSurf.get_rect(center=(self.hx, self.hy))
        self.brain = brain
        self.hunger = MOUSEBELLY

    # draws the mouse to the screen
    def draw(self, screen):
        screen.blit(self.bodySurf, self.bodyRect)
        screen.blit(self.headSurf, self.headRect)

    # moves the mouse body and head in the direction of the head by the step amount, step 0 allows rotation
    def forward(self, step=2):
        xRate = math.cos(self.angle) * step
        yRate = math.sin(self.angle) * step
        self.shift([xRate, yRate])
        self.hunger -= step
        if self.hunger <= 0:
            self.starves()

    # rotate the mouse's head by the rotation / 12 PI with respect to the body
    def turn(self, rotation=1):
        rotation *= PI / 12  # default 1/12 of a 180 degree turn
        self.angle += rotation
        self.angle = angled(self.angle)
        self.hunger -= math.fabs(rotation)
        self.forward(step=0)

    # shifts the mouse by vector addition
    def shift(self, xy):
        x = self.x
        x += xy[0]
        y = self.y
        y -= xy[1]

        # make sure new coordinates would be in bounds
        if x >= WIDTH or x <= 0:
            x = self.x
        if y >= HEIGHT or y <= 0:
            y = self.y

        # update mouse coordinates
        self.x = x
        self.y = y
        self.hx = self.x + math.cos(self.angle) * self.neck
        self.hy = self.y - math.sin(self.angle) * self.neck

        # move mouse to new coordinates
        self.bodyRect = self.bodySurf.get_rect(center=(self.x, self.y))
        self.headRect = self.headSurf.get_rect(center=(self.hx, self.hy))

    # if mouse head overlaps the cheese's center, the mouse eats it
    def consume(self, cheese):
        if self.hx + self.width / HEADSCALE >= cheese.x >= self.hx - self.width / HEADSCALE:
            if self.hy + self.width / HEADSCALE >= cheese.y >= self.hy - self.width / HEADSCALE:
                cheese.consumed()
                self.score += 1
                bestBrains()
                self.hunger = MOUSEBELLY
                print("a mouse has eaten " + self.score.__str__() + " food")

    # is consumed by a cat, respawn at a random coordinate
    def consumed(self):
        bestBrains()
        xy = randCoord()
        if bestMice[0].score == 0:
            self.brain.newWeights()
            self.bColor = randomColor()
            self.hColor = colorPair(self.bColor, 15)
        elif self.score <= bestMice[0].score * .2:
            self.bColor = randomColor()
            self.hColor = colorPair(self.bColor, 15)
            self.brain.merge(random.choice(bestMice))
        else:
            self.brain.merge(random.choice(bestMice))
        self.__init__(x=xy[0], y=xy[1], width=self.width, bodyColor=self.bColor, headColor=self.hColor,
                      brain=self.brain)

    # doesnt eat enough, resets and respawns randomly
    def starves(self):
        bestBrains()
        xy = randCoord()
        if bestMice[0].score == 0:
            self.brain.newWeights()
            self.bColor = randomColor()
            self.hColor = colorPair(self.bColor, 15)
        elif self.score <= bestMice[0].score * .2:
            self.bColor = randomColor()
            self.hColor = colorPair(self.bColor, 15)
            self.brain.merge(random.choice(bestMice))
        else:
            self.brain.merge(random.choice(bestMice))
        self.__init__(x=xy[0], y=xy[1], width=self.width, bodyColor=self.bColor, headColor=self.hColor,
                      brain=self.brain)
        print("mouse starved")


class Food(pygame.sprite.Sprite):

    # x,y starting body coordinates (screen center is WIDTH/2, HEIGHT/2), width is size of body and head, color is body head color
    def __init__(self, x=0, y=0, width=10, color=YELLOW):
        super(Food, self).__init__()
        self.color = color
        self.width = width
        self.surf = pygame.Surface((self.width, self.width), pygame.SRCALPHA, 32)
        self.surf = self.surf.convert_alpha()
        pygame.draw.circle(self.surf, self.color, (self.width / 2, self.width / 2), self.width / 2)
        self.x = WIDTH / 2 + x
        self.y = HEIGHT / 2 - y
        self.rect = self.surf.get_rect(center=(self.x, self.y))

    # draws the mouse to the screen
    def draw(self, screen):
        screen.blit(self.surf, self.rect)

    # is consumed by a mouse, respawn at a random coordinate
    def consumed(self):
        xy = randCoord()
        self.__init__(x=xy[0], y=xy[1], width=self.width, color=self.color)


class Cat(pygame.sprite.Sprite):

    # x,y starting body coordinates (screen center is WIDTH/2, HEIGHT/2), width is size of body and head, color is body head color
    def __init__(self, x=0, y=0, width=40, bodyColor=DARKGRAY, headColor=GRAY, brain=0):
        super(Cat, self).__init__()
        self.score = 0
        self.bColor = bodyColor
        self.hColor = headColor
        self.width = width
        self.neck = width / 2
        self.angle = 0
        self.bodySurf = pygame.Surface((self.width, self.width), pygame.SRCALPHA, 32)
        self.bodySurf = self.bodySurf.convert_alpha()
        pygame.draw.circle(self.bodySurf, self.bColor, (self.width / 2, self.width / 2), self.width / 2)
        self.headSurf = pygame.Surface((self.width, self.width), pygame.SRCALPHA, 32)
        self.headSurf = self.headSurf.convert_alpha()
        pygame.draw.circle(self.headSurf, self.hColor, (self.width / 2, self.width / 2), self.width / HEADSCALE)
        self.x = WIDTH / 2 + x
        self.y = HEIGHT / 2 - y
        self.hx = self.x + math.cos(self.angle) * self.neck
        self.hy = self.y - math.sin(self.angle) * self.neck
        self.bodyRect = self.bodySurf.get_rect(center=(self.x, self.y))
        self.headRect = self.headSurf.get_rect(center=(self.hx, self.hy))
        self.brain = brain
        self.hunger = CATBELLY

    # draws the cat to the screen
    def draw(self, screen):
        screen.blit(self.bodySurf, self.bodyRect)
        screen.blit(self.headSurf, self.headRect)

    # moves the cat body and head in the direction of the head by the step amount, step 0 allows rotation
    def forward(self, step=2):
        xRate = math.cos(self.angle) * step
        yRate = math.sin(self.angle) * step
        self.shift([xRate, yRate])
        self.hunger -= step
        if self.hunger <= 0:
            self.starves()

    # rotate the cat's head by the rotation / 12 PI with respect to the body
    def turn(self, rotation=1):
        rotation *= PI / 12  # default 1/12 of a 180 degree turn
        self.angle += rotation
        self.angle = angled(self.angle)
        self.hunger -= math.fabs(rotation)
        self.forward(step=0)

    # shifts the cat by vector addition
    def shift(self, xy):
        x = self.x
        x += xy[0]
        y = self.y
        y -= xy[1]

        # make sure new coordinates would be in bounds
        if x >= WIDTH or x <= 0:
            x = self.x
        if y >= HEIGHT or y <= 0:
            y = self.y

        # update mouse coordinates
        self.x = x
        self.y = y
        self.hx = self.x + math.cos(self.angle) * self.neck
        self.hy = self.y - math.sin(self.angle) * self.neck

        # move mouse to new coordinates
        self.bodyRect = self.bodySurf.get_rect(center=(self.x, self.y))
        self.headRect = self.headSurf.get_rect(center=(self.hx, self.hy))

    # if cat head overlaps the mouse's body center, the mouse eats it
    def consume(self, mouse):
        if self.hx + self.width / HEADSCALE >= mouse.x >= self.hx - self.width / HEADSCALE:
            if self.hy + self.width / HEADSCALE >= mouse.y >= self.hy - self.width / HEADSCALE:
                mouse.consumed()
                self.score += 1
                bestBrains()
                print("a cat has eaten a mouse")
                self.hunger = CATBELLY

    # doesnt eat enough
    def starves(self):
        bestBrains()
        xy = randCoord()
        if bestCats[0].score == 0:
            self.brain.newWeights()
            self.bColor = random.choice([WHITE,LIGHTGRAY,GRAY,DARKGRAY,ORANGE])
            self.hColor = random.choice([WHITE,LIGHTGRAY,GRAY,DARKGRAY,ORANGE])
        elif self.score <= bestCats[0].score * .2:
            self.bColor = random.choice([WHITE,LIGHTGRAY,GRAY,DARKGRAY,ORANGE])
            self.hColor = colorPair(self.bColor, 15)
            self.brain.merge(random.choice(bestCats))
        else:
            self.brain.merge(random.choice(bestCats))
        self.__init__(x=xy[0], y=xy[1], width=self.width, bodyColor=self.bColor, headColor=self.hColor,
                      brain=self.brain)
        print("a cat starved")


# Simulation classes --------------------------------------------------------------------------------------------------------- Simulation classes
# neural network classes
class MouseBrain:
    # requires mouse to control, list of cats and list of foods to initialize
    # NN inputs are: hunger, nearest cat relative angle and inverse distance %, nearest cheese relative angle and distance.
    # NN outputs are: turn (-1.0 to 1.0), forward (0 to 1)
    def __init__(self, mouse, cats, food):
        self.mouse = mouse
        nCat = self.nStats(cats)
        nFood = self.nStats(food)
        self.inputs = [(MOUSEBELLY - self.mouse.hunger) / (MOUSEBELLY / 10), nCat[1], 1 - nCat[0], nFood[1], nFood[0]]
        # weights: 0 - hunger, 1 - angle to cat, 2 - cat distance, 3 - angle to food, 4 - food distance
        self.turnWeights = randomWeights(self.inputs.__len__())
        self.moveWeights = randomWeights(self.inputs.__len__())
        # assign brain to mouse for ease of access
        self.mouse.brain = self
        self.score = self.mouse.score

    # updates hunger and nearest entities, requires list of cats and list of foods
    def update(self, cats=cats, food=food):
        self.score = self.mouse.score
        nCat = self.nStats(cats)
        nFood = self.nStats(food)
        self.inputs = [(MOUSEBELLY - self.mouse.hunger) / (MOUSEBELLY / 10), nCat[1], nCat[0], nFood[1], nFood[0]]
        self.activate()

    # takes entities with coordinates and returns the closest entity's distance and angle
    def nStats(self, entities):
        if entities.__len__() == 0:
            return [0,0]
        # default value
        nEntity = entities[0]
        # distance to compare
        dist = distance(self.mouse.x, nEntity.x, self.mouse.y, nEntity.y)
        # compare all distances in the list of items
        for entity in entities:
            eDist = distance(self.mouse.x, entity.x, self.mouse.y, entity.y)
            if dist > eDist:
                dist = eDist
                nEntity = entity
        # amount of rotation required to face towards the object
        angle = self.mouse.angle + coordAngle(self.mouse.x, nEntity.x, self.mouse.y, nEntity.y)
        angle = angled(angle)
        # return distance and required turn angle as percentages of their maximum values
        return [dist / DISTANCESCALE, angle / PI]

    # compiles weights to determine outputs
    def activate(self):
        turnOut = 0
        moveOut = 0
        i = 0
        while i < self.inputs.__len__():
            turnOut += self.turnWeights[i] * self.inputs[i]
            moveOut += self.moveWeights[i] * self.inputs[i]
            i += 1
        turnOut = sigmoid2(turnOut)
        moveOut = sigmoid(moveOut)
        self.mouse.turn(turnOut)
        self.mouse.forward(moveOut)

    # creates new weights for the mouse
    def newWeights(self):
        self.turnWeights = randomWeights(self.inputs.__len__())
        self.moveWeights = randomWeights(self.inputs.__len__())

    # merges a brain to self by randomly selecting an attribute from either. n represents self weight in selection. also merges color
    def merge(self, brain, n=.5):
        if len(self.inputs) != len(brain.inputs):
            return
        self.mouse.bColor = colorBetween(self.mouse.hColor, brain.mouse.hColor, n)
        self.mouse.hColor = colorPair(self.mouse.bColor, 15)
        i = 0
        while i < len(self.inputs):
            self.turnWeights[i] = pick(self.turnWeights[i], brain.turnWeights[i], n)
            self.turnWeights[i] = pick(self.turnWeights[i], brain.turnWeights[i], n)
            i += 1

    # returns a copy of the brain
    def stats(self):
        tMouse = self.mouse
        self.mouse = 0
        temp = deepcopy(self)
        temp.mouse = tMouse
        self.mouse = tMouse
        return temp


class CatBrain:
    # requires cat to control and list of mice to initialize
    # NN inputs are: hunger, nearest mouse relative angle and distance.
    # NN outputs are: turn (-1.0 to 1.0), forward (0 to 1)
    def __init__(self, cat, mice):
        self.cat = cat
        nMouse = self.nStats(mice)
        self.inputs = [(CATBELLY - self.cat.hunger) / (CATBELLY / 10), nMouse[1], 1 - nMouse[0]]
        # weights: 0 - bias, 1 - angle to mouse, 2 - mouse distance
        self.turnWeights = randomWeights(self.inputs.__len__())
        self.moveWeights = randomWeights(self.inputs.__len__())
        self.cat.brain = self
        self.score = self.cat.score

    # updates nearest entities, requires list of mice
    def update(self, mice=mice):
        self.score = self.cat.score
        nMouse = self.nStats(mice)
        self.inputs = [(CATBELLY - self.cat.hunger) / (CATBELLY / 10), nMouse[1], nMouse[0]]
        self.activate()

    # takes entities with coordinates and returns the closest entity's distance and angle
    def nStats(self, entities):
        if entities.__len__() == 0:
            return [0,0]
        # default value
        nEntity = entities[0]
        # distance to compare
        dist = distance(self.cat.x, nEntity.x, self.cat.y, nEntity.y)
        # compare all distances in the list of items
        for entity in entities:
            eDist = distance(self.cat.x, entity.x, self.cat.y, entity.y)
            if dist > eDist:
                dist = eDist
                nEntity = entity
        # amount of rotation required to face towards the object
        angle = coordAngle(self.cat.x, nEntity.x, self.cat.y, nEntity.y) + self.cat.angle
        angle = angled(angle)
        # return distance and required turn angle
        return [dist / DISTANCESCALE, angle / PI]

    # compiles weights to determine outputs
    def activate(self):
        turnOut = 0
        moveOut = 0
        i = 0
        while i < self.inputs.__len__():
            turnOut += self.turnWeights[i] * self.inputs[i]
            moveOut += self.moveWeights[i] * self.inputs[i]
            i += 1
        turnOut = sigmoid2(turnOut)
        moveOut = sigmoid(moveOut)
        self.cat.turn(turnOut)
        self.cat.forward(moveOut)

    # creates new weights for the mouse
    def newWeights(self):
        self.turnWeights = randomWeights(self.inputs.__len__())
        self.moveWeights = randomWeights(self.inputs.__len__())

    # merges a brain to self by randomly selecting an attribute from either. n represents self weight in selection, also merges color
    def merge(self, brain, n=.5):
        if len(self.inputs) != len(brain.inputs):
            return
        self.cat.bColor = colorBetween(self.cat.hColor, brain.cat.hColor, n)
        self.cat.hColor = colorPair(self.cat.bColor, 15)
        i = 0
        while i < len(self.inputs):
            self.turnWeights[i] = pick(self.turnWeights[i], brain.turnWeights[i], n)
            self.turnWeights[i] = pick(self.turnWeights[i], brain.turnWeights[i], n)
            i += 1

    # returns a copy of the brain
    def stats(self):
        tCat = self.cat
        self.cat = 0
        temp = deepcopy(self)
        temp.cat = tCat
        self.cat = tCat
        return temp


# Game functions ------------------------------------------------------------------------------------------------------- Game functions
# simulation updating
# sort by score and store top 50%
def bestBrains():
    catBrains.sort(key=lambda x: x.score, reverse=True)
    miceBrains.sort(key=lambda x: x.score, reverse=True)
    global bestCats
    global bestMice
    if len(bestCats) == 0:
        bestCats = catBrains
    if len(bestMice) == 0:
        bestMice = miceBrains
    i = 0
    j = 0
    nBest = []
    while i < bestCats.__len__() and j < catBrains.__len__()/2 and nBest.__len__() <= catBrains.__len__()/2:
        if catBrains[i].score > bestCats[j].score:
            nBest.append(catBrains[i].stats())
            i += 1
        else:
            nBest.append(bestCats[j].stats())
            j += 1
    bestCats = nBest
    i = 0
    j = 0
    nBest = []
    while i < bestMice.__len__() and j < miceBrains.__len__()/2 and nBest.__len__() <= miceBrains.__len__()/2:
        if miceBrains[i].score > bestMice[j].score:
            nBest.append(miceBrains[i].stats())
            i += 1
        else:
            nBest.append(bestMice[j].stats())
            j += 1
    bestMice = nBest


# returns nearest entity (with separate x,y coordinates) to given coordinates
def get_nearest(xy, entities, radius=DISTANCESCALE):
    nEntity = entities[0]
    # distance to compare
    dist = distance(xy[0], nEntity.x, xy[1], nEntity.y)
    # compare all distances in the list of items
    for entity in entities:
        eDist = distance(xy[0], entity.x, xy[1], entity.y)
        if dist > eDist:
            dist = eDist
            nEntity = entity
    if dist >= radius:
        nEntity = 0
    return nEntity


# random functions
# return a random coordinate on the screen
def randCoord():
    return [random.randint(-WIDTH / 2 + 10, WIDTH / 2 - 10), random.randint(-HEIGHT / 2 + 10, HEIGHT / 2 - 10)]


# return n random numbers between -1 and 1
def randomWeights(n):
    weights = []
    i = 0
    while i < n:
        weights.append(random.random() * random.choice([-1, 1]))
        i += 1
    return weights


# picks one of two options, odd of option 1 are n (as a decimal) percent
def pick(op1, op2, n=.5):
    if random.random() >= n:
        return op1
    else:
        return op2


# returns a random color
def randomColor():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return (r, g, b)


# color related functions
# returns a color shifted within range of a given color
def colorPair(color, range):
    r = color[0] + random.randint(-range, range)
    r = bound(r, 0, 255)
    g = color[1] + random.randint(-range, range)
    g = bound(g, 0, 255)
    b = color[2] + random.randint(-range, range)
    b = bound(b, 0, 255)
    return r, g, b


# returns a color that is n (as a decimal) percent between two colors (a lower n value prioritizes color 2)
def colorBetween(c1, c2, n=.5):
    r = c1[0] * n + c2[0] * (1 - n)
    g = c1[1] * n + c2[1] * (1 - n)
    b = c1[2] * n + c2[2] * (1 - n)
    return r, g, b


# screen related functions
# coordinate's angle with respect to another coordinate
def coordAngle(x1, x2, y1, y2):
    return math.atan2(y2 - y1, x2 - x1)


# distance between two coordinates
def distance(x1, x2, y1, y2):
    x = x1 - x2
    y = y1 - y2
    return math.sqrt(x * x + y * y)


# number modification and mapping
# writes a number as an angle in radians between Pi and -PI
def angled(angle):
    if angle > PI:
        angle -= 2 * PI
    elif angle <= -PI:
        angle += 2 * PI
    return angle


# constrains a number to given max and min, inclusive
def bound(num, min, max):
    if num > max:
        num = max
    elif num < min:
        num = min
    return num


# function resulting between 0 and 1. used for distance activation
def sigmoid(x):
    return 1 / (1 + numpy.exp(-x))


# function resulting between -1 and 1. used for turning activation
def sigmoid2(x):
    return sigmoid(x) * x / math.fabs(x)


# Pygame initializations ----------------------------------------------------------------------------------------------- Pygame initializations
pygame.init()
all_sprites = pygame.sprite.Group()
# sprite handling
all_cats = pygame.sprite.Group()
all_mice = pygame.sprite.Group()
all_food = pygame.sprite.Group()
# pygame screen definition
screen = pygame.display.set_mode([WIDTH, HEIGHT])
screen.fill((0, 0, 0))
# playback speed control
playSpeed = 1

# Simulation population ------------------------------------------------------------------------------------------------------ Simulation population
# generate entities
i = 0
while i < NUMFOOD:
    nFood = Food(x=randCoord()[0], y=randCoord()[1])  # give random coordinates
    food.append(nFood)
    i += 1
i = 0
while i < NUMCATS:
    nCat = Cat(x=randCoord()[0], y=randCoord()[1])  # give random coordinates
    cats.append(nCat)

    i += 1
i = 0
while i < NUMMICE:
    color = randomColor()
    nMouse = Mouse(x=randCoord()[0], y=randCoord()[1], bodyColor=color,
                   headColor=colorPair(color, 15))  # give random coordinates and colors
    mice.append(nMouse)
    i += 1
# handle sprite data
all_sprites.add(food, mice, cats)
all_cats.add(cats)
all_mice.add(mice)
all_food.add(food)
# give entities brains
for cat in cats:
    catBrains.append(CatBrain(cat, mice))
for mouse in mice:
    miceBrains.append(MouseBrain(mouse, cats, food))
# update brain collection data
bestBrains()

# Initialize loop conditions + variables ------------------------------------------------------------------------------- Initialize loop conditions + variables
loop = True
# Main loop ------------------------------------------------------------------------------------------------------------ Main loop
while loop:
    # reinitialize surfaces
    screen.fill((0, 0, 0))

    # update and activate brains
    for brain in catBrains:
        brain.update()
    for brain in miceBrains:
        brain.update()

    # process consumption
    for cat in all_cats:
        for mouse in all_mice:
            cat.consume(mouse)
    for mouse in all_mice:
        for food in all_food:
            mouse.consume(food)

    # redraw sprites
    for entity in all_sprites:
        entity.draw(screen)

    # get event data
    pressed_keys = pygame.key.get_pressed()
    mouse_data = pygame.mouse.get_pos()

    # check event data
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                loop = False
            if event.key == K_SPACE:
                if len(bestMice) != 0:
                    print("Mouse HighScore: " + bestMice[0].score.__str__())
                if len(bestCats) != 0:
                    print("Cat HighScore: " + bestCats[0].score.__str__())
            if event.key == K_RIGHT:
                playSpeed += 1
                playSpeed = bound(playSpeed, 1, 10)
                print("play speed " + playSpeed.__str__())
            if event.key == K_LEFT:
                playSpeed -= 1
                playSpeed = bound(playSpeed, 1, 10)
                print("play speed " + playSpeed.__str__())
        if event.type == MOUSEBUTTONDOWN:
            entity = get_nearest(mouse_data, mice + cats, radius=25)
            if entity != 0:
                print(entity.bColor, entity.score)

    # apply screen changes
    pygame.display.flip()

    # regulate frame rate
    time.sleep((33 - 3.2 * playSpeed) / 1000)
