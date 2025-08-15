import pygame
import random
import sys
import os

# -----------------------------
#            Dodge!
# -----------------------------
# Objetivo: desvie dos blocos que caem e faça pontos.
# Controles: Setas (ou WASD) para mover, P = Pausar, R = Reiniciar, ESC = Sair

WIDTH, HEIGHT = 480, 640
FPS = 60

PLAYER_SIZE = 36
PLAYER_SPEED = 5

ENEMY_MIN_SIZE = 20
ENEMY_MAX_SIZE = 50
ENEMY_MIN_SPEED = 2
ENEMY_MAX_SPEED = 6
ENEMY_SPEED_INCREMENT = 1
SPEED_CAP_EXTRA = 3

SPAWN_INTERVAL_START = 600   # ms
SPAWN_INTERVAL_MIN = 250     # ms
SPAWN_INTERVAL_STEP = 40     # ms
DIFFICULTY_STEP_MS = 5000    # a cada 5s aumenta a dificuldade

FONT_NAME = None  # usa fonte padrão do pygame (mais compatível)
SAVE_FILE = "dodge_highscore.sav"

BG_COLOR = (18, 18, 18)
PLAYER_COLOR = (80, 200, 120)
ENEMY_COLOR = (230, 70, 70)
TEXT_COLOR = (240, 240, 240)
PAUSE_TINT = (0, 0, 0, 140)


def load_highscore(path: str) -> int:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
    except Exception:
        pass
    return 0


def save_highscore(path: str, score: int) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(score))
    except Exception:
        pass


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = PLAYER_SPEED

    def handle_input(self, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed
        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, surf):
        pygame.draw.rect(surf, PLAYER_COLOR, self.rect, border_radius=6)


class Enemy:
    def __init__(self):
        size = random.randint(ENEMY_MIN_SIZE, ENEMY_MAX_SIZE)
        x = random.randint(0, WIDTH - size)
        y = -size
        self.rect = pygame.Rect(x, y, size, size)
        self.speed = random.randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)

    def update(self):
        self.rect.y += self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, ENEMY_COLOR, self.rect, border_radius=4)

    def offscreen(self):
        return self.rect.top > HEIGHT


def draw_text(surf, text, size, x, y, center=True, color=TEXT_COLOR):
    font = pygame.font.Font(FONT_NAME, size)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(rendered, rect)


def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PyOS - Dodge!")
    clock = pygame.time.Clock()

    player = Player(WIDTH // 2 - PLAYER_SIZE // 2, HEIGHT - PLAYER_SIZE - 20)
    enemies = []

    spawn_event = pygame.USEREVENT + 1
    spawn_interval = SPAWN_INTERVAL_START
    pygame.time.set_timer(spawn_event, spawn_interval)

    score = 0
    highscore = load_highscore(SAVE_FILE)
    paused = False
    game_over = False
    difficulty_timer = 0

    while True:
        dt = clock.tick(FPS)
        difficulty_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_r and game_over:
                    player = Player(WIDTH // 2 - PLAYER_SIZE // 2, HEIGHT - PLAYER_SIZE - 20)
                    enemies.clear()
                    score = 0
                    paused = False
                    game_over = False
                    spawn_interval = SPAWN_INTERVAL_START
                    pygame.time.set_timer(spawn_event, spawn_interval)
            if event.type == spawn_event and not paused and not game_over:
                enemies.append(Enemy())

        if not paused and not game_over:
            keys = pygame.key.get_pressed()
            player.handle_input(keys)

            for enemy in enemies:
                enemy.update()

            enemies = [enemy for enemy in enemies if not enemy.offscreen()]
            score += 1

            if difficulty_timer >= DIFFICULTY_STEP_MS:
                difficulty_timer = 0
                spawn_interval = max(SPAWN_INTERVAL_MIN, spawn_interval - SPAWN_INTERVAL_STEP)
                pygame.time.set_timer(spawn_event, spawn_interval)
                for enemy in enemies:
                    enemy.speed = min(enemy.speed + ENEMY_SPEED_INCREMENT, ENEMY_MAX_SPEED + SPEED_CAP_EXTRA)

            for enemy in enemies:
                if enemy.rect.colliderect(player.rect):
                    game_over = True
                    if score > highscore:
                        highscore = score
                        save_highscore(SAVE_FILE, highscore)
                    break

        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, WIDTH, 40))
        draw_text(screen, f"Score: {score}", 18, 10, 10, center=False)
        draw_text(screen, f"Recorde: {highscore}", 18, WIDTH - 10, 10, center=False)

        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)

        if paused and not game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(PAUSE_TINT)
            screen.blit(overlay, (0, 0))
            draw_text(screen, "PAUSADO", 36, WIDTH // 2, HEIGHT // 2 - 20)
            draw_text(screen, "Pressione P para continuar", 20, WIDTH // 2, HEIGHT // 2 + 20)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            draw_text(screen, "GAME OVER", 42, WIDTH // 2, HEIGHT // 2 - 40)
            draw_text(screen, f"Score: {score}", 24, WIDTH // 2, HEIGHT // 2)
            draw_text(screen, "R = Reiniciar  |  ESC = Sair", 20, WIDTH // 2, HEIGHT // 2 + 40)

        pygame.display.flip()


if __name__ == "__main__":
    try:
        game_loop()
    except Exception as e:
        pygame.quit()
        print("Erro:", e)