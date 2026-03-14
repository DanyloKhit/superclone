
import socket, threading, json, time, math, random, sys

HOST = '0.0.0.0'
PORT = 5055
W, H = 1280, 720
TICK = 1 / 60

RARITY_W = {'common':50,'uncommon':30,'rare':15}
TEAM_CARDS = [
    {'name':'Health Boost','type':'max_hp','value':20,'rarity':'common'},
    {'name':'Heavy Shot','type':'damage','value':4,'rarity':'common'},
    {'name':'Rapid Fire','type':'fire_rate','value':-0.18,'rarity':'common'},
    {'name':'Speed Demon','type':'speed','value':0.12,'rarity':'uncommon'},
    {'name':'Armor Plating','type':'armor','value':4,'rarity':'uncommon'},
    {'name':'Bulletstorm','type':'multishot','value':1,'rarity':'rare'},
]

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def vec_norm(x, y):
    d = math.hypot(x, y) or 1.0
    return x / d, y / d

def make_player(i):
    x = W * (0.35 if i == 0 else 0.65)
    return {
        'id': i,
        'name': f'P{i+1}',
        'x': x,
        'y': H * 0.5,
        'hp': 100,
        'max_hp': 100,
        'damage': 10,
        'speed': 290,
        'fire_cd': 0.25,
        'shot_t': 0.25,
        'armor': 0,
        'respawn': 0.0,
        'active': False,
        'touch_t': 0.0,
        'color': [55,130,255] if i == 0 else [255,120,60],
        'multishot': False,
    }

players = [make_player(0), make_player(1)]
clients = [None, None]
inputs = [
    {'u':False,'d':False,'l':False,'r':False,'shoot':False,'ax':1.0,'ay':0.0},
    {'u':False,'d':False,'l':False,'r':False,'shoot':False,'ax':-1.0,'ay':0.0},
]
enemies = []
bullets = []
particles = []
active_cards = []
last_card = ''
state = 'waiting'
wave = 0
wave_timer = 2.5
wave_need = 0
wave_done = 0
wave_spawned = 0
spawn_timer = 0.0
team_xp = 0.0
team_level = 1
xp_to_level = 5
team_wipe_timer = 0.0
running = True
lock = threading.Lock()

def active_count():
    return sum(1 for p in players if p['active'])

def alive_players():
    return [p for p in players if p['active'] and p['hp'] > 0]

def living_team():
    return any(p['active'] and p['hp'] > 0 for p in players)

def reset_run():
    global state, wave, wave_timer, wave_need, wave_done, wave_spawned, spawn_timer
    global team_xp, team_level, xp_to_level, team_wipe_timer, last_card
    for i, p in enumerate(players):
        base = make_player(i)
        p.update(base)
        p['active'] = clients[i] is not None
    enemies.clear()
    bullets.clear()
    particles.clear()
    active_cards.clear()
    last_card = ''
    state = 'between'
    wave = 0
    wave_timer = 2.5
    wave_need = 0
    wave_done = 0
    wave_spawned = 0
    spawn_timer = 0.0
    team_xp = 0.0
    team_level = 1
    xp_to_level = 5
    team_wipe_timer = 0.0

def apply_card(card):
    global last_card
    last_card = card['name']
    active_cards.append(card['name'])
    for p in players:
        if not p['active']:
            continue
        t, v = card['type'], card['value']
        if t == 'max_hp':
            p['max_hp'] += v
            p['hp'] = min(p['max_hp'], p['hp'] + v)
        elif t == 'damage':
            p['damage'] += v
        elif t == 'fire_rate':
            p['fire_cd'] = max(0.09, p['fire_cd'] * (1 + v))
        elif t == 'speed':
            p['speed'] = int(p['speed'] * (1 + v))
        elif t == 'armor':
            p['armor'] += v
        elif t == 'multishot':
            p['multishot'] = True

def level_up():
    global team_level, team_xp, xp_to_level
    team_level += 1
    team_xp -= xp_to_level
    xp_to_level += 2
    choices = random.sample(TEAM_CARDS, k=min(3, len(TEAM_CARDS)))
    weights = [RARITY_W[c['rarity']] for c in choices]
    apply_card(random.choices(choices, weights=weights, k=1)[0])

def enemy_quota(wn):
    return 8 + wn * 3

def remaining_spawns():
    return max(0, wave_need - wave_spawned)

def active_enemy_cap():
    return min(4 + wave // 2, 12)

def enemy_color(et):
    return {
        'normal': (255,70,70),
        'fast': (255,145,0),
        'sniper': (180,0,255),
        'melee': (255,75,185),
        'splitter': (90,200,255),
        'boss': (160,20,20),
    }[et]

def spawn_enemy():
    global wave_spawned
    edge = random.randint(0, 3)
    if edge == 0:
        ex, ey = random.randint(0, W), -28
    elif edge == 1:
        ex, ey = random.randint(0, W), H + 28
    elif edge == 2:
        ex, ey = -28, random.randint(0, H)
    else:
        ex, ey = W + 28, random.randint(0, H)
    pool = ['normal'] * 8 + ['fast'] * 4 + ['melee'] * 3
    if wave >= 3:
        pool += ['sniper'] * 2
    if wave >= 4:
        pool += ['splitter'] * 2
    if wave and wave % 5 == 0 and wave_spawned == 0:
        et = 'boss'
    else:
        et = random.choice(pool)
    base_hp = {'normal':32,'fast':24,'sniper':58,'melee':52,'splitter':42,'boss':220}[et]
    rad = {'normal':16,'fast':14,'sniper':15,'melee':16,'splitter':19,'boss':26}[et]
    shot_cd = {'normal':1.35,'fast':1.55,'sniper':1.95,'melee':99,'splitter':1.55,'boss':0.65}[et]
    detect = {'normal':420,'fast':440,'sniper':560,'melee':240,'splitter':440,'boss':650}[et]
    scale = 1.0 + max(0, wave - 8) * 0.08
    hp = int(base_hp * scale)
    enemies.append({
        'x': float(ex),
        'y': float(ey),
        'r': rad,
        'hp': hp,
        'max_hp': hp,
        'type': et,
        'shot_t': random.random() * shot_cd,
        'shot_cd': shot_cd,
        'detect': detect,
        'strafe_dir': random.choice([-1, 1]),
        'strafe_t': 0.0,
        'touch_t': 0.0,
    })
    wave_spawned += 1

def refill_wave(force=False):
    missing = min(max(0, active_enemy_cap() - len(enemies)), remaining_spawns())
    if force and not enemies and remaining_spawns() > 0:
        missing = max(1, missing)
    for _ in range(missing):
        spawn_enemy()

def pick_target(en):
    targets = alive_players()
    if not targets:
        return None
    return min(targets, key=lambda p: (p['x'] - en['x']) ** 2 + (p['y'] - en['y']) ** 2)

def kill_enemy(en):
    global wave_done, team_xp, wave_need, wave_spawned
    if en not in enemies:
        return
    enemies.remove(en)
    for _ in range(8):
        particles.append({
            'x': en['x'],
            'y': en['y'],
            'vx': random.uniform(-90, 90),
            'vy': random.uniform(-90, 90),
            'life': 0.45,
            'max_life': 0.45,
            'color': enemy_color(en['type']),
        })
    if en['type'] == 'splitter' and len(enemies) < 14:
        for _ in range(2):
            a = random.uniform(0, math.pi * 2)
            enemies.append({
                'x': en['x'] + math.cos(a) * 28,
                'y': en['y'] + math.sin(a) * 28,
                'r': 11,
                'hp': 16,
                'max_hp': 16,
                'type': 'fast',
                'shot_t': 0.0,
                'shot_cd': 1.55,
                'detect': 430,
                'strafe_dir': random.choice([-1, 1]),
                'strafe_t': 0.0,
                'touch_t': 0.0,
            })
            wave_need += 1
            wave_spawned += 1
    wave_done += 1
    team_xp += 1.0
    while team_xp >= xp_to_level:
        level_up()

def fire_player_bullet(p, ax, ay):
    nx, ny = vec_norm(ax, ay)
    spd = 720
    if p['multishot']:
        base = math.atan2(ny, nx)
        for off in (-0.14, 0.0, 0.14):
            a = base + off
            bullets.append({'x':p['x'],'y':p['y'],'vx':math.cos(a)*spd,'vy':math.sin(a)*spd,'r':4,'owner':p['id']})
    else:
        bullets.append({'x':p['x'],'y':p['y'],'vx':nx*spd,'vy':ny*spd,'r':4,'owner':p['id']})

def fire_enemy_bullet(en, tx, ty, spread=0.0, speed=430, radius=5):
    dx, dy = tx - en['x'], ty - en['y']
    a = math.atan2(dy, dx) + random.uniform(-spread, spread)
    bullets.append({'x':en['x'],'y':en['y'],'vx':math.cos(a)*speed,'vy':math.sin(a)*speed,'r':radius,'owner':'enemy'})

def update_players(dt):
    global team_wipe_timer
    for i, p in enumerate(players):
        if not p['active']:
            continue
        p['shot_t'] += dt
        p['touch_t'] = max(0.0, p['touch_t'] - dt)
        if p['respawn'] > 0:
            p['respawn'] = max(0.0, p['respawn'] - dt)
            if p['respawn'] == 0 and living_team():
                p['hp'] = p['max_hp']
                p['x'] = W * (0.35 if i == 0 else 0.65)
                p['y'] = H * 0.5
            continue
        inp = inputs[i]
        mvx = (1 if inp['r'] else 0) - (1 if inp['l'] else 0)
        mvy = (1 if inp['d'] else 0) - (1 if inp['u'] else 0)
        if mvx or mvy:
            nx, ny = vec_norm(mvx, mvy)
            p['x'] = clamp(p['x'] + nx * p['speed'] * dt, 20, W - 20)
            p['y'] = clamp(p['y'] + ny * p['speed'] * dt, 20, H - 20)
        if inp['shoot'] and p['shot_t'] >= p['fire_cd']:
            p['shot_t'] = 0.0
            fire_player_bullet(p, inp['ax'], inp['ay'])
    if active_count() == 2 and not living_team():
        team_wipe_timer += dt
        if team_wipe_timer > 2.0:
            reset_run()
    else:
        team_wipe_timer = 0.0

def update_wave(dt):
    global state, wave, wave_timer, wave_need, wave_done, wave_spawned, spawn_timer
    if active_count() < 2:
        state = 'waiting'
        return
    if state == 'waiting':
        reset_run()
    if state == 'between':
        wave_timer -= dt
        if wave_timer <= 0:
            wave += 1
            wave_need = enemy_quota(wave)
            wave_done = 0
            wave_spawned = 0
            spawn_timer = 0.0
            state = 'starting'
            wave_timer = 1.2
            refill_wave(True)
    elif state == 'starting':
        wave_timer -= dt
        if wave_timer <= 0:
            state = 'active'
    elif state == 'active':
        if wave_done >= wave_need:
            state = 'complete'
            wave_timer = 3.0
            for p in players:
                if p['active'] and p['hp'] > 0:
                    p['hp'] = min(p['max_hp'], p['hp'] + 12)
        else:
            spawn_timer += dt
            if not enemies and remaining_spawns() > 0:
                refill_wave(True)
                spawn_timer = 0.0
            elif spawn_timer >= 1.15 and remaining_spawns() > 0:
                spawn_timer = 0.0
                refill_wave(False)
    elif state == 'complete':
        wave_timer -= dt
        if wave_timer <= 0:
            state = 'between'
            wave_timer = 3.5
            enemies.clear()
            bullets[:] = [b for b in bullets if b['owner'] != 'enemy']

def update_enemies(dt):
    for en in enemies[:]:
        en['shot_t'] += dt
        en['strafe_t'] += dt
        en['touch_t'] = max(0.0, en['touch_t'] - dt)
        target = pick_target(en)
        if not target:
            continue
        dx = target['x'] - en['x']
        dy = target['y'] - en['y']
        dist = math.hypot(dx, dy) or 1.0
        sx = sy = 0.0
        for oth in enemies:
            if oth is en:
                continue
            ddx = en['x'] - oth['x']
            ddy = en['y'] - oth['y']
            ddd = math.hypot(ddx, ddy) or 1.0
            min_sep = en['r'] + oth['r'] + 7
            if ddd < min_sep:
                push = (min_sep - ddd) / min_sep
                sx += (ddx / ddd) * push * 1.35
                sy += (ddy / ddd) * push * 1.35
        px = -dy / dist
        py = dx / dist
        if en['strafe_t'] > (0.6 if en['type'] == 'fast' else 1.0):
            en['strafe_dir'] *= -1
            en['strafe_t'] = 0.0
        speed_mult = {'normal':1.0,'fast':1.42,'sniper':0.82,'melee':1.35,'splitter':1.12,'boss':0.76}[en['type']]
        keep_min = {'normal':110,'fast':60,'sniper':265,'melee':0,'splitter':95,'boss':180}[en['type']]
        keep_max = {'normal':230,'fast':155,'sniper':420,'melee':90,'splitter':205,'boss':310}[en['type']]
        strafe = {'normal':0.45,'fast':0.72,'sniper':0.65,'melee':0.0,'splitter':0.58,'boss':0.24}[en['type']]
        mx = my = 0.0
        if dist > keep_max:
            mx += dx / dist
            my += dy / dist
        elif dist < keep_min:
            mx -= dx / dist * (1.25 if en['type'] == 'sniper' else 0.65)
            my -= dy / dist * (1.25 if en['type'] == 'sniper' else 0.65)
        else:
            mx += px * en['strafe_dir'] * strafe
            my += py * en['strafe_dir'] * strafe
        mx -= sx * 0.34
        my -= sy * 0.34
        spd = 120 * speed_mult
        en['x'] = clamp(en['x'] + mx * spd * dt, -50, W + 50)
        en['y'] = clamp(en['y'] + my * spd * dt, -50, H + 50)
        if dist <= en['r'] + 19 and en['touch_t'] <= 0:
            dmg = {'melee':15,'boss':22}.get(en['type'], 10)
            target['hp'] -= max(1, dmg - target['armor'])
            en['touch_t'] = 0.55 if en['type'] != 'boss' else 0.4
            if target['hp'] <= 0:
                target['hp'] = 0
                target['respawn'] = 3.0
        if dist < en['detect'] and en['shot_t'] >= en['shot_cd'] and en['type'] not in ('melee',):
            en['shot_t'] = 0.0
            if en['type'] == 'boss':
                base = math.atan2(dy, dx)
                for off in (-0.22,-0.11,0.0,0.11,0.22):
                    a = base + off
                    bullets.append({'x':en['x'],'y':en['y'],'vx':math.cos(a)*510,'vy':math.sin(a)*510,'r':5,'owner':'enemy'})
            elif en['type'] == 'splitter':
                fire_enemy_bullet(en, target['x'], target['y'], 0.08, 450, 5)
                fire_enemy_bullet(en, target['x'], target['y'], -0.08, 450, 5)
            elif en['type'] == 'sniper':
                fire_enemy_bullet(en, target['x'], target['y'], 0.04, 590, 6)
            else:
                fire_enemy_bullet(en, target['x'], target['y'], 0.08, 430 if en['type'] != 'fast' else 460, 5)

def update_bullets(dt):
    for b in bullets[:]:
        b['x'] += b['vx'] * dt
        b['y'] += b['vy'] * dt
        if not (-80 < b['x'] < W + 80 and -80 < b['y'] < H + 80):
            bullets.remove(b)
            continue
        if b['owner'] == 'enemy':
            for p in players:
                if not p['active'] or p['hp'] <= 0:
                    continue
                if math.hypot(p['x'] - b['x'], p['y'] - b['y']) <= 20 + b['r']:
                    p['hp'] -= max(1, 10 - p['armor'])
                    bullets.remove(b)
                    if p['hp'] <= 0:
                        p['hp'] = 0
                        p['respawn'] = 3.0
                    break
        else:
            owner = players[b['owner']]
            for en in enemies[:]:
                if math.hypot(en['x'] - b['x'], en['y'] - b['y']) <= en['r'] + b['r']:
                    en['hp'] -= owner['damage']
                    bullets.remove(b)
                    if en['hp'] <= 0:
                        kill_enemy(en)
                    break

def update_particles(dt):
    for p in particles[:]:
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['life'] -= dt
        if p['life'] <= 0:
            particles.remove(p)

def build_snapshot():
    return {
        't': 'state',
        'world': [W, H],
        'mode': state,
        'wave': wave,
        'wave_need': wave_need,
        'wave_done': wave_done,
        'wave_timer': round(wave_timer, 2),
        'team_level': team_level,
        'team_xp': round(team_xp, 2),
        'xp_to_level': xp_to_level,
        'last_card': last_card,
        'active_cards': active_cards[-6:],
        'players': [
            {
                'id': p['id'],
                'name': p['name'],
                'x': round(p['x'], 1),
                'y': round(p['y'], 1),
                'hp': int(p['hp']),
                'max_hp': int(p['max_hp']),
                'respawn': round(p['respawn'], 2),
                'active': p['active'],
                'color': p['color'],
            } for p in players
        ],
        'enemies': [
            {
                'x': round(en['x'], 1),
                'y': round(en['y'], 1),
                'r': en['r'],
                'hp': int(en['hp']),
                'max_hp': int(en['max_hp']),
                'type': en['type'],
            } for en in enemies
        ],
        'bullets': [
            {
                'x': round(b['x'], 1),
                'y': round(b['y'], 1),
                'r': b['r'],
                'owner': b['owner'],
            } for b in bullets
        ],
        'particles': [
            {
                'x': round(p['x'], 1),
                'y': round(p['y'], 1),
                'life': round(p['life'], 2),
                'max_life': round(p['max_life'], 2),
                'color': p['color'],
            } for p in particles
        ],
        'connected': active_count(),
    }

def send_json(conn, obj):
    data = (json.dumps(obj, separators=(',', ':')) + '\n').encode()
    conn.sendall(data)

def drop_client(slot):
    conn = clients[slot]
    clients[slot] = None
    players[slot]['active'] = False
    inputs[slot] = {'u':False,'d':False,'l':False,'r':False,'shoot':False,'ax':1.0 if slot == 0 else -1.0,'ay':0.0}
    if conn:
        try:
            conn.close()
        except:
            pass

def client_thread(conn, slot):
    buf = b''
    try:
        send_json(conn, {'t':'hello','id':slot,'world':[W,H],'port':PORT})
        while running:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                if not line:
                    continue
                msg = json.loads(line.decode())
                if msg.get('t') == 'input':
                    inputs[slot] = {
                        'u': bool(msg.get('u')),
                        'd': bool(msg.get('d')),
                        'l': bool(msg.get('l')),
                        'r': bool(msg.get('r')),
                        'shoot': bool(msg.get('shoot')),
                        'ax': float(msg.get('ax', 1.0)),
                        'ay': float(msg.get('ay', 0.0)),
                    }
    except:
        pass
    finally:
        with lock:
            drop_client(slot)

def accept_loop(sock):
    while running:
        try:
            conn, addr = sock.accept()
        except:
            break
        with lock:
            slot = None
            for i in range(2):
                if clients[i] is None:
                    slot = i
                    break
            if slot is None:
                try:
                    send_json(conn, {'t':'full'})
                    conn.close()
                except:
                    pass
                continue
            clients[slot] = conn
            players[slot]['active'] = True
        threading.Thread(target=client_thread, args=(conn, slot), daemon=True).start()

def game_loop(sock):
    global running
    last = time.time()
    send_acc = 0.0
    while running:
        now = time.time()
        dt = min(0.05, now - last)
        last = now
        with lock:
            update_players(dt)
            update_wave(dt)
            if state != 'waiting':
                update_enemies(dt)
                update_bullets(dt)
                update_particles(dt)
            snap = build_snapshot()
            send_targets = [(i, c) for i, c in enumerate(clients) if c is not None]
        send_acc += dt
        if send_acc >= 1 / 20:
            send_acc = 0.0
            dead = []
            for slot, conn in send_targets:
                try:
                    payload = dict(snap)
                    payload['pid'] = slot
                    send_json(conn, payload)
                except:
                    dead.append(slot)
            if dead:
                with lock:
                    for slot in dead:
                        drop_client(slot)
        sleep_left = TICK - (time.time() - now)
        if sleep_left > 0:
            time.sleep(sleep_left)
    try:
        sock.close()
    except:
        pass

def main():
    global PORT
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except:
            pass
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen()
    print(f'LAN co-op server running on port {PORT}')
    print('Open this on two devices with the client file using the server IP.')
    threading.Thread(target=accept_loop, args=(sock,), daemon=True).start()
    try:
        game_loop(sock)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
