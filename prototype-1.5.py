import pygame, random, math

pygame.init()
info = pygame.display.Info()
W, H = info.current_w, info.current_h
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
pygame.display.set_caption("Time Slash")
clock = pygame.time.Clock()

f_xl = pygame.font.Font(None, 90)
f_lg = pygame.font.Font(None, 58)
f_md = pygame.font.Font(None, 38)
f_sm = pygame.font.Font(None, 28)
f_xs = pygame.font.Font(None, 22)

WHITE  = (255,255,255); BLACK = (0,0,0);    GRAY  = (85,88,100)
DGRAY  = (20,22,30);    RED   = (255,55,55); DRED  = (130,0,0)
BLUE   = (55,130,255);  CYAN  = (0,215,255); YELLOW= (255,210,0)
ORANGE = (255,140,0);   PURPLE= (185,0,255); PINK  = (255,75,185)
GREEN  = (35,255,115);  GOLD  = (255,200,0); LBLUE = (90,200,255)
DPUR   = (55,0,110);    TEAL  = (0,200,180)

RARITY_COL = {'common':WHITE,'uncommon':GREEN,'rare':BLUE,'epic':PURPLE,'legendary':GOLD}
RARITY_W   = {'common':50,'uncommon':30,'rare':15,'epic':4,'legendary':1}

CARDS = [
    {'name':'Rapid Fire',      'desc':'-30% Fire Cooldown',     'type':'fire_rate',  'value':-0.3,        'rarity':'common',    'unlock_wave':0},
    {'name':'Heavy Shot',      'desc':'+5 Bullet Damage',       'type':'damage',     'value':5,           'rarity':'common',    'unlock_wave':0},
    {'name':'Health Boost',    'desc':'+20 Max HP',             'type':'max_hp',     'value':20,          'rarity':'common',    'unlock_wave':0},
    {'name':'Speed Demon',     'desc':'+30% Move Speed',        'type':'speed',      'value':0.3,         'rarity':'uncommon',  'unlock_wave':0},
    {'name':'Life Steal',      'desc':'+4 HP per Kill',         'type':'lifesteal',  'value':4,           'rarity':'uncommon',  'unlock_wave':0},
    {'name':'Critical Strike', 'desc':'+20% Crit Chance',       'type':'crit',       'value':0.2,         'rarity':'uncommon',  'unlock_wave':0},
    {'name':'XP Boost',        'desc':'+50% XP Gain',           'type':'xp_mult',    'value':0.5,         'rarity':'uncommon',  'unlock_wave':0},
    {'name':'Lucky Draw',      'desc':'Rare/Epic/Leg +Chance',  'type':'luck',       'value':1,           'rarity':'uncommon',  'unlock_wave':0},
    {'name':'Bulletstorm',     'desc':'Triple Shot',             'type':'multishot',  'value':3,           'rarity':'rare',      'unlock_wave':0},
    {'name':'Tank Mode',       'desc':'+40 HP, -15% Speed',     'type':'tank',       'value':[40,-0.15],  'rarity':'rare',      'unlock_wave':0},
    {'name':'Sniper',          'desc':'+150% Dmg, +40% CD',     'type':'sniper',     'value':[1.5,0.4],   'rarity':'rare',      'unlock_wave':0},
    {'name':'Armor Plating',   'desc':'+15 Armor',              'type':'armor',      'value':15,          'rarity':'rare',      'unlock_wave':0},
    {'name':'Explosive Rounds','desc':'AOE Blast on Hit',       'type':'explosive',  'value':1,           'rarity':'epic',      'unlock_wave':0},
    {'name':'Shockwave',       'desc':'[R] 200px AOE Burst',    'type':'shockwave',  'value':1,           'rarity':'epic',      'unlock_wave':15},
    {'name':'Bullet Time',     'desc':'Min Time -5% (stack)',   'type':'bullet_time','value':-0.05,       'rarity':'epic',      'unlock_wave':15},
    {'name':'Overdrive',       'desc':'+60% Dmg, -20% Speed',   'type':'overdrive',  'value':[0.6,-0.2],  'rarity':'epic',      'unlock_wave':20},
    {'name':'Glass Cannon',    'desc':'x3 Dmg, -50% Max HP',    'type':'glasscannon','value':[3.0,-0.5],  'rarity':'legendary', 'unlock_wave':25},
    {'name':'TIME BREAKER',    'desc':'Unlock Boss & Specials', 'type':'special',    'value':1,           'rarity':'legendary', 'unlock_wave':0},
]

state        = 'menu'
paused       = False
enemies      = []
bullets      = []
particles    = []
active_cards = []
card_choices = []

cx = cy = 0
player_hp = player_max_hp = 100
player_damage = 10
player_base_speed = player_speed = 300
player_fire_cooldown = 250
player_shot_timer    = 250
player_xp = 0; player_level = 1; xp_to_level = 5
player_crit_chance = player_lifesteal_amount = player_armor = 0
player_xp_multiplier = 1.0
player_shockwave_cooldown = 0; player_shockwave_cd_max = 3000
player_luck = 0
special_unlocked = False
MIN_TIME_SCALE = 0.1
time_scale = 1.0

wave = 0
wave_phase         = 'between'
wave_timer         = 3000
wave_kills_needed  = 0
wave_kills_done    = 0
wave_total_spawned = 0
spawn_timer        = 0

slow_shot_count = 0


menu_orbs = []
for _i in range(55):
    menu_orbs.append({
        'x':   random.uniform(0, W),
        'y':   random.uniform(0, H),
        'vx':  random.uniform(-22, 22),
        'vy':  random.uniform(-14, 14),
        'r':   random.uniform(1.5, 4.0),
        'col': random.choice([CYAN, BLUE, PURPLE, (0,170,210), (110,0,190), (0,90,150)]),
        'phase': random.uniform(0, math.pi*2),
    })

def txt(surf, text, fnt, col, px, py, shadow=True):
    if shadow:
        s = fnt.render(text, True, (0,0,0))
        surf.blit(s, s.get_rect(center=(px+2, py+2)))
    s = fnt.render(text, True, col)
    surf.blit(s, s.get_rect(center=(px, py)))

def bar(x, y, w, h, ratio, col, bg=GRAY):
    pygame.draw.rect(screen, bg, (x,y,w,h))
    pygame.draw.rect(screen, col, (x,y,int(w*max(0,min(1,ratio))),h))
    pygame.draw.rect(screen, WHITE, (x,y,w,h), 2)

def overlay(alpha, col=(0,0,0)):
    s = pygame.Surface((W,H), pygame.SRCALPHA)
    s.fill((*col, alpha))
    screen.blit(s, (0,0))

def wave_quota(wn):
    return 10 + wn * 3

def enemy_base_col(et):
    return {'boss':DRED,'teleporter':PURPLE,'phantom':DPUR,
            'splitter':LBLUE,'melee':PINK,'sniper':PURPLE,
            'fast':ORANGE,'normal':RED}.get(et, RED)

def create_particles(x, y, col, n=8):
    for _ in range(n):
        a  = random.uniform(0, math.pi*2)
        sp = random.uniform(60, 190)
        particles.append({'x':x,'y':y,'vx':math.cos(a)*sp,'vy':math.sin(a)*sp,
                          'life':0.55,'max_life':0.55,'color':col})

def spawn_enemy():
    global wave_total_spawned
    if wave_total_spawned >= wave_kills_needed: return
    side = random.randrange(4)
    if   side==0: ex,ey = random.randint(0,W), -38
    elif side==1: ex,ey = random.randint(0,W), H+38
    elif side==2: ex,ey = -38, random.randint(0,H)
    else:         ex,ey = W+38, random.randint(0,H)
    r = random.random()
    if   special_unlocked and r<0.08 and wave>=8:  et='boss'
    elif special_unlocked and r<0.16 and wave>=10: et='teleporter'
    elif r<0.07 and wave>=8:                        et='phantom'
    elif r<0.13 and wave>=7:                        et='splitter'
    elif r<0.18 and wave>=3:                        et='melee'
    elif r<0.32 and wave>=5:                        et='sniper'
    elif r<0.56:                                    et='fast'
    else:                                           et='normal'
    base_hp = {'boss':200,'teleporter':80,'phantom':50,'splitter':40,
               'melee':50,'sniper':60,'fast':22,'normal':32}[et]
    rad = {'boss':24,'splitter':20,'phantom':17,'melee':16,
           'normal':16,'fast':14,'sniper':15,'teleporter':16}[et]
    scd = {'boss':450,'sniper':1800,'teleporter':1500,'phantom':99999,
           'normal':1400,'fast':1600,'melee':99999,'splitter':1400}[et]
    # Late-game HP scaling after wave 10
    scale  = 1.0 + max(0, wave-10) * 0.07
    hp     = int(base_hp * scale)
    enemies.append({'x':ex,'y':ey,'r':rad,'hp':hp,'max_hp':hp,'type':et,
                    'shot_timer':0,'shot_cd':scd,'detect':420,
                    'strafe_dir':random.choice([-1,1]),'strafe_timer':0,
                    'teleport_timer':0,'phase_timer':0,'phased':False})
    wave_total_spawned += 1

def kill_enemy(en):
    global player_hp, player_xp, wave_kills_done, wave_kills_needed, wave_total_spawned
    try: enemies.remove(en)
    except: pass
    create_particles(en['x'], en['y'], enemy_base_col(en['type']), 10)
    if en['type']=='splitter' and en['r']>13 and len(enemies)<11:
        new_children = []
        for _ in range(2):
            a = random.uniform(0, math.pi*2)
            child = {'x':en['x']+math.cos(a)*34, 'y':en['y']+math.sin(a)*34,
                     'r':11, 'hp':15, 'max_hp':15, 'type':'fast',
                     'shot_timer':0, 'shot_cd':1400, 'detect':420,
                     'strafe_dir':random.choice([-1,1]), 'strafe_timer':0,
                     'teleport_timer':0, 'phase_timer':0, 'phased':False}
            new_children.append(child)
        enemies.extend(new_children)
        wave_kills_needed += len(new_children)
        wave_total_spawned += len(new_children)
    player_xp += int(1 * player_xp_multiplier)
    if player_lifesteal_amount:
        player_hp = min(player_max_hp, player_hp + player_lifesteal_amount)
    wave_kills_done += 1
    if player_xp >= xp_to_level: level_up()

def level_up():
    global player_level, player_xp, xp_to_level, state, card_choices
    player_level += 1; player_xp -= xp_to_level; xp_to_level += 2
    avail = [c for c in CARDS
             if (c['name'] not in active_cards or
                 c['type'] in ('lifesteal','damage','max_hp','crit','armor','xp_mult','luck'))
             and c['unlock_wave'] <= wave]
    if not avail: avail = CARDS[:]
    lm = {'common':1.0,'uncommon':1.0,
          'rare':   1 + player_luck*0.6,
          'epic':   1 + player_luck*1.4,
          'legendary': 1 + player_luck*3.0}
    wts = [RARITY_W[c['rarity']] * lm[c['rarity']] for c in avail]
    card_choices = random.choices(avail, weights=wts, k=min(3, len(avail)))
    state = 'cards'

def apply_card(card):
    global player_max_hp,player_hp,player_fire_cooldown,player_damage
    global player_speed,player_base_speed,player_crit_chance
    global player_lifesteal_amount,player_armor,special_unlocked
    global player_xp_multiplier,MIN_TIME_SCALE,player_luck
    active_cards.append(card['name'])
    t, v = card['type'], card['value']
    if   t=='fire_rate':   player_fire_cooldown = int(player_fire_cooldown*(1+v))
    elif t=='damage':      player_damage += v
    elif t=='max_hp':      player_max_hp += v; player_hp += v
    elif t=='speed':       player_base_speed = int(player_base_speed*(1+v)); player_speed = player_base_speed
    elif t=='lifesteal':   player_lifesteal_amount += v
    elif t=='tank':        player_max_hp+=v[0]; player_hp+=v[0]; player_base_speed=int(player_base_speed*(1+v[1])); player_speed=player_base_speed
    elif t=='sniper':      player_damage=int(player_damage*(1+v[0])); player_fire_cooldown=int(player_fire_cooldown*(1+v[1]))
    elif t=='crit':        player_crit_chance += v
    elif t=='armor':       player_armor += v
    elif t=='special':     special_unlocked = True
    elif t=='xp_mult':     player_xp_multiplier += v
    elif t=='bullet_time': MIN_TIME_SCALE += v
    elif t=='luck':        player_luck += 1
    elif t=='overdrive':   player_damage=int(player_damage*(1+v[0])); player_base_speed=int(player_base_speed*(1+v[1])); player_speed=player_base_speed
    elif t=='glasscannon': player_damage=int(player_damage*v[0]); cut=int(player_max_hp*abs(v[1])); player_max_hp=max(1,player_max_hp-cut); player_hp=min(player_hp,player_max_hp)

def shockwave_attack():
    global player_shockwave_cooldown
    if player_shockwave_cooldown > 0: return
    player_shockwave_cooldown = player_shockwave_cd_max
    create_particles(cx, cy, CYAN, 22)
    for en in enemies[:]:
        if not en.get('phased') and math.hypot(en['x']-cx, en['y']-cy) < 220:
            en['hp'] -= player_damage * 3
            if en['hp'] <= 0: kill_enemy(en)

def fire_bullet():
    """Called only on MOUSEBUTTONDOWN. Returns True if shot was fired."""
    global player_shot_timer, slow_shot_count
    if player_shot_timer < player_fire_cooldown: return False
    player_shot_timer = 0

    if time_scale < 0.5:
        slow_shot_count += 1
    mx, my = pygame.mouse.get_pos()
    dx, dy = mx-cx, my-cy
    dist = math.hypot(dx, dy) or 1
    spd = 720
    if 'Bulletstorm' in active_cards:
        for off in (-0.16, 0, 0.16):
            a = math.atan2(dy,dx) + off
            bullets.append({'x':cx,'y':cy,'vx':math.cos(a)*spd,'vy':math.sin(a)*spd,'r':4,'owner':'player'})
    else:
        bullets.append({'x':cx,'y':cy,'vx':(dx/dist)*spd,'vy':(dy/dist)*spd,'r':4,'owner':'player'})
    return True

def reset_game():
    global cx,cy,player_hp,player_max_hp,player_damage,player_speed,player_base_speed
    global player_fire_cooldown,player_shot_timer,player_xp,player_level,xp_to_level
    global player_crit_chance,player_lifesteal_amount,player_armor,player_xp_multiplier
    global player_shockwave_cooldown,special_unlocked,MIN_TIME_SCALE,time_scale,player_luck
    global wave,wave_phase,wave_timer,wave_kills_needed,wave_kills_done,wave_total_spawned
    global spawn_timer,slow_shot_count
    cx, cy = W//2, H//2
    player_hp=player_max_hp=100; player_damage=10
    player_base_speed=player_speed=300
    player_fire_cooldown=250; player_shot_timer=250
    player_xp=0; player_level=1; xp_to_level=5
    player_crit_chance=player_lifesteal_amount=player_armor=0
    player_xp_multiplier=1.0; player_shockwave_cooldown=0; player_luck=0
    special_unlocked=False; MIN_TIME_SCALE=0.1; time_scale=1.0
    wave=0; wave_phase='between'; wave_timer=3000
    wave_kills_needed=wave_kills_done=wave_total_spawned=spawn_timer=slow_shot_count=0
    active_cards.clear(); enemies.clear(); bullets.clear(); particles.clear()

def draw_enemy(en):
    ex,ey,r,et = int(en['x']),int(en['y']),en['r'],en['type']
    if et=='boss':
        pygame.draw.circle(screen,DRED,(ex,ey),r)
        pygame.draw.circle(screen,RED,(ex,ey),r,3)
        hp_r = en['hp']/en['max_hp']
        pygame.draw.rect(screen,GRAY,(ex-r,ey-r-12,r*2,6))
        pygame.draw.rect(screen,RED if hp_r<0.35 else YELLOW if hp_r<0.65 else GREEN,(ex-r,ey-r-12,int(r*2*hp_r),6))
    elif et=='teleporter':
        for off in range(3): pygame.draw.circle(screen,PURPLE,(ex,ey),r-off*3,2)
        pygame.draw.circle(screen,PURPLE,(ex,ey),4)
    elif et=='phantom':
        alpha = 65 if en.get('phased') else 210
        surf = pygame.Surface((r*2+6,r*2+6), pygame.SRCALPHA)
        pygame.draw.circle(surf,(*DPUR,alpha),(r+3,r+3),r)
        pygame.draw.circle(surf,(*TEAL,alpha),(r+3,r+3),r,2)
        if not en.get('phased'):
            pygame.draw.circle(surf,(*PURPLE,255),(r-4,r-4),3)
            pygame.draw.circle(surf,(*PURPLE,255),(r+4,r-4),3)
        screen.blit(surf,(ex-r-3,ey-r-3))
        return
    elif et=='splitter':
        pts=[(ex+r*math.cos(math.radians(60*i)),ey+r*math.sin(math.radians(60*i))) for i in range(6)]
        pygame.draw.polygon(screen,LBLUE,pts); pygame.draw.polygon(screen,WHITE,pts,2)
    elif et=='melee':
        pts=[(ex,ey-r),(ex+r,ey),(ex,ey+r),(ex-r,ey)]
        pygame.draw.polygon(screen,PINK,pts); pygame.draw.polygon(screen,WHITE,pts,2)
    else:
        col = ORANGE if et=='fast' else PURPLE if et=='sniper' else RED
        pts = [(ex,ey-r),(ex-r,ey+r),(ex+r,ey+r)]
        pygame.draw.polygon(screen,col,pts); pygame.draw.polygon(screen,WHITE,pts,2)

def draw_hud():
    hp_r = max(0, player_hp/player_max_hp)
    bar(12,H-54,260,28, hp_r, GREEN if hp_r>0.5 else YELLOW if hp_r>0.25 else RED)
    txt(screen,f'{int(player_hp)}/{player_max_hp}',f_xs,WHITE,142,H-40,False)
    bar(12,H-88,200,14, player_xp/max(1,xp_to_level), CYAN, (40,40,55))
    pygame.draw.rect(screen,WHITE,(12,H-88,200,14),1)
    txt(screen,f'LV {player_level}',f_xs,YELLOW,56,H-110,False)
    if player_luck:
        txt(screen,f'LUCK x{player_luck}',f_xs,GOLD,56,H-125,False)
    if 'Shockwave' in active_cards:
        cd_r = 1-(player_shockwave_cooldown/player_shockwave_cd_max)
        bar(12,H-116,140,12, cd_r, GREEN if cd_r>=1 else CYAN,(40,40,55))
        pygame.draw.rect(screen,WHITE,(12,H-116,140,12),1)
        txt(screen,'[R] Shockwave',f_xs,WHITE,68,H-128,False)
    # Wave info (top-right)
    if wave_phase=='active':
        txt(screen,f'WAVE {wave}',f_md,CYAN,W-170,18)
        txt(screen,f'{wave_kills_done} / {wave_kills_needed} kills',f_sm,WHITE,W-170,46)
        bar(W-310,62,200,8, wave_kills_done/max(1,wave_kills_needed),CYAN,(40,40,55))
        pygame.draw.rect(screen,WHITE,(W-310,62,200,8),1)
    elif wave_phase=='between':
        secs = math.ceil(wave_timer/1000)
        txt(screen,f'WAVE {wave+1}  IN  {secs}s',f_md,YELLOW,W-175,22)
        txt(screen,'Prepare!',f_sm,(180,200,255),W-175,52)
    elif wave_phase=='complete':
        secs = math.ceil(wave_timer/1000)
        txt(screen,f'WAVE {wave} CLEAR!',f_md,GREEN,W-170,22)
        txt(screen,f'Next in {secs}s',f_sm,YELLOW,W-170,52)
    elif wave_phase=='starting':
        txt(screen,f'WAVE {wave}',f_md,CYAN,W-170,22)
        txt(screen,f'{wave_kills_needed} enemies',f_sm,(180,200,255),W-170,52)
    if time_scale < 0.85:
        txt(screen,f'BULLET TIME  {time_scale:.0%}',f_xs,(100,170,255),100,18,False)
menu_time = 0.0

def draw_menu_bg():
    """Animated background: scrolling grid + floating orbs + connection lines."""
    global menu_time
    menu_time += clock.get_time() / 1000.0

    screen.fill(DGRAY)
    offset = (menu_time * 18) % 64
    for gx in range(int(-offset), W+64, 64):
        pygame.draw.line(screen,(28,32,46),(gx,0),(gx,H))
    for gy in range(int(-offset), H+64, 64):
        pygame.draw.line(screen,(28,32,46),(0,gy),(W,gy))

    for bx,by,br,bc in [((W//4,H//3,260,(0,20,55))),((W*3//4,H*2//3,200,(28,0,55))),
                         ((W//2,H//6,150,(0,15,40)))]:
        s = pygame.Surface((br*2,br*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*bc,120), (br,br), br)
        screen.blit(s,(bx-br,by-br))

    dt_s = clock.get_time()/1000.0
    for o in menu_orbs:
        o['x'] = (o['x'] + o['vx']*dt_s) % W
        o['y'] = (o['y'] + o['vy']*dt_s) % H
        o['phase'] += dt_s * 1.4
        alpha = int(140 + 80*math.sin(o['phase']))
        r = int(o['r'] + 1.5*math.sin(o['phase']*0.7))
        s = pygame.Surface((r*2+2,r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*o['col'], alpha), (r+1,r+1), r)
        screen.blit(s, (int(o['x'])-r, int(o['y'])-r))

    for i,a in enumerate(menu_orbs):
        for b in menu_orbs[i+1:]:
            d = math.hypot(a['x']-b['x'], a['y']-b['y'])
            if d < 130:
                alpha = int(55*(1-d/130))
                pygame.draw.line(screen, (60,90,130), (int(a['x']),int(a['y'])),
                                 (int(b['x']),int(b['y'])), 1)

MENU_BTNS = [('PLAY', BLUE), ('SETTINGS', (55,58,75)), ('QUIT', (130,20,20))]

def get_menu_rect(i):
    bw, bh = 340, 68
    return pygame.Rect(W//2-bw//2, H//2-20+i*(bh+16), bw, bh)

def draw_menu():
    draw_menu_bg()
    txt(screen,'TIME  SLASH', f_xl, CYAN, W//2, H//2-200)
    mx, my = pygame.mouse.get_pos()
    for i,(label,col) in enumerate(MENU_BTNS):
        r   = get_menu_rect(i)
        hov = r.collidepoint(mx,my)
        pygame.draw.rect(screen, tuple(min(255,c+45) for c in col) if hov else col, r, border_radius=14)
        if hov: pygame.draw.rect(screen,WHITE,r,2,border_radius=14)
        txt(screen,label,f_md,WHITE,r.centerx,r.centery)
    txt(screen,'WASD Move  |  Click Shoot  |  Still = Bullet Time  |  R = Shockwave  |  ESC Pause',
        f_xs,(100,110,130),W//2,H-30)

# ── card screen ───────────────────────────────────────────────────────────
def card_rect(i):
    return pygame.Rect(W//2-480+i*370, H//2-115+30, 310, 230)

def draw_cards():
    screen.fill(DGRAY)
    for gx in range(0,W,64): pygame.draw.line(screen,(28,30,42),(gx,0),(gx,H))
    for gy in range(0,H,64): pygame.draw.line(screen,(28,30,42),(0,gy),(W,gy))
    txt(screen,f'LEVEL {player_level}  —  Choose Upgrade',f_lg,WHITE,W//2,H//2-195)
    if player_luck:
        txt(screen,f'Lucky Draw x{player_luck} — boosting rarer cards',f_xs,GOLD,W//2,H//2-160)
    mx,my = pygame.mouse.get_pos()
    for i,card in enumerate(card_choices):
        cr  = card_rect(i)
        hov = cr.collidepoint(mx,my)
        rc  = RARITY_COL[card['rarity']]
        pygame.draw.rect(screen,(32,34,52),cr,border_radius=14)
        pygame.draw.rect(screen, rc if hov else (70,75,100), cr,3,border_radius=14)
        if hov:
            s=pygame.Surface((cr.width,cr.height),pygame.SRCALPHA)
            s.fill((*rc[:3],18)); screen.blit(s,(cr.x,cr.y))
        txt(screen,card['name'],    f_md,rc,    cr.centerx,cr.top+60)
        txt(screen,card['desc'],    f_sm,WHITE, cr.centerx,cr.top+110)
        txt(screen,card['rarity'].upper(),f_xs,rc,cr.centerx,cr.top+165)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
running = True
while running:
    dt     = clock.tick(75)
    dt_sec = dt / 1000.0

    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if state=='game': paused = not paused
                elif state != 'cards': running = False
            elif e.key==pygame.K_r and state=='game' and not paused and 'Shockwave' in active_cards:
                shockwave_attack()

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if state == 'menu':
                for i,_ in enumerate(MENU_BTNS):
                    if get_menu_rect(i).collidepoint(e.pos):
                        if i==0: reset_game(); state='game'
                        elif i==2: running=False
            elif state == 'cards':
                for i,card in enumerate(card_choices):
                    if card_rect(i).collidepoint(e.pos):
                        apply_card(card); state='game'; break
            elif state == 'game' and not paused:
                # CLICK-ONLY shooting — no hold-to-fire
                fire_bullet()

    # ── quick exits for non-game states ─────────────────────────────────
    if state == 'menu':  draw_menu();  pygame.display.flip(); continue
    if state == 'cards': draw_cards(); pygame.display.flip(); continue

    # ── Time scale logic ─────────────────────────────────────────────────
    keys   = pygame.key.get_pressed()
    moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]

    # When moving, reset the slow-shot counter (new "slow session" next time)
    if moving: slow_shot_count = 0

    # Time target:
    #   Moving                       → full speed (1.0)
    #   Still, 0 shots fired slow    → bullet time (MIN_TIME_SCALE)
    #   Still, shot once while slow  → still bullet time (1st shot grace)
    #   Still, shot ≥2 while slow    → full speed (old behavior resumes)
    if paused:
        ts_target = time_scale                    # freeze
    elif moving:
        ts_target = 1.0
    elif slow_shot_count >= 2:
        ts_target = 1.0                           # 2nd+ shot in slow → resumes time
    else:
        ts_target = MIN_TIME_SCALE                # still slow (0 or 1 shots)

    time_scale      += (ts_target - time_scale) * 0.18
    scaled_dt_sec    = dt_sec * time_scale
    scaled_dt_ms     = dt    * time_scale

    # ── Background ───────────────────────────────────────────────────────
    screen.fill(DGRAY)
    for gx in range(0,W,64): pygame.draw.line(screen,(25,27,38),(gx,0),(gx,H))
    for gy in range(0,H,64): pygame.draw.line(screen,(25,27,38),(0,gy),(W,gy))

    if not paused:
        # ── Player movement ──────────────────────────────────────────────
        cx = max(20,min(W-20, cx + (keys[pygame.K_d]-keys[pygame.K_a])*player_speed*scaled_dt_sec))
        cy = max(20,min(H-20, cy + (keys[pygame.K_s]-keys[pygame.K_w])*player_speed*scaled_dt_sec))
        player_shot_timer         += dt
        player_shockwave_cooldown  = max(0, player_shockwave_cooldown - dt)

        # ── Wave logic ───────────────────────────────────────────────────
        if wave_phase == 'between':
            wave_timer -= dt
            if wave_timer <= 0:
                wave += 1; wave_kills_needed = wave_quota(wave)
                wave_kills_done = wave_total_spawned = spawn_timer = 0
                wave_phase = 'starting'; wave_timer = 1400
                for _ in range(min(3+wave//2, 7)): spawn_enemy()
        elif wave_phase == 'starting':
            wave_timer -= dt
            if wave_timer <= 0: wave_phase = 'active'
        elif wave_phase == 'active':
            if wave_kills_done >= wave_kills_needed:
                wave_phase = 'complete'; wave_timer = 3500
            else:
                spawn_timer += dt
                if spawn_timer>=1800 and len(enemies)<10 and wave_total_spawned<wave_kills_needed:
                    spawn_timer = 0; spawn_enemy()
        elif wave_phase == 'complete':
            wave_timer -= dt
            if wave_timer <= 0:
                wave_phase = 'between'; wave_timer = 4000
                enemies.clear(); bullets.clear()

        # ── Bullets ──────────────────────────────────────────────────────
        for b in bullets[:]:
            b['x'] += b['vx']*scaled_dt_sec
            b['y'] += b['vy']*scaled_dt_sec
            pygame.draw.circle(screen, CYAN if b['owner']=='player' else YELLOW,
                               (int(b['x']),int(b['y'])), b['r'])
            pygame.draw.circle(screen, WHITE, (int(b['x']),int(b['y'])), b['r'], 1)
            if not (-60<b['x']<W+60 and -60<b['y']<H+60):
                try: bullets.remove(b)
                except: pass
                continue
            if b['owner'] == 'player':
                for en in enemies[:]:
                    if en.get('phased'): continue
                    if math.hypot(en['x']-b['x'], en['y']-b['y']) <= en['r']+b['r']:
                        is_crit = random.random() < player_crit_chance
                        dmg     = player_damage * (2 if is_crit else 1)
                        en['hp'] -= dmg
                        if 'Explosive Rounds' in active_cards:
                            for oth in enemies:
                                if oth is not en and not oth.get('phased') and math.hypot(oth['x']-b['x'],oth['y']-b['y'])<=55:
                                    oth['hp'] -= dmg*0.5
                        try: bullets.remove(b)
                        except: pass
                        if en['hp'] <= 0: kill_enemy(en)
                        break
            else:
                if math.hypot(cx-b['x'], cy-b['y']) <= 20+b['r']:
                    player_hp -= max(1, 10-player_armor)
                    try: bullets.remove(b)
                    except: pass
                    if player_hp <= 0: reset_game(); state='menu'
                    break

        # ── Enemies ──────────────────────────────────────────────────────
        for en in enemies[:]:
            # shot/strafe timers scale with time → enemies fire slowly in bullet time
            en['shot_timer']   += scaled_dt_ms
            en['strafe_timer'] += scaled_dt_ms

            # Phantom phasing (real dt so it cycles independently of time scale)
            if en['type'] == 'phantom':
                en['phase_timer'] += dt
                if not en['phased'] and en['phase_timer'] > 3800:
                    en['phased'] = True; en['phase_timer'] = 0
                    a = random.uniform(0, math.pi*2)
                    en['x'] = cx+math.cos(a)*175; en['y'] = cy+math.sin(a)*175
                elif en['phased'] and en['phase_timer'] > 1400:
                    en['phased'] = False; en['phase_timer'] = 0

            if en['type'] == 'teleporter':
                en['teleport_timer'] += dt
                if en['teleport_timer'] > 2400:
                    en['x'],en['y'] = random.randint(80,W-80),random.randint(80,H-80)
                    en['teleport_timer'] = 0

            dxe,dye  = cx-en['x'], cy-en['y']
            dist_e   = math.hypot(dxe,dye) or 1
            sx = sy  = 0
            for oth in enemies:
                if oth is en: continue
                ddx,ddy = en['x']-oth['x'], en['y']-oth['y']
                ddd = math.hypot(ddx,ddy) or 1
                if ddd < 34: sx+=ddx/ddd; sy+=ddy/ddd
            spd_m = {'fast':1.6,'boss':0.75,'splitter':1.25,
                     'phantom': 2.1 if en.get('phased') else 1.0,
                     'melee':1.15,'sniper':0.8,'teleporter':0.9,'normal':1.0}.get(en['type'],1.0)
            spd  = 118 * spd_m
            vxd  = (dxe/dist_e)*spd - sx*42
            vyd  = (dye/dist_e)*spd - sy*42
            if dist_e < 175:
                px_,py_ = -dye/dist_e, dxe/dist_e
                if en['strafe_timer'] > 950: en['strafe_dir'] *= -1; en['strafe_timer'] = 0
                vxd += px_*en['strafe_dir']*68; vyd += py_*en['strafe_dir']*68
            en['x'] += vxd*scaled_dt_sec; en['y'] += vyd*scaled_dt_sec
            draw_enemy(en)


            if (dist_e < en['detect'] and en['shot_timer'] >= en['shot_cd']
                    and not en.get('phased') and en['type'] not in ('melee','splitter')):
                en['shot_timer'] = 0; bspd = 450
                if en['type'] == 'boss':
                    for aoff in (-0.22,-0.11,0,0.11,0.22):
                        a = math.atan2(dye,dxe)+aoff
                        bullets.append({'x':en['x'],'y':en['y'],'vx':math.cos(a)*bspd,'vy':math.sin(a)*bspd,'r':5,'owner':'enemy'})
                else:
                    bullets.append({'x':en['x'],'y':en['y'],'vx':(dxe/dist_e)*bspd,'vy':(dye/dist_e)*bspd,'r':5,'owner':'enemy'})

            if dist_e <= en['r']+20:
                player_hp -= max(1,22-player_armor)
                try:
                    kill_enemy(en)
                except Exception:
                    try: enemies.remove(en)
                    except: pass
                if player_hp <= 0: reset_game(); state='menu'
                break

        for p in particles[:]:
            p['x'] += p['vx']*dt_sec; p['y'] += p['vy']*dt_sec; p['life'] -= dt_sec
            if p['life'] <= 0: particles.remove(p); continue
            a_ = p['life']/p['max_life']
            pygame.draw.circle(screen,p['color'],(int(p['x']),int(p['y'])),max(1,int(a_*5)))

    mx,my = pygame.mouse.get_pos()
    ang   = math.atan2(my-cy, mx-cx)
    pr    = pygame.Rect(cx-18,cy-18,36,36)
    pygame.draw.rect(screen,BLUE,pr,border_radius=6)
    pygame.draw.rect(screen,WHITE,pr,2,border_radius=6)
    pygame.draw.line(screen,WHITE,(int(cx),int(cy)),(int(cx+math.cos(ang)*18),int(cy+math.sin(ang)*18)),2)

    if time_scale < 0.85 and not paused:
        overlay(int((1-time_scale)*165),(12,12,28))

    if wave_phase == 'starting':
        overlay(155,(0,0,0))
        txt(screen,f'— WAVE  {wave} —',     f_xl,CYAN,W//2,H//2-45)
        txt(screen,f'{wave_kills_needed} enemies to defeat',f_md,(170,210,255),W//2,H//2+40)

    draw_hud()

    if paused:
        overlay(185,(0,0,0))
        txt(screen,'PAUSED',                               f_lg,WHITE, W//2,H//2-90)
        txt(screen,f'Wave {wave}  |  Level {player_level}',f_md,YELLOW,W//2,H//2-28)
        txt(screen,f'{wave_kills_done}/{wave_kills_needed} kills this wave',f_sm,(180,200,220),W//2,H//2+28)
        txt(screen,'ESC to resume',                        f_sm,(120,125,135),W//2,H//2+85)

    pygame.display.flip()

pygame.quit()