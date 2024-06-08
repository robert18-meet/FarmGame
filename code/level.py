import pygame
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import *
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from menu import Menu

class Level:
    def __init__(self):
        # get the display surface
        self.display_surface = pygame.display.get_surface()
        self.bg = pygame.mixer.Sound('../audio/bg.mp3')

        # sprite groups
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        self.shop_active = False
        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.setup()

        self.menu = Menu(self.player, self.toggle_shop)

        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        #sky
        self.rain = Rain(self.all_sprites)
        self.raining = False
        self.soil_layer.raining = self.raining
        self.sky = Sky()

        self.success = pygame.mixer.Sound('../audio/success.wav')

    def setup(self):
        self.bg.play()
        tmx_data = load_pygame('../data/map.tmx')

        # house
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic(pos = (x*TILE_SIZE, y*TILE_SIZE), surf = surf, groups = self.all_sprites,
                        z = LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic(pos = (x*TILE_SIZE, y*TILE_SIZE), surf = surf, groups = self.all_sprites)

        # fence
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x*TILE_SIZE, y*TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

        # water
        water_frames = import_folder('../graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water(pos = (x*TILE_SIZE, y*TILE_SIZE), frames = water_frames, groups = self.all_sprites)

        # trees
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree((obj.x, obj.y), obj.image,
                 [self.all_sprites, self.collision_sprites, self.tree_sprites], obj.name,
                 self.player_add)

        # wildFlowers
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        Generic((0, 0), pygame.image.load('../graphics/world/ground.png').convert_alpha()
                , self.all_sprites, LAYERS['ground'])

        # collision tiles
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)),
                    self.collision_sprites)

        # Player
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name=='Start':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites,
                                     self.tree_sprites, self.interaction_sprites, self.soil_layer,
                                     self.toggle_shop)
            if obj.name=='Bed':
                Interaction((obj.x, obj.y), (obj.height, obj.width), self.interaction_sprites,
                            obj.name)

            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.height, obj.width), self.interaction_sprites,
                            obj.name)

    def reset(self):
        self.soil_layer.update_plants()
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 3
        self.soil_layer.raining = self.raining
        self.sky.start_color = [255,255,255]
        if self.raining:
            self.soil_layer.water_all()

        for tree in self.tree_sprites.sprites():
            if tree.apple_sprites:
                for apple in tree.apple_sprites.sprites():
                    apple.kill()
            tree.create_fruit()

    def run(self, dt):

        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)

        if self.shop_active:
            self.menu.update()
        else:
            self.all_sprites.update(dt)
            self.plant_collision()

        self.overlay.display()

        if self.raining and not self.shop_active:
            self.rain.update()

        self.sky.display(dt)

        if self.player.sleep:
            self.transition.play()

    def player_add(self, item):
        self.success.play()
        self.player.item_inventory[item] += 1

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def plant_collision(self):
        if self.soil_layer.plant_sptires:
            for plant in self.soil_layer.plant_sptires.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, LAYERS['main'])
                    row = plant.rect.centery // TILE_SIZE
                    col = plant.rect.centerx // TILE_SIZE
                    self.soil_layer.grid[row][col].remove('P')

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
                if layer != sprite.z:
                    continue
                offset_rect = sprite.rect.copy()
                offset_rect.center -= self.offset
                self.display_surface.blit(sprite.image, offset_rect)
