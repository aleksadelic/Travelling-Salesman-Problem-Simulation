import math
import random

import pygame
import os
import config

from itertools import permutations
from queue import PriorityQueue


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]


class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = []
        visited = set()
        self.dfs(path, visited, 0, coin_distance)
        print(path)
        return path + [0]

    def dfs(self, path, visited, coin, coin_distance):
        if coin not in visited:
            path.append(coin)
            visited.add(coin)
            min_cost = float('inf')
            min_ind = 0
            for node in range(len(coin_distance)):
                if node not in visited and node != coin:
                    cost = coin_distance[coin][node]
                    if cost < min_cost:
                        min_cost = cost
                        min_ind = node
            self.dfs(path, visited, min_ind, coin_distance)


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = []
        min_cost = float('inf')
        for perm in list(permutations(range(1, len(coin_distance)))):
            cost = 0
            cost += coin_distance[0][perm[0]]
            for i in range(1, len(perm)):
                cost += coin_distance[perm[i]][perm[i - 1]]
            cost += coin_distance[perm[len(perm) - 1]][0]
            if cost < min_cost:
                min_cost = cost
                path = list(perm)
        return [0] + path + [0]


class Uki(Agent):
    counter = 0

    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = self.branch_and_bound(coin_distance)
        return path

    def branch_and_bound(self, coin_distance: list):
        path = [0]
        paths = PriorityQueue()
        paths.put(Wrapper(0, 0, path))

        while paths.qsize() > 0:
            node = paths.get()
            cost, path = node.cost, node.path
            self.counter += 1
            # print(str(self.counter) + ". " + str(path) + " " + str(cost))

            if len(path) > 1 and path[-1] == 0:
                return path

            if len(path) == len(coin_distance):
                distance = coin_distance[0][path[-1]]
                paths.put(Wrapper(cost + distance, 0, path + [0]))
            else:
                for i in range(len(coin_distance)):
                    if i not in path:
                        distance = coin_distance[i][path[-1]]
                        paths.put(Wrapper(cost + distance, 0, path + [i]))


class Micko(Agent):
    counter = 0

    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = self.a_star(coin_distance)
        return path

    def a_star(self, coin_distance: list):
        path = [0]
        paths = PriorityQueue()
        v = set()
        for i in range(len(coin_distance)):
            v.add(i)
        mst_cost = self.mst(coin_distance, v)
        paths.put(Wrapper(0, mst_cost, path))

        while paths.qsize() > 0:
            node = paths.get()
            cost, path = node.cost, node.path
            self.counter += 1
            # print(str(self.counter) + ". " + str(path) + " Heuristic: " + str(node.heuristic) + " cost: " + str(cost))

            if len(path) > 1 and path[-1] == 0:
                return path

            if len(path) == len(coin_distance):
                distance = coin_distance[0][path[-1]]
                paths.put(Wrapper(cost + distance, 0, path + [0]))
            else:
                v = set()
                v.add(0)
                distance = []
                for i in range(len(coin_distance)):
                    if i not in path:
                        v.add(i)
                        distance.append(coin_distance[i][path[-1]])
                mst_cost = self.mst(coin_distance, v)
                j = 0
                for i in range(len(coin_distance)):
                    if i not in path:
                        paths.put(Wrapper(cost + distance[j], mst_cost, path + [i]))
                        # print(path + [i], "Heur: ", mst_cost, "Cena: ", cost + distance[j])
                        j += 1

    def mst(self, graph: list, v: set):
        # print(v)
        s = 0
        u = set()
        u.add(s)
        v.remove(s)
        cost = 0
        while len(v) > 0:
            min_cost = float('inf')
            edge = -1
            for i in u:
                for j in v:
                    if graph[i][j] < min_cost:
                        min_cost = graph[i][j]
                        edge = j
            u.add(edge)
            v.remove(edge)
            cost += min_cost
        # print(cost)
        return cost


class Wrapper:

    def __init__(self, cost, heuristic, path):
        self.cost = cost
        self.length = len(path)
        self.path = path
        self.heuristic = heuristic
        self.total_cost = self.cost + self.heuristic

    def __lt__(self, obj):
        if self.total_cost == obj.total_cost:
            if self.length == obj.length:
                return self.path[-1] < obj.path[-1]
            else:
                return self.length > obj.length
        else:
            return self.total_cost < obj.total_cost

    def __le__(self, obj):
        if self.total_cost == obj.total_cost:
            return self.length >= obj.length
        else:
            return self.total_cost <= obj.total_cost

    def __eq__(self, obj):
        if self.total_cost == obj.total_cost:
            return self.length == obj.length
        else:
            return self.total_cost == obj.total_cost

    def __ne__(self, obj):
        if self.total_cost == obj.total_cost:
            return self.length != obj.length
        else:
            return self.total_cost != obj.total_cost

    def __gt__(self, obj):
        if self.total_cost == obj.total_cost:
            return self.length < obj.length
        else:
            return self.total_cost > obj.total_cost

    def __ge__(self, obj):
        if self.total_cost == obj.total_cost:
            return self.length <= obj.length
        else:
            return self.total_cost >= obj.total_cost
