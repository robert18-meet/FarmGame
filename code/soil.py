import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import randint, choice

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{self.plant_type}')
        self.soil = soil
        self.check_watered = check_watered

        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed =GROW_SPEED[plant_type]
        self.harvestable = False

        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom
                                                  + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']


    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26,-self.rect.height*0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom
                                                  + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):
        self.all_sprites = all_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sptires = pygame.sprite.Group()
        self.collision_sprites = collision_sprites

        self.soil_surfaces = import_folder_dict('../graphics/soil/')
        self.water_surfaces = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_coll, cell in enumerate(row):
                if 'F' in cell:
                    x = index_coll * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE
                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    t = 'X' in self.grid[index_row - 1][index_col]
                    r = 'X' in row[index_col + 1]
                    l = 'X' in row[index_col - 1]
                    b = 'X' in self.grid[index_row + 1][index_col]

                    tile_type = 'o'

                    if all((t,r,b,l)):
                        tile_type = 'x'

                    if l and not any((t,r,b)):
                        tile_type = 'l'
                    if r and not any((t,l,b)):
                        tile_type = 'r'
                    if any((l,r)) and not any((t,b)):
                        tile_type = 'lr'

                    if t and not any((r,l,b)):
                        tile_type = 't'
                    if b and not any ((r,l,t)):
                        tile_type = 'b'
                    if any((t,b)) and not any((l,r)):
                        tile_type = 'tb'

                    if any((l,b)) and not any ((t,r)):
                        tile_type = 'tr'
                    if any((l,t)) and not any ((b,r)):
                        tile_type = 'br'
                    if any((r,b)) and not any ((t,l)):
                        tile_type = 'tl'
                    if any((r,t)) and not any ((b,l)):
                        tile_type = 'bl'

                    if all((t,b,r)) and not l:
                        tile_type = 'tbr'
                    if all((t,b,l)) and not r:
                        tile_type = 'tbl'
                    if all((l,r,t)) and not b:
                        tile_type = 'lrb'
                    if all((l,r,b)) and not t:
                        tile_type = 'lrt'

                    SoilTile((index_col * TILE_SIZE, index_row * TILE_SIZE),
                             self.soil_surfaces[tile_type], [self.all_sprites, self.soil_sprites])

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')
                WaterTile(soil_sprite.rect.topleft, choice(self.water_surfaces),
                          [self.all_sprites, self.water_sprites])

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.collision_sprites, self.plant_sptires] ,soil_sprite, self.check_watered)

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile((x,y), choice(self.water_surfaces), [self.all_sprites,
                                                                   self.water_sprites])

    def remove_water(self):
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def update_plants(self):
        for plant in self.plant_sptires.sprites():
            plant.grow()
