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
enemies = []
bonuses = []

level_index = 1
level_completed = False
game_over = False
paused = False
facing = "right"
health = 3
invulnerable = 0
fire_cooldown = 0
speed_boost = 0

class Enemy:
    def __init__(self, x, y):
        self.rect = enemy_img.get_rect(topleft=(x, y))
        self.speed = 2
        self.state = "patrolling"  # or 'chasing'
        patrol_range = random.randint(100, 200)
        self.patrol_points = [x, min(x + patrol_range, WIDTH - self.rect.width - 20)]
        self.direction = 1  # 1 = right, -1 = left

    def update(self):
        if self.state == "patrolling":
            self.rect.x += self.speed * self.direction
            if self.rect.x < self.patrol_points[0] or self.rect.x > self.patrol_points[1]:
                self.direction *= -1
                self.rect.x += self.speed * self.direction  # prevent sticking on edges
        elif self.state == "chasing":
            dx = dy = 0
            if self.rect.x < goose_rect.x:
                dx = self.speed
            elif self.rect.x > goose_rect.x:
                dx = -self.speed
            if self.rect.y < goose_rect.y:
                dy = self.speed
            elif self.rect.y > goose_rect.y:
                dy = -self.speed
            # Move with collision checking
            orig_x, orig_y = self.rect.x, self.rect.y
            self.rect.x += dx
            if any(self.rect.colliderect(w) for w in walls):
                self.rect.x = orig_x
            self.rect.y += dy
            if any(self.rect.colliderect(w) for w in walls):
                self.rect.y = orig_y

    def can_see_goose(self):
        vision_rect = self.rect.inflate(150, 150)
        return vision_rect.colliderect(goose_rect)

def load_level(idx):
    global walls, enemies, bonuses
    walls = [
        pygame.Rect(0, 0, WIDTH, 20),
        pygame.Rect(0, HEIGHT - 20, WIDTH, 20),
        pygame.Rect(0, 0, 20, HEIGHT),
        pygame.Rect(WIDTH - 20, 0, 20, HEIGHT)
    ]
    bonuses.clear()
    try:
        with open(f"levels/level{idx}.json", "r") as f:
            data = json.load(f)
            for wall_data in data.get("walls", []):
                walls.append(pygame.Rect(wall_data["x"], wall_data["y"], wall_data["w"], wall_data["h"]))
            enemies[:] = spawn_enemies(data.get("enemy_count", 3))
    except FileNotFoundError:
        print(f"Level {idx} not found. Game completed.")
        pygame.quit()
        sys.exit()

def spawn_enemies(n):
    result = []
    attempts = 0
    while len(result) < n and attempts < 200:
        x = random.randint(50, WIDTH - 60)
        y = random.randint(50, HEIGHT - 60)
        r = enemy_img.get_rect(topleft=(x, y))
        if r.colliderect(goose_rect):
            attempts += 1
            continue
        if any(r.colliderect(w) for w in walls):
            attempts += 1
            continue
        result.append(Enemy(x, y))
        attempts += 1
    return result

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

class Bonus:
    def __init__(self, x, y, bonus_type):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.type = bonus_type
        self.color = {"health": (200, 0, 0), "shield": (0, 100, 255), "speed": (255, 255, 0)}[bonus_type]

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

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
                    if choice in ["Start", "Next Level"]:
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
    for enemy in enemies:
        win.blit(enemy_img, enemy.rect)
    for bonus in bonuses:
        bonus.draw(win)
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
    global facing
    speed = 7 if speed_boost > 0 else 4
    orig = goose_rect.copy()
    if keys[pygame.K_a]:
        goose_rect.x -= speed
        facing = "left"
    if keys[pygame.K_d]:
        goose_rect.x += speed
        facing = "right"
    if keys[pygame.K_w]:
        goose_rect.y -= speed
        facing = "up"
    if keys[pygame.K_s]:
        goose_rect.y += speed
        facing = "down"
    goose_rect.x = max(0, min(goose_rect.x, WIDTH - goose_rect.width))
    goose_rect.y = max(0, min(goose_rect.y, HEIGHT - goose_rect.height))
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
            for enemy in enemies[:]:
                if b.rect.colliderect(enemy.rect):
                    bullets.remove(b)
                    enemies.remove(enemy)
                    break

def update_enemies():
    global health, invulnerable, game_over, level_completed
    for enemy in enemies:
        if enemy.can_see_goose():
            enemy.state = "chasing"
        else:
            enemy.state = "patrolling"
        enemy.update()

        if not game_over and enemy.rect.colliderect(goose_rect) and invulnerable == 0:
            health -= 1
            invulnerable = 60
            if health <= 0:
                game_over = True

    if len(enemies) == 0 and not level_completed:
        level_completed = True

def shoot():
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
    global goose_rect, bullets, health, invulnerable, game_over, level_completed, speed_boost
    goose_rect.topleft = (50, 50)
    bullets.clear()
    health = 3
    invulnerable = 0
    game_over = False
    level_completed = False
    speed_boost = 0
    load_level(level_index)
    bonuses.clear()

def game_loop():
    global fire_cooldown, invulnerable, game_over, level_completed, paused, speed_boost, level_index
    fire_cooldown = 0
    run = True
    while run:
        clock.tick(60)
        fire_cooldown += 1
        if invulnerable > 0:
            invulnerable -= 1
        if speed_boost > 0:
            speed_boost -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.VIDEORESIZE:
                global WIDTH, HEIGHT
                WIDTH, HEIGHT = event.w, event.h
                pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                load_level(level_index)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused

        if paused:
            draw_window()
            paused_text = font.render("PAUSED - Press P to resume", True, (255, 255, 0))
            win.blit(paused_text, (WIDTH // 2 - 160, HEIGHT // 2))
            pygame.display.update()
            continue

        keys = pygame.key.get_pressed()
        if not game_over and not level_completed:
            handle_movement(keys)
            if keys[pygame.K_SPACE] and fire_cooldown > 15:
                shoot()
                fire_cooldown = 0
            handle_bullets()
            update_enemies()

            # Проверка сбора бонусов
            for bonus in bonuses[:]:
                if goose_rect.colliderect(bonus.rect):
                    if bonus.type == "health":
                        if health < 5:
                            health += 1
                    elif bonus.type == "shield":
                        invulnerable = 180
                    elif bonus.type == "speed":
                        speed_boost = 180
                    bonuses.remove(bonus)

            # Спавн бонусов (~раз в 7 секунд)
            if pygame.time.get_ticks() % 7000 < 60 and len(bonuses) < 2:
                bx, by = random.randint(50, WIDTH - 80), random.randint(50, HEIGHT - 80)
                if not any(pygame.Rect(bx, by, 30, 30).colliderect(w) for w in walls):
                    bonuses.append(Bonus(bx, by, random.choice(["health", "shield", "speed"])))

        if game_over and keys[pygame.K_r]:
            reset_game()

        if level_completed and keys[pygame.K_n]:
            level_index += 1
            reset_game()

        draw_window()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    load_level(level_index)
    menu_loop()
    game_loop()
