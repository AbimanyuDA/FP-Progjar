import pygame
import os

class Player(pygame.sprite.Sprite):
    def __init__(self, id, x, y, animation_folder, client_interface, is_remote=False):
        super().__init__()
        # Multiplayer attributes
        self.id = id
        self.is_remote = is_remote
        self.client_interface = client_interface

        # --- Sword Attributes ---
        self.sword_image = pygame.image.load('assets/images/sword.png').convert_alpha()
        self.sword_image = pygame.transform.scale(self.sword_image, (self.sword_image.get_width() * 2, self.sword_image.get_height() * 2))
        self.original_sword_image = self.sword_image
        self.sword_offset_x = 20
        self.sword_offset_y = 10
        self.is_attacking = False
        self.attack_duration = 0.25 # in seconds
        self.attack_timer = 0
        self.hit_during_attack = set() # Tracks which players have been hit in the current swing

        # --- Health & Hit Attributes ---
        self.max_health = 6
        self.health = self.max_health
        self.is_hit = False
        self.hit_duration = 0.2 # How long the red flash lasts
        self.hit_timer = 0
        self.heart_full = pygame.image.load('assets/images/heart/ui_heart_full.png').convert_alpha()
        self.heart_half = pygame.image.load('assets/images/heart/ui_heart_half.png').convert_alpha()
        self.heart_empty = pygame.image.load('assets/images/heart/ui_heart_empty.png').convert_alpha()
        self.heart_full = pygame.transform.scale(self.heart_full, (32, 32))
        self.heart_half = pygame.transform.scale(self.heart_half, (32, 32))
        self.heart_empty = pygame.transform.scale(self.heart_empty, (32, 32))

        # Visual and positional attributes
        self.animation_frames = self.load_animation_frames(animation_folder)
        if not self.animation_frames:
            raise ValueError(f"Could not load animation frames from {animation_folder}")

        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))

        # Animation and movement attributes
        self.animation_speed = 10  # frames per second
        self.animation_timer = 0
        self.speed = 200  # pixels per second
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing_right = True

    def load_animation_frames(self, folder_path):
        """Loads all knight running animation frames from a folder."""
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

    def update(self, dt, walls, all_players):
        """Update player based on whether it's remote or local."""
        if self.is_remote:
            self.update_remote()
        else:
            self.update_local(dt, walls, all_players)

        # Update hit visual effect timer for all players
        if self.is_hit:
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                self.is_hit = False
                self.hit_timer = 0

    def update_local(self, dt, walls, all_players):
        """Update logic for the locally controlled player."""
        # --- Handle Input ---
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0
        moving = False

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
            
        # --- Attack Logic ---
        if keys[pygame.K_x] and not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0
            self.hit_during_attack.clear() # Clear hit set at the start of a new attack

        # --- Update State ---
        if self.is_attacking:
            self.attack_timer += dt
            self.check_attack_collision(all_players)
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False

        # --- Movement and Collision ---
        self.rect.x += self.velocity.x * dt
        self.handle_collision(walls, 'horizontal')
        self.rect.y += self.velocity.y * dt
        self.handle_collision(walls, 'vertical')

        # --- Animation ---
        self.update_animation(dt, moving)

        # --- Send State to Server ---
        # Assumes client_interface has a method to send the full state
        state = {
            'x': self.rect.x,
            'y': self.rect.y,
            'facing_right': self.facing_right,
            'is_attacking': self.is_attacking,
            'health': self.health,
            'is_hit': self.is_hit # Send hit state
        }
        self.client_interface.set_player_state(self.id, state)

    def update_remote(self):
        """Update logic for remote players based on server data."""
        # Assumes client_interface has a method to get a player's full state
        state = self.client_interface.get_player_state(self.id)
        if state:
            self.rect.x = state.get('x', self.rect.x)
            self.rect.y = state.get('y', self.rect.y)
            self.facing_right = state.get('facing_right', self.facing_right)
            self.is_attacking = state.get('is_attacking', self.is_attacking)
            self.health = state.get('health', self.health)
            self.is_hit = state.get('is_hit', self.is_hit) # Update hit state
            
            # A simple check for movement to drive animation
            # (This could be improved by sending a 'moving' state from the server)
            # For now, we assume if position changes, it's moving.
            # This part is tricky without knowing the server's exact data.
            # A placeholder for animation update:
            self.update_animation(0.1, True) # Simulate movement for animation

    def check_attack_collision(self, all_players):
        """Checks for collision between the sword and other players."""
        sword_rect = self.get_sword_rect()
        if sword_rect:
            for other_player in all_players:
                if other_player.id != self.id and other_player.id not in self.hit_during_attack:
                    if sword_rect.colliderect(other_player.rect):
                        # In a real multiplayer game, the server would validate this hit.
                        # For now, the client tells the other player it was hit.
                        # In our singleplayer test, this works directly.
                        other_player.register_hit()
                        self.hit_during_attack.add(other_player.id)

    def register_hit(self):
        """Registers that the player has been hit."""
        if not self.is_hit:
            self.take_damage(1)
            self.is_hit = True
            self.hit_timer = 0

    def take_damage(self, amount):
        """Reduces the player's health by the given amount."""
        self.health -= amount
        if self.health < 0:
            self.health = 0
        # Here you might want to add a check for player death

    def get_sword_rect(self):
        """Calculates the current hitbox of the sword."""
        # This is a simplified version. A more accurate implementation might use a rotated rect.
        if not self.is_attacking: return None
        
        # Create a rect for the sword's visual position
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

    def update_animation(self, dt, moving):
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
        # --- Draw Sword ---
        sword_img, sword_rect = self.get_sword_render_info()
        screen.blit(sword_img, sword_rect)

        # --- Draw Player ---
        player_image_to_draw = self.image
        if not self.facing_right:
            player_image_to_draw = pygame.transform.flip(self.image, True, False)
        screen.blit(player_image_to_draw, self.rect)

        # --- Draw Hit Flash ---
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
            # Determine the state of the heart pair (each pair represents 2 health points)
            health_pair_value = self.health - (i * 2)
            
            if health_pair_value >= 2:
                screen.blit(self.heart_full, (heart_x, start_y))
            elif health_pair_value == 1:
                screen.blit(self.heart_half, (heart_x, start_y))
            else:
                screen.blit(self.heart_empty, (heart_x, start_y))