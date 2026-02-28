import pygame
import random
import math

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Time Slash (superhot clone)")
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 32)
tiny_font = pygame.font.Font(None, 24)
button_rect = pygame.Rect(WIDTH//2-80, HEIGHT//2-30, 160, 60)
button2_rect = pygame.Rect(WIDTH//2-90, HEIGHT//2+40, 180, 60)
button_quit_rect = pygame.Rect(WIDTH//2-70, HEIGHT//2+110, 140, 50)

state = "menu"
paused = False
running = True
wave = 1
wave_cooldown = 1
clock = pygame.time.Clock()

cx, cy = WIDTH//2, HEIGHT//2
cr = 20

enemies = []
bullets = []
player_hp = 100
player_max_hp = 100
player_vx = player_vy = 0
player_fire_cooldown = 250
player_shot_timer = player_fire_cooldown
player_damage = 10
player_speed = 300  # pixels per second
player_base_speed = 300
bullet_base_speed = 720
player_xp = 0
player_level = 1
xp_to_level = 3
player_crit_chance = 0
player_lifesteal_amount = 0
player_armor = 0
player_dash_cooldown = 0
player_dash_cd_max = 500

enemy_bullet_speed = 480  # pixels per second
enemy_speed = 120  # pixels per second
TIME_SLOWDOWN = 0.15  # Faster interpolation for 75fps
MIN_TIME_SCALE = 0.1
time_scale = 1.0
special_unlocked = False

WHITE, BLACK, RED, DARK_RED, BLUE, CYAN, YELLOW = (255,255,255), (0,0,0), (255,50,50), (150,0,0), (0,150,255), (0,255,255), (255,255,0)
ORANGE, PURPLE, PINK, GREEN, GRAY, GOLD = (255,165,0), (200,0,255), (255,100,200), (0,255,100), (100,100,100), (255,215,0)

CARDS = [
    {'name': 'Rapid Fire', 'desc': '-30% Cooldown', 'type': 'fire_rate', 'value': -0.3, 'rarity': 'common'},
    {'name': 'Heavy Shot', 'desc': '+5 Damage', 'type': 'damage', 'value': 5, 'rarity': 'common'},
    {'name': 'Health Boost', 'desc': '+20 Max HP', 'type': 'max_hp', 'value': 20, 'rarity': 'common'},
    {'name': 'Speed Demon', 'desc': '+30% Speed', 'type': 'speed', 'value': 0.3, 'rarity': 'uncommon'},
    {'name': 'Life Steal', 'desc': '+3 HP on Kill', 'type': 'lifesteal', 'value': 3, 'rarity': 'uncommon'},
    {'name': 'Bulletstorm', 'desc': 'Triple Shot', 'type': 'multishot', 'value': 3, 'rarity': 'rare'},
    {'name': 'Tank Mode', 'desc': '+40 HP, -15% Speed', 'type': 'tank', 'value': [40, -0.15], 'rarity': 'rare'},
    {'name': 'Sniper', 'desc': '+100% Dmg, +40% CD', 'type': 'sniper', 'value': [1.0, 0.4], 'rarity': 'rare'},
    {'name': 'Critical Strike', 'desc': '+20% Crit Chance', 'type': 'crit', 'value': 0.2, 'rarity': 'uncommon'},
    {'name': 'Speedy Bullets', 'desc': '+30% Bullet Speed', 'type': 'bullet_speed_u', 'value': 0.3, 'rarity': 'uncommon'}, #новий upgrade
    {'name': 'Armor Plating', 'desc': '+15 Armor', 'type': 'armor', 'value': 15, 'rarity': 'rare'},
    {'name': 'Dash', 'desc': 'Dash Ability (Space)', 'type': 'dash', 'value': 1, 'rarity': 'rare'},
    {'name': 'Explosive Rounds', 'desc': 'AOE on Hit', 'type': 'explosive', 'value': 1, 'rarity': 'epic'},
    {'name': 'TIME BREAKER', 'desc': 'Unlock Special Enemies', 'type': 'special', 'value': 1, 'rarity': 'legendary'}
]
active_cards = []
card_choices = []
RARITY_WEIGHTS = {'common': 50, 'uncommon': 30, 'rare': 15, 'epic': 4, 'legendary': 1}
RARITY_COLORS = {'common': WHITE, 'uncommon': GREEN, 'rare': BLUE, 'epic': PURPLE, 'legendary': GOLD}

enemy_surfs = {}
spawn_timer = 0.0
spawn_interval = 1500
max_enemies = 10

def apply_card(card):
    global player_max_hp, player_hp, player_fire_cooldown, player_damage, player_speed, active_cards, player_base_speed, bullet_base_speed
    global player_crit_chance, player_lifesteal_amount, player_armor, special_unlocked, bullet_speed
    active_cards.append(card['name'])
    if card['type'] == 'fire_rate': player_fire_cooldown = int(player_fire_cooldown * (1 + card['value']))
    elif card['type'] == 'damage': player_damage += card['value']
    elif card['type'] == 'max_hp': player_max_hp += card['value']; player_hp += card['value']
    elif card['type'] == 'speed': player_base_speed = int(player_base_speed * (1 + card['value'])); player_speed = player_base_speed
    elif card['type'] == 'lifesteal': player_lifesteal_amount += card['value']
    elif card['type'] == 'tank': player_max_hp += card['value'][0]; player_hp += card['value'][0]; player_base_speed = int(player_base_speed * (1 + card['value'][1])); player_speed = player_base_speed
    elif card['type'] == 'sniper': player_damage = int(player_damage * (1 + card['value'][0])); player_fire_cooldown = int(player_fire_cooldown * (1 + card['value'][1]))
    elif card['type'] == 'crit': player_crit_chance += card['value']
    elif card['type'] == 'bullet_speed_u': bullet_base_speed = int(bullet_base_speed * (1 + card['value'])); bullet_speed = bullet_base_speed
    elif card['type'] == 'armor': player_armor += card['value']
    elif card['type'] == 'special': special_unlocked = True

def level_up():
    global player_level, player_xp, xp_to_level, state, card_choices
    player_level += 1
    player_xp -= xp_to_level
    xp_to_level += 3
    available = [c for c in CARDS if c['name'] not in active_cards or c['type'] in ['lifesteal', 'damage', 'max_hp', 'crit', 'armor']]
    weights = [RARITY_WEIGHTS[c['rarity']] for c in available]
    card_choices = random.choices(available, weights=weights, k=min(3, len(available)))
    state = "cards"

def spawn_wave(n):
    for _ in range(n):
        side = random.choice([0,1,2,3])
        ex, ey = (random.randint(0, WIDTH), -30) if side == 0 else (random.randint(0, WIDTH), HEIGHT+30) if side == 1 else (-30, random.randint(0, HEIGHT)) if side == 2 else (WIDTH+30, random.randint(0, HEIGHT))
        r = random.random()
        if special_unlocked and r < 0.1 and wave >= 8: et = 'boss'
        elif special_unlocked and r < 0.2 and wave >= 10: et = 'teleporter'
        elif r < 0.05 and wave >= 3: et = 'melee'
        elif r < 0.25 and wave >= 5: et = 'sniper'
        elif r < 0.5: et = 'fast'
        else: et = 'normal'
        classEt = {'boss': 200, 'teleporter': 80, 'melee': 50, 'sniper': 60, 'fast': 20, 'normal': 30}[et]
        enemies.append({'x':ex, 'y':ey, 'vx':0, 'vy':0, 'r':24 if et == 'boss' else 16, 'hp':classEt, 'max_hp':classEt, 'type':et, 'shot_timer':0, 'shot_cd':1200 if et != 'boss' else 400, 'detect':400, 'strafe_dir': random.choice([-1,1]), 'strafe_timer':0, 'teleport_timer':0})

while running:
    dt = clock.tick(75)  # 75 FPS
    dt_sec = dt / 1000.0  # Delta time in seconds
    
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if state == "game": paused = not paused
                else: state = "menu"
            elif e.key == pygame.K_SPACE and state == "game" and not paused and 'Dash' in active_cards and player_dash_cooldown <= 0:
                mx, my = pygame.mouse.get_pos()
                dx, dy = mx - cx, my - cy
                dist = math.hypot(dx, dy) or 1
                cx += (dx/dist) * 150; cy += (dy/dist) * 150
                cx = max(cr, min(WIDTH-cr, cx)); cy = max(cr, min(HEIGHT-cr, cy))
                player_dash_cooldown = player_dash_cd_max
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if state == "menu":
                if button_rect.collidepoint(e.pos):
                    state, wave, player_xp, player_level, xp_to_level = "game", 0, 0, 1, 5
                    player_hp, player_max_hp, player_damage = 100, 100, 10
                    player_speed, player_base_speed, player_fire_cooldown = 300, 300, 250
                    player_crit_chance, player_lifesteal_amount, player_armor = 0, 0, 0
                    cx, cy = WIDTH//2, HEIGHT//2
                    enemies.clear(); bullets.clear(); active_cards.clear()
                elif button_quit_rect.collidepoint(e.pos): running = False
            elif state == "cards":
                for i, card in enumerate(card_choices):
                    if pygame.Rect(WIDTH//2 - 450 + i*350, HEIGHT//2-100, 300, 200).collidepoint(e.pos):
                        apply_card(card); state = "game"; break
            elif not paused:
                if player_shot_timer >= player_fire_cooldown:
                    player_shot_timer = 0
                    mx, my = e.pos
                    dxp, dyp = mx - cx, my - cy
                    dist = math.hypot(dxp, dyp) or 1.0
                    bullet_speed = 720  # pixels per second
                    if 'Bulletstorm' in active_cards:
                        for angle_offset in [-0.15, 0, 0.15]:
                            angle = math.atan2(dyp, dxp) + angle_offset
                            bullets.append({'x':cx, 'y':cy, 'vx':math.cos(angle)*bullet_speed, 'vy':math.sin(angle)*bullet_speed, 'r':4, 'owner':'player'})
                    else:
                        bullets.append({'x':cx, 'y':cy, 'vx':(dxp/dist)*bullet_speed, 'vy':(dyp/dist)*bullet_speed, 'r':4, 'owner':'player'})

    screen.fill(BLACK)
    keys = pygame.key.get_pressed()
    moving = any([keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]])
    shooting = pygame.mouse.get_pressed()[0]
    time_scale_target = 1.0 if (moving or shooting) and not paused else MIN_TIME_SCALE if not paused else 0
    time_scale += (time_scale_target - time_scale) * TIME_SLOWDOWN
    scaled_dt_sec = dt_sec * time_scale

    if state == 'menu':
        for btn, text in [(button_rect, "PLAY"), (button2_rect, "Settings"), (button_quit_rect, "QUIT")]:
            pygame.draw.rect(screen, (60,60,60), btn, border_radius=6)
            screen.blit(font.render(text, True, WHITE), font.render(text, True, WHITE).get_rect(center=btn.center))
    elif state == 'cards':
        screen.blit(font.render(f"LEVEL {player_level} - Choose Upgrade", True, WHITE), (WIDTH//2 - font.render(f"LEVEL {player_level} - Choose Upgrade", True, WHITE).get_width()//2, 80))
        for i, card in enumerate(card_choices):
            card_rect = pygame.Rect(WIDTH//2 - 450 + i*350, HEIGHT//2-100, 300, 200)
            is_hovered = card_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(screen, (40,40,60), card_rect, border_radius=10)
            pygame.draw.rect(screen, RARITY_COLORS[card['rarity']] if is_hovered else WHITE, card_rect, 3, border_radius=10)
            screen.blit(small_font.render(card['name'], True, RARITY_COLORS[card['rarity']]), (card_rect.centerx - small_font.render(card['name'], True, YELLOW).get_width()//2, card_rect.top + 60))
            screen.blit(small_font.render(card['desc'], True, WHITE), (card_rect.centerx - small_font.render(card['desc'], True, WHITE).get_width()//2, card_rect.top + 110))
            screen.blit(tiny_font.render(card['rarity'].upper(), True, RARITY_COLORS[card['rarity']]), (card_rect.centerx - tiny_font.render(card['rarity'].upper(), True, RARITY_COLORS[card['rarity']]).get_width()//2, card_rect.top + 150))
    else:
        if not paused:
            dx, dy = (keys[pygame.K_d] - keys[pygame.K_a]) * player_speed * dt_sec, (keys[pygame.K_s] - keys[pygame.K_w]) * player_speed * dt_sec
            cx = max(cr, min(WIDTH-cr, cx+dx)); cy = max(cr, min(HEIGHT-cr, cy+dy))
            spawn_timer += dt; player_shot_timer += dt; player_dash_cooldown = max(0, player_dash_cooldown - dt)

            if len(enemies) == 0 and wave_cooldown <= 0:
                spawn_wave(3 + wave); wave += 1; wave_cooldown = 1200
            wave_cooldown = max(0, wave_cooldown - dt)
            if spawn_timer >= spawn_interval and len(enemies) < max_enemies:
                spawn_timer = 0; spawn_wave(1)

            for b in bullets[:]:
                b['x'] += b['vx'] * scaled_dt_sec
                b['y'] += b['vy'] * scaled_dt_sec
                pygame.draw.circle(screen, CYAN if b['owner'] == 'player' else YELLOW, (int(b['x']), int(b['y'])), b['r'])
                pygame.draw.circle(screen, WHITE, (int(b['x']), int(b['y'])), b['r'], 1)
                if b['x'] < -50 or b['x'] > WIDTH+50 or b['y'] < -50 or b['y'] > HEIGHT+50:
                    try: bullets.remove(b)
                    except: pass
                    continue
                if b['owner'] == 'player':
                    for en in enemies[:]:
                        if math.hypot(en['x']-b['x'], en['y']-b['y']) <= en['r'] + b['r']:
                            is_crit = random.random() < player_crit_chance
                            dmg = player_damage * (2 if is_crit else 1)
                            en['hp'] -= dmg
                            if 'Explosive Rounds' in active_cards:
                                for other in enemies:
                                    if other is not en and math.hypot(other['x']-b['x'], other['y']-b['y']) <= 50:
                                        other['hp'] -= dmg * 0.5
                            try: bullets.remove(b)
                            except: pass
                            if en['hp'] <= 0:
                                try: enemies.remove(en)
                                except: pass
                                player_xp += 1
                                if player_lifesteal_amount > 0 and player_hp < player_max_hp:
                                    player_hp = min(player_max_hp, player_hp + player_lifesteal_amount)
                                if player_xp >= xp_to_level: level_up()
                            break
                else:
                    if math.hypot(cx - b['x'], cy - b['y']) <= cr + b['r']:
                        dmg = max(1, 10 - player_armor)
                        player_hp -= dmg
                        try: bullets.remove(b)
                        except: pass
                        if player_hp <= 0:
                            state, cx, cy, player_hp = 'menu', WIDTH//2, HEIGHT//2, 100
                            enemies.clear(); bullets.clear()
                        break

            for en in enemies[:]:
                en['shot_timer'] += dt; en['strafe_timer'] += dt
                if en['type'] == 'teleporter':
                    en['teleport_timer'] += dt
                    if en['teleport_timer'] > 2000:
                        en['x'], en['y'] = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)
                        en['teleport_timer'] = 0
                dxp, dyp = cx - en['x'], cy - en['y']
                dist = math.hypot(dxp, dyp) or 1.0
                sepx = sepy = 0
                for other in enemies:
                    if other is en: continue
                    ddx, ddy = en['x']-other['x'], en['y']-other['y']
                    ddd = math.hypot(ddx, ddy) or 1.0
                    if ddd < 30: sepx += ddx/ddd; sepy += ddy/ddd
                spd = enemy_speed * (1.5 if en['type'] == 'fast' else 0.8 if en['type'] == 'boss' else 1.0)
                vx_des = (dxp/dist) * spd - 0.5*sepx*50
                vy_des = (dyp/dist) * spd - 0.5*sepy*50
                if dist < 160:
                    perp_x, perp_y = -dyp/dist, dxp/dist
                    if en['strafe_timer'] > 800: en['strafe_dir'] *= -1; en['strafe_timer'] = 0
                    vx_des += perp_x * en['strafe_dir'] * 72
                    vy_des += perp_y * en['strafe_dir'] * 72
                en['x'] += vx_des * scaled_dt_sec
                en['y'] += vy_des * scaled_dt_sec
                ex, ey, size, et = int(en['x']), int(en['y']), en.get('r', 16), en.get('type', 'normal')
                
                if et == 'melee':
                    points = [(ex, ey - size), (ex + size, ey), (ex, ey + size), (ex - size, ey)]
                    pygame.draw.polygon(screen, PINK, points)
                    pygame.draw.polygon(screen, WHITE, points, 2)
                elif et == 'boss':
                    pygame.draw.circle(screen, DARK_RED, (ex, ey), size)
                    pygame.draw.circle(screen, RED, (ex, ey), size, 3)
                    hp_ratio = en['hp'] / en['max_hp']
                    pygame.draw.rect(screen, GRAY, (ex - size, ey - size - 10, size*2, 5))
                    pygame.draw.rect(screen, RED, (ex - size, ey - size - 10, int(size*2*hp_ratio), 5))
                elif et == 'teleporter':
                    for offset in range(3):
                        pygame.draw.circle(screen, PURPLE, (ex, ey), size - offset*3, 2)
                else:
                    points = [(ex, ey - size), (ex - size, ey + size), (ex + size, ey + size)]
                    col = ORANGE if et == 'fast' else PURPLE if et == 'sniper' else RED
                    pygame.draw.polygon(screen, col, points)
                    pygame.draw.polygon(screen, WHITE, points, 2)

                if dist < en['detect'] and en['shot_timer'] >= en['shot_cd']:
                    en['shot_timer'] = 0
                    effective_speed = enemy_bullet_speed * max(time_scale, 0.0001)
                    t_hit = min(2000, dist / effective_speed)
                    lead_x, lead_y = cx + player_vx * t_hit, cy + player_vy * t_hit
                    aimx, aimy = lead_x - en['x'], lead_y - en['y']
                    ad = math.hypot(aimx, aimy) or 1.0
                    if en['type'] == 'boss':
                        for angle_offset in [-0.2, -0.1, 0, 0.1, 0.2]:
                            angle = math.atan2(aimy, aimx) + angle_offset
                            bullets.append({'x':en['x'], 'y':en['y'], 'vx':math.cos(angle)*enemy_bullet_speed, 'vy':math.sin(angle)*enemy_bullet_speed, 'r':5, 'owner':'enemy'})
                    else:
                        bullets.append({'x':en['x'], 'y':en['y'], 'vx':(aimx/ad)*enemy_bullet_speed, 'vy':(aimy/ad)*enemy_bullet_speed, 'r':5, 'owner':'enemy'})

                if dist <= en['r'] + cr:
                    dmg = max(1, 20 - player_armor)
                    player_hp -= dmg
                    try: enemies.remove(en)
                    except: pass
                    if player_hp <= 0:
                        state, cx, cy, player_hp = 'menu', WIDTH//2, HEIGHT//2, 100
                        enemies.clear(); bullets.clear()
                    break

        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - cy, mx - cx)
        px, py = int(cx), int(cy)
        prect = pygame.Rect(px - cr, py - cr, cr*2, cr*2)
        pygame.draw.rect(screen, BLUE, prect, border_radius=6)
        pygame.draw.rect(screen, WHITE, prect, 2, border_radius=6)
        pygame.draw.line(screen, WHITE, (px, py), (px + math.cos(angle) * cr, py + math.sin(angle) * cr), 2)
        
        # HP Bar
        hp_ratio = player_hp / player_max_hp
        pygame.draw.rect(screen, GRAY, (10, 10, 300, 30))
        pygame.draw.rect(screen, GREEN if hp_ratio > 0.3 else RED, (10, 10, int(300 * hp_ratio), 30))
        pygame.draw.rect(screen, WHITE, (10, 10, 300, 30), 2)
        screen.blit(small_font.render(f"{int(player_hp)}/{player_max_hp}", True, WHITE), (15, 15))
        
        screen.blit(tiny_font.render(f"Level {player_level}", True, YELLOW), (10, 50))
        xp_fill = int((player_xp / xp_to_level) * 200)
        pygame.draw.rect(screen, GRAY, (10, 75, 200, 15))
        pygame.draw.rect(screen, CYAN, (10, 75, xp_fill, 15))
        pygame.draw.rect(screen, WHITE, (10, 75, 200, 15), 2)

        if time_scale < 1.0 and not paused:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(int((1.0 - time_scale) * 200))
            overlay.fill((20,20,30))
            screen.blit(overlay, (0,0))
        
        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0,0))
            screen.blit(font.render("PAUSED", True, WHITE), (WIDTH//2 - font.render("PAUSED", True, WHITE).get_width()//2, HEIGHT//2 - 100))
            screen.blit(small_font.render(f"Wave: {wave}", True, YELLOW), (WIDTH//2 - small_font.render(f"Wave: {wave}", True, YELLOW).get_width()//2, HEIGHT//2 - 40))
            screen.blit(tiny_font.render("Press ESC to resume", True, WHITE), (WIDTH//2 - tiny_font.render("Press ESC to resume", True, WHITE).get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()

pygame.quit()