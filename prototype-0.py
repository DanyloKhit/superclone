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

state = "menu"  # or 'game'
clock = pygame.time.Clock()

cx, cy = WIDTH//2, HEIGHT//2
cr = 20

#early stage prototype of enemies
enemies = []
spawn_interval = 1500  # ms
last_spawn = pygame.time.get_ticks()
enemy_speed = 2.2   
# bullets (both player and enemy)
bullets = []  # dicts: {x,y,vx,vy,r,owner}
player_hp = 3
player_vx = player_vy = 0
player_fire_cooldown = 250
last_player_shot = 0
enemy_bullet_speed = 8

running = True
while running:
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
                # shooting by player toward mouse
                nowt = pygame.time.get_ticks()
                if nowt - last_player_shot >= player_fire_cooldown:
                    last_player_shot = nowt
                    mx, my = e.pos
                    dxp = mx - cx; dyp = my - cy
                    dist = math.hypot(dxp, dyp) or 1.0
                    bvx = (dxp/dist) * 12; bvy = (dyp/dist) * 12
                    bullets.append({'x':cx, 'y':cy, 'vx':bvx, 'vy':bvy, 'r':4, 'owner':'player'})

    screen.fill((0, 0, 0))
    if state == "menu":
        pygame.draw.rect(screen, (60, 60, 60), button_rect, border_radius=6)
        play_surf = font.render("PLAY", True, (255, 255, 255))
        screen.blit(play_surf, play_surf.get_rect(center=button_rect.center))

        pygame.draw.rect(screen, (60, 60, 60), button2_rect, border_radius=6)
        settings_surf = font.render("Settings", True, (255, 255, 255))
        screen.blit(settings_surf, settings_surf.get_rect(center=button2_rect.center))

        pygame.draw.rect(screen, (60, 60, 60), button_quit_rect, border_radius=6)
        quit_surf = font.render("QUIT", True, (255, 255, 255))
        screen.blit(quit_surf, quit_surf.get_rect(center=button_quit_rect.center))
    else:
            keys = pygame.key.get_pressed()
            speed = 5
            dx = dy = 0
            if keys[pygame.K_w]: dy -= speed
            if keys[pygame.K_s]: dy += speed
            if keys[pygame.K_a]: dx -= speed
            if keys[pygame.K_d]: dx += speed
            cx += dx; cy += dy
            cx = max(cr, min(WIDTH - cr, cx))
            cy = max(cr, min(HEIGHT - cr, cy))

            now = pygame.time.get_ticks()
            if now - last_spawn >= spawn_interval:
                last_spawn = now
                side = random.choice([0,1,2,3])
                if side == 0: ex = random.randint(cr, WIDTH-cr); ey = -20
                elif side == 1: ex = random.randint(cr, WIDTH-cr); ey = HEIGHT+20
                elif side == 2: ex = -20; ey = random.randint(cr, HEIGHT-cr)
                else: ex = WIDTH+20; ey = random.randint(cr, HEIGHT-cr)
                dxp = cx - ex; dyp = cy - ey
                dist = math.hypot(dxp, dyp) or 1.0
                enemies.append({'x':ex, 'y':ey, 'vx': enemy_speed * dxp/dist, 'vy': enemy_speed * dyp/dist, 'r':16,
                                'hp':2, 'last_shot':0, 'shot_cd':1200, 'detect':400,
                                'strafe_dir': random.choice([-1,1]), 'last_strafe': now})

            # update bullets
            for b in bullets[:]:
                b['x'] += b['vx']; b['y'] += b['vy']
                pygame.draw.circle(screen, (255,220,120) if b['owner']=='player' else (255,120,120), (int(b['x']), int(b['y'])), b['r'])
                # off-screen
                if b['x'] < -50 or b['x'] > WIDTH+50 or b['y'] < -50 or b['y'] > HEIGHT+50:
                    bullets.remove(b)
                    continue
                if b['owner']=='player':
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
                    # enemy bullet hits player
                    if math.hypot(cx - b['x'], cy - b['y']) <= cr + b['r']:
                        player_hp -= 1
                        try: bullets.remove(b)
                        except: pass
                        if player_hp <= 0:
                            state = "menu"
                            cx, cy = WIDTH//2, HEIGHT//2
                            enemies.clear(); bullets.clear(); player_hp = 3
                        break

            # update enemies with basic AI
            for en in enemies[:]:
                # steer: move toward player, but strafe when close
                dxp = cx - en['x']; dyp = cy - en['y']
                dist = math.hypot(dxp, dyp) or 1.0
                # simple separation from other enemies
                sepx = sepy = 0
                for other in enemies:
                    if other is en: continue
                    ddx = en['x'] - other['x']; ddy = en['y'] - other['y']
                    ddd = math.hypot(ddx, ddy) or 1.0
                    if ddd < 30:
                        sepx += ddx/ddd; sepy += ddy/ddd
                # desired velocity
                vx_des = (dxp/dist) * enemy_speed - 0.5*sepx
                vy_des = (dyp/dist) * enemy_speed - 0.5*sepy
                # if close, add strafe
                if dist < 160:
                    # perpendicular vector
                    perp_x = -dyp/dist; perp_y = dxp/dist
                    # change strafe occasionally
                    if pygame.time.get_ticks() - en['last_strafe'] > 800:
                        en['strafe_dir'] *= -1; en['last_strafe'] = pygame.time.get_ticks()
                    vx_des += perp_x * en['strafe_dir'] * 1.2
                    vy_des += perp_y * en['strafe_dir'] * 1.2
                en['x'] += vx_des; en['y'] += vy_des
                pygame.draw.circle(screen, (180, 20, 20), (int(en['x']), int(en['y'])), en['r'])

                # shooting: if player in detect radius and cooldown
                if dist < en['detect']:
                    nowt = pygame.time.get_ticks()
                    if nowt - en['last_shot'] >= en['shot_cd']:
                        en['last_shot'] = nowt
                        # predictive aim: lead target based on player's velocity
                        t_hit = dist / enemy_bullet_speed
                        lead_x = cx + player_vx * t_hit
                        lead_y = cy + player_vy * t_hit
                        aimx = lead_x - en['x']; aimy = lead_y - en['y']
                        ad = math.hypot(aimx, aimy) or 1.0
                        bvx = (aimx/ad) * enemy_bullet_speed; bvy = (aimy/ad) * enemy_bullet_speed
                        bullets.append({'x':en['x'], 'y':en['y'], 'vx':bvx, 'vy':bvy, 'r':5, 'owner':'enemy'})

                # collision with player (touch)
                if dist <= en['r'] + cr:
                    player_hp -= 1
                    enemies.remove(en)
                    if player_hp <= 0:
                        state = "menu"
                        cx, cy = WIDTH//2, HEIGHT//2
                        enemies.clear(); bullets.clear(); player_hp = 3
                        break

            pygame.draw.circle(screen, (200, 40, 40), (int(cx), int(cy)), cr)
            # draw HUD: HP
            hp_s = font.render(f"HP: {player_hp}", True, (255,255,255))
            screen.blit(hp_s, (10,10))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
