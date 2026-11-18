import pygame
import random
import sys
from collections import deque

pygame.init()
pygame.font.init()

MAP = [
    '1111111111111111111111111111',
    '1            11            1',
    '1 1111 11111 11 11111 1111 1',
    '1B1111 11111 11 11111 1111B1',
    '1 1111 11111 11 11111 1111 1',
    '1                          1',
    '1 1111 11 11111111 11 1111 1',
    '1 1111 11 11111111 11 1111 1',
    '1      11    11    11      1',
    '111111 11111011011111 111111',
    '111111 11111011011111 111111',
    '111111 110000r0000011 111111',
    '111111 110111--111011 111111',
    '111111 11010000001011 111111',
    '000000 00010sp0o01000 000000',
    '111111 11010000001011 111111',
    '111111 11011111111011 111111',
    '111111 11000000000011 111111',
    '111111 11011111111011 111111',
    '111111 11011111111011 111111',
    '1            11            1',
    '1 1111 11111 11 11111 1111 1',
    '1 1111 11111 11 11111 1111 1',
    '1B  11       P0       11  B1',
    '111 11 11 11111111 11 11 111',
    '111 11 11 11111111 11 11 111',
    '1      11    11    11      1',
    '1 1111111111 11 1111111111 1',
    '1 1111111111 11 1111111111 1',
    '1                          1',
    '1111111111111111111111111111',
]

BOARD_RATIO = (len(MAP[0]), len(MAP))
CHAR_SIZE = 16
TOP_ROWS, BOTTOM_ROWS = 3, 2
WIDTH, HEIGHT = (BOARD_RATIO[0] * CHAR_SIZE, BOARD_RATIO[1] * CHAR_SIZE)
TOP_HEIGHT = TOP_ROWS * CHAR_SIZE
SCREEN_WIDTH = WIDTH
SCREEN_HEIGHT = (BOARD_RATIO[1] + TOP_ROWS + BOTTOM_ROWS) * CHAR_SIZE
FPS = 30
PAUSE_FRAMES = 30

SPEED_SCALE = 1.0
BASE_SPEED = 75.75 * (CHAR_SIZE / 8) / FPS * SPEED_SCALE

SPEED_PCT = {
    'pac':     [80, 90, 100, 90],
    'pacFr':   [90, 95, 100, 100],
    'ghost':   [75, 85, 95, 95],
    'ghostFr': [50, 55, 60, 60],
    'tunnel':  [40, 45, 50, 50],
    'elroy1':  [80, 90, 100, 90],
    'elroy2':  [85, 95, 105, 95],
}
EYES_SPEED = 1.6 * BASE_SPEED


def level_speeds(level):
    band = 0 if level == 1 else 1 if level <= 4 else 2 if level <= 20 else 3
    return {k: v[band] * BASE_SPEED / 100 for k, v in SPEED_PCT.items()}


FRIGHT_SECONDS = [6, 5, 4, 3, 2, 5, 2, 2, 1, 5, 2, 1, 1, 3, 1, 1, 0, 1, 0, 0, 0]
ELROY_DOTS = [(20, 10), (30, 15), (40, 20), (40, 20), (40, 20), (50, 25), (50, 25),
              (50, 25), (60, 30), (60, 30), (60, 30), (80, 40), (80, 40), (80, 40),
              (100, 50), (100, 50), (100, 50), (100, 50), (120, 60), (120, 60), (120, 60)]
ORIGINAL_DOTS = 244
GHOST_POINTS = [200, 400, 800, 1600]


def level_value(table, level):
    return table[min(level, len(table)) - 1]


MODE_FRAMES = [7 * FPS, 20 * FPS, 7 * FPS, 20 * FPS, 5 * FPS, 20 * FPS, 5 * FPS]
LAST_MODE_IDX = len(MODE_FRAMES)

SCATTER_TARGET = (25, -5)
PINKY_SCATTER_TARGET = (2, -5)
INKY_SCATTER_TARGET = (26, 30)
CLYDE_SCATTER_TARGET = (1, 30)
ARCADE_UP_BUG = True
PINKY_LOOKAHEAD = 4
INKY_LOOKAHEAD = 2
CLYDE_FEAR_DISTANCE = 8

WAITING_KINDS = ('pinky', 'inky', 'clyde')
DOT_LIMITS = {'pinky': {}, 'inky': {1: 30}, 'clyde': {1: 60, 2: 50}}
GLOBAL_LIMITS = {'pinky': 7, 'inky': 17, 'clyde': 32}
HOUSE_IDLE_FRAMES = 4 * FPS

TUNNEL_ROW = next(r for r, row in enumerate(MAP) if row[0] != '1')
TUNNEL_LEFT_COL = 5
TUNNEL_RIGHT_COL = BOARD_RATIO[0] - 6
NO_TURN_ZONES = {(c, r) for c in range(11, 17) for r in (11, 23)}

DIRS = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}
PRIORITY = ['up', 'left', 'down', 'right']


def is_aligned(rect):
    return ((rect.x - 2) % CHAR_SIZE == 0 and (rect.y - 2) % CHAR_SIZE == 0
            and rect.left >= 0 and rect.right <= WIDTH)


def wall_hit(rect, dx, dy, walls):
    return rect.inflate(4, 4).move(dx, dy).collidelist(walls) != -1


def wrap_tunnel(rect):
    if rect.right <= 0:
        rect.x += WIDTH + CHAR_SIZE
    elif rect.left >= WIDTH:
        rect.x -= WIDTH + CHAR_SIZE


def tile_of(rect):
    return (round((rect.x - 2) / CHAR_SIZE), round((rect.y - 2) / CHAR_SIZE))


def in_tunnel(rect):
    col, row = tile_of(rect)
    return row == TUNNEL_ROW and (col <= TUNNEL_LEFT_COL or col >= TUNNEL_RIGHT_COL)


def _find_house_tile():
    for y, row in enumerate(MAP):
        for x, ch in enumerate(row):
            if ch == 'p':
                return (x, y)


HOUSE_TILE = _find_house_tile()
DOOR_TILES = {(x, y) for y, row in enumerate(MAP) for x, ch in enumerate(row) if ch == '-'}
DOOR_ROW = next(iter(DOOR_TILES))[1]
HOUSE_EXIT_ROW = DOOR_ROW - 1


def _build_house_dist():
    dist = {HOUSE_TILE: 0}
    queue = deque([HOUSE_TILE])
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in DIRS.values():
            nx, ny = cx + dx, cy + dy
            if (0 <= ny < len(MAP) and 0 <= nx < len(MAP[0])
                    and MAP[ny][nx] != '1' and (nx, ny) not in dist):
                dist[(nx, ny)] = dist[(cx, cy)] + 1
                queue.append((nx, ny))
    return dist


HOUSE_DIST = _build_house_dist()

WALL_COLOR = (33, 33, 222)
SPRITE_SIZE = CHAR_SIZE * 14 // 8


def _is_wall(x, y):
    if not (0 <= y < len(MAP) and 0 <= x < len(MAP[0])):
        return True
    return MAP[y][x] == '1'


def _eroded_layer(d, color):
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(len(MAP)):
        for x in range(len(MAP[0])):
            if not _is_wall(x, y):
                continue
            l = 0 if _is_wall(x - 1, y) else d
            r = 0 if _is_wall(x + 1, y) else d
            u = 0 if _is_wall(x, y - 1) else d
            b = 0 if _is_wall(x, y + 1) else d
            layer.fill(color, (x * CHAR_SIZE + l, y * CHAR_SIZE + u,
                               CHAR_SIZE - l - r, CHAR_SIZE - u - b))
    for y in range(len(MAP)):
        for x in range(len(MAP[0])):
            if not _is_wall(x, y):
                continue
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                if _is_wall(x + sx, y) and _is_wall(x, y + sy) and not _is_wall(x + sx, y + sy):
                    nx = x * CHAR_SIZE if sx < 0 else (x + 1) * CHAR_SIZE - d
                    ny = y * CHAR_SIZE if sy < 0 else (y + 1) * CHAR_SIZE - d
                    layer.fill((0, 0, 0, 0), (nx, ny, d, d))
    return layer


def build_maze_surface():
    t = max(1, CHAR_SIZE // 8)
    s = max(1, CHAR_SIZE // 4)
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill((0, 0, 0))
    surf.blit(_eroded_layer(s, WALL_COLOR + (255,)), (0, 0))
    surf.blit(_eroded_layer(s + t, (0, 0, 0, 255)), (0, 0))
    return surf


def draw_centered(surface, sprite):
    surface.blit(sprite.image, sprite.image.get_rect(center=sprite.rect.center))


class Display:
    def __init__(self, screen, field):
        self.screen = screen
        self.field = field
        self.font = pygame.font.Font(None, 24)
        self.hud_font = pygame.font.Font(None, CHAR_SIZE + 4)
        self.game_over_font = pygame.font.Font(None, 48)
        self.text_color = pygame.Color("white")

    def show_life(self, life):
        cy = TOP_HEIGHT + HEIGHT + CHAR_SIZE
        for i in range(min(max(life, 0), 5)):
            cx = int((0.5 + 2 * i) * CHAR_SIZE) + CHAR_SIZE
            pygame.draw.rect(self.screen, (255, 255, 0),
                             (cx - CHAR_SIZE // 2, cy - CHAR_SIZE // 2, CHAR_SIZE, CHAR_SIZE))

    def show_level(self, level):
        surf = self.hud_font.render(f'LEVEL {level}', True, self.text_color)
        self.screen.blit(surf, (9 * CHAR_SIZE, 0))

    def show_score(self, score):
        label = self.hud_font.render('1UP', True, self.text_color)
        self.screen.blit(label, (3 * CHAR_SIZE, 0))
        surf = self.hud_font.render(str(score), True, self.text_color)
        self.screen.blit(surf, (7 * CHAR_SIZE - surf.get_width(), CHAR_SIZE))

    def game_over(self):
        message = self.game_over_font.render('GAME OVER!!', True, pygame.Color("chartreuse"))
        instruction = self.font.render('Touch to Restart', True, pygame.Color("aqua"))
        self.field.blit(message, (WIDTH // 4 - 20, HEIGHT // 3))
        self.field.blit(instruction, (WIDTH // 4, HEIGHT // 2))


class Ghost(pygame.sprite.Sprite):
    RANDOM_ORDER = ['right', 'down', 'left', 'up']

    def __init__(self, row, col, color, kind, in_house=False):
        super().__init__()
        self.abs_x = row * CHAR_SIZE
        self.abs_y = col * CHAR_SIZE
        self.kind = kind
        self.scatter_target = {'blinky': SCATTER_TARGET,
                               'pinky': PINKY_SCATTER_TARGET,
                               'inky': INKY_SCATTER_TARGET,
                               'clyde': CLYDE_SCATTER_TARGET}[kind]
        self.color = pygame.Color(color)
        size = SPRITE_SIZE

        self.normal_image = pygame.Surface((size, size))
        self.normal_image.fill(self.color)
        self.scared_image = pygame.Surface((size, size))
        self.scared_image.fill(pygame.Color("royalblue3"))
        self.eyes_image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.eyes_image.fill((255, 255, 255), (size // 4, size // 4, size // 2, size // 2))
        self.image = self.normal_image
        self.rect = pygame.Rect(self.abs_x + 2, self.abs_y + 2, CHAR_SIZE - 4, CHAR_SIZE - 4)
        self.speeds = level_speeds(1)
        self.acc = 0.0
        self.moving_dir = 'left' if kind == 'blinky' else 'up'
        self.reverse_pending = False
        self.frightened = False
        self.eaten = False
        self.elroy = 0
        self.in_house = in_house
        self.waiting = kind in WAITING_KINDS
        self.leaving = False

    def _refresh_image(self):
        if self.eaten:
            self.image = self.eyes_image
        elif self.frightened:
            self.image = self.scared_image
        else:
            self.image = self.normal_image

    def current_speed(self):
        if self.eaten:
            return EYES_SPEED
        in_tun = in_tunnel(self.rect)
        if in_tun and not self.frightened:
            return self.speeds['tunnel']
        if self.frightened:
            return self.speeds['ghostFr']
        if self.kind == 'blinky' and self.elroy == 2:
            return self.speeds['elroy2']
        if self.kind == 'blinky' and self.elroy == 1:
            return self.speeds['elroy1']
        return self.speeds['ghost']

    def move_to_start_pos(self):
        self.rect.x = self.abs_x + 2
        self.rect.y = self.abs_y + 2
        self.moving_dir = 'left' if self.kind == 'blinky' else 'up'
        self.reverse_pending = False
        self.eaten = False
        self.frightened = False
        self.elroy = 0
        self.acc = 0.0
        self.waiting = self.kind in WAITING_KINDS
        self.leaving = False
        self._refresh_image()

    def reverse(self):
        if not (self.waiting or self.leaving or self.eaten):
            self.reverse_pending = True

    def release(self):
        self.waiting = False
        self.leaving = True

    def eat(self):
        self.eaten = True
        self.frightened = False
        self.waiting = False
        self.leaving = False
        self.reverse_pending = False

    def _revive(self):
        self.eaten = False
        self.moving_dir = 'up'
        self.leaving = True

    def _decide(self, walls, target):
        col, row = tile_of(self.rect)
        avail = []
        for k in PRIORITY:
            dx, dy = DIRS[k]
            if wall_hit(self.rect, dx, dy, walls):
                continue
            if (col + dx, row + dy) in DOOR_TILES and not (self.eaten or self.leaving):
                continue
            avail.append(k)
        if not avail:
            return

        if self.leaving and not self.eaten:
            hx, hy = HOUSE_TILE
            if row == hy and col != hx:
                self.moving_dir = 'right' if col < hx else 'left'
                return
            if col == hx and row > HOUSE_EXIT_ROW:
                self.moving_dir = 'up'
                return
            self.leaving = False
            self.moving_dir = 'left'
            return

        if not self.eaten and (col, row) in NO_TURN_ZONES and self.moving_dir in avail:
            return

        if self.eaten:
            if (col, row) == HOUSE_TILE:
                self._revive()
                return
            best = None
            for k in avail:
                d = HOUSE_DIST.get((col + DIRS[k][0], row + DIRS[k][1]))
                if d is not None and (best is None or d < best[0]):
                    best = (d, k)
            if best:
                self.moving_dir = best[1]
                return
            target = HOUSE_TILE
            choices = avail
        else:
            forward = [k for k in avail if k != OPPOSITE[self.moving_dir]]
            choices = forward or avail

        if target is None:
            d = random.randrange(4)
            for _ in range(4):
                k = self.RANDOM_ORDER[d]
                if k in choices:
                    self.moving_dir = k
                    return
                d = (d + 1) % 4
            self.moving_dir = choices[0]
        else:
            tx, ty = target

            def dist(k):
                dx, dy = DIRS[k]
                return (col + dx - tx) ** 2 + (row + dy - ty) ** 2

            self.moving_dir = min(choices, key=dist)

    def update(self, walls, target=None):
        self._refresh_image()
        if self.waiting:
            return
        if self.reverse_pending:
            self.reverse_pending = False
            back = OPPOSITE[self.moving_dir]
            if not wall_hit(self.rect, *DIRS[back], walls):
                self.moving_dir = back

        self.acc += self.current_speed()
        steps = int(self.acc)
        self.acc -= steps
        for _ in range(steps):
            if is_aligned(self.rect):
                self._decide(walls, target)
            dx, dy = DIRS[self.moving_dir]
            if not wall_hit(self.rect, dx, dy, walls):
                self.rect.move_ip(dx, dy)
            wrap_tunnel(self.rect)


class Pac(pygame.sprite.Sprite):
    def __init__(self, row, col):
        super().__init__()
        self.abs_x = row * CHAR_SIZE
        self.abs_y = col * CHAR_SIZE
        self.image = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE))
        self.image.fill((255, 255, 0))
        self.rect = pygame.Rect(self.abs_x + 2, self.abs_y + 2, CHAR_SIZE - 4, CHAR_SIZE - 4)
        self.speed = level_speeds(1)['pac']
        self.speed_fright = level_speeds(1)['pacFr']
        self.acc = 0.0
        self.immune_time = 0
        self.immune = False
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.facing = (-1, 0)
        self.life = 3
        self.pac_score = 0

    def move_to_start_pos(self):
        self.rect.x = self.abs_x + 2
        self.rect.y = self.abs_y + 2
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.facing = (-1, 0)
        self.acc = 0.0

    def queue_direction(self, dir_name):
        if dir_name in DIRS:
            self.next_direction = DIRS[dir_name]

    def _step(self, walls):
        nx, ny = self.next_direction
        dx, dy = self.direction
        if (nx, ny) != (0, 0):
            reverse = (dx, dy) != (0, 0) and (nx, ny) == (-dx, -dy)
            if reverse:
                self.direction = self.next_direction
            elif is_aligned(self.rect) and not wall_hit(self.rect, nx, ny, walls):
                self.direction = self.next_direction

        dx, dy = self.direction
        if (dx, dy) != (0, 0):
            self.facing = (dx, dy)
            if not wall_hit(self.rect, dx, dy, walls):
                self.rect.move_ip(dx, dy)
            else:
                self.direction = (0, 0)
        wrap_tunnel(self.rect)

    def animate(self, walls):
        self.acc += self.speed_fright if self.immune_time > 0 else self.speed
        steps = int(self.acc)
        self.acc -= steps
        for _ in range(steps):
            self._step(walls)

    def update(self):
        self.immune = self.immune_time > 0
        if self.immune_time > 0:
            self.immune_time -= 1


class Berry(pygame.sprite.Sprite):
    def __init__(self, row, col, size, is_power_up=False):
        super().__init__()
        self.power_up = is_power_up
        self.size = size
        self.color = pygame.Color("violetred")
        self.abs_x = row * CHAR_SIZE + CHAR_SIZE // 2
        self.abs_y = col * CHAR_SIZE + CHAR_SIZE // 2
        self.rect = pygame.Rect(self.abs_x - size, self.abs_y - size, size * 2, size * 2)
        self.draw_r = size if is_power_up else max(1, size // 2)

    def update(self, screen):
        pygame.draw.rect(screen, self.color,
                         (self.abs_x - self.draw_r, self.abs_y - self.draw_r, self.draw_r * 2, self.draw_r * 2))


class Cell(pygame.sprite.Sprite):
    def __init__(self, row, col, length, width):
        super().__init__()
        self.rect = pygame.Rect(row * length, col * width, length, width)

    def update(self, screen):
        pygame.draw.rect(screen, pygame.Color("blue2"), self.rect)


class World:
    def __init__(self, screen):
        self.screen = screen
        self.field = screen.subsurface(pygame.Rect(0, TOP_HEIGHT, WIDTH, HEIGHT))
        self.player = pygame.sprite.GroupSingle()
        self.ghosts = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.berries = pygame.sprite.Group()
        self.display = Display(self.screen, self.field)
        self.game_over = False
        self.reset_pos = False
        self.pause = 0
        self.game_level = 1
        self.mode_idx = 0
        self.mode_timer = MODE_FRAMES[0]
        self.kill_combo = 0
        self.dot_counters = [0, 0, 0]
        self.use_global = False
        self.global_counter = 0
        self.idle_frames = 0
        self._generate_world()
        self.total_dots = len(self.berries)
        self._apply_speeds()

    def _generate_world(self):
        ghost_colors = {'s': 'skyblue', 'p': 'pink', 'o': 'orange', 'r': 'red'}
        ghost_kinds = {'r': 'blinky', 'p': 'pinky', 's': 'inky', 'o': 'clyde'}
        self.by_kind = {}
        for y, row in enumerate(MAP):
            for x, char in enumerate(row):
                if char == "1":
                    self.walls.add(Cell(x, y, CHAR_SIZE, CHAR_SIZE))
                elif char == " ":
                    self.berries.add(Berry(x, y, CHAR_SIZE // 4))
                elif char == "B":
                    self.berries.add(Berry(x, y, CHAR_SIZE // 2, is_power_up=True))
                elif char in ghost_colors:
                    ghost = Ghost(x, y, ghost_colors[char], ghost_kinds[char],
                                  in_house=(char != 'r'))
                    self.ghosts.add(ghost)
                    self.by_kind[ghost.kind] = ghost
                elif char == "P":
                    self.player.add(Pac(x, y))
        self.walls_collide_list = [w.rect for w in self.walls.sprites()]
        self.door_rects = [pygame.Rect(x * CHAR_SIZE, y * CHAR_SIZE, CHAR_SIZE, CHAR_SIZE)
                           for x, y in sorted(DOOR_TILES)]
        self.pac_collide_list = self.walls_collide_list + self.door_rects
        self.maze_surface = build_maze_surface()

    @property
    def mode(self):
        return 'scatter' if self.mode_idx % 2 == 0 else 'chase'

    def _apply_speeds(self):
        speeds = level_speeds(self.game_level)
        pac = self.player.sprite
        pac.speed = speeds['pac']
        pac.speed_fright = speeds['pacFr']
        for ghost in self.ghosts.sprites():
            ghost.speeds = speeds

    def _reset_round(self, new_level=True):
        self.mode_idx = 0
        self.mode_timer = MODE_FRAMES[0]
        self.kill_combo = 0
        self.idle_frames = 0
        pac = self.player.sprite
        pac.immune_time = 0
        pac.immune = False
        for ghost in self.ghosts.sprites():
            ghost.frightened = False
        if new_level:
            self.dot_counters = [0, 0, 0]
            self.use_global = False
            self.global_counter = 0
        else:
            self.use_global = True
            self.global_counter = 0

    def generate_new_level(self):
        self.berries.empty()
        for y, row in enumerate(MAP):
            for x, char in enumerate(row):
                if char == " ":
                    self.berries.add(Berry(x, y, CHAR_SIZE // 4))
                elif char == "B":
                    self.berries.add(Berry(x, y, CHAR_SIZE // 2, is_power_up=True))
        self.total_dots = len(self.berries)
        self.pause = PAUSE_FRAMES

    def restart_level(self):
        self.berries.empty()
        self.game_level = 1
        for ghost in self.ghosts.sprites():
            ghost.move_to_start_pos()
        pac = self.player.sprite
        pac.pac_score = 0
        pac.life = 3
        pac.move_to_start_pos()
        self.reset_pos = False
        self._apply_speeds()
        self._reset_round(new_level=True)
        self.generate_new_level()

    def _dashboard(self):
        self.display.show_life(self.player.sprite.life)
        self.display.show_level(self.game_level)
        self.display.show_score(self.player.sprite.pac_score)

    def _check_game_state(self):
        if self.player.sprite.life <= 0:
            self.game_over = True
        if len(self.berries) == 0 and self.player.sprite.life > 0:
            self.game_level += 1
            for ghost in self.ghosts.sprites():
                ghost.move_to_start_pos()
            self.player.sprite.move_to_start_pos()
            self._apply_speeds()
            self._reset_round(new_level=True)
            self.generate_new_level()

    def handle_swipe(self, start_pos, end_pos):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        if max(abs(dx), abs(dy)) > 20:
            if abs(dx) > abs(dy):
                self.player.sprite.queue_direction('right' if dx > 0 else 'left')
            else:
                self.player.sprite.queue_direction('down' if dy > 0 else 'up')

    def _update_mode(self):
        if self.player.sprite.immune_time > 0 or self.mode_idx >= LAST_MODE_IDX:
            return
        self.mode_timer -= 1
        if self.mode_timer <= 0:
            self.mode_idx += 1
            if self.mode_idx < LAST_MODE_IDX:
                self.mode_timer = MODE_FRAMES[self.mode_idx]
            for ghost in self.ghosts.sprites():
                ghost.reverse()

    def _start_fright(self):
        pac = self.player.sprite
        seconds = level_value(FRIGHT_SECONDS, self.game_level)
        if seconds <= 0:
            pac.immune_time = 0
        else:
            pac.immune_time = int(seconds * FPS)
            self.kill_combo = 0
        for ghost in self.ghosts.sprites():
            ghost.reverse()

    def _update_elroy(self):
        blinky = self.by_kind['blinky']
        t1, t2 = level_value(ELROY_DOTS, self.game_level)
        scale = self.total_dots / ORIGINAL_DOTS
        t1, t2 = max(1, round(t1 * scale)), max(1, round(t2 * scale))
        left = len(self.berries)
        blinky.elroy = 2 if left <= t2 else 1 if left <= t1 else 0

    def _on_dot_eaten(self, power_up):
        self.idle_frames = 0
        if power_up:
            self._start_fright()
        if self.use_global:
            self.global_counter += 1
        else:
            for idx, kind in enumerate(WAITING_KINDS):
                if self.by_kind[kind].waiting:
                    self.dot_counters[idx] += 1
                    break

    def _release_waiting_ghosts(self):
        self.idle_frames += 1
        for idx, kind in enumerate(WAITING_KINDS):
            ghost = self.by_kind[kind]
            if not ghost.waiting:
                continue
            if self.use_global:
                ready = self.global_counter >= GLOBAL_LIMITS[kind]
            else:
                ready = self.dot_counters[idx] >= DOT_LIMITS[kind].get(self.game_level, 0)
            if ready:
                ghost.release()
        if self.idle_frames >= HOUSE_IDLE_FRAMES:
            for kind in WAITING_KINDS:
                if self.by_kind[kind].waiting:
                    self.by_kind[kind].release()
                    self.idle_frames = 0
                    break
        if self.use_global and self.global_counter >= GLOBAL_LIMITS['clyde']:
            self.use_global = False

    def _ghost_target(self, ghost, pac):
        if pac.immune_time > 0:
            return None
        elroy_chase = ghost.kind == 'blinky' and ghost.elroy > 0
        if self.mode == 'scatter' and not elroy_chase:
            return ghost.scatter_target
        col, row = tile_of(pac.rect)
        if ghost.kind == 'clyde':
            gcol, grow = tile_of(ghost.rect)
            if (gcol - col) ** 2 + (grow - row) ** 2 >= CLYDE_FEAR_DISTANCE ** 2:
                return (col, row)
            return ghost.scatter_target
        if ghost.kind == 'inky':
            fx, fy = pac.facing
            px, py = col + INKY_LOOKAHEAD * fx, row + INKY_LOOKAHEAD * fy
            if ARCADE_UP_BUG and fy == -1:
                px -= INKY_LOOKAHEAD
            bx, by = tile_of(self.by_kind['blinky'].rect)
            return (2 * px - bx, 2 * py - by)
        if ghost.kind == 'pinky':
            fx, fy = pac.facing
            tx, ty = col + PINKY_LOOKAHEAD * fx, row + PINKY_LOOKAHEAD * fy
            if ARCADE_UP_BUG and fy == -1:
                tx -= PINKY_LOOKAHEAD
            return (tx, ty)
        return (col, row)

    def update(self):
        pac = self.player.sprite

        if self.pause > 0:
            self.pause -= 1
            if self.pause == 0 and self.reset_pos and not self.game_over:
                for ghost in self.ghosts.sprites():
                    ghost.move_to_start_pos()
                pac.move_to_start_pos()
                self._reset_round(new_level=False)
                self.reset_pos = False
            active = False
        else:
            active = not self.game_over

        if active:
            pac.animate(self.pac_collide_list)

            for berry in self.berries.sprites():
                if pac.rect.colliderect(berry.rect):
                    pac.pac_score += 50 if berry.power_up else 10
                    berry.kill()
                    self._on_dot_eaten(berry.power_up)

            for ghost in self.ghosts.sprites():
                if ghost.eaten or ghost.waiting:
                    continue
                if pac.rect.colliderect(ghost.rect):
                    if pac.immune_time <= 0:
                        pac.life -= 1
                        self.reset_pos = True
                        self.pause = PAUSE_FRAMES
                        break
                    ghost.eat()
                    pac.pac_score += GHOST_POINTS[min(self.kill_combo, 3)]
                    self.kill_combo += 1

            self._check_game_state()
            self._update_elroy()
            self._release_waiting_ghosts()
            self._update_mode()
            for ghost in self.ghosts.sprites():
                ghost.frightened = pac.immune_time > 0 and not ghost.eaten
                ghost.update(self.walls_collide_list, self._ghost_target(ghost, pac))
            pac.update()

        self.field.blit(self.maze_surface, (0, 0))
        for sprite in self.berries.sprites():
            sprite.update(self.field)
        for door in self.door_rects:
            pygame.draw.rect(self.field, pygame.Color("pink"),
                             (door.x, door.y + CHAR_SIZE // 2 - 2, door.w, 4))
        for ghost in self.ghosts.sprites():
            draw_centered(self.field, ghost)
        draw_centered(self.field, pac)

        if self.game_over:
            self.display.game_over()
        self._dashboard()


class Main:
    KEYS = {
        pygame.K_LEFT: 'left', pygame.K_a: 'left',
        pygame.K_RIGHT: 'right', pygame.K_d: 'right',
        pygame.K_UP: 'up', pygame.K_w: 'up',
        pygame.K_DOWN: 'down', pygame.K_s: 'down',
    }

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.touch_start = None

    def main(self):
        world = World(self.screen)
        while True:
            self.screen.fill("black")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    if event.key in self.KEYS:
                        world.player.sprite.queue_direction(self.KEYS[event.key])

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.touch_start = event.pos
                    if world.game_over:
                        world.game_over = False
                        world.restart_level()

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.touch_start:
                        world.handle_swipe(self.touch_start, event.pos)
                        self.touch_start = None

            world.update()
            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                         pygame.SCALED | pygame.RESIZABLE)
    except (pygame.error, AttributeError):
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man")
    Main(screen).main()
