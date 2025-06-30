import pygame
import json
import random
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("GooseTanks")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

# Загрузка ассетов
goose_img = pygame.image.load("goose.png")
bullet_img = pygame.image.load("bullet.png")
enemy_img = pygame.image.load("enemy_goose.png")
shoot_sound = pygame.mixer.Sound("shoot.wav")

goose_rect = goose_img.get_rect()
goose_rect.topleft = (50, 50)
bullets = []

walls = []

level_completed = False
game_over = False
facing = "right"
health = 3
invulnerable = 0
fire_cooldown = 0

def load_walls():
    global walls
    walls = [
        pygame.Rect(0, 0, WIDTH, 20),  # Верхняя стена
        pygame.Rect(0, HEIGHT - 20, WIDTH, 20),  # Нижняя стена
        pygame.Rect(0, 0, 20, HEIGHT),  # Левая стена
        pygame.Rect(WIDTH - 20, 0, 20, HEIGHT)  # Правая стена
    ]
    try:
        with open("level1.json", "r") as f:
            data = json.load(f)
            for wall_data in data["walls"]:
                rect = pygame.Rect(wall_data["x"], wall_data["y"], wall_data["w"], wall_data["h"])
                walls.append(rect)
    except Exception as e:
        print("Ошибка загрузки level1.json:", e)

load_walls()

def spawn_enemies(n):
    result = []
    attempts = 0
    while len(result) < n and attempts < 100:
        r = enemy_img.get_rect(topleft=(random.randint(50, WIDTH - 60), random.randint(50, HEIGHT - 60)))
        if r.colliderect(goose_rect): continue
        if any(r.colliderect(w) for w in walls): continue
        result.append(r)
        attempts += 1
    return result

enemies = spawn_enemies(3)

class Bullet:
    def __init__(self, x, y, vx, vy, image):
        self.rect = image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        self.image = image

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def draw(self, surface):
        surface.blit(self.image, self.rect)

def draw_menu(selected_idx, options):
    win.fill((20, 20, 20))
    for i, option in enumerate(options):
        color = (255, 255, 255) if i == selected_idx else (150, 150, 150)
        text_surf = font.render(option, True, color)
        rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 40))
        win.blit(text_surf, rect)
    pygame.display.update()

def menu_loop(level_done=False):
    selected_idx = 0
    options = ["Start", "Exit"] if not level_done else ["Next Level", "Exit"]
    while True:
        clock.tick(60)
        draw_menu(selected_idx, options)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_idx = (selected_idx - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_idx = (selected_idx + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    choice = options[selected_idx]
                    if choice == "Start" or choice == "Next Level":
                        return
                    elif choice == "Exit":
                        pygame.quit()
                        sys.exit()

def draw_window():
    win.fill((30, 30, 30))
    for w in walls:
        pygame.draw.rect(win, (100, 100, 100), w)
    for b in bullets:
        b.draw(win)
    for e in enemies:
        win.blit(enemy_img, e)
    if not game_over:
        win.blit(goose_img, goose_rect)
    else:
        over = font.render("GAME OVER - press R to restart", True, (255, 0, 0))
        win.blit(over, (WIDTH // 2 - 140, HEIGHT // 2))
    if level_completed:
        completed_text = font.render("LEVEL COMPLETED! Press N for Next Level", True, (0, 255, 0))
        win.blit(completed_text, (WIDTH // 2 - 180, HEIGHT // 2 - 40))
    health_surface = font.render(f"💛 {health}", True, (255, 200, 200))
    win.blit(health_surface, (WIDTH - 100, 10))
    pygame.display.update()

def handle_movement(keys):
    global facing, goose_rect
    orig = goose_rect.copy()
    if keys[pygame.K_a]:
        goose_rect.x -= 5
        facing = "left"
    if keys[pygame.K_d]:
        goose_rect.x += 5
        facing = "right"
    if keys[pygame.K_w]:
        goose_rect.y -= 5
        facing = "up"
    if keys[pygame.K_s]:
        goose_rect.y += 5
        facing = "down"
    # Не вылетать за экран
    goose_rect.x = max(0, min(goose_rect.x, WIDTH - goose_rect.width))
    goose_rect.y = max(0, min(goose_rect.y, HEIGHT - goose_rect.height))

    # Проверка столкновений со стенами
    for wall in walls:
        if goose_rect.colliderect(wall):
            goose_rect.topleft = orig.topleft

def handle_bullets():
    for b in bullets[:]:
        b.update()
        if (b.rect.x > WIDTH or b.rect.x < 0 or b.rect.y > HEIGHT or b.rect.y < 0
                or any(b.rect.colliderect(w) for w in walls)):
            bullets.remove(b)
        else:
            for e in enemies[:]:
                if b.rect.colliderect(e):
                    bullets.remove(b)
                    enemies.remove(e)
                    break

def update_enemies():
    global health, invulnerable, game_over, level_completed
    for e in enemies:
        orig = e.copy()
        dx = 1 if e.x < goose_rect.x else -1 if e.x > goose_rect.x else 0
        dy = 1 if e.y < goose_rect.y else -1 if e.y > goose_rect.y else 0
        e.x += dx
        if any(e.colliderect(w) for w in walls): e.x = orig.x
        e.y += dy
        if any(e.colliderect(w) for w in walls): e.y = orig.y

        if not game_over and e.colliderect(goose_rect) and invulnerable == 0:
            health -= 1
            invulnerable = 60
            if health <= 0:
                game_over = True

    if len(enemies) == 0 and not level_completed:
        level_completed = True

def shoot():
    global facing
    dir_map = {
        "right": (10, 0),
        "left": (-10, 0),
        "up": (0, -10),
        "down": (0, 10)
    }
    vx, vy = dir_map.get(facing, (10, 0))
    b = Bullet(goose_rect.centerx, goose_rect.centery, vx, vy, bullet_img)
    bullets.append(b)
    shoot_sound.play()

def reset_game():
    global goose_rect, bullets, enemies, health, invulnerable, game_over, level_completed
    goose_rect.topleft = (50, 50)
    bullets.clear()
    enemies[:] = spawn_enemies(3)
    health = 3
    invulnerable = 0
    game_over = False
    level_completed = False

def game_loop():
    global fire_cooldown, invulnerable, game_over, level_completed
    fire_cooldown = 0
    run = True
    while run:
        clock.tick(60)
        fire_cooldown += 1
        if invulnerable > 0:
            invulnerable -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.VIDEORESIZE:
                global WIDTH, HEIGHT
                WIDTH, HEIGHT = event.w, event.h
                pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                load_walls()  # обновляем стены под новый размер

        keys = pygame.key.get_pressed()
        if not game_over and not level_completed:
            handle_movement(keys)

            if keys[pygame.K_SPACE] and fire_cooldown > 15:
                shoot()
                fire_cooldown = 0

            handle_bullets()
            update_enemies()

        if game_over and keys[pygame.K_r]:
            reset_game()

        if level_completed and keys[pygame.K_n]:
            reset_game()  # позже добавим загрузку следующего уровня

        draw_window()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    menu_loop()
    game_loop()
