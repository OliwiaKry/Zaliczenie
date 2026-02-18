import pygame
import math
import random
import sys
import os
import array 
import json 

# --- INICJALIZACJA ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512) 
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Strzelanka 2D - Bez Muzyki w Tle")
clock = pygame.time.Clock()

# --- KOLORY ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)       
PINK = (255, 105, 180)     
RED = (255, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)   
YELLOW = (255, 255, 0)     
ORANGE = (255, 140, 0)
CYAN = (0, 255, 255)
PURPLE = (150, 0, 255)     
LIGHT_BLUE = (100, 200, 255)

# --- USTAWIENIA GLOBALNE ---
DIFFICULTY_SETTINGS = {
    "easy": {"speed": 0.7, "damage": 0.5, "spawn_rate": 1.5, "name": "Łatwy"},
    "normal": {"speed": 1.0, "damage": 1.0, "spawn_rate": 1.0, "name": "Normalny"},
    "hard": {"speed": 1.4, "damage": 1.5, "spawn_rate": 0.6, "name": "Trudny"}
}

sound_enabled = True
is_fullscreen = False

# --- FUNKCJE POMOCNICZE (Zapis, Odczyt) ---
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file: return json.load(file)
        except: return default
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file: json.dump(data, file)
    except: pass

def load_leaderboard():
    return load_json("leaderboard.json", [])

def save_score(name, score):
    leaderboard = load_leaderboard()
    leaderboard.append({"name": name, "score": score})
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    leaderboard = leaderboard[:10]
    save_json("leaderboard.json", leaderboard)

def check_collision(x1, y1, r1, x2, y2, r2):
    return math.hypot(x1 - x2, y1 - y2) < (r1 + r2)

def draw_button(surface, text, font, text_color, x, y):
    text_surf = font.render(text, True, text_color)
    rect = text_surf.get_rect(center=(x, y))
    rect.inflate_ip(40, 20) 
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    bg_color = (80, 80, 80) if is_hovered else (30, 30, 30)
    pygame.draw.rect(surface, bg_color, rect, border_radius=10)
    pygame.draw.rect(surface, text_color, rect, 2, border_radius=10)
    surface.blit(text_surf, text_surf.get_rect(center=(x, y)))
    return rect

# --- SYNTEZATOR DŹWIĘKÓW ---
def create_melody(notes_with_durations, volume=0.1, wave_type='sine'):
    sample_rate = 44100
    total_samples = sum(int(dur * sample_rate) for freq, dur in notes_with_durations)
    if total_samples == 0: return pygame.mixer.Sound(buffer=array.array('h', []))
    buf = array.array('h', [0] * total_samples)
    current_sample = 0
    for freq, dur in notes_with_durations:
        n_samples = int(dur * sample_rate)
        max_amp = int(32767 * volume)
        for i in range(n_samples):
            if freq > 0:
                time = i / sample_rate
                if wave_type == 'sine':
                    val = int(max_amp * math.sin(2.0 * math.pi * freq * time))
                else: 
                    val = max_amp if math.sin(2.0 * math.pi * freq * time) > 0 else -max_amp
                buf[current_sample] = val
            else:
                buf[current_sample] = 0
            current_sample += 1
    return pygame.mixer.Sound(buffer=buf)

# Usunięto bg_music
boss_death_sound = create_melody([(300, 0.1), (200, 0.1), (100, 0.15), (50, 0.3)], volume=0.3)
victory_sound = create_melody([(523.25, 0.15), (659.25, 0.15), (783.99, 0.15), (1046.50, 0.8)], volume=0.3)
hit_sound = create_melody([(150, 0.05), (100, 0.1)], volume=0.2)
powerup_sound = create_melody([(600, 0.05), (800, 0.1)], volume=0.1)
error_sound = create_melody([(100, 0.15)], volume=0.2) 

def play_sound(sound_obj):
    if sound_enabled: sound_obj.play()

# --- EFEKT 3D TŁA (PARALLAX) ---
class ParallaxBackground:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
        for i in range(3):
            layer = []
            num_stars = int((width * height) / 3000)
            for _ in range(num_stars):
                layer.append([random.randint(0, width), random.randint(0, height), random.randint(1, 3), (i+1)*0.5])
            self.layers.append(layer)

    def resize(self, width, height):
        self.width = width
        self.height = height

    def update_and_draw(self, surface):
        surface.fill(BLACK)
        for i, layer in enumerate(self.layers):
            color = (100 + i*50, 100 + i*50, 100 + i*50)
            for star in layer:
                star[1] += star[3] 
                if star[1] > self.height:
                    star[1] = 0
                    star[0] = random.randint(0, self.width)
                pygame.draw.circle(surface, color, (int(star[0]), int(star[1])), star[2])

# --- KLASY GRY ---
class Player:
    def __init__(self, p_id, x, y, ship_type, save_data):
        self.p_id = p_id 
        self.x = x
        self.y = y
        self.radius = 20
        self.angle = 0
        self.barrel_length = 35
        self.shoot_timer = 0
        
        self.ship_type = ship_type
        self.color = BLUE if p_id == 1 else PINK
        
        bonus_hp = save_data["upgrades"]["hp_bonus"] * 25
        self.level = save_data["upgrades"]["start_lvl"]
        
        if ship_type == "light":
            self.speed = 7
            self.max_health = 60 + bonus_hp
            self.dash_cd_max = 40
        elif ship_type == "heavy":
            self.speed = 3.5
            self.max_health = 180 + bonus_hp
            self.dash_cd_max = 100
        else: 
            self.speed = 5
            self.max_health = 100 + bonus_hp
            self.dash_cd_max = 60
            
        self.health = self.max_health
        
        self.invincible_timer = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        
        self.weapon_type = "normal" 
        self.weapon_timer = 0
        self.rapid_fire_timer = 0
        self.has_shield = False
        self.ghosts = [] 

    def draw(self, surface):
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            pass 
        else:
            num_barrels = min(self.level, 8)
            if self.weapon_type == "shotgun": num_barrels = 3
            
            angle_step = (2 * math.pi) / num_barrels if self.weapon_type != "shotgun" else 0.2
            start_angle = self.angle if self.weapon_type != "shotgun" else self.angle - (0.2 * (num_barrels//2))
            
            for i in range(num_barrels):
                current_angle = start_angle + (i * angle_step)
                end_x = self.x + math.cos(current_angle) * self.barrel_length
                end_y = self.y + math.sin(current_angle) * self.barrel_length
                c = WHITE
                if self.weapon_type == "shotgun": c = ORANGE
                elif self.weapon_type == "pierce": c = CYAN
                pygame.draw.line(surface, c, (self.x, self.y), (end_x, end_y), 4)
                
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            if self.has_shield: pygame.draw.circle(surface, LIGHT_BLUE, (int(self.x), int(self.y)), self.radius + 8, 3)

        for gx, gy, life in self.ghosts:
            ghost_color = (self.color[0], self.color[1], self.color[2])
            pygame.draw.circle(surface, ghost_color, (int(gx), int(gy)), self.radius, 1)

    def update(self, enemies, bosses):
        keys = pygame.key.get_pressed()
        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.rapid_fire_timer > 0: self.rapid_fire_timer -= 1
        if self.weapon_timer > 0:
            self.weapon_timer -= 1
            if self.weapon_timer <= 0: self.weapon_type = "normal"
        
        self.shoot_delay = 5 if self.rapid_fire_timer > 0 else 15
        if self.weapon_type == "shotgun": self.shoot_delay += 10 
        
        current_speed = self.speed
        if self.dash_timer > 0:
            current_speed = self.speed * 3
            self.dash_timer -= 1
            self.invincible_timer = 2 
            if self.dash_timer % 2 == 0: self.ghosts.append([self.x, self.y, 10]) 
        for ghost in self.ghosts[:]:
            ghost[2] -= 1
            if ghost[2] <= 0: self.ghosts.remove(ghost)

        if self.p_id == 1:
            if keys[pygame.K_SPACE] and self.dash_cooldown <= 0:
                self.dash_timer = 12
                self.dash_cooldown = self.dash_cd_max
            if keys[pygame.K_w] and self.y - self.radius > 0: self.y -= current_speed
            if keys[pygame.K_s] and self.y + self.radius < HEIGHT: self.y += current_speed
            if keys[pygame.K_a] and self.x - self.radius > 0: self.x -= current_speed
            if keys[pygame.K_d] and self.x + self.radius < WIDTH: self.x += current_speed
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.angle = math.atan2(mouse_y - self.y, mouse_x - self.x)
            
        elif self.p_id == 2:
            if keys[pygame.K_RCTRL] and self.dash_cooldown <= 0:
                self.dash_timer = 12
                self.dash_cooldown = self.dash_cd_max
            if keys[pygame.K_UP] and self.y - self.radius > 0: self.y -= current_speed
            if keys[pygame.K_DOWN] and self.y + self.radius < HEIGHT: self.y += current_speed
            if keys[pygame.K_LEFT] and self.x - self.radius > 0: self.x -= current_speed
            if keys[pygame.K_RIGHT] and self.x + self.radius < WIDTH: self.x += current_speed
            
            closest_target = None
            min_dist = float('inf')
            for target in enemies + bosses:
                dist = math.hypot(target.x - self.x, target.y - self.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_target = target
            if closest_target:
                self.angle = math.atan2(closest_target.y - self.y, closest_target.x - self.x)

        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

    def take_damage(self, amount):
        if self.invincible_timer > 0: return False 
        if self.has_shield:
            self.has_shield = False
            self.invincible_timer = 30 
            play_sound(hit_sound)
            return True 
        else:
            if self.ship_type == "heavy": amount = int(amount * 0.7)
            self.health -= amount
            self.invincible_timer = 60 
            play_sound(hit_sound)
            return True

class Bullet:
    def __init__(self, x, y, angle, owner="player", b_type="normal"):
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.b_type = b_type
        self.history = [] 
        self.enemies_hit = [] 
        
        if owner == "player":
            if b_type == "pierce":
                self.speed = 15; self.radius = 6; self.color = CYAN
            elif b_type == "shotgun":
                self.speed = 12; self.radius = 4; self.color = ORANGE
            else:
                self.speed = 10; self.radius = 5; self.color = YELLOW
        else:
            self.speed = 4; self.radius = 8; self.color = RED

    def update(self):
        self.history.append((self.x, self.y))
        if len(self.history) > 6: self.history.pop(0)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, surface):
        for i, (hx, hy) in enumerate(self.history):
            size = int(self.radius * (i / len(self.history)))
            if size > 0: pygame.draw.circle(surface, self.color, (int(hx), int(hy)), size)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def is_off_screen(self):
        return self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50

class PowerUp:
    def __init__(self):
        while True:
            self.x = random.randint(50, WIDTH - 50)
            self.y = random.randint(50, HEIGHT - 50)
            if self.x < 320 and self.y < 220: continue
            if self.x > WIDTH - 220 and self.y < 220: continue
            break 
        self.radius = 15
        self.type = random.choice(["shield", "rapid_fire", "shotgun", "pierce"])
        
    def draw(self, surface):
        if self.type == "shield":
            pygame.draw.circle(surface, LIGHT_BLUE, (self.x, self.y), self.radius)
            pygame.draw.circle(surface, WHITE, (self.x, self.y), self.radius, 2)
        elif self.type == "rapid_fire": 
            pygame.draw.circle(surface, YELLOW, (self.x, self.y), self.radius)
            pygame.draw.circle(surface, ORANGE, (self.x, self.y), self.radius, 2)
        elif self.type == "shotgun":
            pygame.draw.circle(surface, RED, (self.x, self.y), self.radius)
            pygame.draw.circle(surface, ORANGE, (self.x, self.y), self.radius, 2)
        elif self.type == "pierce":
            pygame.draw.circle(surface, CYAN, (self.x, self.y), self.radius)
            pygame.draw.circle(surface, WHITE, (self.x, self.y), self.radius, 2)

class Enemy:
    def __init__(self, enemy_type, diff_multiplier, diff_settings):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top': self.x, self.y = random.randint(0, WIDTH), -50
        elif side == 'bottom': self.x, self.y = random.randint(0, WIDTH), HEIGHT + 50
        elif side == 'left': self.x, self.y = -50, random.randint(0, HEIGHT)
        else: self.x, self.y = WIDTH + 50, random.randint(0, HEIGHT)
            
        self.type = enemy_type
        self.shoot_timer = 60 
        
        if self.type == "normal":
            self.radius, base_speed, self.color, self.hp, base_damage = 15, random.uniform(1.5, 3.0), RED, 1, 25
        elif self.type == "tank":
            self.radius, base_speed, self.color, self.hp, base_damage = 30, random.uniform(0.5, 1.0), ORANGE, 5, 50
        elif self.type == "fast":
            self.radius, base_speed, self.color, self.hp, base_damage = 10, random.uniform(3.5, 5.0), CYAN, 1, 15
        elif self.type == "shooter": 
            self.radius, base_speed, self.color, self.hp, base_damage = 15, random.uniform(1.0, 2.0), GREEN, 2, 20
        elif self.type == "kamikaze": 
            self.radius, base_speed, self.color, self.hp, base_damage = 12, random.uniform(4.0, 6.0), PURPLE, 1, 40
            
        self.speed = base_speed * diff_multiplier * diff_settings["speed"]
        self.damage = int(base_damage * diff_settings["damage"])

    def update(self, players, enemy_bullets):
        closest_player = None
        min_dist = float('inf')
        for p in players:
            d = math.hypot(p.x - self.x, p.y - self.y)
            if d < min_dist:
                min_dist = d
                closest_player = p
                
        if closest_player:
            angle = math.atan2(closest_player.y - self.y, closest_player.x - self.x)
            if self.type == "shooter" and min_dist < 200:
                self.shoot_timer -= 1
                if self.shoot_timer <= 0:
                    enemy_bullets.append(Bullet(self.x, self.y, angle, owner="enemy"))
                    self.shoot_timer = 80
            else:
                self.x += math.cos(angle) * self.speed
                self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        if self.type == "kamikaze":
            pygame.draw.polygon(surface, self.color, [(self.x, self.y - self.radius), (self.x - self.radius, self.y + self.radius), (self.x + self.radius, self.y + self.radius)])
        elif self.type == "shooter":
            pygame.draw.rect(surface, self.color, (self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2))
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            
        if self.type == "tank" and self.hp < 5:
            pygame.draw.rect(surface, RED, (self.x - 20, self.y - 40, 40, 5))
            pygame.draw.rect(surface, GREEN, (self.x - 20, self.y - 40, 40 * (self.hp/5), 5))

class Boss:
    def __init__(self, diff_multiplier, diff_settings, shared_level, is_multiplayer):
        self.x, self.y = WIDTH // 2, -100
        self.radius = 60
        self.attack_type = random.choice(["shoot", "dash", "spawn"])
        
        if self.attack_type == "shoot": self.color = PURPLE
        elif self.attack_type == "dash": self.color = YELLOW
        elif self.attack_type == "spawn": self.color = DARK_GREEN
        
        base_hp = 50 + (shared_level * 10)
        if is_multiplayer: base_hp *= 1.5 
        
        self.max_hp = int(base_hp * diff_multiplier * diff_settings["damage"])
        self.hp = self.max_hp
        self.base_speed = 0.8 * diff_multiplier * diff_settings["speed"]
        self.speed = self.base_speed
        self.damage = int(60 * diff_settings["damage"])
        
        self.state = "moving"
        self.attack_timer = 120 
        self.dash_timer = 0

    def update(self, players, enemy_bullets, enemies, diff_multiplier, diff_settings):
        if self.state == "dashing":
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.state = "moving"
                self.speed = self.base_speed 
        else:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.perform_attack(enemy_bullets, enemies, diff_multiplier, diff_settings)

        closest_player = None
        min_dist = float('inf')
        for p in players:
            d = math.hypot(p.x - self.x, p.y - self.y)
            if d < min_dist:
                min_dist = d
                closest_player = p
                
        if closest_player:
            angle = math.atan2(closest_player.y - self.y, closest_player.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def perform_attack(self, enemy_bullets, enemies, diff_multiplier, diff_settings):
        if self.attack_type == "shoot":
            for i in range(12):
                angle = (2 * math.pi / 12) * i
                enemy_bullets.append(Bullet(self.x, self.y, angle, owner="enemy"))
            self.attack_timer = 150 
        elif self.attack_type == "dash":
            self.state = "dashing"
            self.speed = self.base_speed * 4 
            self.dash_timer = 40 
            self.attack_timer = 120
        elif self.attack_type == "spawn":
            for _ in range(2):
                minion = Enemy("fast", diff_multiplier, diff_settings)
                minion.x = self.x + random.randint(-40, 40)
                minion.y = self.y + random.randint(-40, 40)
                enemies.append(minion)
            self.attack_timer = 180

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        if self.state == "dashing":
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 4)
            
        bar_w = 120
        health_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, RED, (self.x - bar_w/2, self.y - self.radius - 20, bar_w, 10))
        pygame.draw.rect(surface, GREEN, (self.x - bar_w/2, self.y - self.radius - 20, bar_w * health_ratio, 10))
        pygame.draw.rect(surface, WHITE, (self.x - bar_w/2, self.y - self.radius - 20, bar_w, 10), 2)

class HealthPack:
    def __init__(self):
        while True:
            self.x = random.randint(50, WIDTH - 50)
            self.y = random.randint(50, HEIGHT - 50)
            if self.x < 320 and self.y < 220: continue
            if self.x > WIDTH - 220 and self.y < 220: continue
            break
        self.radius = 15 
        self.heal_amount = 25
    def draw(self, surface):
        rect = pygame.Rect(self.x - 12, self.y - 12, 24, 24)
        pygame.draw.rect(surface, WHITE, rect)
        pygame.draw.line(surface, RED, (self.x, self.y - 8), (self.x, self.y + 8), 4)
        pygame.draw.line(surface, RED, (self.x - 8, self.y), (self.x + 8, self.y), 4)

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.vx, self.vy = random.uniform(-3, 3), random.uniform(-3, 3)
        self.radius = random.randint(3, 6)
        self.life = random.randint(20, 40)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.life -= 1
        if self.life % 5 == 0 and self.radius > 0: self.radius -= 1
    def draw(self, surface):
        if self.radius > 0: pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

# --- GŁÓWNA PĘTLA ---
def main():
    global WIDTH, HEIGHT, screen, sound_enabled, is_fullscreen
    
    parallax_bg = ParallaxBackground(WIDTH, HEIGHT)
    game_surface = pygame.Surface((WIDTH, HEIGHT)) 
    
    save_data = load_json("save_data.json", {"coins": 0, "upgrades": {"hp_bonus": 0, "start_lvl": 1}})
    
    game_state = "MENU"
    current_difficulty = "normal" 
    is_multiplayer = False
    
    players = []
    bullets = []
    enemy_bullets = [] 
    enemies = []
    bosses = [] 
    health_packs = []
    power_ups = []
    particles = []
    
    shared_score = 0 
    shared_exp = 0    
    shared_level = 1
    combo_multiplier = 1.0
    combo_timer = 0
    endless_mode = False 
    
    p1_ship = "balanced"
    p2_ship = "balanced"
    
    enemy_spawn_timer = 0
    health_spawn_timer = 0
    powerup_spawn_timer = 0
    next_health_spawn = random.randint(300, 900)
    next_powerup_spawn = random.randint(600, 1200)
    next_boss_score = 50 
    
    screen_shake_frames = 0
    player_name = ""
    
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    menu_font_large = pygame.font.SysFont(None, 72)
    menu_font_small = pygame.font.SysFont(None, 36)
    
    menu_btns, shop_btns, lb_btns, end_btns, pause_btns, ship_btns = {}, {}, {}, {}, {}, {}
    
    leaderboard = load_leaderboard()
    high_score = leaderboard[0]["score"] if len(leaderboard) > 0 else 0
    
    def start_game():
        nonlocal game_state, endless_mode
        nonlocal shared_score, shared_exp, shared_level, points_to_next_level, next_level_score
        nonlocal enemy_spawn_timer, health_spawn_timer, next_boss_score, powerup_spawn_timer, screen_shake_frames
        nonlocal combo_multiplier, combo_timer
        
        game_state = "PLAYING"
        endless_mode = False
        
        players.clear()
        if is_multiplayer:
            players.append(Player(1, WIDTH // 2 - 50, HEIGHT // 2, p1_ship, save_data))
            players.append(Player(2, WIDTH // 2 + 50, HEIGHT // 2, p2_ship, save_data))
        else:
            players.append(Player(1, WIDTH // 2, HEIGHT // 2, p1_ship, save_data))
            
        bullets.clear(); enemy_bullets.clear(); enemies.clear(); bosses.clear()
        health_packs.clear(); particles.clear(); power_ups.clear()
        
        shared_score = 0
        shared_exp = 0 
        shared_level = save_data["upgrades"]["start_lvl"] 
        points_to_next_level = 10 * shared_level
        next_level_score = 10 * shared_level 
        combo_multiplier = 1.0
        combo_timer = 0
        
        enemy_spawn_timer = 0; health_spawn_timer = 0; powerup_spawn_timer = 0; next_boss_score = 50 * shared_level 
        screen_shake_frames = 0

    def toggle_fs():
        global is_fullscreen, WIDTH, HEIGHT, screen
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            display_info = pygame.display.Info()
            WIDTH, HEIGHT = display_info.current_w, display_info.current_h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            WIDTH, HEIGHT = 800, 600
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        parallax_bg.resize(WIDTH, HEIGHT)
        return pygame.Surface((WIDTH, HEIGHT))

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                game_surface = pygame.Surface((WIDTH, HEIGHT))
                parallax_bg.resize(WIDTH, HEIGHT)
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                if game_state == "MENU":
                    for action, rect in menu_btns.items():
                        if rect.collidepoint(mouse_pos):
                            if action == "s_easy": current_difficulty, is_multiplayer, game_state = "easy", False, "SHIP_SELECT"
                            elif action == "s_norm": current_difficulty, is_multiplayer, game_state = "normal", False, "SHIP_SELECT"
                            elif action == "s_hard": current_difficulty, is_multiplayer, game_state = "hard", False, "SHIP_SELECT"
                            elif action == "m_easy": current_difficulty, is_multiplayer, game_state = "easy", True, "SHIP_SELECT"
                            elif action == "m_norm": current_difficulty, is_multiplayer, game_state = "normal", True, "SHIP_SELECT"
                            elif action == "m_hard": current_difficulty, is_multiplayer, game_state = "hard", True, "SHIP_SELECT"
                            elif action == "leaderboard":
                                leaderboard = load_leaderboard()
                                game_state = "LEADERBOARD"
                            elif action == "shop": game_state = "SHOP"
                            elif action == "toggle_sound":
                                sound_enabled = not sound_enabled
                                if not sound_enabled: pygame.mixer.stop()
                            elif action == "toggle_fs": game_surface = toggle_fs()
                            
                elif game_state == "SHIP_SELECT":
                    for action, rect in ship_btns.items():
                        if rect.collidepoint(mouse_pos):
                            if action == "p1_light": p1_ship = "light"
                            elif action == "p1_bal": p1_ship = "balanced"
                            elif action == "p1_heavy": p1_ship = "heavy"
                            elif action == "p2_light": p2_ship = "light"
                            elif action == "p2_bal": p2_ship = "balanced"
                            elif action == "p2_heavy": p2_ship = "heavy"
                            elif action == "start": start_game()
                            elif action == "back": game_state = "MENU"
                            
                elif game_state == "SHOP":
                    for action, rect in shop_btns.items():
                        if rect.collidepoint(mouse_pos):
                            if action == "back": game_state = "MENU"
                            elif action == "buy_hp" and save_data["coins"] >= 50:
                                save_data["coins"] -= 50
                                save_data["upgrades"]["hp_bonus"] += 1
                                save_json("save_data.json", save_data)
                            elif action == "buy_lvl" and save_data["coins"] >= 100:
                                save_data["coins"] -= 100
                                save_data["upgrades"]["start_lvl"] += 1
                                save_json("save_data.json", save_data)

                elif game_state == "LEADERBOARD":
                    if "back" in lb_btns and lb_btns["back"].collidepoint(mouse_pos): game_state = "MENU"
                        
                elif game_state in ["GAME_OVER", "VICTORY"]:
                    if "save" in end_btns and end_btns["save"].collidepoint(mouse_pos):
                        name_to_save = player_name.strip()
                        if not name_to_save: name_to_save = "Anonim"
                        save_score(name_to_save, shared_score)
                        leaderboard = load_leaderboard()
                        high_score = leaderboard[0]["score"] if len(leaderboard) > 0 else 0
                        save_data["coins"] += shared_score
                        save_json("save_data.json", save_data)
                        game_state = "MENU"
                    elif "skip" in end_btns and end_btns["skip"].collidepoint(mouse_pos):
                        save_data["coins"] += shared_score
                        save_json("save_data.json", save_data)
                        game_state = "MENU"
                    elif game_state == "VICTORY" and "continue" in end_btns and end_btns["continue"].collidepoint(mouse_pos):
                        endless_mode = True
                        game_state = "PLAYING"
                        
                elif game_state == "PAUSED":
                    for action, rect in pause_btns.items():
                        if rect.collidepoint(mouse_pos):
                            if action == "resume": game_state = "PLAYING"
                            elif action == "save_quit":
                                player_name = ""
                                game_state = "GAME_OVER"
                            elif action == "menu":
                                game_state = "MENU"
                            elif action == "toggle_sound": 
                                sound_enabled = not sound_enabled
                                if not sound_enabled: pygame.mixer.stop()
                            elif action == "toggle_fs": game_surface = toggle_fs()

            if game_state in ["GAME_OVER", "VICTORY"] and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    name_to_save = player_name.strip()
                    if not name_to_save: name_to_save = "Anonim"
                    save_score(name_to_save, shared_score)
                    leaderboard = load_leaderboard()
                    high_score = leaderboard[0]["score"] if len(leaderboard) > 0 else 0
                    save_data["coins"] += shared_score
                    save_json("save_data.json", save_data)
                    game_state = "MENU"
                elif event.key == pygame.K_ESCAPE:
                    save_data["coins"] += shared_score
                    save_json("save_data.json", save_data)
                    game_state = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if len(player_name) < 12 and event.unicode.isprintable():
                        player_name += event.unicode

            elif game_state == "PLAYING" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = "PAUSED"
            elif game_state == "PAUSED" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "PLAYING" 
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    player_name = ""
                    game_state = "GAME_OVER"

        # 2. LOGIKA I RYSOWANIE
        parallax_bg.update_and_draw(game_surface)

        if game_state == "MENU":
            menu_btns.clear()
            title = menu_font_large.render("KOSMICZNA STRZELANKA", True, BLUE)
            game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 220))
            
            left_center, right_center = WIDTH // 4, 3 * WIDTH // 4
            
            single = menu_font_small.render("JEDEN GRACZ (WSAD+Mysz)", True, WHITE)
            game_surface.blit(single, (left_center - single.get_width() // 2, HEIGHT // 2 - 120))
            menu_btns["s_easy"] = draw_button(game_surface, "Łatwy", menu_font_small, GREEN, left_center, HEIGHT // 2 - 50)
            menu_btns["s_norm"] = draw_button(game_surface, "Normalny", menu_font_small, YELLOW, left_center, HEIGHT // 2 + 20)
            menu_btns["s_hard"] = draw_button(game_surface, "Trudny", menu_font_small, RED, left_center, HEIGHT // 2 + 90)
            
            multi = menu_font_small.render("DWÓCH GRACZY (Co-op)", True, PINK)
            game_surface.blit(multi, (right_center - multi.get_width() // 2, HEIGHT // 2 - 120))
            menu_btns["m_easy"] = draw_button(game_surface, "Łatwy", menu_font_small, GREEN, right_center, HEIGHT // 2 - 50)
            menu_btns["m_norm"] = draw_button(game_surface, "Normalny", menu_font_small, YELLOW, right_center, HEIGHT // 2 + 20)
            menu_btns["m_hard"] = draw_button(game_surface, "Trudny", menu_font_small, RED, right_center, HEIGHT // 2 + 90)
            
            menu_btns["shop"] = draw_button(game_surface, f"SKLEP ({save_data['coins']} MONET)", menu_font_small, ORANGE, WIDTH // 2 - 150, HEIGHT - 100)
            menu_btns["leaderboard"] = draw_button(game_surface, "TOP 10 RANKING", menu_font_small, CYAN, WIDTH // 2 + 150, HEIGHT - 100)
            
            snd_text = "DŹWIĘK: ON" if sound_enabled else "DŹWIĘK: OFF"
            snd_col = GREEN if sound_enabled else RED
            fs_text = "OKNO" if not is_fullscreen else "PEŁNY EKRAN"
            
            menu_btns["toggle_sound"] = draw_button(game_surface, snd_text, small_font, snd_col, 100, HEIGHT - 40)
            menu_btns["toggle_fs"] = draw_button(game_surface, fs_text, small_font, WHITE, 250, HEIGHT - 40)

        elif game_state == "SHOP":
            shop_btns.clear()
            title = menu_font_large.render("SKLEP (META-PROGRESJA)", True, ORANGE)
            game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
            
            coins_txt = font.render(f"Posiadasz: {save_data['coins']} monet", True, YELLOW)
            game_surface.blit(coins_txt, (WIDTH // 2 - coins_txt.get_width() // 2, 120))
            
            hp_lvl = save_data["upgrades"]["hp_bonus"]
            hp_txt = font.render(f"Więcej HP (Obecnie: +{hp_lvl*25} MAX HP)", True, WHITE)
            game_surface.blit(hp_txt, (WIDTH // 2 - hp_txt.get_width() // 2, 200))
            col = GREEN if save_data["coins"] >= 50 else RED
            shop_btns["buy_hp"] = draw_button(game_surface, "KUP ZA 50 MONET", small_font, col, WIDTH // 2, 250)
            
            lvl = save_data["upgrades"]["start_lvl"]
            lvl_txt = font.render(f"Startowy Poziom (Obecnie: Level {lvl})", True, WHITE)
            game_surface.blit(lvl_txt, (WIDTH // 2 - lvl_txt.get_width() // 2, 330))
            col = GREEN if save_data["coins"] >= 100 else RED
            shop_btns["buy_lvl"] = draw_button(game_surface, "KUP ZA 100 MONET", small_font, col, WIDTH // 2, 380)
            
            shop_btns["back"] = draw_button(game_surface, "WRÓĆ DO MENU", menu_font_small, WHITE, WIDTH // 2, HEIGHT - 80)

        elif game_state == "SHIP_SELECT":
            ship_btns.clear()
            title = menu_font_large.render("WYBÓR STATKÓW", True, WHITE)
            game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
            
            p1_t = font.render(f"Gracz 1 (Obecnie: {p1_ship.upper()})", True, BLUE)
            game_surface.blit(p1_t, (WIDTH // 4 - p1_t.get_width() // 2, 150))
            ship_btns["p1_light"] = draw_button(game_surface, "Lekki (Szybki, 50HP)", small_font, GREEN if p1_ship == "light" else WHITE, WIDTH // 4, 200)
            ship_btns["p1_bal"] = draw_button(game_surface, "Zbalansowany (100HP)", small_font, GREEN if p1_ship == "balanced" else WHITE, WIDTH // 4, 250)
            ship_btns["p1_heavy"] = draw_button(game_surface, "Ciężki (Wolny, 200HP, Armor)", small_font, GREEN if p1_ship == "heavy" else WHITE, WIDTH // 4, 300)
            
            if is_multiplayer:
                p2_t = font.render(f"Gracz 2 (Obecnie: {p2_ship.upper()})", True, PINK)
                game_surface.blit(p2_t, (3 * WIDTH // 4 - p2_t.get_width() // 2, 150))
                ship_btns["p2_light"] = draw_button(game_surface, "Lekki (Szybki, 50HP)", small_font, GREEN if p2_ship == "light" else WHITE, 3 * WIDTH // 4, 200)
                ship_btns["p2_bal"] = draw_button(game_surface, "Zbalansowany (100HP)", small_font, GREEN if p2_ship == "balanced" else WHITE, 3 * WIDTH // 4, 250)
                ship_btns["p2_heavy"] = draw_button(game_surface, "Ciężki (Wolny, 200HP, Armor)", small_font, GREEN if p2_ship == "heavy" else WHITE, 3 * WIDTH // 4, 300)
                
            ship_btns["start"] = draw_button(game_surface, "START GRY!", menu_font_large, ORANGE, WIDTH // 2, 450)
            ship_btns["back"] = draw_button(game_surface, "WRÓĆ", menu_font_small, WHITE, WIDTH // 2, HEIGHT - 50)

        elif game_state == "LEADERBOARD":
            lb_btns.clear()
            title = menu_font_large.render("TOP 10 GRACZY", True, YELLOW)
            game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
            
            if not leaderboard:
                empty_text = font.render("Brak zapisanych wyników.", True, WHITE)
                game_surface.blit(empty_text, (WIDTH // 2 - empty_text.get_width() // 2, 200))
            else:
                for i, entry in enumerate(leaderboard):
                    c = WHITE
                    if i == 0: c = YELLOW     
                    elif i == 1: c = (192, 192, 192) 
                    elif i == 2: c = (205, 127, 50)  
                    text = font.render(f"{i+1}. {entry['name']} - {entry['score']} pkt", True, c)
                    game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 140 + i * 35))
            
            lb_btns["back"] = draw_button(game_surface, "WRÓĆ DO MENU", menu_font_small, GREEN, WIDTH // 2, HEIGHT - 80)

        elif game_state in ["PLAYING", "PAUSED"]:
            if game_state == "PLAYING":
                diff_settings = DIFFICULTY_SETTINGS[current_difficulty]
                diff_multiplier = 1 + (shared_level * 0.1) + (shared_exp / 500)

                if screen_shake_frames > 0: screen_shake_frames -= 1
                
                if combo_timer > 0:
                    combo_timer -= 1
                    if combo_timer <= 0: combo_multiplier = 1.0 

                while shared_exp >= next_level_score:
                    shared_level += 1
                    points_to_next_level += 5 
                    next_level_score += points_to_next_level
                    for p in players: p.level = shared_level

                if shared_level >= 10 and not endless_mode:
                    play_sound(victory_sound)
                    game_state = "VICTORY"
                    player_name = "" 
                    
                for p in players:
                    p.update(enemies, bosses)
                    p.shoot_timer += 1
                    if p.shoot_timer >= p.shoot_delay:
                        p.shoot_timer = 0
                        num_barrels = min(p.level, 8)
                        if p.weapon_type == "shotgun": num_barrels = 3
                        
                        angle_step = (2 * math.pi) / num_barrels if p.weapon_type != "shotgun" else 0.2
                        start_angle = p.angle if p.weapon_type != "shotgun" else p.angle - (0.2 * (num_barrels//2))
                        
                        for i in range(num_barrels):
                            bullet_angle = start_angle + (i * angle_step)
                            spawn_x = p.x + math.cos(bullet_angle) * p.barrel_length
                            spawn_y = p.y + math.sin(bullet_angle) * p.barrel_length
                            bullets.append(Bullet(spawn_x, spawn_y, bullet_angle, owner="player", b_type=p.weapon_type))

                for bullet in bullets[:]:
                    bullet.update()
                    if bullet.is_off_screen(): bullets.remove(bullet)
                    
                for e_bullet in enemy_bullets[:]:
                    e_bullet.update()
                    if e_bullet.is_off_screen(): 
                        enemy_bullets.remove(e_bullet)
                        continue
                        
                    for p in players[:]:
                        if check_collision(e_bullet.x, e_bullet.y, e_bullet.radius, p.x, p.y, p.radius):
                            if e_bullet in enemy_bullets: enemy_bullets.remove(e_bullet)
                            if p.take_damage(15): 
                                screen_shake_frames = 10
                                shared_score = max(0, shared_score - 2) 
                                play_sound(error_sound)
                            if p.health <= 0 and p in players:
                                for _ in range(30): particles.append(Particle(p.x, p.y, p.color))
                                players.remove(p)
                            break

                for particle in particles[:]:
                    particle.update()
                    if particle.life <= 0: particles.remove(particle)

                if shared_exp >= next_boss_score and len(bosses) == 0:
                    bosses.append(Boss(diff_multiplier, diff_settings, shared_level, is_multiplayer))
                    next_boss_score += 50 
                    
                if len(bosses) == 0:
                    enemy_spawn_timer += 1
                    base_spawn_rate = max(10, 60 - (shared_level * 3))
                    spawn_rate = base_spawn_rate * diff_settings["spawn_rate"]
                    if enemy_spawn_timer >= spawn_rate:
                        chosen_type = random.choices(["normal", "tank", "fast", "shooter", "kamikaze"], weights=[50, 15, 15, 10, 10], k=1)[0]
                        enemies.append(Enemy(chosen_type, diff_multiplier, diff_settings))
                        enemy_spawn_timer = 0

                health_spawn_timer += 1
                if health_spawn_timer >= next_health_spawn:
                    if len(health_packs) < 3: health_packs.append(HealthPack())
                    health_spawn_timer = 0
                    next_health_spawn = random.randint(300, 900)
                    
                powerup_spawn_timer += 1
                if powerup_spawn_timer >= next_powerup_spawn:
                    if len(power_ups) < 2: power_ups.append(PowerUp())
                    powerup_spawn_timer = 0
                    next_powerup_spawn = random.randint(600, 1200)

                for pack in health_packs[:]:
                    for p in players:
                        if check_collision(p.x, p.y, p.radius, pack.x, pack.y, pack.radius):
                            if pack in health_packs: health_packs.remove(pack)
                            p.health += pack.heal_amount
                            if p.health > p.max_health: p.health = p.max_health
                            play_sound(powerup_sound)
                            break 
                            
                for pup in power_ups[:]:
                    for p in players:
                        if check_collision(p.x, p.y, p.radius, pup.x, pup.y, pup.radius):
                            if pup in power_ups: power_ups.remove(pup)
                            if pup.type == "shield": p.has_shield = True
                            elif pup.type == "rapid_fire": p.rapid_fire_timer = 300 
                            elif pup.type == "shotgun": p.weapon_type = "shotgun"; p.weapon_timer = 300
                            elif pup.type == "pierce": p.weapon_type = "pierce"; p.weapon_timer = 300
                            play_sound(powerup_sound)
                            break 

                for bullet in bullets[:]:
                    hit_something = False
                    for boss in bosses[:]:
                        if check_collision(bullet.x, bullet.y, bullet.radius, boss.x, boss.y, boss.radius):
                            if bullet.b_type != "pierce": hit_something = True
                            elif boss in bullet.enemies_hit: continue 
                            if bullet.b_type == "pierce": bullet.enemies_hit.append(boss)
                            
                            boss.hp -= 1
                            if boss.hp <= 0:
                                if boss in bosses:
                                    play_sound(boss_death_sound)
                                    screen_shake_frames = 20 
                                    for _ in range(50): particles.append(Particle(boss.x, boss.y, boss.color))
                                    bosses.remove(boss)
                                    shared_score += int(10 * combo_multiplier)
                                    shared_exp += 10
                                    combo_multiplier = min(4.0, combo_multiplier + 1.0)
                                    combo_timer = 180
                            break
                            
                    if hit_something:
                        if bullet in bullets: bullets.remove(bullet)
                        continue 

                    for enemy in enemies[:]:
                        if check_collision(bullet.x, bullet.y, bullet.radius, enemy.x, enemy.y, enemy.radius):
                            if bullet.b_type != "pierce": hit_something = True
                            elif enemy in bullet.enemies_hit: continue
                            if bullet.b_type == "pierce": bullet.enemies_hit.append(enemy)
                            
                            enemy.hp -= 1
                            if enemy.hp <= 0:
                                if enemy in enemies:
                                    if enemy.type == "kamikaze":
                                        for i in range(8):
                                            ang = (2 * math.pi / 8) * i
                                            enemy_bullets.append(Bullet(enemy.x, enemy.y, ang, owner="enemy"))
                                            
                                    for _ in range(15): particles.append(Particle(enemy.x, enemy.y, enemy.color))
                                    enemies.remove(enemy)
                                    shared_score += int(1 * combo_multiplier)
                                    shared_exp += 1
                                    combo_multiplier = min(4.0, combo_multiplier + 0.1)
                                    combo_timer = 180
                            break
                    if hit_something and bullet in bullets: bullets.remove(bullet)

                for p in players[:]:
                    for boss in bosses:
                        if check_collision(p.x, p.y, p.radius, boss.x, boss.y, boss.radius):
                            if p.take_damage(boss.damage):
                                screen_shake_frames = 15
                                shared_score = max(0, shared_score - 5)
                                combo_multiplier = 1.0
                                play_sound(error_sound)
                                angle = math.atan2(p.y - boss.y, p.x - boss.x)
                                p.x += math.cos(angle) * 80 
                                p.y += math.sin(angle) * 80
                    
                    for enemy in enemies[:]:
                        if check_collision(p.x, p.y, p.radius, enemy.x, enemy.y, enemy.radius):
                            if enemy.type == "kamikaze":
                                for i in range(8):
                                    ang = (2 * math.pi / 8) * i
                                    enemy_bullets.append(Bullet(enemy.x, enemy.y, ang, owner="enemy"))
                            if enemy in enemies: enemies.remove(enemy)
                            
                            if p.take_damage(enemy.damage): 
                                screen_shake_frames = 10
                                shared_score = max(0, shared_score - 3)
                                combo_multiplier = 1.0
                                play_sound(error_sound)

                    if p.health <= 0 and p in players:
                        for _ in range(30): particles.append(Particle(p.x, p.y, p.color)) 
                        players.remove(p)

                for boss in bosses: boss.update(players, enemy_bullets, enemies, diff_multiplier, diff_settings)
                for enemy in enemies: enemy.update(players, enemy_bullets)

                if len(players) == 0:
                    game_state = "GAME_OVER"
                    player_name = "" 

            for pup in power_ups: pup.draw(game_surface)
            for pack in health_packs: pack.draw(game_surface)
            for particle in particles: particle.draw(game_surface)
            for boss in bosses: boss.draw(game_surface) 
            for enemy in enemies: enemy.draw(game_surface)
            for bullet in bullets: bullet.draw(game_surface)
            for e_bullet in enemy_bullets: e_bullet.draw(game_surface) 
            for p in players: p.draw(game_surface)

            for boss in bosses:
                if boss.x < 0 or boss.x > WIDTH or boss.y < 0 or boss.y > HEIGHT:
                    rx = max(20, min(WIDTH - 20, boss.x))
                    ry = max(20, min(HEIGHT - 20, boss.y))
                    if pygame.time.get_ticks() % 500 < 250:
                        pygame.draw.polygon(game_surface, RED, [(rx, ry-15), (rx-10, ry+10), (rx+10, ry+10)])
                        excl = small_font.render("!", True, WHITE)
                        game_surface.blit(excl, (rx - excl.get_width()//2, ry - 5))

            current_displayed_high_score = max(high_score, shared_score)
            diff_name = DIFFICULTY_SETTINGS[current_difficulty]["name"]
            mode_name = "CO-OP" if is_multiplayer else "SINGLE"
            
            score_text = font.render(f"Punkty: {shared_score}", True, WHITE)
            high_score_text = font.render(f"TOP 1: {current_displayed_high_score}", True, YELLOW)
            
            if combo_multiplier > 1.0:
                combo_text = menu_font_small.render(f"COMBO x{combo_multiplier:.1f}", True, ORANGE)
                game_surface.blit(combo_text, (WIDTH // 2 - combo_text.get_width() // 2, 60))
                pygame.draw.rect(game_surface, ORANGE, (WIDTH // 2 - 100, 100, 200 * (combo_timer / 180), 5))
            
            lvl_str = f"Poziom: {shared_level}" if endless_mode else f"Poziom: {shared_level}/10"
            level_text = font.render(lvl_str, True, WHITE)
            
            pts_needed = next_level_score - shared_exp
            level_progress_text = small_font.render(f"(Do awansu brakuje {pts_needed} EXP)", True, (200, 200, 200))
            diff_text = font.render(f"Złoto z gry: {shared_score} monet", True, ORANGE)
            
            if len(bosses) > 0:
                warning = font.render("UWAGA: BOSS!", True, RED)
                game_surface.blit(warning, (WIDTH // 2 - warning.get_width() // 2, 20))

            game_surface.blit(score_text, (10, 10))
            game_surface.blit(high_score_text, (10, 40))
            game_surface.blit(level_text, (10, 70))
            game_surface.blit(level_progress_text, (10, 100))
            game_surface.blit(diff_text, (10, 125))

            bar_w, bar_h = 150, 20
            for p in players:
                ratio = p.health / p.max_health
                if p.p_id == 1:
                    x, y = 10, 160
                else:
                    x, y = WIDTH - 160, 160
                    
                pygame.draw.rect(game_surface, RED, (x, y, bar_w, bar_h))
                pygame.draw.rect(game_surface, GREEN, (x, y, bar_w * ratio, bar_h))
                pygame.draw.rect(game_surface, WHITE, (x, y, bar_w, bar_h), 2)
                
            if game_state == "PAUSED":
                pause_btns.clear()
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180)) 
                game_surface.blit(overlay, (0, 0))
                
                pause_title = menu_font_large.render("PAUZA", True, WHITE)
                game_surface.blit(pause_title, (WIDTH // 2 - pause_title.get_width() // 2, HEIGHT // 2 - 160))
                
                pause_btns["resume"] = draw_button(game_surface, "WZNÓW GRĘ", menu_font_small, GREEN, WIDTH // 2, HEIGHT // 2 - 50)
                
                snd_text = "DŹWIĘK: ON" if sound_enabled else "DŹWIĘK: OFF"
                snd_col = GREEN if sound_enabled else RED
                pause_btns["toggle_sound"] = draw_button(game_surface, snd_text, menu_font_small, snd_col, WIDTH // 2, HEIGHT // 2 + 10)
                
                fs_text = "OKNO" if not is_fullscreen else "PEŁNY EKRAN"
                pause_btns["toggle_fs"] = draw_button(game_surface, fs_text, menu_font_small, WHITE, WIDTH // 2, HEIGHT // 2 + 70)
                
                pause_btns["save_quit"] = draw_button(game_surface, "ZAKOŃCZ I ZAPISZ WYNIK", menu_font_small, YELLOW, WIDTH // 2, HEIGHT // 2 + 130)
                pause_btns["menu"] = draw_button(game_surface, "WYJDŹ BEZ ZAPISU", menu_font_small, RED, WIDTH // 2, HEIGHT // 2 + 190)

        elif game_state in ["GAME_OVER", "VICTORY"]:
            end_btns.clear()
            if game_state == "GAME_OVER":
                title_text = menu_font_large.render("KONIEC GRY", True, RED)
            else:
                vic_str = "WYGRALIŚCIE!" if is_multiplayer else "WYGRAŁEŚ!"
                title_text = menu_font_large.render(vic_str, True, GREEN)

            final_score_text = font.render(f"Zdobyliście: {shared_score} pkt na poziomie {shared_level}", True, YELLOW)
            prompt_text = font.render("Wpisz swój Nick (Klawiatura):", True, WHITE)
            cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
            name_box_text = menu_font_small.render(f"{player_name}{cursor}", True, CYAN)
            
            game_surface.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 180))
            game_surface.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 100))
            game_surface.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 20))
            
            box_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 50)
            pygame.draw.rect(game_surface, (50, 50, 50), box_rect)
            pygame.draw.rect(game_surface, WHITE, box_rect, 2)
            game_surface.blit(name_box_text, (WIDTH // 2 - name_box_text.get_width() // 2, HEIGHT // 2 + 35))
            
            end_btns["save"] = draw_button(game_surface, "ZAPISZ (ENTER)", menu_font_small, GREEN, WIDTH // 2 - 130, HEIGHT // 2 + 120)
            end_btns["skip"] = draw_button(game_surface, "POMIŃ (ESC)", menu_font_small, RED, WIDTH // 2 + 130, HEIGHT // 2 + 120)
            
            if game_state == "VICTORY":
                end_btns["continue"] = draw_button(game_surface, "GRAJ DALEJ (ENDLESS)", menu_font_small, YELLOW, WIDTH // 2, HEIGHT // 2 + 190)

        screen.fill(BLACK) 
        shake_x = random.randint(-5, 5) if screen_shake_frames > 0 else 0
        shake_y = random.randint(-5, 5) if screen_shake_frames > 0 else 0
        screen.blit(game_surface, (shake_x, shake_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()