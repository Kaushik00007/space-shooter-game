import pygame
import random
import sys

pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galactic Warfare")

# Load assets from the assets folder
player_ship_img = pygame.image.load("assets/player_ship.png").convert_alpha()
enemy_ship_img = pygame.image.load("assets/enemy_ship.png").convert_alpha()
background_img = pygame.image.load("assets/space_bg.jpg").convert()
powerup_img = pygame.image.load("assets/powerup.png").convert_alpha()
menu_bg_img = pygame.image.load("assets/menu_bg.jpg").convert()

explosion_frames = [pygame.image.load(f"assets/explosion{i}.png").convert_alpha() for i in range(1, 11)]
explosion_frames = [pygame.transform.scale(img, (100, 100)) for img in explosion_frames]  # Resize

# Load firing animation frames
firing_frames = [pygame.image.load(f"assets/fire{i}.png").convert_alpha() for i in range(1, 5)]
firing_frames = [pygame.transform.scale(img, (25, 60)) for img in firing_frames]  # Resize firing animation

player_ship_img = pygame.transform.scale(player_ship_img, (50, 50))
enemy_ship_img = pygame.transform.scale(enemy_ship_img, (50, 50))
powerup_img = pygame.transform.scale(powerup_img, (30, 30))
menu_bg_img = pygame.transform.scale(menu_bg_img, (WIDTH, HEIGHT))

enemy_ship_img = pygame.transform.rotate(enemy_ship_img, 90)
player_ship_img = pygame.transform.rotate(player_ship_img, 90)

shoot_sound = pygame.mixer.Sound("assets/shoot.wav")
explosion_sound = pygame.mixer.Sound("assets/explosion.wav")
powerup_sound = pygame.mixer.Sound("assets/powerup.wav")

shoot_sound.set_volume(1.0)  
explosion_sound.set_volume(1.0)
powerup_sound.set_volume(1.0)

bg_scroll_speed = 1
bg_y = 0

# Game states: "menu", "playing", "game_over"
game_state = "menu"

player_x = WIDTH // 2 - 25  
player_y = HEIGHT - 80
player_speed = 5
last_shot_time = 0  
shot_cooldown = 300   

# game objects
bullet_trails = []
bullets = []     # each bullet: {'x': value, 'y': value}
powerups = []
enemies = []     # each enemy: {'x': value, 'y': value, 'speed': value}
explosions = []  # each explosion: {'x': value, 'y': value, 'timer': value}
score = 0

shield_active = False
shield_timer = 0
special_shots = 0

clock = pygame.time.Clock()

font_large = pygame.font.SysFont(None, 72)
font_medium = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)


# ---------------------- Functions ---------------------- #
def draw_background():
    global bg_y
    screen.blit(background_img, (0, bg_y))
    screen.blit(background_img, (0, bg_y - HEIGHT))
    bg_y += bg_scroll_speed
    if bg_y >= HEIGHT:
        bg_y = 0

def draw_player():
    screen.blit(player_ship_img, (player_x, player_y))

def draw_bullets():
    for bullet in bullets:
        frame_index = bullet['frame'] % len(firing_frames)
        screen.blit(firing_frames[frame_index], (bullet['x'], bullet['y']))

def update_bullets():
    global score
    for bullet in bullets[:]:
        bullet['y'] -= 8  
        if pygame.time.get_ticks() % 5 == 0:  # Slow down animation
            bullet['frame'] = (bullet['frame'] + 1) % len(firing_frames)  

        if bullet['y'] < -30:
            bullets.remove(bullet)
        else:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], 25, 60)
            for enemy in enemies[:]:
                enemy_rect = pygame.Rect(enemy['x'], enemy['y'], 50, 50)
                if bullet_rect.colliderect(enemy_rect):
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    explosions.append({'x': enemy['x'], 'y': enemy['y'], 'frame': 0, 'timer': 5})
                    score += 10
                    explosion_sound.play()
                    break

def update_trails():
    for trail in bullet_trails[:]:
        trail['y'] -= 8  
        trail['alpha'] -= 10  
        if trail['alpha'] <= 0:
            bullet_trails.remove(trail)

def draw_trails():
    for trail in bullet_trails:
        trail_surf = pygame.Surface((10, 30), pygame.SRCALPHA)
        trail_surf.fill((255, 255, 255, trail['alpha']))
        screen.blit(trail_surf, (trail['x'], trail['y']))

def spawn_enemy():
    enemy_x = random.randint(0, WIDTH - 50)
    enemy_y = -50
    speed = random.randint(2, 4)
    enemies.append({'x': enemy_x, 'y': enemy_y, 'speed': speed})

def draw_enemies():
    for enemy in enemies:
        screen.blit(enemy_ship_img, (enemy['x'], enemy['y']))

def update_enemies():
    global game_state
    for enemy in enemies[:]:
        enemy['y'] += enemy['speed']
        enemy_rect = pygame.Rect(enemy['x'], enemy['y'], 50, 50)
        player_rect = pygame.Rect(player_x, player_y, 50, 50)
        if enemy_rect.colliderect(player_rect):
            if not shield_active:
                game_state = "game_over"
            else:
                enemies.remove(enemy)
                explosions.append({'x': enemy['x'], 'y': enemy['y'], 'frame': 0, 'timer': 5})
                explosion_sound.play()
        if enemy['y'] > HEIGHT:
            enemies.remove(enemy)

def draw_powerups():
    for powerup in powerups:
        screen.blit(powerup_img, (powerup['x'], powerup['y']))

def update_powerups():
    global shield_active, shield_timer, special_shots
    for powerup in powerups[:]:
        powerup['y'] += 3
        if powerup['y'] > HEIGHT:
            powerups.remove(powerup)
        if pygame.Rect(player_x, player_y, 50, 50).colliderect(pygame.Rect(powerup['x'], powerup['y'], 30, 30)):
            powerups.remove(powerup)
            powerup_sound.play()
            power_type = powerup['type']
            if power_type == 'shield':
                shield_active = True
                shield_timer = pygame.time.get_ticks() + 5000
            elif power_type == 'triple_shot':
                special_shots += 5

def spawn_powerup():
    power_type = random.choice(['shield', 'triple_shot'])
    powerups.append({'x': random.randint(0, WIDTH - 30), 'y': -30, 'type': power_type})

def draw_explosions():
    for explosion in explosions:
        frame_index = explosion['frame']
        if frame_index < len(explosion_frames):
            screen.blit(explosion_frames[frame_index], (explosion['x'], explosion['y']))

def update_explosions():
    for explosion in explosions[:]:  
        explosion['timer'] -= 1
        if explosion['timer'] <= 0:
            explosion['frame'] += 1
            explosion['timer'] = 5
        if explosion['frame'] >= len(explosion_frames):  
            explosions.remove(explosion)

def draw_menu():

    shadow_offset = 3  
    instruct_shadow = font_medium.render("Use Arrow Keys to Move | SPACE to Shoot", True, (0, 0, 0))  
    start_shadow = font_medium.render("Press SPACE to Start", True, (0, 0, 0))  

    screen.blit(menu_bg_img, (0, 0))  
    instruct_text = font_medium.render("Use Arrow Keys to Move | SPACE to Shoot", True, (255, 165, 0))   
    start_text = font_medium.render("Press SPACE to Start", True, (50, 205, 50))  

    screen.blit(instruct_shadow, (WIDTH // 2 - instruct_shadow.get_width() // 2 + shadow_offset, HEIGHT // 2 - 40 + shadow_offset))
    screen.blit(start_shadow, (WIDTH // 2 - start_shadow.get_width() // 2 + shadow_offset, HEIGHT // 2 + 10 + shadow_offset))

    screen.blit(instruct_text, (WIDTH // 2 - instruct_text.get_width() // 2, HEIGHT // 2 - 40))
    screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 + 10))


def draw_game_over():
    screen.fill((0, 0, 0))
    over_text = font_large.render("Game Over", True, (255, 0, 0))
    score_text = font_medium.render("Score: " + str(score), True, (255, 255, 255))
    restart_text = font_medium.render("Press R to Restart", True, (200, 200, 200))
    screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 3))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))

def reset_game():
    global player_x, player_y, bullets, enemies, explosions, score, last_shot_time, shield_active, shield_timer, special_shots
    player_x = WIDTH // 2 - 25
    player_y = HEIGHT - 80
    bullets = []
    enemies = []
    explosions = []
    powerups = []
    score = 0
    last_shot_time = 0
    shield_active = False
    shield_timer = 0
    special_shots = 0

#  Main Game Loop
running = True
while running:
    dt = clock.tick(60) 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                reset_game()
                game_state = "playing"
        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()
                game_state = "menu"

    if game_state == "playing":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - 50:
            player_x += player_speed
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
        if current_time - last_shot_time >= shot_cooldown:
           bullets.append({'x': player_x + 20, 'y': player_y, 'frame': 0})  
           last_shot_time = current_time

           if not pygame.mixer.get_busy():
            shoot_sound.play()

        update_bullets()
        update_enemies()
        update_explosions()
        update_powerups()
        update_trails()

        if random.randint(1, 60) == 1:
            spawn_enemy()
        if random.randint(1, 300) == 1:
            spawn_powerup()

        draw_background()
        draw_player()
        draw_bullets()
        draw_enemies()
        draw_explosions()
        draw_powerups()
        draw_trails()

        score_display = font_medium.render("Score: " + str(score), True, (255, 255, 255))
        screen.blit(score_display, (10, 10))

        if shield_active:
            shield_text = font_small.render("Shield Active", True, (0, 255, 0))
            screen.blit(shield_text, (10, 50))
            if pygame.time.get_ticks() > shield_timer:
                shield_active = False

        if special_shots > 0:
            special_text = font_small.render("Special Shots: " + str(special_shots), True, (255, 255, 0))
            screen.blit(special_text, (10, 90))
    elif game_state == "menu":
        draw_menu()
    elif game_state == "game_over":
        draw_game_over()

    pygame.display.flip()

pygame.quit()