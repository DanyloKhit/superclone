import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

# ============================================================================
# настройки гри
# ============================================================================

class Config:
    """Centralized game configuration"""
    
    # Display
    FULLSCREEN = True
    FPS = 60
    
    # Player
    PLAYER_RADIUS = 20
    PLAYER_SPEED = 5
    PLAYER_HP = 3
    PLAYER_FIRE_COOLDOWN = 250
    PLAYER_BULLET_SPEED = 12
    PLAYER_BULLET_RADIUS = 4
    
    # Time mechanics
    TIME_SLOWDOWN = 0.1
    MIN_TIME_SCALE = 0.1
    SLOW_OVERLAY_MAX_ALPHA = 200
    
    # Spawning
    SPAWN_INTERVAL = 1500
    MAX_ENEMIES = 20
    WAVE_COOLDOWN = 1200
    BASE_WAVE_SIZE = 3
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 50, 50)
    DARK_RED = (150, 0, 0)
    BLUE = (0, 150, 255)
    CYAN = (0, 255, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (200, 0, 255)
    PINK = (255, 100, 200)
    OVERLAY = (20, 20, 30)


class EnemyType(Enum):
    """Enemy type enumeration"""
    NORMAL = "normal"
    FAST = "fast"
    SNIPER = "sniper"
    MELEE = "melee"


@dataclass
class EnemyConfig:
    """Configuration for a specific enemy type"""
    radius: int
    hp: int
    speed_multiplier: float
    shot_cooldown: int
    detection_range: int
    color: Tuple[int, int, int]
    shape: str  # 'triangle' or 'diamond'
    bullet_speed: float = 8.0
    spawn_weight: float = 1.0
    min_wave: int = 0


class EnemyConfigs:
    """All enemy type configurations"""
    
    CONFIGS = {
        EnemyType.NORMAL: EnemyConfig(
            radius=16,
            hp=2,
            speed_multiplier=1.0,
            shot_cooldown=1200,
            detection_range=400,
            color=Config.RED,
            shape='triangle',
            spawn_weight=1.0,
            min_wave=0
        ),
        EnemyType.FAST: EnemyConfig(
            radius=16,
            hp=2,
            speed_multiplier=1.5,
            shot_cooldown=1200,
            detection_range=400,
            color=Config.ORANGE,
            shape='triangle',
            spawn_weight=0.5,
            min_wave=0
        ),
        EnemyType.SNIPER: EnemyConfig(
            radius=16,
            hp=2,
            speed_multiplier=0.8,
            shot_cooldown=1200,
            detection_range=400,
            color=Config.PURPLE,
            shape='triangle',
            spawn_weight=0.25,
            min_wave=5
        ),
        EnemyType.MELEE: EnemyConfig(
            radius=16,
            hp=2,
            speed_multiplier=1.8,
            shot_cooldown=999999,  # Never shoots
            detection_range=0,
            color=Config.PINK,
            shape='diamond',
            spawn_weight=0.05,
            min_wave=3
        ),
    }
    
    @classmethod
    def get(cls, enemy_type: EnemyType) -> EnemyConfig:
        return cls.CONFIGS[enemy_type]


# ============================================================================
# GAME OBJECTS
# ============================================================================

class Bullet:
    """Bullet class for both player and enemy projectiles"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 radius: int, owner: str):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.owner = owner  # 'player' or 'enemy'
        
    def update(self, time_scale: float):
        """Update bullet position"""
        self.x += self.vx * time_scale
        self.y += self.vy * time_scale
        
    def is_offscreen(self, width: int, height: int) -> bool:
        """Check if bullet is off screen"""
        margin = 50
        return (self.x < -margin or self.x > width + margin or 
                self.y < -margin or self.y > height + margin)
    
    def draw(self, screen: pygame.Surface):
        """Draw the bullet"""
        pos = (int(self.x), int(self.y))
        if self.owner == 'player':
            pygame.draw.circle(screen, Config.CYAN, pos, self.radius)
            pygame.draw.circle(screen, Config.WHITE, pos, self.radius, 1)
        else:
            pygame.draw.circle(screen, Config.YELLOW, pos, self.radius)
            pygame.draw.circle(screen, Config.WHITE, pos, self.radius, 1)
    
    def collides_with(self, x: float, y: float, radius: float) -> bool:
        """Check collision with a circular object"""
        return math.hypot(self.x - x, self.y - y) <= self.radius + radius


class Enemy:
    """Enemy class with configurable behavior"""
    
    BASE_SPEED = 2  # Base enemy speed
    
    def __init__(self, x: float, y: float, enemy_type: EnemyType):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.config = EnemyConfigs.get(enemy_type)
        
        # Stats from config
        self.radius = self.config.radius
        self.hp = self.config.hp
        self.max_hp = self.config.hp
        
        # Movement
        self.vx = 0
        self.vy = 0
        self.strafe_dir = random.choice([-1, 1])
        self.strafe_timer = 0
        
        # Shooting
        self.shot_timer = 0
        
    def update(self, player_x: float, player_y: float, 
               player_vx: float, player_vy: float,
               enemies: List['Enemy'], time_scale: float, 
               scaled_dt: float) -> Optional[Bullet]:
        """Update enemy state and return bullet if fired"""
        self.shot_timer += scaled_dt
        self.strafe_timer += scaled_dt
        
        # Calculate direction to player
        dx_player = player_x - self.x
        dy_player = player_y - self.y
        dist_to_player = math.hypot(dx_player, dy_player) or 1.0
        
        # Separation from other enemies
        sep_x = sep_y = 0
        for other in enemies:
            if other is self:
                continue
            ddx = self.x - other.x
            ddy = self.y - other.y
            sep_dist = math.hypot(ddx, ddy) or 1.0
            if sep_dist < 30:
                sep_x += ddx / sep_dist
                sep_y += ddy / sep_dist
        
        # Calculate desired velocity
        speed = self.BASE_SPEED * self.config.speed_multiplier
        vx_desired = (dx_player / dist_to_player) * speed - 0.5 * sep_x
        vy_desired = (dy_player / dist_to_player) * speed - 0.5 * sep_y
        
        # Strafing behavior when close
        if dist_to_player < 160:
            perp_x = -dy_player / dist_to_player
            perp_y = dx_player / dist_to_player
            if self.strafe_timer > 800:
                self.strafe_dir *= -1
                self.strafe_timer = 0
            vx_desired += perp_x * self.strafe_dir * 1.2
            vy_desired += perp_y * self.strafe_dir * 1.2
        
        # Move
        self.x += vx_desired * time_scale
        self.y += vy_desired * time_scale
        
        # Shoot if in range
        bullet = None
        if dist_to_player < self.config.detection_range:
            if self.shot_timer >= self.config.shot_cooldown:
                self.shot_timer = 0
                bullet = self._create_bullet(player_x, player_y, 
                                            player_vx, player_vy, time_scale)
        
        return bullet
    
    def _create_bullet(self, player_x: float, player_y: float,
                       player_vx: float, player_vy: float,
                       time_scale: float) -> Bullet:
        """Create a bullet aimed at the player with lead"""
        effective_speed = self.config.bullet_speed * max(time_scale, 0.0001)
        dist = math.hypot(player_x - self.x, player_y - self.y) or 1.0
        t_hit = min(2000, dist / effective_speed)
        
        # Lead the target
        lead_x = player_x + player_vx * t_hit
        lead_y = player_y + player_vy * t_hit
        
        aim_x = lead_x - self.x
        aim_y = lead_y - self.y
        aim_dist = math.hypot(aim_x, aim_y) or 1.0
        
        bullet_vx = (aim_x / aim_dist) * self.config.bullet_speed
        bullet_vy = (aim_y / aim_dist) * self.config.bullet_speed
        
        return Bullet(self.x, self.y, bullet_vx, bullet_vy, 5, 'enemy')
    
    def draw(self, screen: pygame.Surface):
        """Draw the enemy"""
        ex = int(self.x)
        ey = int(self.y)
        size = self.radius
        
        if self.config.shape == 'diamond':
            points = [
                (ex, ey - size),
                (ex + size, ey),
                (ex, ey + size),
                (ex - size, ey)
            ]
        else:  # triangle
            points = [
                (ex, ey - size),
                (ex - size, ey + size),
                (ex + size, ey + size)
            ]
        
        pygame.draw.polygon(screen, self.config.color, points)
        pygame.draw.polygon(screen, Config.WHITE, points, 2)
    
    def take_damage(self, damage: int = 1) -> bool:
        """Take damage and return True if dead"""
        self.hp -= damage
        return self.hp <= 0
    
    def collides_with_player(self, player_x: float, player_y: float, 
                            player_radius: float) -> bool:
        """Check collision with player"""
        return math.hypot(self.x - player_x, self.y - player_y) <= self.radius + player_radius


class Player:
    """Player class"""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = Config.PLAYER_RADIUS
        self.hp = Config.PLAYER_HP
        self.max_hp = Config.PLAYER_HP
        self.shot_timer = Config.PLAYER_FIRE_COOLDOWN
        
    def update(self, keys, dt: float, width: int, height: int):
        """Update player position based on input"""
        # Calculate movement
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= Config.PLAYER_SPEED
        if keys[pygame.K_s]:
            dy += Config.PLAYER_SPEED
        if keys[pygame.K_a]:
            dx -= Config.PLAYER_SPEED
        if keys[pygame.K_d]:
            dx += Config.PLAYER_SPEED
        
        # Update velocity (for enemy prediction)
        self.vx = dx
        self.vy = dy
        
        # Move
        self.x += dx
        self.y += dy
        
        # Clamp to screen
        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))
        
        # Update shot timer
        self.shot_timer += dt
    
    def shoot(self, target_x: float, target_y: float) -> Optional[Bullet]:
        """Attempt to shoot towards target"""
        if self.shot_timer >= Config.PLAYER_FIRE_COOLDOWN:
            self.shot_timer = 0
            
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy) or 1.0
            
            bullet_vx = (dx / dist) * Config.PLAYER_BULLET_SPEED
            bullet_vy = (dy / dist) * Config.PLAYER_BULLET_SPEED
            
            return Bullet(self.x, self.y, bullet_vx, bullet_vy, 
                         Config.PLAYER_BULLET_RADIUS, 'player')
        return None
    
    def draw(self, screen: pygame.Surface, mouse_x: int, mouse_y: int):
        """Draw the player with direction indicator"""
        px = int(self.x)
        py = int(self.y)
        
        # Draw body
        rect = pygame.Rect(px - self.radius, py - self.radius, 
                          self.radius * 2, self.radius * 2)
        pygame.draw.rect(screen, Config.BLUE, rect, border_radius=6)
        pygame.draw.rect(screen, Config.WHITE, rect, 2, border_radius=6)
        
        # Draw direction line
        angle = math.atan2(mouse_y - py, mouse_x - px)
        end_x = px + math.cos(angle) * self.radius
        end_y = py + math.sin(angle) * self.radius
        pygame.draw.line(screen, Config.WHITE, (px, py), (end_x, end_y), 2)
    
    def take_damage(self, damage: int = 1) -> bool:
        """Take damage and return True if dead"""
        self.hp -= damage
        return self.hp <= 0
    
    def reset(self, x: float, y: float):
        """Reset player to initial state"""
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.hp = Config.PLAYER_HP
        self.shot_timer = Config.PLAYER_FIRE_COOLDOWN


# ============================================================================
# WAVE MANAGER
# ============================================================================

class WaveManager:
    """Manages enemy waves and spawning"""
    
    def __init__(self):
        self.wave = 0
        self.wave_cooldown = 0
        self.spawn_timer = 0
        
    def update(self, dt: float, scaled_dt: float, enemy_count: int) -> List[Enemy]:
        """Update wave state and return list of enemies to spawn"""
        self.wave_cooldown = max(0, self.wave_cooldown - dt)
        self.spawn_timer += scaled_dt
        
        enemies_to_spawn = []
        
        # Spawn new wave when all enemies dead
        if enemy_count == 0 and self.wave_cooldown <= 0:
            count = Config.BASE_WAVE_SIZE + self.wave
            enemies_to_spawn.extend(self._create_wave(count))
            self.wave += 1
            self.wave_cooldown = Config.WAVE_COOLDOWN
        
        # Continuous spawning
        if self.spawn_timer >= Config.SPAWN_INTERVAL and enemy_count < Config.MAX_ENEMIES:
            self.spawn_timer = 0
            enemies_to_spawn.extend(self._create_wave(1))
        
        return enemies_to_spawn
    
    def _create_wave(self, count: int) -> List[Enemy]:
        """Create a wave of enemies"""
        enemies = []
        for _ in range(count):
            x, y = self._random_spawn_position()
            enemy_type = self._choose_enemy_type()
            enemies.append(Enemy(x, y, enemy_type))
        return enemies
    
    def _random_spawn_position(self) -> Tuple[float, float]:
        """Get random spawn position at screen edge"""
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        
        side = random.choice([0, 1, 2, 3])
        if side == 0:  # Top
            return random.randint(0, width), -30
        elif side == 1:  # Bottom
            return random.randint(0, width), height + 30
        elif side == 2:  # Left
            return -30, random.randint(0, height)
        else:  # Right
            return width + 30, random.randint(0, height)
    
    def _choose_enemy_type(self) -> EnemyType:
        """Choose enemy type based on wave and weights"""
        available_types = []
        weights = []
        
        for enemy_type in EnemyType:
            config = EnemyConfigs.get(enemy_type)
            if self.wave >= config.min_wave:
                available_types.append(enemy_type)
                weights.append(config.spawn_weight)
        
        return random.choices(available_types, weights=weights)[0]
    
    def reset(self):
        """Reset wave manager"""
        self.wave = 0
        self.wave_cooldown = 0
        self.spawn_timer = 0


# ============================================================================
# GAME STATES
# ============================================================================

class GameState(Enum):
    """Game state enumeration"""
    MENU = "menu"
    PLAYING = "playing"


class Game:
    """Main game class"""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        flags = pygame.FULLSCREEN if Config.FULLSCREEN else 0
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("Time Slash (superhot clone)")
        
        # Font
        self.font = pygame.font.Font(None, 48)
        
        # Game state
        self.state = GameState.MENU
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Time mechanics
        self.time_scale = 1.0
        
        # Game objects
        self.player = Player(self.width // 2, self.height // 2)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.wave_manager = WaveManager()
        
        # UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI elements"""
        cx = self.width // 2
        cy = self.height // 2
        
        self.button_play = pygame.Rect(cx - 80, cy - 30, 160, 60)
        self.button_settings = pygame.Rect(cx - 90, cy + 40, 180, 60)
        self.button_quit = pygame.Rect(cx - 70, cy + 110, 140, 50)
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(Config.FPS)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                    
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.MENU:
                    self._handle_menu_click(event.pos)
                else:
                    self._handle_game_click(event.pos)
    
    def _handle_menu_click(self, pos: Tuple[int, int]):
        """Handle clicks in menu state"""
        if self.button_play.collidepoint(pos):
            self.state = GameState.PLAYING
            self._reset_game()
        elif self.button_quit.collidepoint(pos):
            self.running = False
    
    def _handle_game_click(self, pos: Tuple[int, int]):
        """Handle clicks in game state (shooting)"""
        bullet = self.player.shoot(pos[0], pos[1])
        if bullet:
            self.bullets.append(bullet)
    
    def _update(self, dt: float):
        """Update game state"""
        if self.state == GameState.PLAYING:
            self._update_game(dt)
    
    def _update_game(self, dt: float):
        """Update game logic"""
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        # Calculate time scale based on player activity
        is_moving = any([keys[pygame.K_w], keys[pygame.K_a], 
                        keys[pygame.K_s], keys[pygame.K_d]])
        
        if is_moving or mouse_pressed:
            time_scale_target = 1.0
        else:
            time_scale_target = Config.MIN_TIME_SCALE
        
        self.time_scale += (time_scale_target - self.time_scale) * Config.TIME_SLOWDOWN
        scaled_dt = dt * self.time_scale
        
        # Update player
        self.player.update(keys, dt, self.width, self.height)
        
        # Update wave manager and spawn enemies
        new_enemies = self.wave_manager.update(dt, scaled_dt, len(self.enemies))
        self.enemies.extend(new_enemies)
        
        # Update bullets
        self._update_bullets()
        
        # Update enemies
        self._update_enemies(scaled_dt)
        
        # Check player death
        if self.player.hp <= 0:
            self._game_over()
    
    def _update_bullets(self):
        """Update all bullets and handle collisions"""
        for bullet in self.bullets[:]:
            bullet.update(self.time_scale)
            
            # Remove if offscreen
            if bullet.is_offscreen(self.width, self.height):
                self.bullets.remove(bullet)
                continue
            
            # Check collisions
            if bullet.owner == 'player':
                self._check_bullet_enemy_collision(bullet)
            else:
                self._check_bullet_player_collision(bullet)
    
    def _check_bullet_enemy_collision(self, bullet: Bullet):
        """Check if player bullet hits any enemy"""
        for enemy in self.enemies[:]:
            if bullet.collides_with(enemy.x, enemy.y, enemy.radius):
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                if enemy.take_damage():
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                break
    
    def _check_bullet_player_collision(self, bullet: Bullet):
        """Check if enemy bullet hits player"""
        if bullet.collides_with(self.player.x, self.player.y, self.player.radius):
            if bullet in self.bullets:
                self.bullets.remove(bullet)
            self.player.take_damage()
            if self.player.hp <= 0:
                self._game_over()
    
    def _update_enemies(self, scaled_dt: float):
        """Update all enemies"""
        for enemy in self.enemies[:]:
            # Update enemy and get bullet if fired
            bullet = enemy.update(
                self.player.x, self.player.y,
                self.player.vx, self.player.vy,
                self.enemies, self.time_scale, scaled_dt
            )
            
            if bullet:
                self.bullets.append(bullet)
            
            # Check collision with player
            if enemy.collides_with_player(self.player.x, self.player.y, 
                                         self.player.radius):
                self.player.take_damage()
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                if self.player.hp <= 0:
                    self._game_over()
                    break
    
    def _draw(self):
        """Draw everything"""
        self.screen.fill(Config.BLACK)
        
        if self.state == GameState.MENU:
            self._draw_menu()
        else:
            self._draw_game()
    
    def _draw_menu(self):
        """Draw menu screen"""
        # Play button
        pygame.draw.rect(self.screen, (60, 60, 60), self.button_play, 
                        border_radius=6)
        play_surf = self.font.render("PLAY", True, Config.WHITE)
        self.screen.blit(play_surf, 
                        play_surf.get_rect(center=self.button_play.center))
        
        # Settings button
        pygame.draw.rect(self.screen, (60, 60, 60), self.button_settings, 
                        border_radius=6)
        settings_surf = self.font.render("Settings", True, Config.WHITE)
        self.screen.blit(settings_surf, 
                        settings_surf.get_rect(center=self.button_settings.center))
        
        # Quit button
        pygame.draw.rect(self.screen, (60, 60, 60), self.button_quit, 
                        border_radius=6)
        quit_surf = self.font.render("QUIT", True, Config.WHITE)
        self.screen.blit(quit_surf, 
                        quit_surf.get_rect(center=self.button_quit.center))
    
    def _draw_game(self):
        """Draw game screen"""
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw player
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.player.draw(self.screen, mouse_x, mouse_y)
        
        # Draw HP
        hp_surf = self.font.render(f"HP: {self.player.hp}", True, Config.WHITE)
        self.screen.blit(hp_surf, (10, 10))
        
        # Draw slow-motion overlay
        if self.time_scale < 1.0:
            overlay = pygame.Surface((self.width, self.height))
            alpha = int((1.0 - self.time_scale) * Config.SLOW_OVERLAY_MAX_ALPHA)
            overlay.set_alpha(alpha)
            overlay.fill(Config.OVERLAY)
            self.screen.blit(overlay, (0, 0))
    
    def _reset_game(self):
        """Reset game to initial state"""
        self.player.reset(self.width // 2, self.height // 2)
        self.enemies.clear()
        self.bullets.clear()
        self.wave_manager.reset()
        self.time_scale = 1.0
    
    def _game_over(self):
        """Handle game over"""
        self.state = GameState.MENU
        self._reset_game()


# ============================================================================
# MAIN
# ============================================================================

def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
