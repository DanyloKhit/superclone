import pygame
import random
import math

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Time Slash (superhot clone)")
font = pygame.font.Font(None, 48)
button_rect = pygame.Rect(WIDTH//2-80, HEIGHT//2-30, 160, 60)
button2_rect = pygame.Rect(WIDTH//2-90, HEIGHT//2+40, 180, 60)
button_quit_rect = pygame.Rect(WIDTH//2-70, HEIGHT//2+110, 140, 50)

state = "menu"
running = True
wave = 0
wave_cooldown = 0
clock = pygame.time.Clock()

cx, cy = WIDTH//2, HEIGHT//2
cr = 20

enemies = []
bullets = []
player_hp = 3
player_vx = player_vy = 0
player_fire_cooldown = 250
player_shot_timer = player_fire_cooldown
enemy_bullet_speed = 8
enemy_speed = 2
TIME_SLOWDOWN = 0.1
MIN_TIME_SCALE = 0.1
time_scale = 1.0

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,50,50)
DARK_RED = (150,0,0)
BLUE = (0,150,255)
CYAN = (0,255,255)
YELLOW = (255,255,0)
ORANGE = (255,165,0)
PURPLE = (200,0,255)
PINK = (255,100,200)

enemy_surfs = {}

spawn_timer = 0.0
spawn_interval = 1500
max_enemies = 10
def spawn_wave(n):
    for _ in range(n):
        side = random.choice([0,1,2,3])
        if side == 0:
            ex = random.randint(0, WIDTH); ey = -30
        elif side == 1:
            ex = random.randint(0, WIDTH); ey = HEIGHT+30
        elif side == 2:
            ex = -30; ey = random.randint(0, HEIGHT)
        else:
            ex = WIDTH+30; ey = random.randint(0, HEIGHT)
        r = random.random()
        if r < 0.05 and wave >= 3:
            et = 'melee'
        elif r < 0.25 and wave >= 5:
            et = 'sniper'
        elif r < 0.5:
            et = 'fast'
        else:
            et = 'normal'

        
        if et == 'melee':
            classEt = 5
        elif et == 'sniper':
            classEt = 6
        elif et == 'fast':
            classEt = 2
        else:
            classEt = 3
        enemies.append({'x':ex, 'y':ey, 'vx':0, 'vy':0, 'r':16, 'hp':classEt, 'type':et, 'shot_timer':0, 'shot_cd':1200, 'detect':400, 'strafe_dir': random.choice([-1,1]), 'strafe_timer':0})

while running:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            state = "menu"
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if state == "menu":
                if button_rect.collidepoint(e.pos):
                    state = "game"
                elif button_quit_rect.collidepoint(e.pos):
                    running = False
            else:
                if player_shot_timer >= player_fire_cooldown:
                    player_shot_timer = 0
                    mx, my = e.pos
                    dxp = mx - cx; dyp = my - cy
                    dist = math.hypot(dxp, dyp) or 1.0
                    bvx = (dxp/dist) * 12; bvy = (dyp/dist) * 12
                    bullets.append({'x':cx, 'y':cy, 'vx':bvx, 'vy':bvy, 'r':4, 'owner':'player'})

    screen.fill((0,0,0))
    keys = pygame.key.get_pressed()
    moving = any([keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]])
    shooting = pygame.mouse.get_pressed()[0]
    if moving or shooting:
        time_scale_target = 1.0
    else:
        time_scale_target = MIN_TIME_SCALE

    time_scale += (time_scale_target - time_scale) * TIME_SLOWDOWN
    scaled_dt = dt * time_scale

    if state == 'menu':
        pygame.draw.rect(screen, (60,60,60), button_rect, border_radius=6)
        play_surf = font.render("PLAY", True, (255,255,255))
        screen.blit(play_surf, play_surf.get_rect(center=button_rect.center))
        pygame.draw.rect(screen, (60,60,60), button2_rect, border_radius=6)
        settings_surf = font.render("Settings", True, (255,255,255))
        screen.blit(settings_surf, settings_surf.get_rect(center=button2_rect.center))
        pygame.draw.rect(screen, (60,60,60), button_quit_rect, border_radius=6)
        quit_surf = font.render("QUIT", True, (255,255,255))
        screen.blit(quit_surf, quit_surf.get_rect(center=button_quit_rect.center))
    else:
        speed = 5
        dx = dy = 0
        if keys[pygame.K_w]: dy -= speed
        if keys[pygame.K_s]: dy += speed
        if keys[pygame.K_a]: dx -= speed
        if keys[pygame.K_d]: dx += speed
        cx += dx
        cy += dy
        cx = max(cr, min(WIDTH-cr, cx))
        cy = max(cr, min(HEIGHT-cr, cy))

        spawn_timer += scaled_dt
        player_shot_timer += dt

        if len(enemies) == 0 and wave_cooldown <= 0:
            spawn_wave(3 + wave)
            wave += 1
            wave_cooldown = 1200
        wave_cooldown = max(0, wave_cooldown - dt)

        if spawn_timer >= spawn_interval and len(enemies) < max_enemies:
            spawn_timer = 0
            spawn_wave(1)

        for b in bullets[:]:
            b['x'] += b['vx'] * time_scale
            b['y'] += b['vy'] * time_scale
            if b['owner'] == 'player':
                pygame.draw.circle(screen, CYAN, (int(b['x']), int(b['y'])), b['r'])
                pygame.draw.circle(screen, WHITE, (int(b['x']), int(b['y'])), b['r'], 1)
            else:
                pygame.draw.circle(screen, YELLOW, (int(b['x']), int(b['y'])), b['r'])
                pygame.draw.circle(screen, WHITE, (int(b['x']), int(b['y'])), b['r'], 1)
            if b['x'] < -50 or b['x'] > WIDTH+50 or b['y'] < -50 or b['y'] > HEIGHT+50:
                try: bullets.remove(b)
                except: pass
                continue
            if b['owner'] == 'player':
                for en in enemies[:]:
                    if math.hypot(en['x']-b['x'], en['y']-b['y']) <= en['r'] + b['r']:
                        en['hp'] -= 1
                        try: bullets.remove(b)
                        except: pass
                        if en['hp'] <= 0:
                            try: enemies.remove(en)
                            except: pass
                        break
            else:
                if math.hypot(cx - b['x'], cy - b['y']) <= cr + b['r']:
                    player_hp -= 1
                    try: bullets.remove(b)
                    except: pass
                    if player_hp <= 0:
                        state = 'menu'
                        cx, cy = WIDTH//2, HEIGHT//2
                        enemies.clear(); bullets.clear(); player_hp = 3
                    break

        for en in enemies[:]:
            en['shot_timer'] += scaled_dt
            en['strafe_timer'] += scaled_dt
            dxp = cx - en['x']; dyp = cy - en['y']
            dist = math.hypot(dxp, dyp) or 1.0
            sepx = sepy = 0
            for other in enemies:
                if other is en: continue
                ddx = en['x'] - other['x']; ddy = en['y'] - other['y']
                ddd = math.hypot(ddx, ddy) or 1.0
                if ddd < 30:
                    sepx += ddx/ddd; sepy += ddy/ddd
            vx_des = (dxp/dist) * enemy_speed - 0.5*sepx
            vy_des = (dyp/dist) * enemy_speed - 0.5*sepy
            if dist < 160:
                perp_x = -dyp/dist; perp_y = dxp/dist
                if en['strafe_timer'] > 800:
                    en['strafe_dir'] *= -1; en['strafe_timer'] = 0
                vx_des += perp_x * en['strafe_dir'] * 1.2
                vy_des += perp_y * en['strafe_dir'] * 1.2
            en['x'] += vx_des * time_scale
            en['y'] += vy_des * time_scale
            surf = enemy_surfs.get(en.get('type','normal'))
            ex = int(en['x']); ey = int(en['y'])
            size = en.get('r', 16)
            et = en.get('type', 'normal')
            if et == 'melee':
                points = [(ex, ey - size), (ex + size, ey), (ex, ey + size), (ex - size, ey)]
                pygame.draw.polygon(screen, PINK if et == 'melee' else RED, points)
                pygame.draw.polygon(screen, WHITE, points, 2)
            else:
                points = [(ex, ey - size), (ex - size, ey + size), (ex + size, ey + size)]
                col = RED
                if et == 'fast': col = ORANGE
                elif et == 'sniper': col = PURPLE
                pygame.draw.polygon(screen, col, points)
                pygame.draw.polygon(screen, WHITE, points, 2)

            if dist < en['detect']:
                if en['shot_timer'] >= en['shot_cd']:
                    en['shot_timer'] = 0
                    effective_speed = enemy_bullet_speed * max(time_scale, 0.0001)
                    t_hit = min(2000, dist / effective_speed)
                    lead_x = cx + player_vx * t_hit
                    lead_y = cy + player_vy * t_hit
                    aimx = lead_x - en['x']; aimy = lead_y - en['y']
                    ad = math.hypot(aimx, aimy) or 1.0
                    bvx = (aimx/ad) * enemy_bullet_speed; bvy = (aimy/ad) * enemy_bullet_speed
                    bullets.append({'x':en['x'], 'y':en['y'], 'vx':bvx, 'vy':bvy, 'r':5, 'owner':'enemy'})

            if dist <= en['r'] + cr:
                player_hp -= 1
                try: enemies.remove(en)
                except: pass
                if player_hp <= 0:
                    state = 'menu'
                    cx, cy = WIDTH//2, HEIGHT//2
                    enemies.clear(); bullets.clear(); player_hp = 3
                break

        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - cy, mx - cx)
        px = int(cx); py = int(cy)
        prect = pygame.Rect(px - cr, py - cr, cr*2, cr*2)
        pygame.draw.rect(screen, BLUE, prect, border_radius=6)
        pygame.draw.rect(screen, WHITE, prect, 2, border_radius=6)
        end_x = px + math.cos(angle) * (cr)
        end_y = py + math.sin(angle) * (cr)
        pygame.draw.line(screen, WHITE, (px, py), (end_x, end_y), 2)
        hp_s = font.render(f"HP: {player_hp}", True, (255,255,255))
        screen.blit(hp_s, (10,10))

        if time_scale < 1.0:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            alpha = int((1.0 - time_scale) * 200)
            overlay.set_alpha(alpha)
            overlay.fill((20,20,30))
            screen.blit(overlay, (0,0))

    pygame.display.flip()

pygame.quit()

