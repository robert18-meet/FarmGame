import pygame
from settings import *
from random import randint, choice
from timer import Timer

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width*0.2, -self.rect.height*0.75)

class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name

class Water(Generic):
    def __init__(self, pos, frames, groups):
        self.frames = frames
        self.frame_index = 0

        super().__init__(pos = pos, surf = self.frames[self.frame_index], groups = groups,
                         z = LAYERS['water'])

    def animate(self, dt):
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)

class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos = pos, surf = surf, groups = groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height*0.9)

class Tree(Generic):
    def __init__(self, pos, surf, groups, name, player_add):
        super().__init__(pos, surf, groups)

        self.health = 10
        self.alive = True
        self.stump_surf = pygame.image.load(f'../graphics/stumps/{name}.png').convert_alpha()
        self.invul_timer = Timer(200)

        self.apple_surf = pygame.image.load('../graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.apple_sprites = pygame.sprite.Group()

        self.create_fruit()

        self.player_add = player_add

        self.axe_sound = pygame.mixer.Sound('../audio/axe.mp3')

    def damage(self):
        self.health = self.health - 0.01
        self.axe_sound.play()
        if len(self.apple_sprites.sprites()) <= 0 or randint(0, 1000) > 5:
            return
        random_apple = choice(self.apple_sprites.sprites())
        Particle(random_apple.rect.topleft, random_apple.image, self.groups()[0], LAYERS['fruit'])
        random_apple.kill()
        self.player_add('apple')


    def check_death(self):
        if self.health >= 0:
            return
        self.alive = False
        Particle(self.rect.topleft, self.image, self.groups()[0], LAYERS['main'])
        self.image = self.stump_surf
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
        self.hitbox = self.rect.copy().inflate(-10, -self.rect.height*0.6)
        self.player_add('wood')
        for apple in self.apple_sprites.sprites():
            apple.kill()
            self.player_add('apple')

    def update(self, dt):
        if self.alive is False:
            return
        self.check_death()

    def create_fruit(self):
        for pos in self.apple_pos:
            if randint(0, 10) > 8:
                continue
            x = self.rect.left + pos[0]
            y = self.rect.top + pos[1]
            Generic((x, y), self.apple_surf, [self.apple_sprites, self.groups()[0]],
                    z=LAYERS['fruit'])

class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration = 200):
        super().__init__(pos, surf, groups, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0,0,0))
        self.image = new_surf

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time < self.duration:
            return
        self.kill()
