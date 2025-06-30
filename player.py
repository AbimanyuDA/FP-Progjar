import pygame
import os

class Player(pygame.sprite.Sprite):
    def __init__(self, id, x, y, animation_folder, client_interface, is_remote=False):
        super().__init__()
        self.id = id
        self.client_interface = client_interface
        self.is_remote = is_remote

        self.sword_image = pygame.image.load('assets/images/sword.png').convert_alpha()
        self.sword_image = pygame.transform.scale(self.sword_image, (self.sword_image.get_width() * 2, self.sword_image.get_height() * 2))
        self.original_sword_image = self.sword_image
        self.sword_offset_x = 40
        self.sword_offset_y = 10
        self.is_attacking = False
        self.attack_duration = 0.25
        self.attack_timer = 0
        self.hit_during_attack = set()

        self.max_health = 6
        self.health = self.max_health
        self.is_hit = False
        self.hit_duration = 0.2
        self.hit_timer = 0
        self.heart_full = pygame.image.load('assets/images/heart/ui_heart_full.png').convert_alpha()
        self.heart_half = pygame.image.load('assets/images/heart/ui_heart_half.png').convert_alpha()
        self.heart_empty = pygame.image.load('assets/images/heart/ui_heart_empty.png').convert_alpha()
        self.heart_full = pygame.transform.scale(self.heart_full, (32, 32))
        self.heart_half = pygame.transform.scale(self.heart_half, (32, 32))
        self.heart_empty = pygame.transform.scale(self.heart_empty, (32, 32))

        self.animation_frames = self.load_animation_frames(animation_folder)
        if not self.animation_frames:
            raise ValueError(f"Could not load animation frames from {animation_folder}")

        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.animation_speed = 10
        self.animation_timer = 0
        self.speed = 200
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing_right = True
        self.display_name = f"Player {self.id}"
        self.name_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.kill_score = 0

    def load_animation_frames(self, folder_path):
        frames = []
        file_names = sorted([f for f in os.listdir(folder_path) if f.startswith('knight_m_run_anim') and f.endswith('.png')])
        for file_name in file_names:
            img_path = os.path.join(folder_path, file_name)
            try:
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
                frames.append(img)
            except pygame.error as e:
                print(f"Error loading frame {img_path}: {e}")
        return frames

    def get_state_dict(self):
        """Mengembalikan state pemain sebagai dictionary untuk dikirim ke server."""
        state = {
            'position': [self.rect.x, self.rect.y],
            'health': self.health,
            'facing_right': self.facing_right,
            'is_attacking': self.is_attacking,
            'is_hit': self.is_hit
        }
    
        if self.is_attacking:
            state['attacker_id'] = self.id

        return state

    def update_from_state(self, state_dict):
        """Memperbarui atribut pemain dari dictionary state yang diterima dari server."""
        if not state_dict:
            return
        self.rect.topleft = state_dict.get('position', self.rect.topleft)
        self.health = state_dict.get('health', self.health)
        self.facing_right = state_dict.get('facing_right', self.facing_right)
        self.is_attacking = state_dict.get('is_attacking', self.is_attacking)
        self.is_hit = state_dict.get('is_hit', self.is_hit)

    def update(self, dt, walls, all_players):
        if self.is_remote:
            state = self.client_interface.get_player_state(self.id)
            if state:
                self.update_from_state(state)
            self.update_animation(dt, moving=True) 
        else:

            keys = pygame.key.get_pressed()
            self.velocity.x = 0
            self.velocity.y = 0
            moving = False

            if not self.is_hit and self.health > 0:
                if keys[pygame.K_LEFT]:
                    self.velocity.x = -self.speed
                    moving = True
                    self.facing_right = False
                if keys[pygame.K_RIGHT]:
                    self.velocity.x = self.speed
                    moving = True
                    self.facing_right = True
                if keys[pygame.K_UP]:
                    self.velocity.y = -self.speed
                    moving = True
                if keys[pygame.K_DOWN]:
                    self.velocity.y = self.speed
                    moving = True
                
                if keys[pygame.K_x] and not self.is_attacking:
                    self.is_attacking = True
                    self.attack_timer = 0
                    self.hit_during_attack.clear()

            if self.is_attacking:
                self.attack_timer += dt

                self.perform_attack(all_players)
                if self.attack_timer >= self.attack_duration:
                    self.is_attacking = False

            if self.is_hit:
                self.hit_timer += dt
                if self.hit_timer >= self.hit_duration:
                    self.is_hit = False
                    self.hit_timer = 0

            self.rect.x += self.velocity.x * dt
            self.handle_collision(walls, 'horizontal')
            self.rect.y += self.velocity.y * dt
            self.handle_collision(walls, 'vertical')
            self.update_animation(dt, moving)

            self.client_interface.set_player_state(self.id, self.get_state_dict())

    def perform_attack(self, all_players):
        attack_rect = self.get_sword_rect()
        if not attack_rect: return

        for other_player in all_players.values():
            if other_player.id == self.id:
                continue

            if other_player.id not in self.hit_during_attack:
                if attack_rect.colliderect(other_player.rect):
                    print(f"Player {self.id} hit Player {other_player.id}")
                    
                    if not other_player.is_remote:
                        other_player.take_damage(1)
                        other_player.is_hit = True
                        other_player.hit_timer = 0
                    
                    self.hit_during_attack.add(other_player.id)

    def check_if_hit(self, all_players):
        if self.is_hit: return

        for other_id, other_player in all_players.items():
            if other_id == self.id:
                continue

            if other_player.is_remote and other_player.is_attacking:
                attacker_id = other_player.client_interface.get_player_state(other_id).get('attacker_id')
                if attacker_id == self.id or other_id == self.id:
                    continue

                attack_rect = other_player.get_sword_rect()
                if attack_rect and self.rect.colliderect(attack_rect):
                    print(f"Player {self.id} got hit by Player {other_id}")
                    self.register_hit()
                    break

    def register_hit(self):
        if not self.is_hit:
            self.take_damage(1)
            self.is_hit = True
            self.hit_timer = 0

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def get_sword_rect(self):
        """Calculates the current hitbox of the sword."""
        if not self.is_attacking: return None
        
        sword_img, sword_pos_rect = self.get_sword_render_info()
        return sword_pos_rect

    def get_sword_render_info(self):
        """Helper to get sword image and rect for drawing and collision."""
        sword_image_to_draw = self.original_sword_image
        if not self.facing_right:
            sword_image_to_draw = pygame.transform.flip(self.original_sword_image, True, False)

        if self.is_attacking:
            angle = -90 if self.facing_right else 90
            sword_image_to_draw = pygame.transform.rotate(sword_image_to_draw, angle)

        if self.facing_right:
            sword_rect = sword_image_to_draw.get_rect(center=self.rect.center + pygame.math.Vector2(self.sword_offset_x, self.sword_offset_y))
        else:
            sword_rect = sword_image_to_draw.get_rect(center=self.rect.center - pygame.math.Vector2(self.sword_offset_x, -self.sword_offset_y))
        return sword_image_to_draw, sword_rect

    def update_animation(self, dt, moving=True):
        """Handles the player's sprite animation."""
        if moving:
            self.animation_timer += dt
            if self.animation_timer > 1 / self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
                self.image = self.animation_frames[self.current_frame]
        else:
            self.current_frame = 0
            self.image = self.animation_frames[self.current_frame]

    def handle_collision(self, walls, direction):
        for wall in walls:
            if self.rect.colliderect(wall):
                if direction == 'horizontal':
                    if self.velocity.x > 0: self.rect.right = wall.left
                    if self.velocity.x < 0: self.rect.left = wall.right
                if direction == 'vertical':
                    if self.velocity.y > 0: self.rect.bottom = wall.top
                    if self.velocity.y < 0: self.rect.top = wall.bottom

    def draw(self, screen):
        """Draw the sword and then the player on the screen."""
        if self.is_attacking:
            sword_image, sword_rect = self.get_sword_render_info()
            screen.blit(sword_image, sword_rect)

        player_image_to_draw = self.image
        if not self.facing_right:
            player_image_to_draw = pygame.transform.flip(self.image, True, False)
        screen.blit(player_image_to_draw, self.rect)

        if self.is_hit:
            hit_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            hit_surface.fill((255, 0, 0, 100)) # Red, semi-transparent
            screen.blit(hit_surface, self.rect.topleft)

    def draw_health(self, screen):
        """Draws the player's health bar on the screen."""
        heart_spacing = 40
        start_x = 20
        start_y = screen.get_height() - 40

        for i in range(self.max_health // 2):
            heart_x = start_x + (i * heart_spacing)
            health_pair_value = self.health - (i * 2)
            
            if health_pair_value >= 2:
                screen.blit(self.heart_full, (heart_x, start_y))
            elif health_pair_value == 1:
                screen.blit(self.heart_half, (heart_x, start_y))
            else:
                screen.blit(self.heart_empty, (heart_x, start_y))

    def draw_enemy_health_bar(self, screen):
        """Draw simple horizontal health bar above enemy players only."""
        if not self.is_remote:
            return
        
        bar_width = 50
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 15  # Move health bar higher to avoid overlap with name

        health_ratio = max(self.health / self.max_health, 0)

        # Red background (damage/missing health)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Green foreground (current health)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))
        # Black border
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 1)

    def draw_name(self, screen):
        """Draw player name above the character."""
        if self.display_name:
            name_surface = self.name_font.render(self.display_name, True, (255, 255, 255))
            name_rect = name_surface.get_rect(center=(self.rect.centerx, self.rect.top - 5))
            screen.blit(name_surface, name_rect)

    def respawn(self, x=100, y=100):
        self.health = self.max_health
        self.rect.topleft = (x, y)
        self.is_hit = False
        self.is_attacking = False