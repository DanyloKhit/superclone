import pygame
import math
import random

pygame.init()

# Константи
WIDTH, HEIGHT = 1920, 1080
FPS = 60

# Кольори
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
DARK_RED = (150, 0, 0)
BLUE = (0, 150, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
PURPLE = (200, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
PINK = (255, 100, 200)

# Налаштування
PLAYER_SIZE = 30
PLAYER_SPEED = 6
BULLET_RADIUS = 5
BULLET_SPEED = 14
TIME_SLOWDOWN = 0.1
MIN_TIME_SCALE = 0.02
DASH_SPEED = 18
DASH_DURATION = 10
DODGE_SPEED = 15
DODGE_DURATION = 8
MAX_AMMO = 12
RELOAD_TIME = 90

class Obstacle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)
        
    def draw(self, screen, camera):
        rect = pygame.Rect(self.x - camera.x, self.y - camera.y, self.w, self.h)
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, WHITE, rect, 2)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def update(self, target_x, target_y):
        self.x += (target_x - WIDTH // 2 - self.x) * 0.1
        self.y += (target_y - HEIGHT // 2 - self.y) * 0.1

class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_life = lifetime
        
    def update(self, ts):
        self.x += self.vx * ts
        self.y += self.vy * ts
        self.lifetime -= ts
        
    def draw(self, screen, camera):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_life))
            s = int(self.size * (self.lifetime / self.max_life))
            if s > 0:
                surf = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*self.color[:3], alpha), (s, s), s)
                screen.blit(surf, (int(self.x - camera.x - s), int(self.y - camera.y - s)))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.size = PLAYER_SIZE
        self.angle = 0
        self.health = 5
        self.max_health = 5
        self.ammo = MAX_AMMO
        self.max_ammo = MAX_AMMO
        self.reloading = False
        self.reload_timer = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.invincible = 0
        self.dash_dir = [0, 0]
        self.dodge_dir = [0, 0]
        
    def update(self, keys, mouse_pos, camera, obstacles, ts):
        # Cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
            
        # Перезарядка
        if self.reloading:
            self.reload_timer -= ts
            if self.reload_timer <= 0:
                self.reloading = False
                self.ammo = self.max_ammo
                
        # Кут до миші
        mx, my = mouse_pos[0] + camera.x, mouse_pos[1] + camera.y
        self.angle = math.atan2(my - self.y, mx - self.x)
        
        # Рух
        if self.dash_timer > 0:
            self.vx = self.dash_dir[0] * DASH_SPEED
            self.vy = self.dash_dir[1] * DASH_SPEED
            self.dash_timer -= 1
        elif self.dodge_timer > 0:
            self.vx = self.dodge_dir[0] * DODGE_SPEED
            self.vy = self.dodge_dir[1] * DODGE_SPEED
            self.dodge_timer -= 1
        else:
            self.vx = 0
            self.vy = 0
            if keys[pygame.K_w]:
                self.vy = -PLAYER_SPEED
            if keys[pygame.K_s]:
                self.vy = PLAYER_SPEED
            if keys[pygame.K_a]:
                self.vx = -PLAYER_SPEED
            if keys[pygame.K_d]:
                self.vx = PLAYER_SPEED
                
        # Нормалізація діагоналі
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.707
            self.vy *= 0.707
            
        # Застосування руху
        new_x = self.x + self.vx * ts
        new_y = self.y + self.vy * ts
        
        # Перевірка колізій з перешкодами
        player_rect = pygame.Rect(new_x - self.size/2, new_y - self.size/2, self.size, self.size)
        collision = False
        for obs in obstacles:
            if player_rect.colliderect(obs.rect):
                collision = True
                break
                
        if not collision:
            self.x = new_x
            self.y = new_y
            
    def dash(self, keys):
        if self.dash_cooldown <= 0 and self.dash_timer <= 0:
            dx, dy = 0, 0
            if keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_s]:
                dy = 1
            if keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_d]:
                dx = 1
            if dx != 0 or dy != 0:
                length = math.sqrt(dx**2 + dy**2)
                self.dash_dir = [dx/length, dy/length]
                self.dash_timer = DASH_DURATION
                self.dash_cooldown = 50
                self.invincible = DASH_DURATION
                return True
        return False
        
    def dodge(self):
        if self.dodge_cooldown <= 0 and self.dodge_timer <= 0:
            dx, dy = math.cos(self.angle), math.sin(self.angle)
            # Додж у сторону від напрямку погляду
            self.dodge_dir = [-dy, dx]
            self.dodge_timer = DODGE_DURATION
            self.dodge_cooldown = 30
            self.invincible = DODGE_DURATION
            return True
        return False
        
    def shoot(self, mouse_pos, camera):
        if self.ammo > 0 and not self.reloading:
            mx, my = mouse_pos[0] + camera.x, mouse_pos[1] + camera.y
            dx = mx - self.x
            dy = my - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                self.ammo -= 1
                return Bullet(self.x, self.y, dx/dist, dy/dist, True)
        return None
        
    def reload(self):
        if not self.reloading and self.ammo < self.max_ammo:
            self.reloading = True
            self.reload_timer = RELOAD_TIME
            
    def take_damage(self, amount=1):
        if self.invincible <= 0:
            self.health -= amount
            self.invincible = 60
            return True
        return False
        
    def get_rect(self):
        return pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
        
    def draw(self, screen, camera):
        x, y = self.x - camera.x, self.y - camera.y
        
        # Мерехтіння при непроніканості
        if self.invincible > 0 and self.invincible % 8 < 4:
            color = CYAN
        else:
            color = BLUE
            
        pygame.draw.rect(screen, color, (x - self.size/2, y - self.size/2, self.size, self.size), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x - self.size/2, y - self.size/2, self.size, self.size), 2, border_radius=3)
        
        # Напрямок
        end_x = x + math.cos(self.angle) * self.size
        end_y = y + math.sin(self.angle) * self.size
        pygame.draw.line(screen, WHITE, (x, y), (end_x, end_y), 2)

class Enemy:
    def __init__(self, x, y, etype="normal"):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.size = 25
        self.type = etype
        self.health = 1
        self.shoot_timer = random.randint(60, 120)
        self.state = "search"  # search, chase, hide, flank
        self.target_pos = None
        self.state_timer = 0
        self.hit_flash = 0
        
        if etype == "fast":
            self.speed = 4
            self.color = ORANGE
            self.shoot_delay = 80
        elif etype == "sniper":
            self.speed = 2
            self.color = PURPLE
            self.shoot_delay = 150
            self.health = 2
        elif etype == "melee":
            self.speed = 7
            self.color = PINK
            self.health = 3
            self.attack_range = 50
            self.attack_cooldown = 0
        else:
            self.speed = 3
            self.color = RED
            self.shoot_delay = 100
            
    def find_cover(self, player, obstacles):
        # Знайти найближче укриття між ворогом та гравцем
        best_cover = None
        best_dist = float('inf')
        
        for obs in obstacles:
            # Центр перешкоди
            cx = obs.x + obs.w / 2
            cy = obs.y + obs.h / 2
            
            # Перевірити чи перешкода між нами та гравцем
            to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            to_obs = math.sqrt((cx - self.x)**2 + (cy - self.y)**2)
            
            if to_obs < to_player and to_obs < best_dist:
                best_dist = to_obs
                best_cover = (cx, cy)
                
        return best_cover
        
    def can_see_player(self, player, obstacles):
        # Raycast до гравця
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 10:
            return True
            
        steps = int(dist / 10)
        for i in range(steps):
            t = i / steps
            check_x = self.x + dx * t
            check_y = self.y + dy * t
            
            for obs in obstacles:
                if obs.rect.collidepoint(check_x, check_y):
                    return False
        return True
        
    def update(self, player, obstacles, bullets, ts):
        if self.hit_flash > 0:
            self.hit_flash -= ts
            
        self.state_timer -= ts
        
        # Melee AI
        if self.type == "melee":
            self.attack_cooldown = max(0, self.attack_cooldown - ts)
            
            dist_to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            
            if dist_to_player < self.attack_range:
                # Атака
                if self.attack_cooldown <= 0:
                    self.attack_cooldown = 60
                    return {"type": "melee_attack"}
            else:
                # Переслідування з ухиленням від куль
                dx = player.x - self.x
                dy = player.y - self.y
                
                # Перевірка небезпечних куль
                dodge_vx, dodge_vy = 0, 0
                for bullet in bullets:
                    if bullet.is_player:
                        bullet_dist = math.sqrt((bullet.x - self.x)**2 + (bullet.y - self.y)**2)
                        if bullet_dist < 100:
                            # Ухилення перпендикулярно до кулі
                            dodge_vx -= (bullet.y - self.y) / 100
                            dodge_vy += (bullet.x - self.x) / 100
                            
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.vx = (dx/dist + dodge_vx) * self.speed
                    self.vy = (dy/dist + dodge_vy) * self.speed
        else:
            # Звичайний AI
            can_see = self.can_see_player(player, obstacles)
            dist_to_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            
            # Зміна стану
            if self.state_timer <= 0:
                if not can_see:
                    self.state = "search"
                    self.state_timer = 120
                elif dist_to_player < 200 and random.random() < 0.3:
                    self.state = "hide"
                    self.target_pos = self.find_cover(player, obstacles)
                    self.state_timer = 180
                elif dist_to_player > 400:
                    self.state = "chase"
                    self.state_timer = 90
                elif random.random() < 0.4:
                    self.state = "flank"
                    # Фланкування - рух перпендикулярно
                    angle = math.atan2(player.y - self.y, player.x - self.x)
                    offset_angle = angle + random.choice([-math.pi/2, math.pi/2])
                    offset_dist = 200
                    self.target_pos = (
                        player.x + math.cos(offset_angle) * offset_dist,
                        player.y + math.sin(offset_angle) * offset_dist
                    )
                    self.state_timer = 150
                    
            # Виконання стану
            if self.state == "hide" and self.target_pos:
                dx = self.target_pos[0] - self.x
                dy = self.target_pos[1] - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 20:
                    self.vx = (dx/dist) * self.speed * 0.7
                    self.vy = (dy/dist) * self.speed * 0.7
                else:
                    self.vx, self.vy = 0, 0
            elif self.state == "flank" and self.target_pos:
                dx = self.target_pos[0] - self.x
                dy = self.target_pos[1] - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 30:
                    self.vx = (dx/dist) * self.speed
                    self.vy = (dy/dist) * self.speed
            elif self.state == "chase":
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.vx = (dx/dist) * self.speed
                    self.vy = (dy/dist) * self.speed
            else:
                # Патрулювання
                if random.random() < 0.02:
                    self.vx = random.uniform(-self.speed, self.speed)
                    self.vy = random.uniform(-self.speed, self.speed)
                    
            # Стрілянина
            if can_see and dist_to_player < 600:
                self.shoot_timer -= ts
                if self.shoot_timer <= 0:
                    self.shoot_timer = random.randint(self.shoot_delay - 20, self.shoot_delay + 40)
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        # Передбачення
                        predict_x = player.x + player.vx * 10
                        predict_y = player.y + player.vy * 10
                        dx = predict_x - self.x
                        dy = predict_y - self.y
                        dist = math.sqrt(dx**2 + dy**2)
                        speed_mult = 1.3 if self.type == "sniper" else 1.0
                        return {"type": "bullet", "bullet": Bullet(self.x, self.y, dx/dist, dy/dist, False, speed_mult)}
                        
        # Рух з колізіями
        new_x = self.x + self.vx * ts
        new_y = self.y + self.vy * ts
        
        enemy_rect = pygame.Rect(new_x - self.size/2, new_y - self.size/2, self.size, self.size)
        collision = False
        for obs in obstacles:
            if enemy_rect.colliderect(obs.rect):
                collision = True
                break
                
        if not collision:
            self.x = new_x
            self.y = new_y
        else:
            # Спроба обійти
            self.vx *= -0.5
            self.vy *= -0.5
            
        return None
        
    def get_rect(self):
        return pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
        
    def draw(self, screen, camera):
        x, y = self.x - camera.x, self.y - camera.y
        color = WHITE if self.hit_flash > 0 else self.color
        
        if self.type == "melee":
            # Ромб для melee
            points = [
                (x, y - self.size/2),
                (x + self.size/2, y),
                (x, y + self.size/2),
                (x - self.size/2, y)
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        else:
            # Трикутник
            points = [
                (x, y - self.size/2),
                (x - self.size/2, y + self.size/2),
                (x + self.size/2, y + self.size/2)
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)

class Bullet:
    def __init__(self, x, y, dx, dy, is_player, speed_mult=1.0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = BULLET_SPEED * speed_mult
        self.radius = BULLET_RADIUS
        self.is_player = is_player
        
    def update(self, obstacles, ts):
        self.x += self.dx * self.speed * ts
        self.y += self.dy * self.speed * ts
        
        # Колізія з перешкодами
        for obs in obstacles:
            if obs.rect.collidepoint(self.x, self.y):
                return True
        return False
        
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        
    def draw(self, screen, camera):
        x, y = self.x - camera.x, self.y - camera.y
        color = CYAN if self.is_player else YELLOW
        pygame.draw.circle(screen, color, (int(x), int(y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(x), int(y)), self.radius, 1)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Time Slash v2.0 - Complete Overhaul")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 32)
        self.font_big = pygame.font.Font(None, 84)
        self.running = True
        self.paused = False
        self.reset()
        
    def reset(self):
        self.camera = Camera()
        self.player = Player(1500, 1000)
        self.enemies = []
        self.bullets = []
        self.particles = []
        self.obstacles = self.generate_obstacles()
        self.time_scale = 1.0
        self.target_time = 1.0
        self.score = 0
        self.wave = 1
        self.spawn_timer = 120
        self.game_over = False
        self.spawn_wave()
        
    def generate_obstacles(self):
        obs = []
        # Зовнішні стіни - більша карта
        obs.append(Obstacle(0, 0, 3000, 20))
        obs.append(Obstacle(0, 0, 20, 2000))
        obs.append(Obstacle(0, 1980, 3000, 20))
        obs.append(Obstacle(2980, 0, 20, 2000))
        
        # Випадкові перешкоди
        for _ in range(30):
            x = random.randint(100, 2800)
            y = random.randint(100, 1800)
            w = random.randint(80, 200)
            h = random.randint(80, 200)
            obs.append(Obstacle(x, y, w, h))
        return obs
        
    def spawn_wave(self):
        count = 3 + self.wave
        for _ in range(count):
            x = random.randint(300, 2700)
            y = random.randint(300, 1700)
            
            # Melee ворог - дуже рідкісний
            if self.wave >= 3 and random.random() < 0.05:
                self.enemies.append(Enemy(x, y, "melee"))
            elif self.wave >= 5 and random.random() < 0.25:
                self.enemies.append(Enemy(x, y, "sniper"))
            elif self.wave >= 3 and random.random() < 0.35:
                self.enemies.append(Enemy(x, y, "fast"))
            else:
                self.enemies.append(Enemy(x, y, "normal"))
                
    def create_explosion(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(2, 4), random.randint(15, 30)))
            
    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not self.game_over:
                        self.paused = not self.paused
                    else:
                        self.running = False
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_r and self.game_over:
                    self.reset()
                if not self.game_over and not self.paused:
                    if event.key == pygame.K_LSHIFT:
                        self.player.dash(keys)
                    if event.key == pygame.K_SPACE:
                        if self.player.dodge():
                            self.create_explosion(self.player.x, self.player.y, CYAN, 8)
                    if event.key == pygame.K_r:
                        self.player.reload()
                        
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.paused:
                if event.button == 1:  # ЛКМ
                    bullet = self.player.shoot(mouse_pos, self.camera)
                    if bullet:
                        self.bullets.append(bullet)
                        
        # Time scale
        moving = any([keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]])
        shooting = pygame.mouse.get_pressed()[0]
        
        if moving or shooting or self.player.dash_timer > 0 or self.player.dodge_timer > 0:
            self.target_time = 1.0
        else:
            self.target_time = MIN_TIME_SCALE
            
        return keys, mouse_pos
        
    def update(self, keys, mouse_pos):
        if self.game_over or self.paused:
            return
            
        # Time scale
        self.time_scale += (self.target_time - self.time_scale) * TIME_SLOWDOWN
        ts = self.time_scale
        
        # Player
        self.player.update(keys, mouse_pos, self.camera, self.obstacles, ts)
        self.camera.update(self.player.x, self.player.y)
        
        # Enemies
        for enemy in self.enemies[:]:
            result = enemy.update(self.player, self.obstacles, self.bullets, ts)
            if result:
                if result["type"] == "bullet":
                    self.bullets.append(result["bullet"])
                elif result["type"] == "melee_attack":
                    dist = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
                    if dist < enemy.attack_range:
                        if self.player.take_damage(1):
                            self.create_explosion(self.player.x, self.player.y, RED, 30)
                            if self.player.health <= 0:
                                self.game_over = True
                                
        # Bullets
        for bullet in self.bullets[:]:
            if bullet.update(self.obstacles, ts):
                self.bullets.remove(bullet)
                continue
                
            # Перевірка за межами - більша для 3000x2000 карти
            if abs(bullet.x - self.player.x) > 2000 or abs(bullet.y - self.player.y) > 2000:
                self.bullets.remove(bullet)
                continue
                
            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if bullet.get_rect().colliderect(enemy.get_rect()):
                        enemy.health -= 1
                        enemy.hit_flash = 10
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            bonus = 200 if enemy.type == "melee" else 100
                            self.score += bonus
                            self.create_explosion(enemy.x, enemy.y, enemy.color, 25)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
            else:
                if bullet.get_rect().colliderect(self.player.get_rect()):
                    if self.player.take_damage(1):
                        self.create_explosion(self.player.x, self.player.y, RED, 20)
                        if self.player.health <= 0:
                            self.game_over = True
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                        
        # Particles
        for p in self.particles[:]:
            p.update(ts)
            if p.lifetime <= 0:
                self.particles.remove(p)
                
        # Wave system
        if len(self.enemies) == 0:
            self.spawn_timer -= ts
            if self.spawn_timer <= 0:
                self.wave += 1
                self.spawn_wave()
                self.spawn_timer = 120
                
    def draw_ui(self):
        # Health - більші серця для 1920x1080
        for i in range(self.player.max_health):
            x, y = 30 + i * 45, 30
            color = RED if i < self.player.health else DARK_GRAY
            pygame.draw.rect(self.screen, color, (x, y, 40, 40), border_radius=4)
            pygame.draw.rect(self.screen, WHITE, (x, y, 40, 40), 2, border_radius=4)
            
        # Ammo
        ammo_text = self.font.render(f"AMMO: {self.player.ammo}/{self.player.max_ammo}", True, WHITE)
        self.screen.blit(ammo_text, (30, 85))
        
        if self.player.reloading:
            progress = 1 - (self.player.reload_timer / RELOAD_TIME)
            pygame.draw.rect(self.screen, DARK_GRAY, (30, 125, 250, 20))
            pygame.draw.rect(self.screen, YELLOW, (30, 125, int(250 * progress), 20))
            
        # Score & Wave - краще позиціонування для 1920x1080
        score_text = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - 320, 30))
        
        wave_text = self.font.render(f"WAVE: {self.wave}", True, CYAN)
        self.screen.blit(wave_text, (WIDTH - 320, 75))
        
        # Time scale
        time_color = RED if self.time_scale < 0.1 else WHITE
        time_text = self.font_small.render(f"TIME: {self.time_scale:.2f}x", True, time_color)
        self.screen.blit(time_text, (WIDTH - 320, 120))
        
        # Cooldowns - більші для 1920x1080
        if self.player.dash_cooldown > 0:
            pygame.draw.rect(self.screen, DARK_GRAY, (30, HEIGHT - 100, 180, 24))
            filled = int(180 * (1 - self.player.dash_cooldown / 50))
            pygame.draw.rect(self.screen, CYAN, (30, HEIGHT - 100, filled, 24))
            text = self.font_small.render("DASH [Shift]", True, WHITE)
            self.screen.blit(text, (35, HEIGHT - 98))
            
        if self.player.dodge_cooldown > 0:
            pygame.draw.rect(self.screen, DARK_GRAY, (30, HEIGHT - 68, 180, 24))
            filled = int(180 * (1 - self.player.dodge_cooldown / 30))
            pygame.draw.rect(self.screen, YELLOW, (30, HEIGHT - 68, filled, 24))
            text = self.font_small.render("DODGE [Space]", True, WHITE)
            self.screen.blit(text, (35, HEIGHT - 66))
            
        # Mini-map - більша для 1920x1080
        minimap_size = 250
        minimap_scale = 0.08
        mx, my = WIDTH - minimap_size - 30, HEIGHT - minimap_size - 30
        
        pygame.draw.rect(self.screen, (0, 0, 0, 150), (mx, my, minimap_size, minimap_size))
        pygame.draw.rect(self.screen, WHITE, (mx, my, minimap_size, minimap_size), 2)
        
        # Player на мінікарті
        px = mx + (self.player.x * minimap_scale)
        py = my + (self.player.y * minimap_scale)
        pygame.draw.circle(self.screen, BLUE, (int(px), int(py)), 4)
        
        # Вороги на мінікарті
        for enemy in self.enemies:
            ex = mx + (enemy.x * minimap_scale)
            ey = my + (enemy.y * minimap_scale)
            color = PINK if enemy.type == "melee" else RED
            pygame.draw.circle(self.screen, color, (int(ex), int(ey)), 3)
            
    def draw(self):
        self.screen.fill(BLACK)
        
        # Grid background - більша сітка
        for i in range(0, 3000, 100):
            x = i - int(self.camera.x)
            if -100 < x < WIDTH + 100:
                pygame.draw.line(self.screen, DARK_GRAY, (x, 0), (x, HEIGHT), 1)
        for i in range(0, 2000, 100):
            y = i - int(self.camera.y)
            if -100 < y < HEIGHT + 100:
                pygame.draw.line(self.screen, DARK_GRAY, (0, y), (WIDTH, y), 1)
                
        # Obstacles
        for obs in self.obstacles:
            obs.draw(self.screen, self.camera)
            
        # Particles
        for p in self.particles:
            p.draw(self.screen, self.camera)
            
        # Entities
        self.player.draw(self.screen, self.camera)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)
            
        # UI
        self.draw_ui()
        
        # Fade effect
        if self.time_scale < 0.5:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.set_alpha(int((0.5 - self.time_scale) * 300))
            fade.fill(BLACK)
            self.screen.blit(fade, (0, 0))
            
        # Pause
        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font_big.render("PAUSED", True, CYAN)
            rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
            self.screen.blit(pause_text, rect)
            
            help_text = self.font_small.render("ESC - Resume | R - Reload | F11 - Toggle Fullscreen", True, WHITE)
            rect = help_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            self.screen.blit(help_text, rect)
            
            controls = [
                "WASD - Move | Mouse - Aim/Shoot | Shift+Direction - Dash",
                "Space - Dodge | R - Reload"
            ]
            for i, text in enumerate(controls):
                control_text = self.font_small.render(text, True, GRAY)
                rect = control_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80 + i * 40))
                self.screen.blit(control_text, rect)
            
        # Game Over
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            text = self.font_big.render("GAME OVER", True, RED)
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
            self.screen.blit(text, rect)
            
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
            self.screen.blit(score_text, rect)
            
            wave_text = self.font.render(f"Wave Reached: {self.wave}", True, CYAN)
            rect = wave_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
            self.screen.blit(wave_text, rect)
            
            restart = self.font_small.render("Press R to Restart | ESC to Exit", True, WHITE)
            rect = restart.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
            self.screen.blit(restart, rect)
            
        pygame.display.flip()
        
    def run(self):
        while self.running:
            keys, mouse_pos = self.handle_input()
            self.update(keys, mouse_pos)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()