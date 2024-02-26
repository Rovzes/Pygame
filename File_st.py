import os
import sys
import pygame
import csv
from math import fabs, copysign, sqrt, pow
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox


pygame.init()
size = WIDTH, HEIGHT = 1000, 1000
display = pygame.display
screen = pygame.display.set_mode(size)
mus = pygame.mixer.Sound("data/music.mp3")
mus.set_volume(0.5)
step = pygame.mixer.music
step.load('data/footstep_grass_000.ogg')
step.set_volume(0.5)
enter = pygame.mixer.Sound('data/enter.wav')
sound = pygame.mixer.Sound('data/sound.mp3')
flPause = True
FPS = 25
level_posx = 1
level_posy = 1
inventory = []
open_doors = []


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(all_sprites)
        self.type = tile_type
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x, tile_height * self.pos_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x + (tile_width // 2 - self.image.get_rect().w // 2),
            tile_height * self.pos_y + (tile_width // 2 - self.image.get_rect().h // 2))
        self.look_x = 0
        self.look_y = 1

    def movement(self, args):
        move_x = 0
        move_y = 0
        if args[pygame.K_a]:
            move_x += -8
            self.look_x = -1
            self.look_y = 0
        if args[pygame.K_d]:
            move_x += 8
            self.look_x = 1
            self.look_y = 0
        if args[pygame.K_w]:
            move_y += -8
            self.look_x = 0
            self.look_y = -1
        if args[pygame.K_s]:
            move_y += 8
            self.look_x = 0
            self.look_y = 1
        if ([(self.rect.x + move_x) // tile_width, self.rect.y // tile_width] in borders or
            [(self.rect.x + self.rect.w + move_x) // tile_width, self.rect.y // tile_width] in borders) or \
                ([(self.rect.x + move_x) // tile_width, (self.rect.y + self.rect.h) // tile_width] in borders or
                 [(self.rect.x + self.rect.w + move_x) // tile_width,
                  (self.rect.y + self.rect.h) // tile_width] in borders):
            move_x = 0
        if ([self.rect.x // tile_width, (self.rect.y + move_y) // tile_width] in borders or
            [(self.rect.x + self.rect.w) // tile_width, (self.rect.y + move_y) // tile_width] in borders) or \
                ([self.rect.x // tile_width, (self.rect.y + self.rect.h + move_y) // tile_width] in borders or
                 [(self.rect.x + self.rect.w) // tile_width,
                  (self.rect.y + self.rect.h + move_y) // tile_width] in borders):
            move_y = 0
        if fabs(move_x) == fabs(move_y):
            move_x = copysign(fabs(move_x) / 1.5, move_x)
            move_y = copysign(fabs(move_y) / 1.5, move_y)
        if move_x != 0 or move_y != 0:
            if not step.get_busy():
                step.play()
            if move_x != 0:
                if move_x > 0:
                    self.image = walk_right.anim()[0]
                else:
                    self.image = walk_left.anim()[0]
            if move_y != 0:
                if move_y > 0:
                    self.image = walk_down.anim()[0]
                else:
                    self.image = walk_up.anim()[0]
        else:
            self.image = load_image(f"guy{self.look_x}{self.look_y}.png")
        if self.rect.x + self.rect.w + move_x > WIDTH or self.rect.x + move_x < 0 or \
                self.rect.y + move_y < 0 or self.rect.y + self.rect.h + move_y > HEIGHT:
            self.next_level(move_x, move_y)
            move_x,  move_y = 0, 0
        self.rect.x += move_x
        self.rect.y += move_y

    def next_level(self, move_x, move_y):
        global player, level_posx, level_posy, level_x, level_y
        x, y = None, None
        if self.rect.x + self.rect.w + move_x > WIDTH:
            level_posx += 1
            x = 1
            y = self.rect.y // tile_width
        elif self.rect.x + move_x < 0:
            level_posx -= 1
            x = level_x - 1
            y = self.rect.y // tile_width
        elif self.rect.y + move_y < 0:
            level_posy += 1
            x = self.rect.x // tile_width
            y = level_y - 1
        elif self.rect.y + self.rect.h + move_y > HEIGHT:
            level_posy -= 1
            x = self.rect.x // tile_width
            y = 1
        enter.play()
        player, a, b, c = generate_level(load_level(f'level{level_posx}{level_posy}.csv'), (x, y))

    def action(self):
        for i in list(action_group):
            if [(self.rect.x + self.rect.w / 2) // tile_width + self.look_x,
                (self.rect.y + self.rect.h / 2) // tile_width + self.look_y] == \
                    [(i.rect.x + i.rect.w / 2) // tile_width, (i.rect.y + i.rect.h / 2) // tile_width]:
                i.act()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(enemy_group, all_sprites)
        self.image = enemy_image
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x + (tile_width // 2 - self.image.get_rect().w // 2),
            tile_height * self.pos_y + (tile_width // 2 - self.image.get_rect().h // 2))
        self.rl = 1
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, target):
        image, frame = enemy_walk_right.anim()
        dx = target.x - self.rect.x
        dy = self.rect.y - target.y
        r = sqrt(pow(dx, 2) + pow(dy, 2))
        move_x = 0
        move_y = 0
        if r != 0:
            move_y = dy / r * 5
            move_x = dx / r * 5
        if frame in range(4, 8):
            move_x = move_y = 0
        if move_x > 0:
            self.image = image
        elif move_x < 0:
            self.image = pygame.transform.flip(image, True, False)
        if ([(self.rect.x + move_x) // tile_width, self.rect.y // tile_width] in borders or
            [(self.rect.x + self.rect.w + move_x) // tile_width, self.rect.y // tile_width] in borders) or \
                ([(self.rect.x + move_x) // tile_width, (self.rect.y + self.rect.h) // tile_width] in borders or
                 [(self.rect.x + self.rect.w + move_x) // tile_width,
                  (self.rect.y + self.rect.h) // tile_width] in borders):
            move_x = 0
        if ([self.rect.x // tile_width, (self.rect.y - move_y) // tile_width] in borders or
            [(self.rect.x + self.rect.w) // tile_width, (self.rect.y - move_y) // tile_width] in borders) or \
                ([self.rect.x // tile_width, (self.rect.y + self.rect.h - move_y) // tile_width] in borders or
                 [(self.rect.x + self.rect.w) // tile_width,
                  (self.rect.y + self.rect.h - move_y) // tile_width] in borders):
            move_y = 0
        self.rect.x += move_x
        self.rect.y -= move_y
        if pygame.sprite.collide_mask(self, player):
            player.kill()
            end_screen('lose.png')


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def anim(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]
        return [self.image, self.cur_frame]


class Item(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(action_group, all_sprites)
        self.type = tile_type
        self.pos_x = pos_x
        self.pos_y = pos_y
        if [f"{self.type}{level_posx}{level_posy}", self.pos_x, self.pos_y] in open_doors:
            self.image = self.image1 = tile_images[tile_type][1]
            if self.type == "door":
                borders.remove([self.pos_x, self.pos_y])
        else:
            self.image, self.image1 = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x + (tile_width // 2 - self.image.get_rect().w // 2),
            tile_height * self.pos_y + (tile_width // 2 - self.image.get_rect().h // 2))

    def act(self):
        if self.type == "door":
            if self.image != self.image1:
                if f"key{level_posx}{level_posy}" in inventory:
                    open_doors.append([f"{self.type}{level_posx}{level_posy}", self.pos_x, self.pos_y])
                    borders.remove([self.pos_x, self.pos_y])
                    self.image = self.image1
        elif self.type == "chest" and f"key{level_posx}{level_posy}" not in inventory:
            a = self.rect.y - 55
            sound.play()
            for i in range(24):
                self.image, frame = get_key.anim()
                self.rect.y = a
                all_sprites.draw(screen)
                display.flip()
                clock.tick(20)
            inventory.append(f"key{level_posx}{level_posy}")
            open_doors.append([f"{self.type}{level_posx}{level_posy}", self.pos_x, self.pos_y])
            self.rect.y += 55
            self.image = self.image1
        elif self.type == "flag":
            player.kill()
            end_screen("win.png")


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, type, image):
        super().__init__(menu_group)
        self.pos_x = x
        self.pos_y = y
        self.type = type
        self.image = image
        self.rect = self.image.get_rect().move(self.pos_x, self.pos_y)


def load_image(name, colorkey=None):
    fullname = os.path.join('data/images', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    menu_group.empty()
    fon = pygame.transform.scale(load_image('bg_menu.png'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 80)
    text_coord = HEIGHT / 2 - font.get_height() / 2
    play = Button(20, 100, "play", load_image("play.png"))
    options = Button(20, 200, "options", load_image("options.png"))
    quit = Button(20, 300, "quit", load_image("quit.png"))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i in menu_group:
                    if i.rect.collidepoint(event.pos):
                        if i.type == "play":
                            return
                        elif i.type == "options":
                            option_screen()
                            return 
                        elif i.type == "quit":
                            terminate()
        menu_group.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def option_screen():
    menu_group.empty()
    controllers = ["Move - W A S D", "Action - L Shift", "Exit - Escape"]
    volume = ["Music volume", "Sound volume"]
    fon = pygame.transform.scale(load_image('bg_menu.png'), (WIDTH, HEIGHT))

    back = Button(20, 30, "back", load_image("back.png"))

    mus_vol = Slider(screen, 300, 380, 400, 30, min=0, max=1, step=0.01, handleRadius=15)
    mus_vol.setValue(mus.get_volume())
    out_mus = TextBox(screen, 220, 365, 50, 50, fontSize=30)

    snd_vol = Slider(screen, 300, 580, 400, 30, min=0, max=1, step=0.01, handleRadius=15)
    snd_vol.setValue(step.get_volume())
    out_snd = TextBox(screen, 220, 565, 50, 50, fontSize=30)

    while True:
        screen.blit(fon, (0, 0))
        clock.tick(FPS)
        control = pygame.font.Font(None, 80)
        vol = pygame.font.Font(None, 40)
        text_coord = 70
        for line in controllers:
            string_rendered = control.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = WIDTH / 2 - intro_rect.width / 2
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)
        text_coord = 320
        for line in volume:
            string_rendered = vol.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            intro_rect.top = text_coord
            intro_rect.x = WIDTH / 2 - intro_rect.width / 2
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)
            text_coord += 180
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back.rect.collidepoint(event.pos):
                    start_screen()
                    return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    start_screen()
                    return
        out_mus.setText(int(mus_vol.getValue() * 100))
        out_snd.setText(int(snd_vol.getValue() * 100))
        menu_group.draw(screen)
        pygame_widgets.update(pygame.event.get())
        mus.set_volume(mus_vol.getValue())
        step.set_volume(snd_vol.getValue())
        enter.set_volume(snd_vol.getValue())
        sound.set_volume(snd_vol.getValue())
        pygame.display.flip()


def end_screen(final):
    intro_text = ["поздравляем"]
    fon = pygame.transform.scale(load_image(final), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 100)
    text_coord = HEIGHT / 2 - font.get_height() / 2
    """for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = WIDTH / 2 - intro_rect.width / 2
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)"""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                terminate()
        pygame.display.flip()
        clock.tick(FPS)


tile_images = {
    'wall': load_image('wall.png'),
    'wall1': load_image('wall1.png'),
    'grass1': load_image('grass1.png'),
    'grass2': load_image('grass2.png'),
    'grass3': load_image('grass3.png'),
    'ground1': load_image('ground1.png'),
    'tree1': load_image('tree1.png'),
    'slime': load_image('SlimeIdle.png'),
    'chest': [load_image('chest-closed.png'), load_image('chest-opened.png')],
    'door': [load_image('door-closed.png'), load_image('door-opened.png')],
    'flag': [load_image('flag.png'), load_image('flag.png')]
}

player_image = load_image('guy01.png')
enemy_image = load_image('SlimeIdle.png')
tile_width = tile_height = 100

player = None
all_sprites = pygame.sprite.Group()
action_group = pygame.sprite.Group()
menu_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
borders = []


walk_up = AnimatedSprite(load_image("character_move_up.png"), 8, 2, 64, 64)
walk_down = AnimatedSprite(load_image("character_move_down.png"), 8, 2, 64, 64)
walk_left = AnimatedSprite(load_image("character_move_left.png"), 8, 2, 64, 64)
walk_right = AnimatedSprite(load_image("character_move_right.png"), 8, 2, 64, 64)

get_key = AnimatedSprite(load_image("get_key.png"), 8, 2, 100, 155)

enemy_walk_right = AnimatedSprite(load_image("Slime.png"), 8, 2, 64, 64)


def load_level(filename):
    filename = "data/" + filename
    with open(filename, encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        return list(reader)


def generate_level(level, pl_pos):
    new_player, enem, x, y = None, None, None, None
    en_pos = []
    player_group.empty()
    enemy_group.empty()
    action_group.empty()
    borders.clear()
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                borders.append([x, y])
                Tile('wall1', x, y)

            elif level[y][x] == ".":
                print(1)
                Tile("floor", x, y)

            elif level[y][x] == 'wall':
                borders.append([x, y])
                Tile('wall', x, y)

            elif level[y][x] == "grass1":
                Tile("grass1", x, y)

            elif level[y][x] == "grass2":
                Tile("grass2", x, y)

            elif level[y][x] == "grass3":
                Tile("grass3", x, y)

            elif level[y][x] == "ground1":
                Tile("ground1", x, y)

            elif level[y][x] == "tree1":
                borders.append([x, y])
                Tile("tree1", x, y)

            elif level[y][x] == "slime":
                Tile("grass3", x, y)
                en_pos.append((x, y))

            elif level[y][x] == "chest":
                borders.append([x, y])
                Tile("grass2", x, y)
                Item("chest", x, y)

            elif level[y][x] == "door":
                borders.append([x, y])
                Tile("ground1", x, y)
                Item("door", x, y)

            elif level[y][x] == "flag":
                borders.append([x, y])
                Tile("ground1", x, y)
                Item("flag", x, y)
    new_player = Player(*pl_pos)
    for i in en_pos:
        enem = Enemy(*i)
    return new_player, enem, x, y


clock = pygame.time.Clock()
start_screen()
pygame.mixer.find_channel().play(mus)
player, enemy, level_x, level_y = generate_level(load_level(f'level{level_posx}{level_posy}.csv'), (1, 8))
font = pygame.font.Font(None, 30)
text_coord = 50
while True:
    screen.fill(pygame.Color('black'))
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                flPause = not flPause
                if flPause:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            if event.key == pygame.K_LSHIFT:
                player.action()
            elif event.key == pygame.K_ESCAPE:
                start_screen()
    if len(enemy_group):
        enemy_group.update(player.rect)
    player.movement(pygame.key.get_pressed())
    all_sprites.draw(screen)
    display.flip()
