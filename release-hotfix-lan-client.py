
import pygame, socket, threading, json, math, sys, time

pygame.init()
info = pygame.display.Info()
SW, SH = info.current_w, info.current_h
screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN)
pygame.display.set_caption('Time Slash LAN Client')
clock = pygame.time.Clock()

f_xl = pygame.font.Font(None, 92)
f_lg = pygame.font.Font(None, 58)
f_md = pygame.font.Font(None, 36)
f_sm = pygame.font.Font(None, 26)
f_xs = pygame.font.Font(None, 22)

WHITE=(255,255,255)
BLACK=(0,0,0)
DGRAY=(20,22,30)
GRAY=(75,78,95)
CYAN=(0,215,255)
BLUE=(55,130,255)
ORANGE=(255,145,0)
PURPLE=(185,0,255)
PINK=(255,75,185)
RED=(255,70,70)
GREEN=(35,255,115)
YELLOW=(255,210,0)
LBLUE=(90,200,255)
DRED=(140,20,20)

server_ip = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5055

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server_ip, server_port))
sock.setblocking(True)

state = None
my_id = None
world_w, world_h = 1280, 720
connected = True
state_lock = threading.Lock()

def txt(text, font, color, x, y, shadow=True):
    if shadow:
        s = font.render(text, True, BLACK)
        screen.blit(s, s.get_rect(center=(x + 2, y + 2)))
    s = font.render(text, True, color)
    screen.blit(s, s.get_rect(center=(x, y)))

def send_json(obj):
    try:
        sock.sendall((json.dumps(obj, separators=(',', ':')) + '\n').encode())
    except:
        pass

def recv_loop():
    global state, my_id, connected, world_w, world_h
    buf = b''
    try:
        while connected:
            data = sock.recv(65536)
            if not data:
                break
            buf += data
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                if not line:
                    continue
                msg = json.loads(line.decode())
                if msg.get('t') == 'hello':
                    my_id = msg.get('id')
                    world_w, world_h = msg.get('world', [1280, 720])
                elif msg.get('t') == 'state':
                    with state_lock:
                        state = msg
                        my_id = msg.get('pid', my_id)
                        world_w, world_h = msg.get('world', [world_w, world_h])
                elif msg.get('t') == 'full':
                    connected = False
                    break
    except:
        pass
    connected = False

threading.Thread(target=recv_loop, daemon=True).start()

def sx(v):
    return int(v * SW / world_w)

def sy(v):
    return int(v * SH / world_h)

def draw_bar(x, y, w, h, ratio, col, bg=GRAY):
    pygame.draw.rect(screen, bg, (x, y, w, h))
    pygame.draw.rect(screen, col, (x, y, int(w * max(0, min(1, ratio))), h))
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 2)

def enemy_color(et):
    return {
        'normal': RED,
        'fast': ORANGE,
        'sniper': PURPLE,
        'melee': PINK,
        'splitter': LBLUE,
        'boss': DRED,
    }.get(et, RED)

def draw_enemy(en):
    ex, ey, r, et = sx(en['x']), sy(en['y']), max(6, sx(en['r'])), en['type']
    if et == 'boss':
        pygame.draw.circle(screen, DRED, (ex, ey), r)
        pygame.draw.circle(screen, RED, (ex, ey), r, 3)
    elif et == 'splitter':
        pts = [(ex + r * math.cos(math.radians(60 * i)), ey + r * math.sin(math.radians(60 * i))) for i in range(6)]
        pygame.draw.polygon(screen, LBLUE, pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)
    elif et == 'melee':
        pts = [(ex, ey - r), (ex + r, ey), (ex, ey + r), (ex - r, ey)]
        pygame.draw.polygon(screen, PINK, pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)
    else:
        col = enemy_color(et)
        pts = [(ex, ey - r), (ex - r, ey + r), (ex + r, ey + r)]
        pygame.draw.polygon(screen, col, pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)

def draw_player(p):
    px, py = sx(p['x']), sy(p['y'])
    rect = pygame.Rect(px - 18, py - 18, 36, 36)
    col = tuple(p['color'])
    pygame.draw.rect(screen, col, rect, border_radius=6)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=6)
    txt(p['name'], f_xs, WHITE, px, py - 28, False)
    if p['respawn'] > 0 or p['hp'] <= 0:
        txt(f"RESPAWN {max(1, math.ceil(p['respawn']))}", f_xs, YELLOW, px, py + 34, False)

running = True
while running and connected:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

    with state_lock:
        snap = dict(state) if state else None

    screen.fill(DGRAY)
    for gx in range(0, world_w + 1, 64):
        pygame.draw.line(screen, (28, 30, 42), (sx(gx), 0), (sx(gx), SH))
    for gy in range(0, world_h + 1, 64):
        pygame.draw.line(screen, (28, 30, 42), (0, sy(gy)), (SW, sy(gy)))

    my_player = None
    if snap:
        for p in snap.get('players', []):
            if p['id'] == my_id:
                my_player = p
                break

        for p in snap.get('particles', []):
            life = p['life'] / max(0.001, p['max_life'])
            rr = max(2, int(6 * life * SW / world_w))
            pygame.draw.circle(screen, tuple(p['color']), (sx(p['x']), sy(p['y'])), rr)

        for b in snap.get('bullets', []):
            col = CYAN if b['owner'] != 'enemy' else YELLOW
            pygame.draw.circle(screen, col, (sx(b['x']), sy(b['y'])), max(3, sx(b['r'])))
            pygame.draw.circle(screen, WHITE, (sx(b['x']), sy(b['y'])), max(3, sx(b['r'])), 1)

        for en in snap.get('enemies', []):
            draw_enemy(en)

        for p in snap.get('players', []):
            if p['active']:
                draw_player(p)

        if my_player:
            draw_bar(16, SH - 54, 260, 28, my_player['hp'] / max(1, my_player['max_hp']), GREEN if my_player['hp'] > my_player['max_hp'] * 0.5 else YELLOW if my_player['hp'] > my_player['max_hp'] * 0.25 else RED)
            txt(f"{my_player['hp']}/{my_player['max_hp']}", f_xs, WHITE, 146, SH - 40, False)

        xp = snap.get('team_xp', 0)
        xp_to = max(1, snap.get('xp_to_level', 1))
        draw_bar(16, SH - 88, 210, 12, xp / xp_to, CYAN, (40, 40, 55))
        txt(f"TEAM LV {snap.get('team_level', 1)}", f_xs, YELLOW, 68, SH - 103, False)
        if snap.get('wave', 0) > 0:
            txt(f"WAVE {snap['wave']}", f_md, CYAN, SW - 145, 22)
            txt(f"{snap.get('wave_done', 0)} / {snap.get('wave_need', 0)} kills", f_sm, WHITE, SW - 155, 50)
        txt(f"Players: {snap.get('connected', 0)}/2", f_xs, WHITE, SW - 95, SH - 24, False)
        if snap.get('last_card'):
            txt(f"Last upgrade: {snap['last_card']}", f_xs, YELLOW, SW // 2, 26, False)

        mode = snap.get('mode', 'waiting')
        if mode == 'waiting':
            txt('WAITING FOR 2 PLAYERS', f_lg, WHITE, SW // 2, SH // 2 - 30)
            txt(f'Host: {server_ip}:{server_port}', f_sm, CYAN, SW // 2, SH // 2 + 28)
        elif mode == 'starting':
            txt(f"WAVE {snap.get('wave', 1)}", f_xl, CYAN, SW // 2, SH // 2 - 22)
        elif mode == 'between':
            secs = max(1, math.ceil(snap.get('wave_timer', 1)))
            txt(f"NEXT WAVE IN {secs}", f_lg, YELLOW, SW // 2, SH // 2 - 22)
        elif mode == 'complete':
            txt('WAVE CLEAR', f_lg, GREEN, SW // 2, SH // 2 - 22)
    else:
        txt('CONNECTING...', f_lg, WHITE, SW // 2, SH // 2 - 20)
        txt(f'{server_ip}:{server_port}', f_sm, CYAN, SW // 2, SH // 2 + 28)

    keys = pygame.key.get_pressed()
    aim_x, aim_y = 1.0, 0.0
    if my_player:
        mx, my = pygame.mouse.get_pos()
        wx = mx * world_w / SW
        wy = my * world_h / SH
        aim_x = wx - my_player['x']
        aim_y = wy - my_player['y']
        if abs(aim_x) < 0.01 and abs(aim_y) < 0.01:
            aim_x = 1.0
            aim_y = 0.0
    send_json({
        't': 'input',
        'u': bool(keys[pygame.K_w]),
        'd': bool(keys[pygame.K_s]),
        'l': bool(keys[pygame.K_a]),
        'r': bool(keys[pygame.K_d]),
        'shoot': bool(pygame.mouse.get_pressed()[0]),
        'ax': aim_x,
        'ay': aim_y,
    })

    pygame.display.flip()

connected = False
try:
    sock.close()
except:
    pass
pygame.quit()
