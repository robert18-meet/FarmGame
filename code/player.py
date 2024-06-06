import pygame
from settings import *
from support import *
from timer import Timer

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer,
                 toggle_shop):
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0

        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200

        # collisions
        self.collision_sptires = collision_sprites
        self.hitbox = self.rect.copy().inflate((-126, -70))

        # timers
        self.timers = {
            'tool switch': Timer(200),
            'seed switch': Timer(200)
        }

        # actions
        self.actions = {
            'tool_use' : False,
            'seed_use' : False
        }

        # tools
        self.tools  = ['hoe', 'axe', 'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]
        self.tool_use = False

        # seeds
        self.seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # inventory
        self.item_inventory = {
            "wood": 0,
            "apple": 0,
            "corn": 0,
            "tomato": 0
        }

        self.seed_inventory = {
            'corn': 5,
            'tomato': 5
        }
        self.money = 200

        # interaction
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.target_pos = 0
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop
        self.wattering = pygame.mixer.Sound('../audio/water.mp3')

        self.seed_timer = Timer(400)

    def use_tool(self):
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
            self.wattering.play()

    def get_target_position(self):
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def use_seed(self):
        if self.seed_inventory[self.selected_seed]:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1

    def import_assets(self):
        self.animations = {'up': [],'down': [],'left': [],'right': [],
						   'right_idle':[],'left_idle':[],'up_idle':[],'down_idle':[],
						   'right_hoe':[],'left_hoe':[],'up_hoe':[],'down_hoe':[],
						   'right_axe':[],'left_axe':[],'up_axe':[],'down_axe':[],
						   'right_water':[],'left_water':[],'up_water':[],'down_water':[]}

        for animation in self.animations.keys():
            full_path = '../graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index > len(self.animations[self.status]):
            self.frame_index = 0
        try:
            self.image = self.animations[self.status][int(self.frame_index)]
        except:
            self.frame_index = 0
            self.image = self.animations[self.status][int(self.frame_index)]

    def input(self):
        keys = pygame.key.get_pressed()

        if not (True in self.actions.values()) and not self.sleep:
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

        # tool use
        if keys[pygame.K_SPACE]:
            self.actions['tool_use'] = True
            self.direction = pygame.math.Vector2()
            self.use_tool()
            self.seed_timer.activate()
        else:
            self.actions['tool_use'] = False

        # change tool
        if keys[pygame.K_q] and not self.timers['tool switch'].active and not self.actions['tool_use']:
            self.timers['tool switch'].activate()
            self.tool_index +=1

            if self.tool_index >= len(self.tools):
                self.tool_index = 0

            self.selected_tool = self.tools[self.tool_index]

        # seed use
        if keys[pygame.K_LCTRL] and not self.seed_timer.active:
            self.actions['seed_use'] = True
            self.direction = pygame.math.Vector2()
            self.use_seed()
            self.seed_timer.activate()
        else:
            self.actions['seed_use'] = False

        # change use
        if keys[pygame.K_e] and not self.timers['seed switch'].active and not self.actions['seed_use']:
            self.timers['seed switch'].activate()
            self.seed_index +=1

            if self.seed_index >= len(self.seeds):
                self.seed_index = 0

            self.selected_seed = self.seeds[self.seed_index]

        if keys[pygame.K_RETURN]:
            collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
            if collided_interaction_sprite:
                if collided_interaction_sprite[0].name == 'Bed':
                    self.status = 'left_idle'
                    self.sleep = True
                if collided_interaction_sprite[0].name == 'Trader':
                    self.toggle_shop()

    def get_status(self):
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        if self.actions['tool_use']:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def collision(self, direction):
        for sprite in self.collision_sptires.sprites():
            if not hasattr(sprite, 'hitbox'):
                continue
            if not sprite.hitbox.colliderect(self.hitbox):
                continue
            if direction == 'horizontal':
                if self.direction.x > 0:
                    self.hitbox.right = sprite.hitbox.left
                if self.direction.x < 0:
                    self.hitbox.left = sprite.hitbox.right
                self.rect.centerx = self.hitbox.centerx
                self.pos.x = self.hitbox.centerx
            if direction == 'vertical':
                if self.direction.y > 0:
                    self.hitbox.bottom = sprite.hitbox.top
                if self.direction.y < 0:
                    self.hitbox.top = sprite.hitbox.bottom
                self.rect.centery = self.hitbox.centery
                self.pos.y = self.hitbox.centery

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()
            self.seed_timer.update()

    def move(self, dt):

        # normalizing a vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')
        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def update(self, dt):
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_position()
        self.move(dt)
        self.animate(dt)
