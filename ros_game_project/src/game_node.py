#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import random
import sys
import math
import array
import rospy
from ros_game_project_msgs.msg import user_msg
from std_msgs.msg import String, Int64
from ros_game_project.srv import GetUserScore, GetUserScoreResponse
from ros_game_project.srv import SetGameDifficulty, SetGameDifficultyResponse

# ============================================================================
# GLOBAL CONFIGURATION - MODIFY THESE VALUES TO CUSTOMIZE THE GAME
# ============================================================================
# Initialize pygame to get screen dimensions
pygame.init()
info = pygame.display.Info()

# Screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Game FPS
BASE_FPS = 60

# Player configuration
PLAYER_SIZE = 40
PLAYER_LIVES = 3
JUMP_DISTANCE = 60  # Distance of each jump

# Collision system
INSTANT_DEATH = False

# Difficulty configuration
BASE_ENEMY_SPEED = 2
BASE_SPAWN_INTERVAL = 120
DIFFICULTY_INCREASE_RATE = 0.0002

# Scoring system
POINTS_PER_ROW = 10
POINTS_PER_COIN = 50

# Lane configuration
LANE_HEIGHT = 60
LANES_ON_SCREEN = SCREEN_HEIGHT // LANE_HEIGHT + 2

# Enhanced Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (46, 204, 113)  # Brighter green
DARK_GREEN = (22, 160, 133)  # Teal green
RED = (231, 76, 60)  # Vibrant red
YELLOW = (241, 196, 15)  # Golden yellow
BLUE = (52, 152, 219)  # Bright blue
DARK_BLUE = (41, 128, 185)  # Darker blue
GRAY = (149, 165, 166)  # Light gray
DARK_GRAY = (44, 62, 80)  # Dark slate
LIGHT_GRAY = (236, 240, 241)  # Very light gray
BROWN = (160, 82, 45)  # Saddle brown
SAND = (210, 180, 140)  # Tan
PURPLE = (155, 89, 182)  # Amethyst
ORANGE = (230, 126, 34)  # Carrot
PINK = (233, 30, 99)  # Pink
CYAN = (26, 188, 156)  # Turquoise

# ============================================================================
# GAME CLASSES
# ============================================================================

class SoundManager:
    """Manages all game sounds"""
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.audio_available = False
        
        # Try to initialize mixer with error handling
        try:
            pygame.mixer.init()
            self.audio_available = True
            # Create synthetic sounds
            self.create_sounds()
        except pygame.error as e:
            print(f"Audio not available: {e}")
            print("Game will continue without sound.")
            self.audio_available = False
    
    def create_sounds(self):
        """Creates synthetic sounds using pygame"""
        try:
            # Jump sound (short ascending beep)
            self.sounds['jump'] = self.create_jump_sound()
            
            # Coin sound (sharp ding)
            self.sounds['coin'] = self.create_coin_sound()
            
            # Hit sound (low buzz)
            self.sounds['hit'] = self.create_hit_sound()
            
            # Game over sound (descending)
            self.sounds['game_over'] = self.create_game_over_sound()
            
        except Exception as e:
            print(f"Could not create sounds: {e}")
    
    def create_jump_sound(self):
        """Creates a jump sound"""
        sample_rate = 22050
        duration = 0.1
        frequency = 440
        
        samples = int(sample_rate * duration)
        wave = [int(32767 * 0.3 * math.sin(2 * math.pi * frequency * (i + x * 500) / sample_rate)) 
                for x, i in enumerate(range(samples))]
        
        sound = pygame.sndarray.make_sound(array.array('h', wave * 2))
        sound.set_volume(0.3)
        return sound
    
    def create_coin_sound(self):
        """Creates a coin sound"""
        sample_rate = 22050
        duration = 0.15
        
        samples = int(sample_rate * duration)
        wave = []
        
        for i in range(samples):
            t = i / sample_rate
            freq = 880 + (440 * t / duration)
            amplitude = 0.4 * (1 - t / duration)
            wave.append(int(32767 * amplitude * math.sin(2 * math.pi * freq * t)))
        
        sound = pygame.sndarray.make_sound(array.array('h', wave * 2))
        sound.set_volume(0.4)
        return sound
    
    def create_hit_sound(self):
        """Creates a hit sound"""
        sample_rate = 22050
        duration = 0.2
        
        samples = int(sample_rate * duration)
        wave = []
        
        for i in range(samples):
            t = i / sample_rate
            freq = 200 - (100 * t / duration)
            amplitude = 0.5 * (1 - t / duration)
            noise = random.uniform(-0.3, 0.3)
            wave.append(int(32767 * (amplitude * math.sin(2 * math.pi * freq * t) + noise * 0.2)))
        
        sound = pygame.sndarray.make_sound(array.array('h', wave * 2))
        sound.set_volume(0.5)
        return sound
    
    def create_game_over_sound(self):
        """Creates a game over sound"""
        sample_rate = 22050
        duration = 0.5
        
        samples = int(sample_rate * duration)
        wave = []
        
        for i in range(samples):
            t = i / sample_rate
            freq = 440 - (300 * t / duration)
            amplitude = 0.6 * (1 - t / duration)
            wave.append(int(32767 * amplitude * math.sin(2 * math.pi * freq * t)))
        
        sound = pygame.sndarray.make_sound(array.array('h', wave * 2))
        sound.set_volume(0.6)
        return sound
    
    def play_sound(self, sound_name):
        """Plays a sound"""
        if self.audio_available and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def start_music(self):
        """Starts background music (simple note loop)"""
        if self.audio_available and not self.music_playing:
            self.music_playing = True
            # In a real implementation, you would load a music file here
            # pygame.mixer.music.load('music.mp3')
            # pygame.mixer.music.play(-1)
    
    def stop_music(self):
        """Stops the music"""
        if self.audio_available and self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False


class Player:
    """Represents the player controlled by the user"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.lives = PLAYER_LIVES
        self.max_row_reached = 0
        self.invincible_timer = 0
        self.on_log = None
        
        # Variables for jump animation
        self.is_jumping = False
        self.jump_start_x = x
        self.jump_start_y = y
        self.jump_target_x = x
        self.jump_target_y = y
        self.jump_progress = 0
        self.jump_speed = 0.15
        
        # Visual direction
        self.facing = 'up'

        color = rospy.get_param('~change_player_color')
        rospy.loginfo(f"Player color set to ¨{color}, (1 = red, 2 = purple, 3 = blue)")
        
        if color == 1:
            self.PLAYER_COLOR = (148, 9, 9) # Red
            self.GLOW_COLOR = (212, 70, 70)

        elif color == 2:
            self.PLAYER_COLOR = (155, 89, 182) # Purple
            self.GLOW_COLOR = (175, 119, 202)

        elif color == 3:
            self.PLAYER_COLOR = (13, 72, 148) # Blue
            self.GLOW_COLOR = (70, 132, 212)
        
    def get_rect(self):
        """Returns the player's collision rectangle"""
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, 
                          self.size, self.size)
    
    def start_jump(self, direction):
        """Starts a jump in the specified direction"""
        if self.is_jumping:
            return False
        
        self.jump_start_x = self.x
        self.jump_start_y = self.y
        self.jump_progress = 0
        
        # Calculate destination based on direction
        if direction == 'up':
            self.jump_target_x = self.x
            self.jump_target_y = self.y - JUMP_DISTANCE
            self.facing = 'up'
        elif direction == 'down':
            self.jump_target_x = self.x
            self.jump_target_y = self.y + JUMP_DISTANCE
            self.facing = 'down'
        elif direction == 'left':
            self.jump_target_x = self.x - JUMP_DISTANCE
            self.jump_target_y = self.y
            self.facing = 'left'
        elif direction == 'right':
            self.jump_target_x = self.x + JUMP_DISTANCE
            self.jump_target_y = self.y
            self.facing = 'right'
        
        # Check horizontal boundaries
        self.jump_target_x = max(self.size // 2, min(SCREEN_WIDTH - self.size // 2, self.jump_target_x))
        
        self.is_jumping = True
        return True
    
    def update(self, camera_y):
        """Updates the player's state"""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # Update jump animation
        if self.is_jumping:
            self.jump_progress += self.jump_speed
            
            if self.jump_progress >= 1.0:
                self.x = self.jump_target_x
                self.y = self.jump_target_y
                self.is_jumping = False
                self.jump_progress = 1.0
            else:
                # Smooth interpolation with parabolic arc
                t = self.jump_progress
                # Ease out cubic
                t = 1 - pow(1 - t, 3)
                
                self.x = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * t
                self.y = self.jump_start_y + (self.jump_target_y - self.jump_start_y) * t
        
        # If on a log AND not jumping, move with it
        if self.on_log and not self.is_jumping:
            self.x += self.on_log.speed
            self.x = max(self.size // 2, min(SCREEN_WIDTH - self.size // 2, self.x))
    
    def hit(self):
        """Handles when the player is hit"""
        if self.invincible_timer > 0:
            return False
        
        if INSTANT_DEATH:
            self.lives = 0
        else:
            self.lives -= 1
            self.invincible_timer = 60  # 1 second at 60 FPS
        
        return True
    
    def draw(self, screen, camera_y):
        """Draws the player on screen"""
        screen_y = self.y - camera_y
        
        # Only draw if visible
        if -50 < screen_y < SCREEN_HEIGHT + 50:
            # Color with invincibility effect
            if self.invincible_timer > 0 and (self.invincible_timer // 10) % 2 == 0:
                color = (255, 150, 255)  # Bright pink for invincibility
                glow_color = (255, 200, 255)
            else:
                color = self.PLAYER_COLOR
                glow_color = self.GLOW_COLOR  
            
            # "Stretching" effect during jump
            scale = 1.0
            if self.is_jumping:
                jump_height = abs(math.sin(self.jump_progress * math.pi)) * 15
                screen_y -= jump_height
                scale = 1.0 + (math.sin(self.jump_progress * math.pi) * 0.3)
            
            # Body with glow effect
            size = int(self.size * scale)
            
            # Outer glow
            pygame.draw.circle(screen, glow_color, (int(self.x), int(screen_y)), size // 2 + 3)
            # Main body
            pygame.draw.circle(screen, color, (int(self.x), int(screen_y)), size // 2)
            # Inner highlight
            highlight_color = tuple(min(255, c + 40) for c in color)
            pygame.draw.circle(screen, highlight_color, (int(self.x - 3), int(screen_y - 3)), size // 3)
            
            # Eyes with better positioning
            eye_offset = size // 5
            eye_size = max(3, size // 12)
            
            if self.facing == 'up':
                eye_y = screen_y - eye_offset
            elif self.facing == 'down':
                eye_y = screen_y + eye_offset
            else:
                eye_y = screen_y - eye_offset // 2
            
            # Eye whites
            pygame.draw.circle(screen, WHITE, (int(self.x - eye_offset), int(eye_y)), eye_size + 1)
            pygame.draw.circle(screen, WHITE, (int(self.x + eye_offset), int(eye_y)), eye_size + 1)
            
            # Eye pupils
            pygame.draw.circle(screen, BLACK, (int(self.x - eye_offset), int(eye_y)), eye_size)
            pygame.draw.circle(screen, BLACK, (int(self.x + eye_offset), int(eye_y)), eye_size)
            
            # Eye highlights
            pygame.draw.circle(screen, WHITE, (int(self.x - eye_offset - 1), int(eye_y - 1)), 1)
            pygame.draw.circle(screen, WHITE, (int(self.x + eye_offset - 1), int(eye_y - 1)), 1)


class Enemy:
    """Represents a mobile obstacle/enemy (vehicles)"""
    def __init__(self, lane_y, direction, speed, enemy_type='car'):
        self.y = lane_y
        self.direction = direction
        self.speed = speed * direction
        self.enemy_type = enemy_type
        
        if direction > 0:
            self.x = -100
        else:
            self.x = SCREEN_WIDTH + 100
        
        if enemy_type == 'car':
            self.width = 80
            self.height = 40
            self.color = RED
        elif enemy_type == 'truck':
            self.width = 120
            self.height = 45
            self.color = DARK_GRAY
        else:  # 'fast'
            self.width = 60
            self.height = 35
            self.color = YELLOW
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2,
                          self.width, self.height)
    
    def update(self):
        self.x += self.speed
    
    def is_off_screen(self):
        return self.x < -200 or self.x > SCREEN_WIDTH + 200
    
    def draw(self, screen, camera_y):
        screen_y = self.y - camera_y
        if -100 < screen_y < SCREEN_HEIGHT + 100:
            rect = pygame.Rect(self.x - self.width // 2, screen_y - self.height // 2,
                              self.width, self.height)
            
            # Shadow effect
            shadow_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
            pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=5)
            
            # Main body with gradient effect
            pygame.draw.rect(screen, self.color, rect, border_radius=5)
            
            # Highlight on top
            highlight_color = tuple(min(255, c + 30) for c in self.color)
            highlight_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height // 3)
            pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=3)
            
            # Windows with reflection
            if self.enemy_type == 'car':
                window_color = CYAN
                window_highlight = (100, 200, 255)
            elif self.enemy_type == 'truck':
                window_color = GRAY
                window_highlight = (200, 200, 200)
            else:  # fast
                window_color = YELLOW
                window_highlight = (255, 255, 150)
            
            window_rect = pygame.Rect(rect.x + 8, rect.y + 4, rect.width - 16, rect.height - 8)
            pygame.draw.rect(screen, window_color, window_rect, border_radius=2)
            
            # Window reflection
            reflection_rect = pygame.Rect(window_rect.x + 2, window_rect.y + 2, window_rect.width // 2, window_rect.height // 2)
            pygame.draw.rect(screen, window_highlight, reflection_rect, border_radius=1)
            
            # Wheels
            wheel_color = DARK_GRAY
            wheel_size = 6
            pygame.draw.circle(screen, wheel_color, (rect.x + 8, rect.bottom - 4), wheel_size)
            pygame.draw.circle(screen, wheel_color, (rect.right - 8, rect.bottom - 4), wheel_size)
            pygame.draw.circle(screen, BLACK, (rect.x + 8, rect.bottom - 4), wheel_size - 2)
            pygame.draw.circle(screen, BLACK, (rect.right - 8, rect.bottom - 4), wheel_size - 2)


class Log:
    """Represents a floating log in the river"""
    def __init__(self, lane_y, direction, speed):
        self.y = lane_y
        self.direction = direction
        self.speed = speed * direction
        
        if direction > 0:
            self.x = -150
        else:
            self.x = SCREEN_WIDTH + 150
        
        self.width = random.randint(120, 200)
        self.height = 45
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2,
                          self.width, self.height)
    
    def update(self):
        self.x += self.speed
    
    def is_off_screen(self):
        return self.x < -300 or self.x > SCREEN_WIDTH + 300
    
    def draw(self, screen, camera_y):
        screen_y = self.y - camera_y
        if -100 < screen_y < SCREEN_HEIGHT + 100:
            rect = pygame.Rect(self.x - self.width // 2, screen_y - self.height // 2,
                              self.width, self.height)
            
            # Shadow in water
            shadow_rect = pygame.Rect(rect.x + 1, rect.y + 1, rect.width, rect.height)
            pygame.draw.rect(screen, (0, 0, 0, 30), shadow_rect, border_radius=8)
            
            # Main log body with gradient
            pygame.draw.rect(screen, BROWN, rect, border_radius=8)
            
            # Top highlight
            highlight_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height // 4)
            pygame.draw.rect(screen, (180, 100, 60), highlight_rect, border_radius=4)
            
            # Wood grain lines
            for i in range(4):
                line_y = screen_y - 8 + i * 8
                if i % 2 == 0:
                    line_color = (120, 60, 20)
                else:
                    line_color = (100, 50, 10)
                pygame.draw.line(screen, line_color, 
                               (rect.x + 8, line_y), 
                               (rect.x + rect.width - 8, line_y), 2)
            
            # Bark texture
            for i in range(0, rect.width, 15):
                bark_x = rect.x + i
                pygame.draw.line(screen, (80, 40, 5), 
                               (bark_x, rect.y + 2), 
                               (bark_x, rect.bottom - 2), 1)


class Coin:
    """Represents a collectible coin"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.collected = False
        self.animation_frame = 0
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                          self.size, self.size)
    
    def update(self):
        self.animation_frame += 1
    
    def draw(self, screen, camera_y):
        if not self.collected:
            screen_y = self.y - camera_y
            if -50 < screen_y < SCREEN_HEIGHT + 50:
                # Pulsing animation
                scale = abs((self.animation_frame % 40) - 20) / 20
                width = int(self.size * scale)
                if width > 2:
                    # Glow effect
                    glow_rect = pygame.Rect(self.x - width // 2 - 3, screen_y - self.size // 2 - 3,
                                          width + 6, self.size + 6)
                    pygame.draw.ellipse(screen, (255, 255, 100), glow_rect)
                    
                    # Main coin
                    rect = pygame.Rect(self.x - width // 2, screen_y - self.size // 2,
                                      width, self.size)
                    pygame.draw.ellipse(screen, YELLOW, rect)
                    
                    # Inner highlight
                    highlight_rect = pygame.Rect(self.x - width // 4, screen_y - self.size // 4,
                                               width // 2, self.size // 2)
                    pygame.draw.ellipse(screen, (255, 255, 150), highlight_rect)
                    
                    # Border
                    pygame.draw.ellipse(screen, (218, 165, 32), rect, 2)
                    
                    # Sparkle effect
                    if self.animation_frame % 20 < 10:
                        sparkle_x = self.x + random.randint(-width//2, width//2)
                        sparkle_y = screen_y + random.randint(-self.size//2, self.size//2)
                        pygame.draw.circle(screen, WHITE, (sparkle_x, sparkle_y), 1)


class Lane:
    """Represents a lane with its configuration"""
    def __init__(self, row_number, lane_type=None):
        self.row_number = row_number
        self.y = row_number * LANE_HEIGHT
        
        if lane_type is None:
            self.lane_type = self.generate_lane_type(row_number)
        else:
            self.lane_type = lane_type
        
        self.direction = random.choice([-1, 1])
        self.spawn_timer = random.randint(0, BASE_SPAWN_INTERVAL)
        self.enemy_type = random.choice(['car', 'car', 'truck', 'fast'])
        
    def generate_lane_type(self, row):
        """Generates lane type based on patterns"""
        if row == 0:
            return 'grass'
        
        # Ensure first few levels are safe (grass/sidewalk)
        if row >= -3:  # First few levels are safe
            return random.choice(['grass', 'grass', 'sidewalk'])
        
        zone = (abs(row) // 6) % 4
        
        if zone == 0:
            return random.choice(['grass', 'grass', 'sidewalk'])
        elif zone == 1:
            return 'road'
        elif zone == 2:
            return random.choice(['grass', 'sidewalk'])
        else:
            return 'river'
    
    def reset_spawn_timer(self, difficulty_multiplier):
        base_interval = BASE_SPAWN_INTERVAL / difficulty_multiplier
        self.spawn_timer = random.randint(int(base_interval * 0.8), int(base_interval * 1.5))
    
    def draw(self, screen, camera_y):
        """Draws the lane with its visual style"""
        screen_y = self.y - camera_y
        
        if -LANE_HEIGHT < screen_y < SCREEN_HEIGHT + LANE_HEIGHT:
            rect = pygame.Rect(0, screen_y, SCREEN_WIDTH, LANE_HEIGHT)
            
            if self.lane_type == 'grass':
                base_color = GREEN if self.row_number % 2 == 0 else DARK_GREEN
                pygame.draw.rect(screen, base_color, rect)
                
                # Static grass texture with consistent pattern
                for i in range(0, SCREEN_WIDTH, 8):
                    for j in range(0, LANE_HEIGHT, 6):
                        grass_x = i + (self.row_number * 7) % 8
                        grass_y = screen_y + j + (self.row_number * 3) % 6
                        if 0 < grass_x < SCREEN_WIDTH:
                            # Fixed grass blade height and color
                            blade_height = 4
                            grass_color = (34, 180, 80)
                            
                            # Draw grass blade
                            pygame.draw.line(screen, grass_color, 
                                           (grass_x, grass_y), 
                                           (grass_x, grass_y - blade_height), 1)
                
                # Static natural details
                for i in range(0, SCREEN_WIDTH, 60):
                    detail_x = i + (self.row_number * 23) % 60
                    detail_y = screen_y + (self.row_number * 17) % LANE_HEIGHT
                    # Fixed pattern for stones and grass tufts
                    if (i + self.row_number) % 3 == 0:
                        # Small stones
                        pygame.draw.circle(screen, (120, 100, 80), (detail_x, detail_y), 1)
                    elif (i + self.row_number) % 5 == 0:
                        # Small grass tufts
                        for k in range(3):
                            tuft_x = detail_x + k - 1
                            tuft_y = detail_y + k
                            pygame.draw.line(screen, (50, 150, 60), 
                                           (tuft_x, tuft_y), 
                                           (tuft_x, tuft_y - 2), 1)
            
            elif self.lane_type == 'sidewalk':
                # Concrete sidewalk base
                concrete_color = (200, 200, 200)
                pygame.draw.rect(screen, concrete_color, rect)
                
                # Concrete texture with subtle variations
                for y in range(0, LANE_HEIGHT, 4):
                    for x in range(0, SCREEN_WIDTH, 8):
                        # Random concrete grain
                        grain_intensity = random.randint(-15, 15)
                        grain_color = tuple(max(0, min(255, c + grain_intensity)) for c in concrete_color)
                        pygame.draw.line(screen, grain_color, (x, screen_y + y), (x + 4, screen_y + y), 1)
                
                # Concrete slab divisions (like real sidewalks)
                for i in range(0, SCREEN_WIDTH, 80):
                    # Vertical slab lines
                    pygame.draw.line(screen, (180, 180, 180), (i, screen_y), (i, screen_y + LANE_HEIGHT), 2)
                    
                    # Horizontal slab lines (every other slab)
                    if (i // 80) % 2 == 0:
                        pygame.draw.line(screen, (180, 180, 180), (i, screen_y + LANE_HEIGHT // 2), (i + 80, screen_y + LANE_HEIGHT // 2), 2)
                
                # Concrete wear patterns
                for i in range(0, SCREEN_WIDTH, 40):
                    wear_x = i + (self.row_number * 13) % 40
                    wear_y = screen_y + (self.row_number * 7) % LANE_HEIGHT
                    if random.random() < 0.3:
                        # Subtle wear marks
                        pygame.draw.circle(screen, (190, 190, 190), (wear_x, wear_y), 2)
                
                # Sidewalk edge lines
                pygame.draw.line(screen, (160, 160, 160), (0, screen_y), (SCREEN_WIDTH, screen_y), 1)
                pygame.draw.line(screen, (160, 160, 160), (0, screen_y + LANE_HEIGHT), (SCREEN_WIDTH, screen_y + LANE_HEIGHT), 1)
            
            elif self.lane_type == 'road':
                # Asphalt road base
                asphalt_color = (60, 60, 60)
                pygame.draw.rect(screen, asphalt_color, rect)
                
                # Static asphalt texture
                for y in range(0, LANE_HEIGHT, 3):
                    for x in range(0, SCREEN_WIDTH, 6):
                        # Fixed asphalt grain
                        grain_color = (55, 55, 55)
                        pygame.draw.line(screen, grain_color, (x, screen_y + y), (x + 3, screen_y + y), 1)
                
                # Road wear patterns (darker areas where cars drive)
                for i in range(0, SCREEN_WIDTH, 100):
                    wear_rect = pygame.Rect(i, screen_y + LANE_HEIGHT // 4, 80, LANE_HEIGHT // 2)
                    pygame.draw.rect(screen, (50, 50, 50), wear_rect)
                
                # Lane markings with realistic spacing
                for i in range(0, SCREEN_WIDTH, 60):
                    if i % 120 < 60:
                        # Dashed center line
                        pygame.draw.rect(screen, WHITE, 
                                       (i, screen_y + LANE_HEIGHT // 2 - 2, 40, 4))
                        
                        # Road reflectors (smaller, more realistic)
                        pygame.draw.circle(screen, YELLOW, 
                                         (i + 20, int(screen_y + LANE_HEIGHT // 2)), 1)
                
                # Road edges
                pygame.draw.line(screen, (40, 40, 40), (0, screen_y), (SCREEN_WIDTH, screen_y), 2)
                pygame.draw.line(screen, (40, 40, 40), (0, screen_y + LANE_HEIGHT), (SCREEN_WIDTH, screen_y + LANE_HEIGHT), 2)
                
                # Static oil stains and road wear
                for i in range(0, SCREEN_WIDTH, 80):
                    stain_x = i + (self.row_number * 19) % 80
                    stain_y = screen_y + (self.row_number * 11) % LANE_HEIGHT
                    # Fixed pattern for oil stains
                    if (i + self.row_number) % 4 == 0:
                        # Oil stain
                        pygame.draw.circle(screen, (30, 30, 30), (stain_x, stain_y), 3)
                        pygame.draw.circle(screen, (20, 20, 20), (stain_x, stain_y), 2)
            
            elif self.lane_type == 'river':
                # Realistic water with depth
                base_water_color = (30, 144, 255)  # Deep blue
                
                # Water base
                pygame.draw.rect(screen, base_water_color, rect)
                
                # Water depth effect with darker bottom
                for y in range(LANE_HEIGHT):
                    water_y = screen_y + y
                    depth_factor = y / LANE_HEIGHT
                    # Darker towards bottom
                    r = int(30 + depth_factor * 20)
                    g = int(144 - depth_factor * 30)
                    b = int(255 - depth_factor * 40)
                    water_color = (r, g, b)
                    pygame.draw.line(screen, water_color, (0, water_y), (SCREEN_WIDTH, water_y))
                
                # Animated flowing water effect
                time = pygame.time.get_ticks() // 50
                for i in range(0, SCREEN_WIDTH, 30):
                    wave_x = (i + time * 2) % (SCREEN_WIDTH + 30)
                    wave_y = screen_y + LANE_HEIGHT // 2 + int(3 * math.sin((wave_x + time) * 0.1))
                    
                    # Main wave
                    pygame.draw.circle(screen, (100, 200, 255), (wave_x, wave_y), 8, 1)
                    # Wave highlight
                    pygame.draw.circle(screen, (150, 220, 255), (wave_x - 2, wave_y - 2), 4, 1)
                
                # Secondary smaller waves
                for i in range(0, SCREEN_WIDTH, 15):
                    small_wave_x = (i + time * 3) % (SCREEN_WIDTH + 15)
                    small_wave_y = screen_y + LANE_HEIGHT // 2 + int(2 * math.sin((small_wave_x + time * 1.5) * 0.15))
                    pygame.draw.circle(screen, (120, 180, 255), (small_wave_x, small_wave_y), 3, 1)
                
                # Water foam/bubbles
                for i in range(0, SCREEN_WIDTH, 40):
                    bubble_x = i + (self.row_number * 17) % 40
                    bubble_y = screen_y + (self.row_number * 11) % LANE_HEIGHT
                    if random.random() < 0.4:
                        # Small bubbles
                        pygame.draw.circle(screen, (200, 230, 255), (bubble_x, bubble_y), 1)
                        pygame.draw.circle(screen, WHITE, (bubble_x, bubble_y), 1, 1)
                
                # Water surface reflection
                for i in range(0, SCREEN_WIDTH, 60):
                    reflection_x = i + (self.row_number * 23) % 60
                    reflection_y = screen_y + 5
                    pygame.draw.line(screen, (180, 220, 255), 
                                   (reflection_x, reflection_y), 
                                   (reflection_x + 20, reflection_y), 1)


class Game:
    """Main class that handles game logic"""
    def __init__(self):
        rospy.init_node("GAME_NODE")
        rospy.loginfo("Game node started!")
        self.__sub_usr = rospy.Subscriber("user_information", user_msg, self.userinfo_callback)
        self.__sub_cmd = rospy.Subscriber("keyboard_control", String, self.command_callback)
        self.__pub = rospy.Publisher("result_information", Int64, queue_size = 10)
        self.last_command = None 
        self.username = None
        self.name = None
        self.age = None
        self.published_score = False
        self.difficulty_chosen = 1.0

        rospy.Service('user_score', GetUserScore, self.handle_get_user_score)
        rospy.Service('difficulty', SetGameDifficulty, self.handle_set_game_difficulty)
        self.max_score = 10000
        self.user_scores = {}

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Infinite Crossy Road")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Sound system
        self.sound_manager = SoundManager()
        
        self.reset_game()

        self.game_state = 'waiting_user'

    def handle_get_user_score(self, req):
        requested_user = req.username
        
        last_score = self.user_scores.get(requested_user, 0)
        
        percentage = int((last_score / self.max_score) * 100.0)
                
        rospy.loginfo(f"Service 'user_score' called for {requested_user}. Percentage sent: {percentage:.2f}%")

        return GetUserScoreResponse(percentage)

    def handle_set_game_difficulty(self, req):
        difficulty_level = req.change_difficulty.lower()
        success = False

        current_phase = rospy.get_param('~screen_param')
        if current_phase == 'phase1':
            success = True

            if difficulty_level == 'easy':
                self.difficulty_chosen = 0.5
                rospy.loginfo("Success. Game difficulty set to EASY (0.5x).")

            elif difficulty_level == 'medium':
                self.difficulty_chosen = 1.0
                rospy.loginfo("Success. Game difficulty set to MEDIUM (1.0x).")

            elif difficulty_level == 'hard':
                self.difficulty_chosen = 1.5
                rospy.loginfo("Success. Game difficulty set to HARD (1.5x).")

        else:
            success = False
            rospy.loginfo("Failure. Could not change the difficulty (not in phase1)")
        
        return SetGameDifficultyResponse(success)

    def userinfo_callback(self,msg):
        self.name = msg.name
        self.username = msg.username
        try:
            self.age = int(msg.age) 
        except:
            self.age = 0

        rospy.loginfo(f"New user logged!---------")
        rospy.loginfo(f"Name: {self.name}")     
        rospy.loginfo(f"Age: {self.age}")

        rospy.set_param('/user_name', self.name)
        rospy.loginfo(f"User name received set user_name parameter to: {self.name}")
        
        if self.game_state == 'waiting_user':
            self.game_state = 'welcome'

    def command_callback(self,msg):
        self.last_command = msg.data.upper().strip() # Receive command
        rospy.loginfo(f"Command received: {self.last_command}")

    def handle_input(self, cmd):
        moved = False
        
        if cmd == "UP":
            moved = self.player.start_jump('up')
        elif cmd == "DOWN":       
            moved = self.player.start_jump('down')
        elif cmd == "RIGHT":       
            moved = self.player.start_jump('right')
        elif cmd == "LEFT":       
            moved = self.player.start_jump('left')
        if moved: 
            self.sound_manager.play_sound('jump')        
    
    def reset_game(self):
        """Resets all game values"""
        self.lanes = {}
        self.lowest_row_generated = 0
        
        # Generate initial lanes downward
        for i in range(LANES_ON_SCREEN + 5):
            row_num = -i
            self.lanes[row_num] = Lane(row_num)
            self.lowest_row_generated = row_num
        
        # Find a safe lane (grass or sidewalk) to spawn the player
        safe_row = 0
        for row_num in sorted(self.lanes.keys(), reverse=True):
            if self.lanes[row_num].lane_type in ['grass', 'sidewalk']:
                safe_row = row_num
                break
        
        # If no safe one found, force lane 0 to be grass
        if self.lanes[safe_row].lane_type not in ['grass', 'sidewalk']:
            self.lanes[0] = Lane(0, lane_type='grass')
            safe_row = 0
        
        # Place player in center of safe lane
        spawn_y = safe_row * LANE_HEIGHT + LANE_HEIGHT // 2
        self.player = Player(SCREEN_WIDTH // 2, spawn_y)
        self.camera_y = spawn_y - SCREEN_HEIGHT + 100
        
        self.enemies = []
        self.logs = []
        self.coins = []
        self.score = 0
        self.coins_collected = 0
        self.game_state = 'welcome'
        self.difficulty_multiplier = 1.0
        self.frames_played = 0
        
        # Life gain animation
        self.life_gain_timer = 0
        self.life_gain_text = ""
        
        # Pause menu
        self.paused = False
        
        # Key control (to prevent multiple jumps)
        self.key_pressed = {'up': False, 'down': False, 'left': False, 'right': False}
    
    def generate_new_lanes(self):
        """Generates new lanes when player advances upward"""
        # Calculate which row is at the top (most negative)
        top_row = int(self.camera_y // LANE_HEIGHT) - 2
        target_row = top_row - LANES_ON_SCREEN - 10
        
        # Generate necessary lanes upward (more negative numbers)
        while self.lowest_row_generated > target_row:
            self.lowest_row_generated -= 1
            self.lanes[self.lowest_row_generated] = Lane(self.lowest_row_generated)
    
    def cleanup_old_lanes(self):
        """Removes lanes that are far below (positive numbers)"""
        bottom_row = int(self.camera_y // LANE_HEIGHT) + LANES_ON_SCREEN + 5
        
        lanes_to_remove = [row for row in self.lanes.keys() if row > bottom_row]
        for row in lanes_to_remove:
            del self.lanes[row]
        
        # Clean up enemies and logs out of range
        self.enemies = [e for e in self.enemies if not e.is_off_screen() and 
                       abs(e.y - self.camera_y) < SCREEN_HEIGHT * 3]
        self.logs = [l for l in self.logs if not l.is_off_screen() and 
                    abs(l.y - self.camera_y) < SCREEN_HEIGHT * 3]
    
    def update_camera(self):
        """Updates camera position to follow the player"""
        target_camera = self.player.y - SCREEN_HEIGHT * 0.6
        
        if target_camera < self.camera_y:
            self.camera_y = target_camera
    
    def spawn_enemy(self, lane):
        """Spawns an enemy in the specified lane"""
        if lane.lane_type != 'road':
            return
        if lane.enemy_type == 'truck' and random.random() > 0.5:
            return
        
        speed = BASE_ENEMY_SPEED * self.difficulty_multiplier
        
        if lane.enemy_type == 'fast':
            speed *= 1.5
        elif lane.enemy_type == 'truck':
            speed *= 0.7
        
        enemy = Enemy(lane.y + LANE_HEIGHT // 2, lane.direction, speed, lane.enemy_type)
        self.enemies.append(enemy)
    
    def spawn_log(self, lane):
        """Spawns a log in the specified lane"""
        if lane.lane_type != 'river':
            return
        
        speed = BASE_ENEMY_SPEED * 0.8 * self.difficulty_multiplier
        log = Log(lane.y + LANE_HEIGHT // 2, lane.direction, speed)
        self.logs.append(log)
    
    def spawn_coin(self):
        """Spawns a coin in a random safe position"""
        if random.random() < 0.015:
            player_row = int(self.player.y // LANE_HEIGHT)
            
            for _ in range(5):
                row = random.randint(player_row - 10, player_row - 5)
                if row in self.lanes:
                    lane = self.lanes[row]
                    if lane.lane_type in ['grass', 'sidewalk']:
                        x = random.randint(100, SCREEN_WIDTH - 100)
                        y = lane.y + LANE_HEIGHT // 2
                        
                        safe = True
                        for enemy in self.enemies:
                            if abs(enemy.x - x) < 150 and abs(enemy.y - y) < LANE_HEIGHT:
                                safe = False
                                break
                        
                        if safe:
                            self.coins.append(Coin(x, y))
                            break
    
    def update_difficulty(self):
        """Updates difficulty based on height reached"""
        # Calculate height reached (more negative = higher up)
        height_reached = abs(self.player.max_row_reached)
        # Increase difficulty by 0.1 for every 10 rows of height
        self.difficulty_multiplier = 1.0 + (height_reached * (self.difficulty_chosen*0.01))
    
    def check_collisions(self):
        """Checks player collisions"""
        # Only check collisions if not jumping
        if self.player.is_jumping:
            return
        
        player_rect = self.player.get_rect()
        player_row = int(self.player.y // LANE_HEIGHT)
        
        if player_row in self.lanes:
            current_lane = self.lanes[player_row]
            
            if current_lane.lane_type == 'river':
                self.player.on_log = None
                on_log = False
                
                for log in self.logs:
                    if player_rect.colliderect(log.get_rect()):
                        on_log = True
                        self.player.on_log = log
                        break
                
                if not on_log:
                    if self.player.hit():
                        self.sound_manager.play_sound('hit')
                        if self.player.lives <= 0:
                            self.sound_manager.play_sound('game_over')
                            self.game_state = 'game_over'
            else:
                self.player.on_log = None
        
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                if self.player.hit():
                    self.sound_manager.play_sound('hit')
                    if self.player.lives <= 0:
                        self.sound_manager.play_sound('game_over')
                        self.game_state = 'game_over'
        
        for coin in self.coins[:]:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                self.score += POINTS_PER_COIN
                self.coins_collected += 1
                self.coins.remove(coin)
                self.sound_manager.play_sound('coin')
                
                # Check if player earned a new life (every 10 coins)
                if self.coins_collected % 10 == 0:
                    self.player.lives += 1
                    self.life_gain_timer = 60  # 1 second at 60 FPS
                    self.life_gain_text = "+1 LIFE!"
                    # Play a special sound (reuse coin sound with extra feedback)
                    self.sound_manager.play_sound('coin')
                    self.sound_manager.play_sound('jump')
    
    def update_score_by_position(self):
        """Updates score based on player progress"""
        current_row = int(self.player.y // LANE_HEIGHT)
        
        if current_row < self.player.max_row_reached:
            rows_advanced = self.player.max_row_reached - current_row
            self.score += rows_advanced * POINTS_PER_ROW
            self.player.max_row_reached = current_row
    
    def handle_input(self, cmd):
        moved = False
        
        # UP / W
        if cmd == "UP":
            if self.player.start_jump('up'):
                self.sound_manager.play_sound('jump')
                self.key_pressed['up'] = True
        elif not cmd == "UP":
            self.key_pressed['up'] = False
        
        # DOWN / S
        if cmd == "DOWN":
            if self.player.start_jump('down'):
                self.sound_manager.play_sound('jump')
                self.key_pressed['down'] = True
        elif not cmd == "DOWN":
            self.key_pressed['down'] = False
        
        # LEFT / A
        if cmd == "LEFT":
            if self.player.start_jump('left'):
                self.sound_manager.play_sound('jump')
                self.key_pressed['left'] = True
        elif not cmd == "LEFT":
            self.key_pressed['left'] = False
        
        # RIGHT / D
        if cmd == "RIGHT":
            if self.player.start_jump('right'):
                self.sound_manager.play_sound('jump')
                self.key_pressed['right'] = True
        elif not cmd == "RIGHT":
            self.key_pressed['right'] = False
    
    def update(self):
        """Updates game state"""
        if self.game_state != 'playing' or self.paused:
            return
        
        self.frames_played += 1
        
        # Update life gain animation timer
        if self.life_gain_timer > 0:
            self.life_gain_timer -= 1
        
        # Update camera
        self.update_camera()
        
        # Generate new lanes infinitely
        self.generate_new_lanes()
        self.cleanup_old_lanes()
        
        # Update player
        self.player.update(self.camera_y)
        
        # Update difficulty
        self.update_difficulty()
        
        # Spawning by ALL lanes (not just visible ones)
        # This ensures that lanes continue spawning even when off-screen
        camera_row = int(self.camera_y // LANE_HEIGHT)
        for row in range(camera_row - LANES_ON_SCREEN - 5, camera_row + LANES_ON_SCREEN + 5):
            if row in self.lanes:
                lane = self.lanes[row]
                lane.spawn_timer -= 1
                
                if lane.spawn_timer <= 0:
                    if lane.lane_type == 'road':
                        self.spawn_enemy(lane)
                    elif lane.lane_type == 'river':
                        self.spawn_log(lane)
                    
                    lane.reset_spawn_timer(self.difficulty_multiplier)
        
        # Coin spawning
        self.spawn_coin()
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update()
            if enemy.is_off_screen():
                self.enemies.remove(enemy)
        
        # Update logs
        for log in self.logs[:]:
            log.update()
            if log.is_off_screen():
                self.logs.remove(log)
        
        # Update coins
        for coin in self.coins[:]:
            coin.update()
            if abs(coin.y - self.camera_y) > SCREEN_HEIGHT * 2:
                self.coins.remove(coin)
        
        # Check collisions
        self.check_collisions()
        
        # Update score
        self.update_score_by_position()
    
    def draw_welcome_screen(self):
        """Draws the welcome screen"""
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            color_intensity = int(46 + (y / SCREEN_HEIGHT) * 50)
            color = (color_intensity, color_intensity + 100, color_intensity + 50)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Decorative elements
        for i in range(0, SCREEN_WIDTH, 100):
            for j in range(0, SCREEN_HEIGHT, 80):
                pygame.draw.circle(self.screen, (255, 255, 255, 30), (i, j), 2)
        
        # Title with multiple shadows for depth
        title_text = self.font.render("INFINITE CROSSY ROAD", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        
        # Multiple shadow layers
        for offset in [(4, 4), (3, 3), (2, 2), (1, 1)]:
            shadow_text = self.font.render("INFINITE CROSSY ROAD", True, BLACK)
            shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], SCREEN_HEIGHT // 3 + offset[1]))
            self.screen.blit(shadow_text, shadow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Decorative border
        pygame.draw.rect(self.screen, WHITE, (10, 10, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20), 3)
        
        instructions = [
             "WELCOME USER!------------",
            f"    > Name: {self.name}",
            f"    > Userame: {self.username}",
            f"    > Age: {self.age}",
            "",
            "Press SPACE to start",
            "",
            "Controls: ARROW KEYS or WASD to jump",
            "F to toggle fullscreen",
            "",
            "Advance upward!",
            "Dodge vehicles, jump on logs,",
            "and collect coins!"
        ]
        
        y_offset = SCREEN_HEIGHT // 2
        for line in instructions:
            text = self.small_font.render(line, True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 30
    
    def draw_pause_menu(self):
        """Draws the pause menu overlay"""
        # Semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Pause title
        pause_title = self.font.render("PAUSED", True, WHITE)
        pause_rect = pause_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        
        # Shadow for title
        shadow_title = self.font.render("PAUSED", True, DARK_GRAY)
        shadow_rect = shadow_title.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 3 + 3))
        self.screen.blit(shadow_title, shadow_rect)
        self.screen.blit(pause_title, pause_rect)
        
        # Menu options
        options = [
            "Press ESC to Continue",
            "Press R to Restart",
            "Press SPACE to Exit"
        ]
        
        y_offset = SCREEN_HEIGHT // 2
        for i, line in enumerate(options):
            # Highlight current option with color
            if i == 0:
                color = GREEN
            elif i == 1:
                color = YELLOW
            else:
                color = RED
            
            text = self.small_font.render(line, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            
            # Background box for each option
            box = pygame.Rect(rect.x - 10, rect.y - 5, rect.width + 20, rect.height + 10)
            pygame.draw.rect(self.screen, (40, 40, 40), box, border_radius=5)
            pygame.draw.rect(self.screen, color, box, 2, border_radius=5)
            
            self.screen.blit(text, rect)
            y_offset += 50
    
    def draw_game_over_screen(self):
        """Draws the game over screen"""
        # Dark gradient background
        for y in range(SCREEN_HEIGHT):
            color_intensity = int(100 + (y / SCREEN_HEIGHT) * 50)
            color = (color_intensity, 20, 20)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Animated background elements
        time = pygame.time.get_ticks() // 100
        for i in range(0, SCREEN_WIDTH, 50):
            for j in range(0, SCREEN_HEIGHT, 50):
                pulse = int(10 * math.sin((time + i + j) * 0.1))
                pygame.draw.circle(self.screen, (255, 100, 100, 50), (i, j), 2 + pulse)
        
        # Title with glow effect
        title_text = self.font.render("GAME OVER", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        
        # Glow effect
        for offset in [(3, 3), (2, 2), (1, 1)]:
            glow_text = self.font.render("GAME OVER", True, RED)
            glow_rect = glow_text.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], SCREEN_HEIGHT // 3 + offset[1]))
            self.screen.blit(glow_text, glow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Score with highlight
        score_text = self.font.render(f"Final Score: {self.score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # Score background
        score_bg = pygame.Rect(score_rect.x - 10, score_rect.y - 5, score_rect.width + 20, score_rect.height + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), score_bg, border_radius=5)
        
        self.screen.blit(score_text, score_rect)
        
        options = [
            "Press R to play again",
            "Press ESC to exit"
        ]
        
        y_offset = SCREEN_HEIGHT // 2 + 80
        for line in options:
            text = self.small_font.render(line, True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 35
    
    def draw_hud(self):
        """Draws the HUD"""
        # Semi-transparent background for HUD
        hud_bg = pygame.Surface((SCREEN_WIDTH, 100))
        hud_bg.set_alpha(150)
        hud_bg.fill((0, 0, 0))
        self.screen.blit(hud_bg, (0, 0))
        
        # Score with background
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        score_bg = pygame.Rect(5, 5, score_text.get_width() + 10, score_text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), score_bg, border_radius=5)
        self.screen.blit(score_text, (10, 10))
        
        # Coins collected with coin icon
        coins_text = self.small_font.render(f"Coins: {self.coins_collected}", True, YELLOW)
        coins_bg = pygame.Rect(5, 45, coins_text.get_width() + 30, coins_text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), coins_bg, border_radius=5)
        
        # Draw coin icon
        coin_x = 15
        coin_y = 55
        pygame.draw.circle(self.screen, YELLOW, (coin_x, coin_y), 8)
        pygame.draw.circle(self.screen, (255, 255, 150), (coin_x - 2, coin_y - 2), 4)
        pygame.draw.circle(self.screen, (218, 165, 32), (coin_x, coin_y), 8, 2)
        
        self.screen.blit(coins_text, (30, 50))
        
        # Progress bar to next life (every 10 coins)
        coins_to_next_life = self.coins_collected % 10
        progress = coins_to_next_life / 10.0
        bar_width = 100
        bar_height = 8
        bar_x = 10
        bar_y = 73
        
        # Background bar
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        # Progress bar
        if progress > 0:
            progress_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, progress_width, bar_height), border_radius=4)
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)
        
        # Text showing coins needed
        next_life_text = self.small_font.render(f"{coins_to_next_life}/10", True, WHITE)
        self.screen.blit(next_life_text, (bar_x + bar_width + 5, bar_y - 2))
        
        # Lives with heart icons
        lives_text = self.font.render(f"Lives: {self.player.lives}", True, WHITE)
        lives_bg = pygame.Rect(SCREEN_WIDTH - 155, 5, lives_text.get_width() + 10, lives_text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), lives_bg, border_radius=5)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))
        
        # Draw heart icons for lives
        for i in range(min(self.player.lives, 10)):  # Limit display to 10 hearts
            heart_x = SCREEN_WIDTH - 150 + lives_text.get_width() + 10 + i * 20
            heart_y = 15
            # Simple heart shape
            pygame.draw.circle(self.screen, RED, (heart_x, heart_y), 4)
            pygame.draw.circle(self.screen, RED, (heart_x + 6, heart_y), 4)
            pygame.draw.polygon(self.screen, RED, [(heart_x - 2, heart_y + 2), (heart_x + 8, heart_y + 2), (heart_x + 3, heart_y + 8)])
        
        # If more than 10 lives, show "+X"
        if self.player.lives > 10:
            extra_lives_text = self.small_font.render(f"+{self.player.lives - 10}", True, RED)
            self.screen.blit(extra_lives_text, (SCREEN_WIDTH - 150 + lives_text.get_width() + 210, 10))
        
        # Height reached and difficulty with color coding
        height_reached = abs(self.player.max_row_reached)
        diff_color = YELLOW if self.difficulty_multiplier < 2.0 else ORANGE if self.difficulty_multiplier < 3.0 else RED
        height_text = self.small_font.render(f"Height: {height_reached}", True, CYAN)
        diff_text = self.small_font.render(f"Difficulty: {self.difficulty_multiplier:.2f}x", True, diff_color)
        
        height_bg = pygame.Rect(SCREEN_WIDTH - 155, 45, height_text.get_width() + 10, height_text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), height_bg, border_radius=5)
        self.screen.blit(height_text, (SCREEN_WIDTH - 150, 50))
        
        diff_bg = pygame.Rect(SCREEN_WIDTH - 155, 70, diff_text.get_width() + 10, diff_text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), diff_bg, border_radius=5)
        self.screen.blit(diff_text, (SCREEN_WIDTH - 150, 75))
        
        # Life gain animation (center screen, fast)
        if self.life_gain_timer > 0:
            # Calculate animation properties - very fast
            progress = 1.0 - (self.life_gain_timer / 60.0)
            alpha = int(255 * (self.life_gain_timer / 60.0))  # Fade out quickly
            scale = 1.0 + (0.5 * math.sin(progress * math.pi * 2))  # Fast pulse
            
            # Position in center of screen
            text_x = SCREEN_WIDTH // 2
            text_y = SCREEN_HEIGHT // 2 - int(30 * progress)  # Move upward
            
            # Create large text
            life_gain_font = pygame.font.Font(None, int(56 * scale))
            life_text = life_gain_font.render(self.life_gain_text, True, GREEN)
            life_rect = life_text.get_rect(center=(text_x, text_y))
            
            # Draw glow effect
            for offset in [(4, 4), (3, 3), (2, 2)]:
                glow_text = life_gain_font.render(self.life_gain_text, True, (100, 255, 100))
                glow_rect = glow_text.get_rect(center=(text_x + offset[0], text_y + offset[1]))
                glow_text.set_alpha(alpha // 2)
                self.screen.blit(glow_text, glow_rect)
            
            # Draw main text
            life_text.set_alpha(alpha)
            self.screen.blit(life_text, life_rect)
            
            # Draw heart icon next to text
            heart_size = int(20 * scale)
            heart_x = text_x - 80
            heart_y = text_y
            
            # Pulsing heart
            pygame.draw.circle(self.screen, RED, (heart_x, heart_y), heart_size // 2)
            pygame.draw.circle(self.screen, RED, (heart_x + heart_size // 2, heart_y), heart_size // 2)
            pygame.draw.polygon(self.screen, RED, [
                (heart_x - heart_size // 4, heart_y + heart_size // 4),
                (heart_x + heart_size * 3 // 4, heart_y + heart_size // 4),
                (heart_x + heart_size // 4, heart_y + heart_size)
            ])
    
    def draw_game(self):
        """Draws the game state"""
        self.screen.fill(BLACK)
        
        # Draw visible lanes
        camera_row = int(self.camera_y // LANE_HEIGHT)
        for row in range(camera_row - 2, camera_row + LANES_ON_SCREEN + 2):
            if row in self.lanes:
                self.lanes[row].draw(self.screen, self.camera_y)
        
        # Draw logs
        for log in self.logs:
            log.draw(self.screen, self.camera_y)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_y)
        
        # Draw coins
        for coin in self.coins:
            coin.draw(self.screen, self.camera_y)
        
        # Draw player
        self.player.draw(self.screen, self.camera_y)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw pause menu if paused
        if self.paused:
            self.draw_pause_menu()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while not rospy.is_shutdown() and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            if self.game_state == 'welcome':
                if rospy.get_param('~screen_param') != 'phase1':
                    rospy.set_param('~screen_param', 'phase1')
                    rospy.loginfo(f"Game phase changed to phase1")

            if self.game_state == 'playing' or self.paused:
                if rospy.get_param('~screen_param') != 'phase2':
                    rospy.set_param('~screen_param', 'phase2')
                    rospy.loginfo(f"Game phase changed to phase2")

            elif self.game_state == 'game_over':
                if rospy.get_param('~screen_param') != 'phase3':
                    rospy.set_param('~screen_param', 'phase3')
                    rospy.loginfo(f"Game phase changed to phase3")

                if not self.published_score:
                    score_msg = Int64()
                    score_msg.data = self.score
                    self.__pub.publish(score_msg)
                    self.published_score = True  

                    current_score = self.score
                    user = self.name 
                    self.user_scores[user] = current_score
                
                    rospy.loginfo(f"Game Over. Score {current_score} sent and saved for {user}.")

            if self.last_command:
                cmd = self.last_command

                if cmd == "QUIT":
                    running = False

                elif self.game_state == 'waiting_user':
                        pass 

                elif self.game_state == 'welcome':
                    if cmd in ["SPACE", "START", " "]:
                        self.game_state = 'playing'
                        self.sound_manager.start_music()

                elif self.game_state == 'playing':
                    if cmd == "ESC":
                        self.paused = not self.paused
                        if self.paused: self.sound_manager.stop_music()
                        else: self.sound_manager.start_music()
                    elif not self.paused:
                        self.handle_input(cmd) 

                elif self.paused:
                    if cmd == "SPACE":
                        running = False
                    elif cmd in ["RESET", "R"]:
                        self.reset_game()
                        self.game_state = 'playing'
                        self.paused = False
                        self.sound_manager.start_music()
                        self.published_score=False
                    elif cmd == "ESC":
                        self.paused = False
                        self.sound_manager.start_music()

                elif self.game_state == 'game_over':
                    if cmd in ["RESET", "R"]:
                        self.published_score = False
                        self.reset_game()
                        self.game_state = 'playing'
                        self.sound_manager.start_music()
                    elif cmd == "ESC":
                        running = False

                self.last_command = None
            
            if self.game_state == 'playing' and not self.paused:
                self.update()
            
            if self.game_state == 'waiting_user':
                self.screen.fill(BLACK)
                txt = self.font.render("Waiting for User Node info...", True, WHITE)
                self.screen.blit(txt, (100, 300))
            elif self.game_state == 'welcome':
                self.draw_welcome_screen()
            elif self.game_state == 'playing':
                self.draw_game()
            elif self.game_state == 'game_over':
                self.draw_game_over_screen()
            
            pygame.display.flip()
            self.clock.tick(BASE_FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except rospy.ROSInterruptException:
        pass
