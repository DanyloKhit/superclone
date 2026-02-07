#reworked version of prototype-0's code, doesnt include additions in prototype-0
import pygame
import random
import math

# color
COLORS = {
    'white': (255,255,255), 'black': (0,0,0), 'red': (255,50,50),
    'dark_red': (150,0,0), 'blue': (0,150,255), 'cyan': (0,255,255),
    'yellow': (255,255,0), 'orange': (255,165,0), 'purple': (200,0,255),
    'pink': (255,100,200), 'overlay': (20,20,30), 'ui_bg': (60,60,60)
}

PLAYER_CONFIG = {
    'radius': 20, 'hp': 3, 'speed': 5, 'fire_cooldown': 250,
    'bullet_speed': 12, 'bullet_radius': 4, 'bullet_color': 'cyan'
}

ENEMY_CONFIG = {
    'radius': 16, 'speed': 2, 'bullet_speed': 8, 'bullet_radius': 5,
    'detect_range': 400, 'shot_cooldown': 1200, 'separation_force': 0.5,
    'strafe_threshold': 160, 'strafe_speed': 1.2, 'strafe_switch_time': 800,
    'max_enemies': 10, 'spawn_interval': 1500, 'collision_distance': 30
}

ENEMY_TYPES = {
    'normal': {'hp': 3, 'color': 'red', 'unlock_wave': 0},
    'fast': {'hp': 2, 'color': 'orange', 'unlock_wave': 0},
    'sniper': {'hp': 6, 'color': 'purple', 'unlock_wave': 5},
    'melee': {'hp': 5, 'color': 'pink', 'unlock_wave': 3}
}

TIME_CONFIG = {
    'slowdown': 0.1, 'min_scale': 0.1, 'overlay_alpha_mult': 200
}

WAVE_CONFIG = {'initial_enemies': 3, 'cooldown': 1200}

# int
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Time Slash (superhot clone)")
font = pygame.font.Font(None, 48)
clock = pygame.time.Clock()

UI_BUTTONS = {
    'play': pygame.Rect(WIDTH//2-80, HEIGHT//2-30, 160, 60),
    'settings': pygame.Rect(WIDTH//2-90, HEIGHT//2+40, 180, 60),
    'quit': pygame.Rect(WIDTH//2-70, HEIGHT//2+110, 140, 50)
}

# g-state
game_state = {
    'screen': 'menu', 'running': True, 'wave': 0, 'wave_cooldown': 0,
    'spawn_timer': 0.0, 'time_scale': 1.0,
    'player': {'x': WIDTH//2, 'y': HEIGHT//2, 'vx': 0, 'vy': 0,
               'hp': PLAYER_CONFIG['hp'], 'shot_timer': PLAYER_CONFIG['fire_cooldown']},
    'enemies': [], 'bullets': []
}

# functions
def get_spawn_position():
    side = random.choice([0,1,2,3])
    if side == 0: return random.randint(0, WIDTH), -30
    elif side == 1: return random.randint(0, WIDTH), HEIGHT+30
    elif side == 2: return -30, random.randint(0, HEIGHT)
    else: return WIDTH+30, random.randint(0, HEIGHT)

def get_enemy_type(wave):
    r = random.random()
    if r < 0.05 and wave >= ENEMY_TYPES['melee']['unlock_wave']: return 'melee'
    elif r < 0.25 and wave >= ENEMY_TYPES['sniper']['unlock_wave']: return 'sniper'
    elif r < 0.5: return 'fast'
    else: return 'normal'

def create_enemy(wave):
    x, y = get_spawn_position()
    etype = get_enemy_type(wave)
    return {
        'x': x, 'y': y, 'vx': 0, 'vy': 0, 'r': ENEMY_CONFIG['radius'],
        'hp': ENEMY_TYPES[etype]['hp'], 'type': etype, 'shot_timer': 0,
        'shot_cd': ENEMY_CONFIG['shot_cooldown'], 'detect': ENEMY_CONFIG['detect_range'],
        'strafe_dir': random.choice([-1,1]), 'strafe_timer': 0
    }

def spawn_wave(count):
    for _ in range(count):
        game_state['enemies'].append(create_enemy(game_state['wave']))

def create_bullet(x, y, vx, vy, owner):
    radius = PLAYER_CONFIG['bullet_radius'] if owner == 'player' else ENEMY_CONFIG['bullet_radius']
    return {'x': x, 'y': y, 'vx': vx, 'vy': vy, 'r': radius, 'owner': owner}

def draw_enemy(enemy):
    ex, ey = int(enemy['x']), int(enemy['y'])
    size = enemy['r']
    etype = enemy['type']
    color = COLORS[ENEMY_TYPES[etype]['color']]
    
    if etype == 'melee':
        points = [(ex, ey-size), (ex+size, ey), (ex, ey+size), (ex-size, ey)]
    else:
        points = [(ex, ey-size), (ex-size, ey+size), (ex+size, ey+size)]
    
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, COLORS['white'], points, 2)

def draw_player(px, py, angle):
    cr = PLAYER_CONFIG['radius']
    prect = pygame.Rect(px-cr, py-cr, cr*2, cr*2)
    pygame.draw.rect(screen, COLORS['blue'], prect, border_radius=6)
    pygame.draw.rect(screen, COLORS['white'], prect, 2, border_radius=6)
    end_x = px + math.cos(angle) * cr
    end_y = py + math.sin(angle) * cr
    pygame.draw.line(screen, COLORS['white'], (px, py), (end_x, end_y), 2)

# m-loop
while game_state['running']:
    dt = clock.tick(60)
    
    # events
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            game_state['running'] = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            game_state['screen'] = 'menu'
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if game_state['screen'] == 'menu':
                if UI_BUTTONS['play'].collidepoint(e.pos): game_state['screen'] = 'game'
                elif UI_BUTTONS['quit'].collidepoint(e.pos): game_state['running'] = False
            else:
                if game_state['player']['shot_timer'] >= PLAYER_CONFIG['fire_cooldown']:
                    game_state['player']['shot_timer'] = 0
                    mx, my = e.pos
                    dx = mx - game_state['player']['x']
                    dy = my - game_state['player']['y']
                    dist = math.hypot(dx, dy) or 1.0
                    bvx = (dx/dist) * PLAYER_CONFIG['bullet_speed']
                    bvy = (dy/dist) * PLAYER_CONFIG['bullet_speed']
                    game_state['bullets'].append(create_bullet(
                        game_state['player']['x'], game_state['player']['y'], bvx, bvy, 'player'))
    
    screen.fill(COLORS['black'])
    
    # time
    keys = pygame.key.get_pressed()
    moving = any([keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]])
    shooting = pygame.mouse.get_pressed()[0]
    target_scale = 1.0 if (moving or shooting) else TIME_CONFIG['min_scale']
    game_state['time_scale'] += (target_scale - game_state['time_scale']) * TIME_CONFIG['slowdown']
    scaled_dt = dt * game_state['time_scale']
    
    # menu
    if game_state['screen'] == 'menu':
        for btn_name, btn_rect in [('play', UI_BUTTONS['play']), ('settings', UI_BUTTONS['settings']), ('quit', UI_BUTTONS['quit'])]:
            pygame.draw.rect(screen, COLORS['ui_bg'], btn_rect, border_radius=6)
            text = font.render(btn_name.upper(), True, COLORS['white'])
            screen.blit(text, text.get_rect(center=btn_rect.center))
    
    #GS
    else:
        p = game_state['player']
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_CONFIG['speed']
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * PLAYER_CONFIG['speed']
        p['x'] = max(PLAYER_CONFIG['radius'], min(WIDTH-PLAYER_CONFIG['radius'], p['x']+dx))
        p['y'] = max(PLAYER_CONFIG['radius'], min(HEIGHT-PLAYER_CONFIG['radius'], p['y']+dy))
        
        game_state['spawn_timer'] += scaled_dt
        p['shot_timer'] += dt
        
        # WS
        if len(game_state['enemies']) == 0 and game_state['wave_cooldown'] <= 0:
            spawn_wave(WAVE_CONFIG['initial_enemies'] + game_state['wave'])
            game_state['wave'] += 1
            game_state['wave_cooldown'] = WAVE_CONFIG['cooldown']
        game_state['wave_cooldown'] = max(0, game_state['wave_cooldown'] - dt)
        
        if game_state['spawn_timer'] >= ENEMY_CONFIG['spawn_interval'] and len(game_state['enemies']) < ENEMY_CONFIG['max_enemies']:
            game_state['spawn_timer'] = 0
            spawn_wave(1)
        
        # UB
        for b in game_state['bullets'][:]:
            b['x'] += b['vx'] * game_state['time_scale']
            b['y'] += b['vy'] * game_state['time_scale']
            color = COLORS[PLAYER_CONFIG['bullet_color']] if b['owner'] == 'player' else COLORS['yellow']
            pygame.draw.circle(screen, color, (int(b['x']), int(b['y'])), b['r'])
            pygame.draw.circle(screen, COLORS['white'], (int(b['x']), int(b['y'])), b['r'], 1)
            
            if b['x'] < -50 or b['x'] > WIDTH+50 or b['y'] < -50 or b['y'] > HEIGHT+50:
                try: game_state['bullets'].remove(b)
                except: pass
                continue
            
            if b['owner'] == 'player':
                for en in game_state['enemies'][:]:
                    if math.hypot(en['x']-b['x'], en['y']-b['y']) <= en['r']+b['r']:
                        en['hp'] -= 1
                        try: game_state['bullets'].remove(b)
                        except: pass
                        if en['hp'] <= 0:
                            try: game_state['enemies'].remove(en)
                            except: pass
                        break
            else:
                if math.hypot(p['x']-b['x'], p['y']-b['y']) <= PLAYER_CONFIG['radius']+b['r']:
                    p['hp'] -= 1
                    try: game_state['bullets'].remove(b)
                    except: pass
                    if p['hp'] <= 0:
                        game_state['screen'] = 'menu'
                        p['x'], p['y'], p['hp'] = WIDTH//2, HEIGHT//2, PLAYER_CONFIG['hp']
                        game_state['enemies'].clear(); game_state['bullets'].clear()
                    break
        
        # UE
        for en in game_state['enemies'][:]:
            en['shot_timer'] += scaled_dt
            en['strafe_timer'] += scaled_dt
            dx = p['x'] - en['x']
            dy = p['y'] - en['y']
            dist = math.hypot(dx, dy) or 1.0
            
            sepx = sepy = 0
            for other in game_state['enemies']:
                if other is en: continue
                ddx, ddy = en['x']-other['x'], en['y']-other['y']
                ddd = math.hypot(ddx, ddy) or 1.0
                if ddd < ENEMY_CONFIG['collision_distance']:
                    sepx += ddx/ddd; sepy += ddy/ddd
            
            vx = (dx/dist)*ENEMY_CONFIG['speed'] - ENEMY_CONFIG['separation_force']*sepx
            vy = (dy/dist)*ENEMY_CONFIG['speed'] - ENEMY_CONFIG['separation_force']*sepy
            
            if dist < ENEMY_CONFIG['strafe_threshold']:
                perp_x, perp_y = -dy/dist, dx/dist
                if en['strafe_timer'] > ENEMY_CONFIG['strafe_switch_time']:
                    en['strafe_dir'] *= -1; en['strafe_timer'] = 0
                vx += perp_x * en['strafe_dir'] * ENEMY_CONFIG['strafe_speed']
                vy += perp_y * en['strafe_dir'] * ENEMY_CONFIG['strafe_speed']
            
            en['x'] += vx * game_state['time_scale']
            en['y'] += vy * game_state['time_scale']
            draw_enemy(en)
            
            if dist < en['detect'] and en['shot_timer'] >= en['shot_cd']:
                en['shot_timer'] = 0
                effective_speed = ENEMY_CONFIG['bullet_speed'] * max(game_state['time_scale'], 0.0001)
                t_hit = min(2000, dist / effective_speed)
                lead_x, lead_y = p['x'] + p['vx']*t_hit, p['y'] + p['vy']*t_hit
                aimx, aimy = lead_x - en['x'], lead_y - en['y']
                ad = math.hypot(aimx, aimy) or 1.0
                bvx = (aimx/ad) * ENEMY_CONFIG['bullet_speed']
                bvy = (aimy/ad) * ENEMY_CONFIG['bullet_speed']
                game_state['bullets'].append(create_bullet(en['x'], en['y'], bvx, bvy, 'enemy'))
            
            if dist <= en['r'] + PLAYER_CONFIG['radius']:
                p['hp'] -= 1
                try: game_state['enemies'].remove(en)
                except: pass
                if p['hp'] <= 0:
                    game_state['screen'] = 'menu'
                    p['x'], p['y'], p['hp'] = WIDTH//2, HEIGHT//2, PLAYER_CONFIG['hp']
                    game_state['enemies'].clear(); game_state['bullets'].clear()
                break
        
        # Draw player
        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - p['y'], mx - p['x'])
        draw_player(int(p['x']), int(p['y']), angle)
        
        # UI
        hp_text = font.render(f"HP: {p['hp']}", True, COLORS['white'])
        screen.blit(hp_text, (10,10))
        
        # Time slowdown overlay
        if game_state['time_scale'] < 1.0:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            alpha = int((1.0 - game_state['time_scale']) * TIME_CONFIG['overlay_alpha_mult'])
            overlay.set_alpha(alpha)
            overlay.fill(COLORS['overlay'])
            screen.blit(overlay, (0,0))
    
    pygame.display.flip()

pygame.quit()
