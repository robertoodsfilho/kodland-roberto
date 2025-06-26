import pgzrun
import random
import math
from pygame import Rect
WIDTH = 640
HEIGHT = 480
CELL_SIZE = 40
ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE
STATE_MENU = 'menu'
STATE_PLAYING = 'playing'
def load_animation_images(base_name, count):
    return [f"{base_name}{i}" for i in range(count)]
class Button:
    def __init__(self, rect, text):
        self.rect = rect
        self.text = text       
    def draw(self):
        screen.draw.filled_rect(self.rect, (50, 50, 50))
        screen.draw.textbox(self.text, self.rect, color='white')       
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
class AnimatedSprite:
    def __init__(self, pos, animations, frame_duration=0.2):
        self.pos = list(pos)
        self.animations = animations
        self.current_animation = 'idle'
        self.frame_duration = frame_duration
        self.frame_timer = 0
        self.frame_index = 0
        self.image = self.animations[self.current_animation][0]       
    def update(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])
            self.image = self.animations[self.current_animation][self.frame_index]            
    def draw(self):
        screen.blit(self.image, (self.pos[0], self.pos[1]))        
    def set_animation(self, anim_name):
        if anim_name != self.current_animation:
            self.current_animation = anim_name
            self.frame_index = 0
            self.frame_timer = 0
            self.image = self.animations[anim_name][0]
class Hero(AnimatedSprite):
    def __init__(self, pos):
        idle_imgs = load_animation_images('hero_idle_', 2)
        walk_imgs = load_animation_images('hero_walk_', 5)
        animations = {'idle': idle_imgs, 'walk': walk_imgs}
        super().__init__(pos, animations, frame_duration=0.15)
        self.speed = 120
        self.target_pos = pos[:]
        self.moving = False        
    def move_to(self, target_cell):
        target_x = target_cell[0] * CELL_SIZE
        target_y = target_cell[1] * CELL_SIZE
        self.target_pos = [target_x, target_y]
        if self.target_pos != self.pos:
            self.moving = True
            self.set_animation('walk')            
    def update(self, dt):
        if self.moving:
            dx = self.target_pos[0] - self.pos[0]
            dy = self.target_pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist < 1:
                self.pos = self.target_pos[:]
                self.moving = False
                self.set_animation('idle')
            else:
                vx = (dx / dist) * self.speed
                vy = (dy / dist) * self.speed
                self.pos[0] += vx * dt
                self.pos[1] += vy * dt
        super().update(dt)        
    def current_cell(self):
        return (round(self.pos[0] / CELL_SIZE), round(self.pos[1] / CELL_SIZE))
class Enemy(AnimatedSprite):
    def __init__(self, pos, territory_rect):
        idle_imgs = load_animation_images('enemy_idle_', 4)
        walk_imgs = load_animation_images('enemy_walk_', 4)
        animations = {'idle': idle_imgs, 'walk': walk_imgs}
        super().__init__(pos, animations, frame_duration=0.2)
        self.speed = 60
        self.territory = territory_rect
        self.direction = [0, 0]
        self.moving = False
        self.target_pos = pos[:]
        self.choose_new_target()        
    def choose_new_target(self):
        left = self.territory.left // CELL_SIZE
        right = self.territory.right // CELL_SIZE - 1
        top = self.territory.top // CELL_SIZE
        bottom = self.territory.bottom // CELL_SIZE - 1
        target_cell = (random.randint(left, right), random.randint(top, bottom))
        self.target_pos = [target_cell[0] * CELL_SIZE, target_cell[1] * CELL_SIZE]
        self.moving = True
        self.set_animation('walk')       
    def update(self, dt):
        if self.moving:
            dx = self.target_pos[0] - self.pos[0]
            dy = self.target_pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist < 2:
                self.pos = self.target_pos[:]
                self.moving = False
                self.set_animation('idle')
                clock.schedule_unique(self.choose_new_target, 1 + random.random() * 2)
            else:
                vx = (dx / dist) * self.speed
                vy = (dy / dist) * self.speed
                self.pos[0] += vx * dt
                self.pos[1] += vy * dt
        super().update(dt)
class Game:
    def __init__(self):
        self.state = STATE_MENU
        self.hero = None
        self.enemies = []
        self.buttons = []
        self.sound_on = True
        self.level = 1
        self.door_rect = Rect((WIDTH - 1 * CELL_SIZE, HEIGHT - 1 * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        self.background = "background"
        self.background_music = "background_music"
        self.load_assets()
        self.create_menu()        
    def load_assets(self):
        music.set_volume(0.3)
        try:
            music.play(self.background_music)
            if self.sound_on:
                music.play(self.background_music)
        except:
            music.unpause()    
    def create_menu(self):
        self.buttons = [
            Button(Rect((WIDTH // 2 - 100, HEIGHT // 2 - 60), (200, 50)), "Start Game"),
            Button(Rect((WIDTH // 2 - 100, HEIGHT // 2), (200, 50)), "Sound: On"),
            Button(Rect((WIDTH // 2 - 100, HEIGHT // 2 + 60), (200, 50)), "Quit"),
        ]        
    def start_game(self):
        self.level = 1
        self._start_level()       
    def _start_level(self):
        start_pos = (COLS // 2 * CELL_SIZE, ROWS // 2 * CELL_SIZE)
        self.hero = Hero(start_pos)
        self.enemies = []
        clock.unschedule(self.spawn_enemy)
        clock.schedule_interval(self.spawn_enemy, 10.0)
        for _ in range(5 + (self.level - 1) * 3):
            self.spawn_enemy()
        self.state = STATE_PLAYING        
    def next_level(self):
        self.level += 1
        self._start_level()        
    def spawn_enemy(self):
        if not self.hero:
            return    
        hero_cell = self.hero.current_cell()
        max_attempts = 100        
        for _ in range(max_attempts):
            cell_x = random.randint(0, COLS - 5)
            cell_y = random.randint(0, ROWS - 5)           
            if abs(cell_x - hero_cell[0]) > 1 or abs(cell_y - hero_cell[1]) > 1:
                territory = Rect(cell_x * CELL_SIZE, cell_y * CELL_SIZE, 4 * CELL_SIZE, 4 * CELL_SIZE)
                enemy_x = territory.left + CELL_SIZE
                enemy_y = territory.top + CELL_SIZE
                enemy = Enemy([enemy_x, enemy_y], territory)
                self.enemies.append(enemy)
                return               
        fallback_territory = Rect(0, 0, 4 * CELL_SIZE, 4 * CELL_SIZE)
        fallback_enemy = Enemy([CELL_SIZE, CELL_SIZE], fallback_territory)
        self.enemies.append(fallback_enemy)       
    def toggle_sound(self):
        if self.sound_on:
            music.pause()
            self.sound_on = False
        else:
            music.unpause()
            self.sound_on = True
        self.buttons[1].text = f"Sound: {'On' if self.sound_on else 'Off'}"       
    def quit_game(self):
        exit()       
    def on_mouse_down(self, pos):
        if self.state == STATE_MENU:
            for button in self.buttons:
                if button.is_clicked(pos):
                    if button.text == "Start Game":
                        self.start_game()
                    elif button.text.startswith("Sound"):
                        self.toggle_sound()
                    elif button.text == "Quit":
                        self.quit_game()
        elif self.state == STATE_PLAYING:
            grid_x = pos[0] // CELL_SIZE
            grid_y = pos[1] // CELL_SIZE
            if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                self.hero.move_to((grid_x, grid_y))                   
    def update(self, dt):
        if self.state == STATE_PLAYING:
            self.hero.update(dt)
            for enemy in self.enemies:
                enemy.update(dt)              
            hero_rect = Rect(self.hero.pos[0], self.hero.pos[1], CELL_SIZE, CELL_SIZE)
            for enemy in self.enemies:
                enemy_rect = Rect(enemy.pos[0], enemy.pos[1], CELL_SIZE, CELL_SIZE)
                if hero_rect.colliderect(enemy_rect):
                    self.state = STATE_MENU
                    return                   
            if hero_rect.colliderect(self.door_rect):
                self.next_level()               
    def draw(self):
        screen.clear()
        if self.state == STATE_MENU:
            screen.blit(self.background, (0, 0))
            screen.draw.text("ROGUEALIKE KODLAND", center=(WIDTH // 2, 100), fontsize=50, color="white")
            for button in self.buttons:
                button.draw()
        elif self.state == STATE_PLAYING:
            screen.blit(self.background, (0, 0))
            for x in range(COLS):
                for y in range(ROWS):
                    screen.draw.rect(Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), (100, 150, 100))
            for enemy in self.enemies:
                enemy.draw()
            self.hero.draw()
            screen.draw.text(f"Level: {self.level}", topleft=(10, 10), fontsize=30, color="white")
game = Game()
def update(dt):
    game.update(dt)   
def draw():
    game.draw()   
def on_mouse_down(pos):
    game.on_mouse_down(pos)
pgzrun.go()

#made by: Robertoodsfilho
