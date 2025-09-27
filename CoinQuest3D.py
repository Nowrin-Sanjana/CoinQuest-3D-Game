from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time
import math
import random

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
LANE_WIDTH = 4.0
FORWARD_SPEED = 20.0
LANE_SWITCH_COOLDOWN = 0.25
LANE_TRANSITION_SPEED = 8.0  # Add smooth transition speed
JUMP_STRENGTH = 15.0
GRAVITY = 50.0
SLIDE_HEIGHT_REDUCTION = 0.5

# Spawner constants
SEGMENT_LENGTH = 20.0
SPAWN_DISTANCE = 100.0
CLEANUP_DISTANCE = -50.0

# Camera constants
CAMERA_DISTANCE_BEHIND = 10.0
CAMERA_HEIGHT = 6.0
CAMERA_LOOK_AHEAD = 8.0
CAMERA_MIN_HEIGHT = 2.0
CAMERA_MAX_HEIGHT = 15.0
CAMERA_MIN_DISTANCE = 5.0
CAMERA_MAX_DISTANCE = 25.0
CAMERA_MOVE_SPEED = 5.0

# Shooting constants
MAX_AMMO = 5  # Changed from 10 to 5
BULLET_SPEED = 70.0
BULLET_LIFETIME = 2.0
RELOAD_PICKUP_LIFETIME = 10.0

# Enemy spawn logic
ENEMY_SPAWN_CHANCE = 0.3  # 30% chance after obstacle
ENEMY_SPAWN_DELAY = 10.0
OBSTACLE_PASS_DISTANCE = 15.0

# Flight mode constants
FLIGHT_DURATION = 5.0  # seconds
FLIGHT_HEIGHT = 10.0  # height player reaches in flight mode (lowered from 10.0)
FLIGHT_TRANSITION_SPEED = 15.0  # speed of ascent/descent
AERIAL_COIN_SPAWN_INTERVAL = 7.0  # seconds
FLIGHT_POWERUP_LIFETIME = 15.0  # How long the powerup lasts after collecting
FLIGHT_POWERUP_SPAWN_BEFORE = 5.0  # Spawn powerup 5 seconds before aerial coin

# Coin multiplier constants
COIN_MULTIPLIER_DURATION = 5.0  # 5 seconds
COIN_MULTIPLIER_SPAWN_CHANCE = 0.002  # 0.2% chance per frame
COIN_MULTIPLIER_COOLDOWN = 60.0  # 60 seconds between spawns

# Magnet mode constants
MAGNET_DURATION = 8.0  # seconds
MAGNET_RADIUS = 15.0  # radius to attract coins
MAGNET_ATTRACTION_SPEED = 25.0  # speed coins move toward player
MAGNET_POWERUP_SPAWN_CHANCE = 0.001  # 0.1% chance per frame
MAGNET_POWERUP_COOLDOWN = 45.0  # 45 seconds between spawns

# Door and environment constants
DOOR_SPAWN_INTERVAL = 200.0  # Spawn door every 200 units
DOOR_WIDTH = 6.0
DOOR_HEIGHT = 8.0
DOOR_DEPTH = 2.0
ENVIRONMENT_TRANSITION_TIME = 0.5  # seconds for transition
DOOR_SPAWN_CHANCE = 0.0005  # 0.05% chance per frame for random spawning
DOOR_MIN_DISTANCE = 500.0  # Minimum distance between doors

# Environment types
ENVIRONMENTS = [
    "forest",
    "desert",
    "snow",
    "night",
    "storm",
    "underwater"
]

# Game state
player_lane = 0  # -1, 0, 1 (left, center, right)
player_x = 0.0  # Add actual X position for smooth movement
target_x = 0.0  # Add target X position
player_y = 0.0
player_z = 0.0
player_velocity_y = 0.0
is_jumping = False
is_sliding = False
is_flying = False
slide_timer = 0.0
lane_switch_timer = 0.0
score = 0
game_over = False
ammo = MAX_AMMO
lives = 3  # <--- Add this line

# Animation variables for running motion
leg_angle = 0.0
arm_angle = 0.0

# Cheat modes
god_mode = False
infinite_ammo = False
coin_multiplier_cheat = False  # Add coin multiplier cheat

# Object pools
obstacles = []
coins = []
enemies = []
bullets = []
reload_pickups = []
aerial_coins = []
flight_powerups = []
coin_multiplier_powerups = []  # Add this list
magnet_powerups = []  # Add this list
segments_spawned = 0

# Enemy spawning logic
last_obstacle_z = -1000.0
enemy_cooldown_timer = 0.0
reload_spawn_cooldown = 0.0

# Time tracking
last_time = time.time()
fps_counter = 0
fps_time = 0.0
last_aerial_coin_spawn = time.time()  # Add this line
game_start_time = time.time()  # Add this line to initialize game_start_time

# New global variables for camera mode and manual controls
camera_mode = "third_person"  # "third_person" or "first_person"
camera_manual_height = CAMERA_HEIGHT
camera_manual_distance = CAMERA_DISTANCE_BEHIND
camera_manual_x_offset = 0.0

# Flight powerup variables
flight_powerup_active = False
flight_powerup_timer = 0.0

# Coin multiplier variables
coin_multiplier_active = False
coin_multiplier_timer = 0.0
coin_multiplier_spawn_cooldown = 0.0

# Magnet mode variables
magnet_mode_active = False
magnet_mode_timer = 0.0
magnet_powerup_spawn_cooldown = 0.0

# Add new global variables after the existing globals
infinite_ammo_timer = 0.0  # Add this line

current_environment = "default"
environment_transition_active = False
environment_transition_timer = 0.0
next_environment = "default"
last_door_spawn = 0.0
doors = []
weather_intensity = 0.0
weather_timer = 0.0
god_mode_timer = 0.0  # Add this line

# Add new global variable for door spawning
door_spawn_cooldown = 0.0  # Add this line

# Add new global variable for pause state
game_paused = False  # Add this line after other global variables

class AABB:
    def __init__(self, x, y, z, width, height, depth):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
    
    def intersects(self, other):
        return (abs(self.x - other.x) < (self.width + other.width) / 2 and
                abs(self.y - other.y) < (self.height + other.height) / 2 and
                abs(self.z - other.z) < (self.depth + other.depth) / 2)

class Obstacle:
    def __init__(self, lane, z, obstacle_type):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 0.0
        self.z = z
        self.type = obstacle_type  # 'solid', 'jumpable', 'slidable'
        self.active = True
        
        if obstacle_type == 'jumpable':
            self.height = 1.5
            self.color = (1.0, 0.5, 0.0)  # Orange

        elif obstacle_type == 'slidable':
            self.height = 3.0
            self.y = 3.5  # obstacle sits on ground
            self.color = (0.8, 0.2, 0.2)  # Red

        else:  # solid
            self.height = 4.0
            self.color = (0.5, 0.5, 0.5)  # Gray
            # Normal hitbox center
        hitbox_center_y = self.y + self.height/2
        
        self.aabb = AABB(self.x, hitbox_center_y, self.z, 1.5, self.height, 1.5)
    
    def update(self):
        self.aabb.x = self.x
        self.aabb.y = self.y + self.height/2
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glColor3f(*self.color)
        glTranslatef(self.x, self.y + self.height/2, self.z)
        glScalef(1.5, self.height, 1.5)
        glutSolidCube(1.0)
        glPopMatrix()

class Coin:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.5
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.aabb = AABB(self.x, self.y, self.z, 0.8, 0.8, 0.3)

    def update(self, delta_time):
        self.rotation += 180.0 * delta_time
        self.aabb.x, self.aabb.y, self.aabb.z = self.x, self.y, self.z

    def draw(self):
        if not self.active:
            return
        glPushMatrix()
        glColor3f(1.0, 0.9, 0.0)  # shiny gold
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glutSolidTorus(0.1, 0.4, 12, 24)  # torus coin
        glPopMatrix()

class Enemy:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 0.0
        self.z = z
        self.active = True
        self.width = 2.2  # Increased from 1.5 to 2.2
        self.height = 3.5  # Increased from 2.0 to 3.5
        self.depth = 2.2  # Increased from 1.5 to 2.2
        self.aabb = AABB(self.x, self.y + self.height/2, self.z, self.width, self.height, self.depth)
        self.bob_timer = 0.0  # Add bobbing animation
        self.speed = 15.0  # Movement speed towards player
        self.target_lane = lane  # Initial target lane
        self.lane_switch_timer = 0.0  # Timer for lane switching
        self.lane_switch_cooldown = 2.0  # How often enemy can switch lanes
    
    def update(self):
        # Move towards player (backward along Z-axis)
        self.z -= self.speed * 0.016  # Approximate delta_time
        
        # Update lane switching logic - enemy follows player
        if self.lane_switch_timer <= 0:
            # Determine which lane the player is in and move towards it
            if self.lane < player_lane:
                self.target_lane = min(self.lane + 1, 1)  # Move right towards player
            elif self.lane > player_lane:
                self.target_lane = max(self.lane - 1, -1)  # Move left towards player
            
            # If we're changing lanes, start the switch
            if self.target_lane != self.lane:
                self.lane = self.target_lane
                self.lane_switch_timer = self.lane_switch_cooldown
        else:
            self.lane_switch_timer -= 0.016  # Decrease timer
        
        # Smooth movement to target lane position
        target_x = self.lane * LANE_WIDTH
        if abs(self.x - target_x) > 0.1:
            direction = 1 if target_x > self.x else -1
            self.x += direction * 8.0 * 0.016  # Lane transition speed
            # Clamp to target to avoid overshooting
            if direction > 0 and self.x >= target_x:
                self.x = target_x
            elif direction < 0 and self.x <= target_x:
                self.x = target_x
        
        # Update AABB
        self.aabb.x = self.x
        self.aabb.y = self.y + self.height/2
        self.aabb.z = self.z
        
        # Update bobbing animation
        self.bob_timer += 0.05  # Slow bobbing
        
        # Deactivate if enemy has passed too far behind player
        if self.z < player_z - 30:
            self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Add slight bobbing motion
        bob_offset = math.sin(self.bob_timer) * 0.1
        glTranslatef(0, bob_offset, 0)
        
        # Draw bigger red sphere (body) at bottom - INCREASED SIZE
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glPushMatrix()
        glTranslatef(0, 1.2, 0)  # Position above ground (raised slightly)
        glutSolidSphere(1.5, 20, 20)  # Increased from 1.0 to 1.5
        glPopMatrix()
        
        # Draw smaller black sphere (head) on top - INCREASED SIZE
        glColor3f(0.1, 0.1, 0.1)  # Dark/black color
        glPushMatrix()
        glTranslatef(0, 3.0, 0)  # Position on top of red sphere (adjusted for bigger body)
        glutSolidSphere(0.9, 15, 15)  # Increased from 0.6 to 0.9
        glPopMatrix()
        
        # Add glowing red eyes to make them more menacing
        glColor3f(1.0, 0.0, 0.0)  # Bright red eyes
        glPushMatrix()
        glTranslatef(-0.3, 3.2, 0.8)  # Left eye position
        glutSolidSphere(0.1, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.3, 3.2, 0.8)  # Right eye position
        glutSolidSphere(0.1, 8, 8)
        glPopMatrix()
        
        glPopMatrix()

class Bullet:
    def __init__(self, lane, start_z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.5  # gun level
        self.z = start_z
        self.active = True
        self.speed = BULLET_SPEED
        self.time_alive = 0.0
        self.width = 0.5
        self.height = 0.5
        self.depth = 1.0
        self.aabb = AABB(self.x, self.y, self.z, self.width, self.height, self.depth)
    
    def update(self, delta_time):
        if not self.active:
            return
        self.z += self.speed * delta_time
        self.time_alive += delta_time
        self.aabb.z = self.z
        if self.time_alive > BULLET_LIFETIME:
            self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glColor3f(1.0, 1.0, 0.0)  # Yellow bullets
        glTranslatef(self.x, self.y, self.z)
        glScalef(self.width, self.height, self.depth)
        glutSolidCube(1.0)
        glPopMatrix()

class ReloadPickup:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.5
        self.z = z
        self.active = True
        self.time_alive = 0.0
        self.width = 1.0
        self.height = 1.0
        self.depth = 1.0
        self.aabb = AABB(self.x, self.y, self.z, self.width, self.height, self.depth)
    
    def update(self, delta_time):
        if not self.active:
            return
        self.time_alive += delta_time
        self.aabb.z = self.z
        if self.time_alive > RELOAD_PICKUP_LIFETIME:
            self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glColor3f(0.0, 1.0, 1.0)  # Cyan for reload
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(0.5, 16, 16)
        glPopMatrix()

class AerialCoin:
    def __init__(self, lane, z, height):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = height  # Height above the rail tracks
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.bob_timer = 0.0  # Add bobbing animation
        self.base_height = height  # Store original height
        self.aabb = AABB(self.x, self.y, self.z, 1.0, 1.0, 1.0)
    
    def update(self, delta_time):
        self.rotation += 240.0 * delta_time  # Rotate a bit faster than ground coins
        self.bob_timer += delta_time * 1.5
        # Reduce bobbing motion to keep coins in collectible range
        self.y = self.base_height + math.sin(self.bob_timer) * 0.2  # Reduced from 0.3
        
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)  # Spin around Y-axis like ground coins
        
        # Draw similar to ground coins but with enhanced appearance
        # Main bright gold color (brighter than ground coins)
        glColor3f(1.0, 0.95, 0.1)  # Bright gold
        
        # Draw main torus like ground coins but slightly larger
        glutSolidTorus(0.15, 0.5, 12, 24)  # Slightly larger than ground coins
        
        # Add a subtle glow ring around the coin
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 0.3, 0.4)  # Semi-transparent bright yellow glow
        
        # Outer glow torus
        glutSolidTorus(0.05, 0.65, 8, 16)  # Thinner outer ring for glow
        
        glDisable(GL_BLEND)
        glPopMatrix()

class FlightPowerup:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.0
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.bob_timer = 0.0
        self.aabb = AABB(self.x, self.y, self.z, 1.2, 1.2, 1.2)
    
    def update(self, delta_time):
        self.rotation += 120.0 * delta_time  # Rotate faster than coins
        self.bob_timer += delta_time * 3.0
        self.y = 1.0 + math.sin(self.bob_timer) * 0.3  # Bob up and down
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        # Special color - bright cyan/white glow effect
        glColor3f(0.0, 1.0, 1.0)
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glRotatef(45, 1, 0, 0)  # Tilt for diamond shape
        
        # Draw as a diamond/star shape - larger than regular coins
        glScalef(1.2, 0.3, 1.2)
        glutSolidCube(1.0)
        
        # Add a glowing effect with a second, slightly larger transparent cube
        glColor4f(0.5, 1.0, 1.0, 0.3)
        glScalef(1.3, 1.3, 1.3)
        glutSolidCube(1.0)
        glPopMatrix()

# Add new class for coin multiplier powerup
class CoinMultiplierPowerup:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.5
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.pulse_timer = 0.0
        self.scale = 1.0
        self.aabb = AABB(self.x, self.y, self.z, 1.2, 1.2, 1.2)
    
    def update(self, delta_time):
        self.rotation += 200.0 * delta_time  # Rotate fast
        self.pulse_timer += delta_time * 4.0
        self.scale = 1.0 + math.sin(self.pulse_timer) * 0.3  # Pulsing effect
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        # Special golden/yellow color with glow effect
        glColor3f(1.0, 0.8, 0.0)
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glRotatef(45, 1, 0, 1)  # Tilt for diamond effect
        
        # Draw main X symbol as intersecting rectangles
        glScalef(self.scale, self.scale * 0.3, self.scale)
        
        # First bar of X
        glPushMatrix()
        glRotatef(45, 0, 0, 1)
        glScalef(2.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Second bar of X
        glPushMatrix()
        glRotatef(-45, 0, 0, 1)
        glScalef(2.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Add glowing effect with transparent outer layer
        glColor4f(1.0, 1.0, 0.0, 0.3)
        glScalef(1.5, 1.5, 1.5)
        
        # Outer glow X
        glPushMatrix()
        glRotatef(45, 0, 0, 1)
        glScalef(2.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glRotatef(-45, 0, 0, 1)
        glScalef(2.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPopMatrix()

# Add new class for magnet powerup
class MagnetPowerup:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 1.5
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.pulse_timer = 0.0
        self.scale = 1.0
        self.aabb = AABB(self.x, self.y, self.z, 1.2, 1.2, 1.2)
    
    def update(self, delta_time):
        self.rotation += 150.0 * delta_time
        self.pulse_timer += delta_time * 3.0
        self.scale = 1.0 + math.sin(self.pulse_timer) * 0.2
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        # Simple gray-blue magnet color
        glColor3f(0.6, 0.7, 0.8)  # Gray-blue color
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        
        # Draw as a simple horseshoe magnet shape using rectangles
        glScalef(self.scale, self.scale, self.scale)
        
        # Left pole of magnet (simple rectangle)
        glPushMatrix()
        glTranslatef(-0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Right pole of magnet (simple rectangle)
        glPushMatrix()
        glTranslatef(0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Top connector (simple rectangle)
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        glScalef(1.1, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Add simple glow effect
        glColor4f(0.7, 0.8, 0.9, 0.3)  # Lighter gray-blue glow
        glScalef(1.2, 1.2, 1.2)
        
        # Glow left pole
        glPushMatrix()
        glTranslatef(-0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Glow right pole
        glPushMatrix()
        glTranslatef(0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Glow top connector
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        glScalef(1.1, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPopMatrix()

# Add the Door class after the MagnetPowerup class
class Door:
    def __init__(self, lane, z, environment_type):
        self.lane = lane
        self.x = lane * LANE_WIDTH  # Position based on lane
        self.y = 0.0
        self.z = z
        self.active = True
        self.environment_type = environment_type
        self.rotation = 0.0
        self.glow_timer = 0.0
        self.width = DOOR_WIDTH
        self.height = DOOR_HEIGHT
        self.depth = DOOR_DEPTH
        self.aabb = AABB(self.x, self.y + self.height/2, self.z, self.width, self.height, self.depth)
        
        # Environment-specific colors
        self.colors = {
            "forest": (0.2, 0.8, 0.2),    # Green
            "desert": (1.0, 0.8, 0.2),    # Sandy yellow
            "snow": (0.8, 0.9, 1.0),      # Ice blue
            "night": (0.3, 0.2, 0.6),     # Dark purple
            "storm": (0.4, 0.4, 0.4),     # Storm gray
            "underwater": (0.2, 0.6, 1.0) # Ocean blue
        }
    
    def update(self, delta_time):
        self.rotation += 30.0 * delta_time  # Slow rotation
        self.glow_timer += delta_time * 2.0
        self.aabb.x = self.x
        self.aabb.y = self.y + self.height/2
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y + self.height/2, self.z)
        
        # Get environment color
        color = self.colors.get(self.environment_type, (0.5, 0.5, 0.5))
        
        # Draw border (outer frame)
        glColor3f(0.5, 0.2, 0.3)  # Dark pink frame
        glPushMatrix()
        glScalef(self.width + 1.0, self.height + 0.8, 0.2)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Draw door frame
        glColor3f(1.0, 0.7, 0.8)  # Light pink frame
        glPushMatrix()
        glScalef(self.width + 0.3, self.height + 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Draw door portal with glow effect
        glow = 0.3 + 0.2 * math.sin(self.glow_timer)
        glColor3f(color[0] + glow, color[1] + glow, color[2] + glow)
        glPushMatrix()
        glScalef(self.width, self.height, 0.1)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Draw swirling energy effect
        glPushMatrix()
        glRotatef(self.rotation, 0, 0, 1)
        for i in range(8):
            angle = i * 45.0
            glPushMatrix()
            glRotatef(angle, 0, 0, 1)
            glTranslatef(self.width/3, 0, 0.2)
            glColor4f(color[0], color[1], color[2], 0.6)
            glutSolidSphere(0.2, 8, 8)
            glPopMatrix()
        glPopMatrix()
        
        # Draw environment label
        self.draw_label()
        
        glPopMatrix()
    
    def draw_label(self):
        # Draw text label above door (simplified)
        glPushMatrix()
        glTranslatef(0, self.height/2 + 1.0, 0.5)
        glColor3f(1.0, 1.0, 1.0)
        # Note: In a real implementation, you'd want proper 3D text rendering
        glPopMatrix()

def get_player_aabb():
    base_height = 4.0
    height = base_height * (SLIDE_HEIGHT_REDUCTION if is_sliding else 1.0)
    y_center = player_y + height / 2.0
    
    return AABB(player_x, y_center, player_z, 1.0, height, 1.0)

def spawn_segment():
    global segments_spawned
    spawn_z = segments_spawned * SEGMENT_LENGTH
    
    # Skip first few segments to let player start safely
    if segments_spawned < 3:
        segments_spawned += 1
        return
    
    # Check if there's a door nearby that needs safe passage
    door_safe_zone = check_door_safe_zone(spawn_z)
    
    # Get current difficulty-adjusted spawn frequency
    _, current_spawn_freq = get_current_difficulty()
    
    # Spawn multiple segments based on difficulty
    for _ in range(current_spawn_freq):
        current_z = spawn_z + (_ * SEGMENT_LENGTH)
        
        # If we're in a door safe zone, skip spawning anything
        if door_safe_zone:
            continue  # Skip spawning entirely in safe zones
        
        # Normal segment spawning logic
        segment_type = random.choice(['obstacles', 'coins', 'mixed'])
        
        if segment_type == 'obstacles':
            # Spawn obstacles in 1-2 lanes, leaving at least one safe lane
            occupied_lanes = random.sample([-1, 0, 1], random.randint(1, 2))
            
            for lane in occupied_lanes:
                obstacle_type = random.choice(['solid', 'jumpable', 'slidable'])
                obstacle = Obstacle(lane, current_z, obstacle_type)
                obstacles.append(obstacle)
        
        elif segment_type == 'coins':
            # Spawn coins in ONLY ONE lane (randomly selected)
            coin_lane = random.choice([-1, 0, 1])  # Pick only one lane
            
            for i in range(3):  # 3 coins per line in the selected lane
                coin_z = current_z + i * 2.0
                coin = Coin(coin_lane, coin_z)
                coins.append(coin)
                
                # If coin multiplier is active, spawn a second coin side by side
                if coin_multiplier_active or coin_multiplier_cheat:
                    # Create a second coin slightly offset to the side
                    coin2 = Coin(coin_lane, coin_z)
                    coin2.x = coin_lane * LANE_WIDTH + 0.8  # Offset to the right
                    coin2.aabb.x = coin2.x  # Update AABB position
                    coins.append(coin2)
        
        elif segment_type == 'mixed':
            # Mix of obstacles and coins
            safe_lane = random.choice([-1, 0, 1])
            
            for lane in [-1, 0, 1]:
                if lane != safe_lane and random.random() < 0.7:
                    obstacle_type = random.choice(['jumpable', 'slidable'])
                    obstacle = Obstacle(lane, current_z, obstacle_type)
                    obstacles.append(obstacle)
            
            # Add some coins in safe areas - only in ONE lane
            if random.random() < 0.5:
                coin = Coin(safe_lane, current_z + 5.0)
                coins.append(coin)
                
                # If coin multiplier is active, spawn a second coin side by side
                if coin_multiplier_active or coin_multiplier_cheat:
                    coin2 = Coin(safe_lane, current_z + 5.0)
                    coin2.x = safe_lane * LANE_WIDTH + 0.8  # Offset to the right
                    coin2.aabb.x = coin2.x  # Update AABB position
                    coins.append(coin2)
    
    segments_spawned += current_spawn_freq

def check_door_safe_zone(spawn_z):
    """Check if the spawn zone is near any doors and should be kept clear of obstacles"""
    safe_zone_distance = 50.0  # Distance before and after door to keep clear
    
    for door in doors:
        if door.active:
            # Check if spawn zone is within safe distance of door
            if abs(spawn_z - door.z) <= safe_zone_distance:
                return True
    
    return False

def spawn_door():
    """Spawn a door that leads to a new environment"""
    door_lane = random.choice([-1, 0, 1])  # Random lane
    door_z = player_z + SPAWN_DISTANCE + 100  # Spawn far ahead
    
    # Choose environment type - ensure it's different from current environment
    available_environments = [env for env in ENVIRONMENTS if env != current_environment]
    environment_type = random.choice(available_environments)
    
    door = Door(door_lane, door_z, environment_type)
    doors.append(door)

def clear_obstacles_around_door(door_z):
    """Remove any obstacles, coins, and powerups in the safe zone around a door"""
    safe_zone_distance = 30.0  # Same as in check_door_safe_zone
    
    # Remove obstacles that are too close to the door
    global obstacles, coins, reload_pickups, flight_powerups, coin_multiplier_powerups, magnet_powerups, aerial_coins
    
    obstacles[:] = [obs for obs in obstacles if abs(obs.z - door_z) > safe_zone_distance]
    coins[:] = [coin for coin in coins if abs(coin.z - door_z) > safe_zone_distance]
    reload_pickups[:] = [rp for rp in reload_pickups if abs(rp.z - door_z) > safe_zone_distance]
    flight_powerups[:] = [fp for fp in flight_powerups if abs(fp.z - door_z) > safe_zone_distance]
    coin_multiplier_powerups[:] = [cmp for cmp in coin_multiplier_powerups if abs(cmp.z - door_z) > safe_zone_distance]
    magnet_powerups[:] = [mp for mp in magnet_powerups if abs(mp.z - door_z) > safe_zone_distance]
    aerial_coins[:] = [ac for ac in aerial_coins if abs(ac.z - door_z) > safe_zone_distance]

def check_obstacle_pass_and_spawn_enemies():
    """Check if player has passed obstacles and potentially spawn enemies"""
    global last_obstacle_z, enemy_cooldown_timer
    
    if game_over:
        return
    
    # Find the furthest obstacle behind the player that we haven't counted yet
    furthest_passed_obstacle = -1000.0
    for obs in obstacles:
        if obs.active and obs.z < player_z and obs.z > last_obstacle_z:
            if obs.z > furthest_passed_obstacle:
                furthest_passed_obstacle = obs.z
    
    # If player has passed an obstacle far enough and cooldown expired
    if (furthest_passed_obstacle > last_obstacle_z and 
        player_z - furthest_passed_obstacle > OBSTACLE_PASS_DISTANCE and 
        enemy_cooldown_timer <= 0):
        
        # Random chance to spawn enemy (not guaranteed)
        if random.random() < ENEMY_SPAWN_CHANCE:
            # Spawn enemy farther behind the player so they have time to chase
            enemy_z = player_z + SPAWN_DISTANCE + 40  # Spawn further ahead
            # Spawn only ONE enemy in a random lane instead of all three lanes
            enemy_lane = random.choice([-1, 0, 1])
            enemy = Enemy(enemy_lane, enemy_z)
            enemies.append(enemy)
            enemy_cooldown_timer = ENEMY_SPAWN_DELAY
        
        last_obstacle_z = furthest_passed_obstacle
    
    if enemy_cooldown_timer > 0:
        enemy_cooldown_timer -= 0.1

# Modify the update_spawner function to include door spawning
def update_spawner():
    global reload_spawn_cooldown, last_aerial_coin_spawn, coin_multiplier_spawn_cooldown
    global magnet_powerup_spawn_cooldown, last_door_spawn, door_spawn_cooldown
    global obstacles, coins, enemies, bullets, reload_pickups, aerial_coins, flight_powerups, coin_multiplier_powerups
    global magnet_powerups, doors
    
    # Spawn new segments ahead of player
    while (segments_spawned * SEGMENT_LENGTH) < (player_z + SPAWN_DISTANCE):
        spawn_segment()
    
    # Random door spawning with much delay and cooldown
    if door_spawn_cooldown <= 0:
        # Very low random chance to spawn a door
        if random.random() < DOOR_SPAWN_CHANCE:
            # Check if enough distance has passed since last door
            if player_z - last_door_spawn > DOOR_MIN_DISTANCE:
                spawn_door()
                last_door_spawn = player_z
                # Set a long random cooldown (3-8 minutes worth of distance)
                door_spawn_cooldown = random.uniform(300.0, 800.0)
    else:
        door_spawn_cooldown -= 1.0  # Decrease cooldown
    
    # Check for enemy spawning after passing obstacles
    check_obstacle_pass_and_spawn_enemies()
    
    # Spawn aerial coins periodically, but check for door safe zone first
    if time.time() - last_aerial_coin_spawn > AERIAL_COIN_SPAWN_INTERVAL:
        spawn_aerial_coin()
        last_aerial_coin_spawn = time.time()
    
    # Spawn reload pickups very rarely and randomly, but not in door safe zones
    if reload_spawn_cooldown <= 0:
        # Much lower chance (0.5% per frame instead of 5%) and longer cooldown
        if random.random() < 0.005:
            pickup_lane = random.choice([-1, 0, 1])
            pickup_z = player_z + SPAWN_DISTANCE + random.uniform(10, 30)  # Random distance
            
            # Check if spawn location is in door safe zone
            if not check_door_safe_zone(pickup_z):
                reload_pickups.append(ReloadPickup(pickup_lane, pickup_z))
            
            reload_spawn_cooldown = random.uniform(40.0, 80.0)  # Random cooldown between 40-80 seconds
    else:
        reload_spawn_cooldown -= 0.1
    
    # Spawn coin multiplier powerups randomly, but not in door safe zones
    if coin_multiplier_spawn_cooldown <= 0:
        if random.random() < COIN_MULTIPLIER_SPAWN_CHANCE:
            powerup_lane = random.choice([-1, 0, 1])
            powerup_z = player_z + SPAWN_DISTANCE + random.uniform(20, 50)
            
            # Check if spawn location is in door safe zone
            if not check_door_safe_zone(powerup_z):
                coin_multiplier_powerups.append(CoinMultiplierPowerup(powerup_lane, powerup_z))
            
            coin_multiplier_spawn_cooldown = COIN_MULTIPLIER_COOLDOWN
    else:
        coin_multiplier_spawn_cooldown -= 0.1
    
    # Spawn magnet powerups randomly, but not in door safe zones
    if magnet_powerup_spawn_cooldown <= 0:
        if random.random() < MAGNET_POWERUP_SPAWN_CHANCE:
            powerup_lane = random.choice([-1, 0, 1])
            powerup_z = player_z + SPAWN_DISTANCE + random.uniform(25, 60)
            
            # Check if spawn location is in door safe zone
            if not check_door_safe_zone(powerup_z):
                magnet_powerups.append(MagnetPowerup(powerup_lane, powerup_z))
            
            magnet_powerup_spawn_cooldown = MAGNET_POWERUP_COOLDOWN
    else:
        magnet_powerup_spawn_cooldown -= 0.1
    
    # Clean up objects behind player
    temp_obstacles = []
    for obs in obstacles:
        if obs.z > player_z + CLEANUP_DISTANCE:
            temp_obstacles.append(obs)
    obstacles[:] = temp_obstacles
    
    temp_coins = []
    for coin in coins:
        if coin.z > player_z + CLEANUP_DISTANCE:
            temp_coins.append(coin)
    coins[:] = temp_coins
    
    temp_enemies = []
    for e in enemies:
        if e.z > player_z + CLEANUP_DISTANCE:
            temp_enemies.append(e)
    enemies[:] = temp_enemies
    
    temp_bullets = []
    for b in bullets:
        if b.z < player_z + SPAWN_DISTANCE and b.active:
            temp_bullets.append(b)
    bullets[:] = temp_bullets
    
    temp_reload_pickups = []
    for rp in reload_pickups:
        if rp.z > player_z + CLEANUP_DISTANCE:
            temp_reload_pickups.append(rp)
    reload_pickups[:] = temp_reload_pickups
    
    temp_aerial_coins = []
    for coin in aerial_coins:
        if coin.z > player_z + CLEANUP_DISTANCE:
            temp_aerial_coins.append(coin)
    aerial_coins[:] = temp_aerial_coins
    
    # Clean up flight powerups behind player
    temp_flight_powerups = []
    for powerup in flight_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_flight_powerups.append(powerup)
    flight_powerups[:] = temp_flight_powerups
    
    # Clean up coin multiplier powerups behind player
    temp_coin_multiplier_powerups = []
    for powerup in coin_multiplier_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_coin_multiplier_powerups.append(powerup)
    coin_multiplier_powerups[:] = temp_coin_multiplier_powerups
    
    # Clean up magnet powerups behind player
    temp_magnet_powerups = []
    for powerup in magnet_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_magnet_powerups.append(powerup)
    magnet_powerups[:] = temp_magnet_powerups
    
    # Clean up doors behind player
    temp_doors = []
    for door in doors:
        if door.z > player_z + CLEANUP_DISTANCE:
            temp_doors.append(door)
    doors[:] = temp_doors

def check_collisions():
    global score, game_over, lives  # <--- Add lives here

    player_aabb = get_player_aabb()

    # Check obstacle collisions
    for obstacle in obstacles:
        if not obstacle.active:
            continue

        if player_aabb.intersects(obstacle.aabb):
            # Handle collision based on obstacle type and player state
            if obstacle.type == 'jumpable' and is_jumping and player_y > 1.0:
                continue  # Successfully jumped over
            elif obstacle.type == 'slidable' and is_sliding and player_y < 3.0:
                continue  # Successfully slid under
            elif is_flying:
                continue  # In flight mode - ignore ground obstacles
            else:
                if obstacle.type == 'solid':
                    # Collision with grey barrier: game over unless god mode
                    if not god_mode:
                        game_over = True
                    obstacle.active = False
                
                else:
                    # Other barriers: lose a life unless god mode
                    if not god_mode:
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                    obstacle.active = False

    # Check coin collisions
    for coin in coins:
        if not coin.active:
            continue

        if player_aabb.intersects(coin.aabb):
            score += 1
            coin.active = False

    # Check aerial coin collisions - only when flying
    for coin in aerial_coins:
        if not coin.active:
            continue

        if is_flying and player_aabb.intersects(coin.aabb):
            score += 2
            coin.active = False

    # Check enemy collisions
    for enemy in enemies:
        if not enemy.active:
            continue

        if player_aabb.intersects(enemy.aabb):
            # Collision with enemy: lose a life unless god mode or flying
            if not god_mode and not is_flying:
                lives -= 1
                if lives <= 0:
                    game_over = True
            enemy.active = False

def check_bullet_enemy_collision():
    global score
    
    for bullet in bullets:
        if not bullet.active:
            continue
        for enemy in enemies:
            if not enemy.active:
                continue
            if bullet.aabb.intersects(enemy.aabb):
                bullet.active = False
                enemy.active = False
                score += 5  # +5 points for enemy kill
                break

def check_reload_pickup_collision():
    global ammo
    
    player_aabb = get_player_aabb()
    for rp in reload_pickups:
        if not rp.active:
            continue
        if player_aabb.intersects(rp.aabb):
            rp.active = False
            ammo = MAX_AMMO  # Restore to full ammo

def shoot():
    global ammo
    
    if game_over:
        return
    if ammo > 0 or infinite_ammo:
        if not infinite_ammo:
            ammo -= 1
        bullet = Bullet(player_lane, player_z + 2.0)
        bullets.append(bullet)

def update_fps():
    global fps_counter, fps_time
    current_time = time.time()
    fps_counter += 1
    if current_time - fps_time >= 1.0:
        fps = fps_counter / (current_time - fps_time)
        title = f"Runner3Lanes - FPS: {fps:.1f}"
        glutSetWindowTitle(title.encode('ascii'))
        fps_counter = 0
        fps_time = current_time

def get_player_x():
    return player_x

def draw_player():
    global leg_angle, arm_angle
    
    glPushMatrix()
    
    # Position the robot at current X position (smooth movement)
    slide_offset = -1.5 if is_sliding else 0.0  # Lower the robot when sliding
    glTranslatef(player_x, player_y + 1.5 + slide_offset, player_z)
    
    # Rotate to face forward (+Z direction) and stand upright
    glRotatef(-90, 1, 0, 0)  # Stand upright (head up)
    glRotatef(180, 0, 0, 1)  # Face away from camera (toward +Z direction)
    
    # Scale down the robot to be smaller
    scale = 0.02
    glScalef(scale, scale, scale)
    
    # Change color if god mode is active
    if god_mode:
        glColor3f(1.0, 1.0, 1.0)  # White when invincible
    
    # Calculate running animation angles
    running_speed = 8.0 if not game_over else 0.0
    leg_swing = math.sin(leg_angle * running_speed) * 25.0  # Leg swing amplitude
    arm_swing = math.sin(arm_angle * running_speed) * 20.0  # Arm swing amplitude
    
    # Robot legs with running animation
    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.0, 1.0)
    glTranslatef(-22, 0, 50)
    glRotatef(leg_swing, 1, 0, 0)  # Left leg swings forward/back
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 50, 8, 1)
    glPopMatrix()

    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.0, 1.0)
    glTranslatef(22, 0, 50)
    glRotatef(-leg_swing, 1, 0, 0)  # Right leg swings opposite
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 50, 8, 1)
    glPopMatrix()

    # Robot torso (green cube)
    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.6, 0.0)
    glTranslatef(0, 0, 75)
    glScalef(1.5, 1.0, 1.5)
    glutSolidCube(40)
    glPopMatrix()

    # Robot head (dark sphere) with slight bob
    head_bob = math.sin(leg_angle * running_speed * 2) * 2.0  # Head bobs faster
    glPushMatrix()
    if not god_mode:
        glColor3f(0.1, 0.1, 0.1)
    glTranslatef(0, 0, 130 + head_bob)
    gluSphere(gluNewQuadric(), 25, 16, 16)
    glPopMatrix()

    # Robot arms with running swing (opposite to legs)
    glPushMatrix()
    if not god_mode:
        glColor3f(1.0, 0.8, 0.6)
    glTranslatef(-22, 20, 100)
    glRotatef(-arm_swing - 90, 1, 0, 0)  # Left arm swings opposite to left leg
    gluCylinder(gluNewQuadric(), 8, 4, 50, 8, 1)
    glPopMatrix()
    
    glPushMatrix()
    if not god_mode:
        glColor3f(1.0, 0.8, 0.6)
    glTranslatef(22, 20, 100)
    glRotatef(arm_swing - 90, 1, 0, 0)  # Right arm swings opposite to right leg
    gluCylinder(gluNewQuadric(), 8, 4, 50, 8, 1)
    glPopMatrix()

    # Robot weapon/tool (dark cylinder)
    glPushMatrix()
    glTranslatef(0, 0, 100)
    glTranslatef(0, 20, 0)
    glRotatef(-90, 1, 0, 0)
    if not god_mode:
        glColor3f(0.2, 0.2, 0.2)
    gluCylinder(gluNewQuadric(), 12, 4, 60, 10, 10)
    glPopMatrix()

    glPopMatrix()

# Modify the draw_ground function to reflect current environment
def draw_ground():
    # Environment-specific ground colors
    ground_colors = {
        "forest": (0.2, 0.4, 0.1),    # Dark green
        "desert": (0.8, 0.6, 0.3),    # Sandy brown
        "snow": (0.9, 0.9, 1.0),      # White snow
        "night": (0.1, 0.1, 0.2),     # Dark blue
        "storm": (0.3, 0.3, 0.3),     # Dark gray
        "underwater": (0.1, 0.3, 0.6) # Deep blue
    }
    
    base_color = ground_colors.get(current_environment, (0.3, 0.25, 0.15))
    
    # Draw ground plane with environment-specific color
    glColor3f(*base_color)
    glBegin(GL_QUADS)
    ground_size = 100.0
    glVertex3f(-ground_size, -1.0, player_z - 50.0)
    glVertex3f(ground_size, -1.0, player_z - 50.0)
    glVertex3f(ground_size, -1.0, player_z + 100.0)
    glVertex3f(-ground_size, -1.0, player_z + 100.0)
    glEnd()
    
    # Environment-specific side terrain
    side_colors = {
        "forest": (0.1, 0.6, 0.1),    # Forest green
        "desert": (0.9, 0.7, 0.4),    # Sand
        "snow": (0.95, 0.95, 1.0),    # Snow white
        "night": (0.2, 0.2, 0.3),     # Dark grass
        "storm": (0.4, 0.4, 0.4),     # Storm grass
        "underwater": (0.2, 0.4, 0.8) # Ocean floor
    }
    
    side_color = side_colors.get(current_environment, (0.4, 0.8, 0.3))
    glColor3f(*side_color)
    
    glBegin(GL_QUADS)
    # Left side terrain
    glVertex3f(-ground_size, -0.8, player_z - 50.0)
    glVertex3f(-8.0, -0.8, player_z - 50.0)
    glVertex3f(-8.0, -0.8, player_z + 100.0)
    glVertex3f(-ground_size, -0.8, player_z + 100.0)
    # Right side terrain
    glVertex3f(8.0, -0.8, player_z - 50.0)
    glVertex3f(ground_size, -0.8, player_z - 50.0)
    glVertex3f(ground_size, -0.8, player_z + 100.0)
    glVertex3f(8.0, -0.8, player_z + 100.0)
    glEnd()
    
    # ... rest of the existing ground drawing code ...
    
    # Draw elevated track foundation
    glColor3f(0.4, 0.35, 0.25)  # Gravel color
    glBegin(GL_QUADS)
    foundation_height = -0.9
    glVertex3f(-8.0, foundation_height, player_z - 50.0)
    glVertex3f(8.0, foundation_height, player_z - 50.0)
    glVertex3f(8.0, foundation_height, player_z + 100.0)
    glVertex3f(-8.0, foundation_height, player_z + 100.0)
    glEnd()
    
    # Draw train rails with environment-appropriate colors
    rail_color = (0.7, 0.7, 0.8) if current_environment != "underwater" else (0.5, 0.8, 1.0)
    glColor3f(*rail_color)
    glLineWidth(6.0)
    glBegin(GL_LINES)
    
    # Main outer rails
    for rail_offset in [-6.0, 6.0]:
        z_start = player_z - 50
        z_end = player_z + 100
        glVertex3f(rail_offset, 0.2, z_start)
        glVertex3f(rail_offset, 0.2, z_end)
    
    # Inner lane separator rails
    for rail_offset in [-2.0, 2.0]:
        z_start = player_z - 50
        z_end = player_z + 100
        glVertex3f(rail_offset, 0.15, z_start)
        glVertex3f(rail_offset, 0.15, z_end)
    glEnd()
    
    # Draw environment-specific effects
    draw_environment_effects()
    
    # Continue with existing railroad ties and other elements...
    draw_railroad_ties()
    draw_environment_objects()

def draw_tree(x, z):
    """Draw a simple tree"""
    glPushMatrix()
    glTranslatef(x, -0.8, z)  # Position on grass level (-0.8)
    
    # Tree trunk
    glColor3f(0.4, 0.2, 0.1)  # Brown
    glPushMatrix()
    glTranslatef(0, 1.5, 0)  # Trunk height from grass level
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.3, 0.2, 3.0, 8, 1)
    glPopMatrix()
    
    # Tree foliage (multiple green spheres)
    glColor3f(0.1, 0.6, 0.1)  # Dark green
    for j in range(3):
        glPushMatrix()
        glTranslatef(0, 2.7 + j * 0.8, 0)  # Adjusted for grass level base
        glutSolidSphere(1.2 - j * 0.2, 12, 12)
        glPopMatrix()
    
    glPopMatrix()

def draw_tunnel_structure(z):
    """Draw tunnel entrance/archway"""
    glPushMatrix()
    glTranslatef(0, -0.8, z)  # Position on grass level
    
    # Tunnel arch
    glColor3f(0.4, 0.4, 0.5)  # Stone gray
    
    # Left pillar - positioned from grass level
    glPushMatrix()
    glTranslatef(-10.0, 3.8, 0)  # Adjusted Y to sit on grass
    glScalef(2.0, 6.0, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Right pillar - positioned from grass level
    glPushMatrix()
    glTranslatef(10.0, 3.8, 0)  # Adjusted Y to sit on grass
    glScalef(2.0, 6.0, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Top arch - positioned relative to pillars
    glPushMatrix()
    glTranslatef(0, 7.3, 0)  # Adjusted Y to sit on top of pillars
    glScalef(22.0, 1.5, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Arch curve (simplified) - adjusted positions
    glColor3f(0.35, 0.35, 0.45)
    for angle in range(-90, 91, 15):
        glPushMatrix()
        rad = math.radians(angle)
        arch_x = 8.0 * math.sin(rad)
        arch_y = 6.8 + 2.0 * math.cos(rad)  # Adjusted base height
        glTranslatef(arch_x, arch_y, 0)
        glutSolidSphere(0.8, 8, 8)
        glPopMatrix()
    
    glPopMatrix()

def draw_signal_pole(x, z):
    """Draw a railway signal pole"""
    glPushMatrix()
    glTranslatef(x, -0.8, z)  # Position on grass level
    
    # Main pole - extends from grass level
    glColor3f(0.6, 0.6, 0.6)  # Gray metal
    glPushMatrix()
    glTranslatef(0, 2.5, 0)  # Adjusted for grass level base
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.15, 0.15, 5.0, 8, 1)
    glPopMatrix()
    
    # Signal light (red/green based on distance) - adjusted height
    signal_color = (1.0, 0.0, 0.0) if abs(z - player_z) < 30 else (0.0, 1.0, 0.0)
    glColor3f(*signal_color)
    glPushMatrix()
    glTranslatef(0, 4.0, 0)  # Adjusted for grass level base
    glutSolidSphere(0.3, 12, 12)
    glPopMatrix()
    
    # Support arm - adjusted height
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(-1.0, 3.7, 0)  # Adjusted for grass level base
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), 0.08, 0.08, 2.0, 6, 1)
    glPopMatrix()
    
    glPopMatrix()

def draw_environment_objects():
    """Draw additional environment objects like signs, poles, etc."""
    # Draw signal poles periodically
    pole_spacing = 40.0
    pole_offset = int(player_z / pole_spacing) * pole_spacing
    
    for i in range(-1, 4):  # Draw a few poles ahead and behind
        pole_z = pole_offset + (i * pole_spacing)
        if abs(pole_z - player_z) < 80:  # Only draw if close enough
            # Left side signal pole
            draw_signal_pole(-12.0, pole_z)
            # Right side signal pole
            draw_signal_pole(12.0, pole_z)
    
    # Draw tunnel entrances/exits occasionally
    tunnel_spacing = 200.0
    tunnel_offset = int(player_z / tunnel_spacing) * tunnel_spacing
    
    for i in range(-1, 2):
        tunnel_z = tunnel_offset + (i * tunnel_spacing)
        if abs(tunnel_z - player_z) < 120:
            draw_tunnel_structure(tunnel_z)
    
    # Add distant mountains/hills
    draw_background_scenery()

def draw_background_scenery():
    """Draw distant background elements"""
    # Draw distant mountains - positioned on far ground
    glColor3f(0.3, 0.4, 0.6)  # Blue-gray mountains
    
    mountain_distance = 200.0
    for i in range(-5, 6):
        mountain_x = i * 40.0
        mountain_z = player_z + mountain_distance
        mountain_height = 15.0 + abs(i * 3.0)
        
        glPushMatrix()
        # Position mountains on distant ground level
        glTranslatef(mountain_x, (mountain_height/2) - 1.0, mountain_z)  # Slightly below ground for natural look
        glScalef(30.0, mountain_height, 20.0)
        glutSolidCube(1.0)
        glPopMatrix()
    
    # Add some clouds (simple white spheres) - these should float
    glColor3f(0.9, 0.9, 1.0)  # White clouds
    cloud_distance = 150.0
    cloud_height = 25.0
    
    for i in range(-3, 4):
        cloud_x = i * 60.0 + math.sin(player_z * 0.01) * 10.0  # Slight movement
        cloud_z = player_z + cloud_distance + (i % 2) * 20.0
        
        # Draw cloud as multiple spheres - clouds naturally float
        for j in range(3):
            glPushMatrix()
            glTranslatef(cloud_x + j * 4.0, cloud_height + j * 1.0, cloud_z)
            glutSolidSphere(3.0 + j * 0.5, 12, 12)
            glPopMatrix()
    
    # Add some trees on the sides
    draw_side_trees()

def draw_side_trees():
    """Draw trees along the track sides"""
    tree_spacing = 25.0
    tree_offset = int(player_z / tree_spacing) * tree_spacing
    
    for i in range(-2, 5):
        tree_z = tree_offset + (i * tree_spacing) + (i % 3) * 5.0  # Irregular spacing
        if abs(tree_z - player_z) < 60:
            # Left side trees - positioned on grass
            tree_x = -15.0 + (i % 3) * 3.0
            draw_tree(tree_x, tree_z)
            
            # Right side trees - positioned on grass
            tree_x = 15.0 + (i % 3) * 3.0
            draw_tree(tree_x, tree_z)

def draw_improved_sky():
    """Draw a gradient sky background"""
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Sky gradient from horizon to zenith
    glBegin(GL_QUADS)
    # Bottom (horizon) - lighter blue
    glColor3f(0.4, 0.6, 0.8)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(1.0, -0.2, -1.0)
    
    # Top (zenith) - darker blue
    glColor3f(0.1, 0.3, 0.6)
    glVertex3f(1.0, 1.0, -1.0)
    glVertex3f(-1.0, 1.0, -1.0)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)

# Modify the draw_hud function to show current environment
def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Pause display - show this prominently if game is paused
    if game_paused:
        # Large "PAUSED" text in center of screen
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        paused_text = "PAUSED"
        
        # Calculate text position to center it
        text_width = len(paused_text) * 18  # Approximate width for HELVETICA_18
        text_x = (WINDOW_WIDTH - text_width) // 2
        text_y = WINDOW_HEIGHT // 2 + 50
        
        glRasterPos2f(text_x, text_y)
        for c in paused_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        
        # Show unpause instruction
        unpause_text = "Press SPACE to continue"
        unpause_width = len(unpause_text) * 8  # Approximate width for smaller font
        unpause_x = (WINDOW_WIDTH - unpause_width) // 2
        unpause_y = text_y - 40
        
        glColor3f(1.0, 1.0, 1.0)  # White for instruction
        glRasterPos2f(unpause_x, unpause_y)
        for c in unpause_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))
    
    # Game Over display - show this first and prominently
    if game_over:
        # Large "GAME OVER" text in center of screen
        glColor3f(1.0, 0.0, 0.0)  # Bright red
        game_over_text = "GAME OVER"
        
        # Calculate text position to center it
        text_width = len(game_over_text) * 18  # Approximate width for HELVETICA_18
        text_x = (WINDOW_WIDTH - text_width) // 2
        text_y = WINDOW_HEIGHT // 2 + 50
        
        glRasterPos2f(text_x, text_y)
        for c in game_over_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        
        # Show restart instruction
        restart_text = "Press 'R' to restart"
        restart_width = len(restart_text) * 10  # Approximate width for smaller font
        restart_x = (WINDOW_WIDTH - restart_width) // 2
        restart_y = text_y - 40
        
        glColor3f(1.0, 1.0, 1.0)  # White for instruction
        glRasterPos2f(restart_x, restart_y)
        for c in restart_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))
        
        # Show final score prominently
        final_score_text = f"Final Score: {score}"
        score_width = len(final_score_text) * 12
        score_x = (WINDOW_WIDTH - score_width) // 2
        score_y = restart_y - 30
        
        glColor3f(1.0, 1.0, 0.0)  # Yellow for final score
        glRasterPos2f(score_x, score_y)
        for c in final_score_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))
    
    # Regular HUD elements (always show)
    glColor3f(1.0, 1.0, 1.0)
    
    # Score - show multiplier if active
    if coin_multiplier_active or coin_multiplier_cheat:
        if coin_multiplier_active:
            score_text = f"Score: {score} (x10 MULTIPLIER - {coin_multiplier_timer:.1f}s)"
        else:
            score_text = f"Score: {score} (x10 MULTIPLIER CHEAT)"
        glColor3f(1.0, 1.0, 0.0)  # Yellow when multiplier is active
    else:
        score_text = f"Score: {score}"
        glColor3f(1.0, 1.0, 1.0)  # White normally
    
    glRasterPos2f(10, WINDOW_HEIGHT - 30)
    for c in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)  # Reset to white
    
    # Distance (meters = z/10)
    distance = int(player_z / 10.0)
    distance_text = f"Distance: {distance}m"
    glRasterPos2f(10, WINDOW_HEIGHT - 60)
    for c in distance_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    # Current Environment
    env_text = f"Environment: {current_environment.upper()}"
    glRasterPos2f(10, WINDOW_HEIGHT - 90)
    for c in env_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    # Lives display
    lives_text = f"Lives: {lives}"
    glColor3f(1.0, 0.5, 0.5)  # Red color for lives
    glRasterPos2f(10, WINDOW_HEIGHT - 120)
    for c in lives_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)  # Reset to white
    
    # Ammo display with timer - COMPLETE THIS SECTION
    if infinite_ammo and infinite_ammo_timer > 0:
        ammo_text = f"Ammo: ∞ ({infinite_ammo_timer:.1f}s) / {MAX_AMMO}"
        glColor3f(0.0, 1.0, 0.0)  # Green for infinite ammo
    else:
        ammo_text = f"Ammo: {ammo} / {MAX_AMMO}"
        if ammo == 0:
            glColor3f(1.0, 0.0, 0.0)  # Red when out of ammo
        elif ammo <= 2:
            glColor3f(1.0, 1.0, 0.0)  # Yellow when low ammo
        else:
            glColor3f(1.0, 1.0, 1.0)  # White when normal ammo
    
    glRasterPos2f(10, WINDOW_HEIGHT - 150)
    for c in ammo_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)  # Reset to white
    
    # God mode timer display
    if god_mode and god_mode_timer > 0:
        god_mode_text = f"GOD MODE: {god_mode_timer:.1f}s"
        glColor3f(1.0, 1.0, 0.0)  # Yellow for god mode
        glRasterPos2f(10, WINDOW_HEIGHT - 180)
        for c in god_mode_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)  # Reset to white
        status_offset = 30
    else:
        status_offset = 0
    
    # Camera mode and controls
    camera_text = f"Camera: {camera_mode.upper()} (Press C to switch)"
    glRasterPos2f(10, WINDOW_HEIGHT - 180 - status_offset)
    for c in camera_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    # Controls based on camera mode (updated text)
    if camera_mode == "third_person":
        controls_text = "Arrows: Move Camera | D/A: Move Player Left/Right"
        glRasterPos2f(10, WINDOW_HEIGHT - 210 - status_offset)
        for c in controls_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    else:
        controls_text = "D/A: Move Left/Right | W: Jump | S: Slide"
        glRasterPos2f(10, WINDOW_HEIGHT - 210 - status_offset)
        for c in controls_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    # Current lane indicator (only show in first person)
    if camera_mode == "first_person":
        lane_names = {-1: "LEFT", 0: "CENTER", 1: "RIGHT"}
        lane_text = f"Lane: {lane_names[player_lane]}"
        glRasterPos2f(10, WINDOW_HEIGHT - 240 - status_offset)
        for c in lane_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    # Status indicators
    status_y = WINDOW_HEIGHT - 270 - status_offset
    if environment_transition_active:
        transition_text = f"ENTERING {next_environment.upper()}... ({environment_transition_timer:.1f}s)"
        glColor3f(0.0, 1.0, 1.0)  # Cyan for transition
        glRasterPos2f(10, status_y)
        for c in transition_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)  # Reset to white
        status_y -= 30
    
    if is_jumping:
        jump_text = "JUMPING"
        glRasterPos2f(10, status_y)
        for c in jump_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    elif is_sliding:
        slide_text = "SLIDING"
        glRasterPos2f(10, status_y)
        for c in slide_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    elif is_flying:
        flight_text = f"FLIGHT MODE: {flight_timer:.1f}s"
        glRasterPos2f(10, status_y)
        for c in flight_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    elif magnet_mode_active:
        magnet_text = f"MAGNET MODE: {magnet_mode_timer:.1f}s"
        glColor3f(1.0, 0.0, 1.0)  # Purple for magnet mode
        glRasterPos2f(10, status_y)
        for c in magnet_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)  # Reset to white
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_player(delta_time):
    global player_y, player_z, player_velocity_y, is_jumping, is_sliding, slide_timer, lane_switch_timer
    global is_flying, flight_timer, flight_target_height, player_x, target_x
    
    if game_over:
        return
    
    # Get current difficulty-adjusted speed
    current_speed, _ = get_current_difficulty()
    
    # Forward movement along +Z axis - BOTH PLAYER AND CAMERA MOVE FORWARD
    player_z += current_speed * delta_time
    
    # Smooth lane transition
    if abs(player_x - target_x) > 0.1:
        direction = 1 if target_x > player_x else -1
        player_x += direction * LANE_TRANSITION_SPEED * delta_time
        # Clamp to target to avoid overshooting
        if direction > 0 and player_x >= target_x:
            player_x = target_x
        elif direction < 0 and player_x <= target_x:
            player_x = target_x
    
    # Update timers
    if lane_switch_timer > 0:
        lane_switch_timer -= delta_time
    if is_sliding and slide_timer > 0:
        slide_timer -= delta_time
        if slide_timer <= 0:
            is_sliding = False
    
    # Flight mode handling
    if is_flying:
        flight_timer -= delta_time
        
        # Ascend/descend to target height
        height_diff = flight_target_height - player_y
        if abs(height_diff) > 0.1:
            player_y += math.copysign(FLIGHT_TRANSITION_SPEED * delta_time, height_diff)
            player_y = min(max(player_y, 0), FLIGHT_HEIGHT)
        
        # End flight mode when timer expires
        if flight_timer <= 0:
            is_flying = False
            flight_target_height = 0.0
    elif player_y > 0 and not is_jumping:
        # Return to ground after flight mode ends
        player_y -= FLIGHT_TRANSITION_SPEED * delta_time
        if player_y <= 0:
            player_y = 0.0
    
    # Jumping physics (Y axis movement) - only when not in flight mode
    elif is_jumping:
        player_y += player_velocity_y * delta_time
        player_velocity_y -= GRAVITY * delta_time
        
        # Land on ground
        if player_y <= 0.0:
            player_y = 0.0
            player_velocity_y = 0.0
            is_jumping = False

# Modify the reset_game function to include door reset
def reset_game():
    global player_lane, player_y, player_z, player_velocity_y, is_jumping, is_sliding
    global slide_timer, lane_switch_timer, score, game_over, segments_spawned, ammo
    global obstacles, coins, enemies, bullets, reload_pickups, leg_angle, arm_angle
    global last_obstacle_z, enemy_cooldown_timer, reload_spawn_cooldown
    global camera_manual_height, camera_manual_distance, camera_manual_x_offset
    global is_flying, flight_timer, last_aerial_coin_spawn, aerial_coins
    global player_x, target_x, flight_powerup_active, flight_powerup_timer, flight_powerups
    global coin_multiplier_active, coin_multiplier_timer, coin_multiplier_spawn_cooldown, coin_multiplier_powerups
    global magnet_mode_active, magnet_mode_timer, magnet_powerup_spawn_cooldown, magnet_powerups
    global game_start_time, doors, current_environment, last_door_spawn, door_spawn_cooldown
    global environment_transition_active, weather_intensity, god_mode_timer, infinite_ammo_timer
    global lives, game_paused  # Add game_paused here

    player_lane = 0
    player_x = 0.0
    target_x = 0.0
    player_y = 0.0
    player_z = 0.0
    player_velocity_y = 0.0
    is_jumping = False
    is_sliding = False
    is_flying = False
    slide_timer = 0.0
    lane_switch_timer = 0.0
    score = 0
    game_over = False
    game_paused = False  # Reset pause state
    segments_spawned = 0
    ammo = MAX_AMMO
    leg_angle = 0.0
    arm_angle = 0.0
    last_obstacle_z = -1000.0
    enemy_cooldown_timer = 0.0
    reload_spawn_cooldown = random.uniform(20.0, 40.0)
    flight_timer = 0.0
    last_aerial_coin_spawn = time.time()
    god_mode_timer = 0.0
    infinite_ammo_timer = 0.0
    lives = 3  # <--- Reset lives to 5

    # Reset environment
    current_environment = "default"
    last_door_spawn = 0.0
    environment_transition_active = False
    weather_intensity = 0.0
    
    # Initialize game start time for difficulty scaling
    game_start_time = time.time()
    
    # Reset camera settings
    camera_manual_height = CAMERA_HEIGHT
    camera_manual_distance = CAMERA_DISTANCE_BEHIND
    camera_manual_x_offset = 0.0
    
    # Reset powerup systems
    flight_powerup_active = False
    flight_powerup_timer = 0.0
    coin_multiplier_active = False
    coin_multiplier_timer = 0.0
    coin_multiplier_spawn_cooldown = random.uniform(30.0, 60.0)
    magnet_mode_active = False
    magnet_mode_timer = 0.0
    magnet_powerup_spawn_cooldown = random.uniform(20.0, 40.0)
    
    # Manual list clearing - reset to empty lists
    obstacles[:] = []
    coins[:] = []
    enemies[:] = []
    bullets[:] = []
    reload_pickups[:] = []
    aerial_coins[:] = []
    flight_powerups[:] = []
    coin_multiplier_powerups[:] = []
    magnet_powerups[:] = []
    doors[:] = []  # Add this line

    # Reset door spawning
    last_door_spawn = -1000.0  # Start far back so first door can spawn after some distance
    door_spawn_cooldown = random.uniform(200.0, 400.0)  # Initial random cooldown

def setup_camera():
    global camera_manual_height, camera_manual_distance, camera_manual_x_offset
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(65.0, float(WINDOW_WIDTH)/float(WINDOW_HEIGHT), 0.1, 1000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if camera_mode == "first_person":
        # First person view - camera at player position looking forward
        camera_x = player_x  # Use smooth player_x position
        # Adjust camera height based on sliding state
        base_camera_height = player_y + 1.8  # Normal eye level height
        if is_sliding:
            base_camera_height = player_y + 0.8  # Lower camera when sliding
        camera_y = base_camera_height
        camera_z = player_z
        
        # Look ahead in the direction of movement
        look_x = player_x  # Use smooth player_x position
        look_y = base_camera_height  # Keep look target at same height as camera
        look_z = player_z + 10.0  # Look forward
        
        gluLookAt(camera_x, camera_y, camera_z,
                  look_x, look_y, look_z,
                  0.0, 1.0, 0.0)
    
    else:  # third_person mode
        # Third person view with manual controls
        camera_x = camera_manual_x_offset
        camera_y = camera_manual_height + player_y * 0.3
        camera_z = player_z - camera_manual_distance
        
        # Look at center track position (fixed at x=0) instead of following player
        look_x = 0.0  # Always look at center of the track
        look_y = player_y + 1.0
        look_z = player_z + CAMERA_LOOK_AHEAD
        
        gluLookAt(camera_x, camera_y, camera_z,
                  look_x, look_y, look_z,
                  0.0, 1.0, 0.0)

# Modify the display function to draw doors
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    setup_camera()
    
    draw_ground()
    draw_player()
    
    # Draw obstacles
    for obstacle in obstacles:
        obstacle.draw()
    
    # Draw coins
    for coin in coins:
        coin.draw()
    
    # Draw aerial coins
    for coin in aerial_coins:
        coin.draw()
    
    # Draw flight powerups
    for powerup in flight_powerups:
        powerup.draw()
    
    # Draw coin multiplier powerups
    for powerup in coin_multiplier_powerups:
        powerup.draw()
    
    # Draw magnet powerups
    for powerup in magnet_powerups:
        powerup.draw()
    
    # Draw doors
    for door in doors:
        door.draw()
    
    # Draw enemies
    for enemy in enemies:
        enemy.draw()
    
    # Draw bullets
    for bullet in bullets:
        bullet.draw()
    
    # Draw reload pickups
    for pickup in reload_pickups:
        pickup.draw()
    
    draw_hud()
    
    glutSwapBuffers()
    update_fps()

# Modify the update function to include environment updates
def update(delta_time):
    global leg_angle, arm_angle, flight_powerup_timer, flight_powerup_active
    global coin_multiplier_timer, coin_multiplier_active, magnet_mode_timer, magnet_mode_active
    global god_mode, god_mode_timer, infinite_ammo, infinite_ammo_timer  # Add infinite_ammo variables here
    
    # Don't update anything if game is paused
    if game_paused:
        return
    
    if not game_over:
        update_player(delta_time)
        update_spawner()
        update_environment(delta_time)  # Add this line
        
        # Update god mode timer
        if god_mode and god_mode_timer > 0:
            god_mode_timer -= delta_time
            if god_mode_timer <= 0:
                god_mode = False
                god_mode_timer = 0.0
        
        # Update infinite ammo timer
        if infinite_ammo and infinite_ammo_timer > 0:
            infinite_ammo_timer -= delta_time
            if infinite_ammo_timer <= 0:
                infinite_ammo = False
                infinite_ammo_timer = 0.0
        
        # Update flight powerup timer
        if flight_powerup_active:
            flight_powerup_timer -= delta_time
            if flight_powerup_timer <= 0:
                flight_powerup_active = False
        
        # Update coin multiplier timer
        if coin_multiplier_active:
            coin_multiplier_timer -= delta_time
            if coin_multiplier_timer <= 0:
                coin_multiplier_active = False
        
        # Update magnet mode timer
        if magnet_mode_active:
            magnet_mode_timer -= delta_time
            if magnet_mode_timer <= 0:
                magnet_mode_active = False
        
        # Update magnet attraction
        update_magnet_attraction(delta_time)
        
        # Update coins rotation
        for coin in coins:
            coin.update(delta_time)
        
        # Update aerial coins rotation
        for coin in aerial_coins:
            coin.update(delta_time)
        
        # Update flight powerups
        for powerup in flight_powerups:
            powerup.update(delta_time)
        
        # Update coin multiplier powerups
        for powerup in coin_multiplier_powerups:
            powerup.update(delta_time)
        
        # Update magnet powerups
        for powerup in magnet_powerups:
            powerup.update(delta_time)
        
        # Update doors
        for door in doors:
            door.update(delta_time)
        
        # Update obstacle AABBs
        for obstacle in obstacles:
            obstacle.update()
        
        # Update enemies
        for enemy in enemies:
            enemy.update()
        
        # Update bullets
        for bullet in bullets:
            bullet.update(delta_time)
        
        # Update reload pickups
        for pickup in reload_pickups:
            pickup.update(delta_time)
        
        check_collisions()
        check_bullet_enemy_collision()
        check_reload_pickup_collision()
        check_flight_powerup_collision()
        check_coin_multiplier_collision()
        check_magnet_powerup_collision()
        check_door_collision()
    
    # Update running animation angles only if not paused
    leg_angle += delta_time
    arm_angle += delta_time

def mouse(button, state, x, y):
    """Handle mouse clicks"""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not game_paused:  # Only shoot if not paused
            shoot()

def keyboard(key, x, y):
    global god_mode, infinite_ammo, camera_mode, coin_multiplier_cheat, god_mode_timer, infinite_ammo_timer
    global game_paused  # Add this line
    
    if key == b'\x1b':  # ESC
        exit()
    elif key == b'g' or key == b'G':  # Toggle God Mode
        if not god_mode:  # Only activate if not already active
            god_mode = True
            god_mode_timer = 10.0  # Set 10 second timer
    elif key == b'r' or key == b'R':  # Reset game
        reset_game()
    elif key == b'i' or key == b'I':  # Toggle Infinite Ammo
        if not infinite_ammo:  # Only activate if not already active
            infinite_ammo = True
            infinite_ammo_timer = 10.0  # Set 10 second timer
    elif key == b'c' or key == b'C':  # Toggle camera mode
        if camera_mode == "third_person":
            camera_mode = "first_person"
        else:
            camera_mode = "third_person"
    elif key == b'f' or key == b'F':  # Activate flight mode
        activate_flight_mode()
    elif key == b' ':  # Space bar - toggle pause/unpause or shoot
        if game_over:
            return  # Don't do anything if game is over
        
        # Toggle pause state
        game_paused = not game_paused
        return  # Don't shoot when pausing/unpausing
    
    # Handle WASD for player movement (only if not paused)
    if not game_paused:
        keyboard_wasd(key, x, y)

def special_keys(key, x, y):
    """Handle special keys like arrow keys"""
    global camera_manual_height, camera_manual_distance, camera_manual_x_offset
    
    if camera_mode == "third_person":
        # Camera controls in third person mode
        if key == GLUT_KEY_UP:
            camera_manual_height = min(camera_manual_height + CAMERA_MOVE_SPEED * 0.1, CAMERA_MAX_HEIGHT)
        elif key == GLUT_KEY_DOWN:
            camera_manual_height = max(camera_manual_height - CAMERA_MOVE_SPEED * 0.1, CAMERA_MIN_HEIGHT)
        elif key == GLUT_KEY_LEFT:
            camera_manual_x_offset -= CAMERA_MOVE_SPEED * 0.1
        elif key == GLUT_KEY_RIGHT:
            camera_manual_x_offset += CAMERA_MOVE_SPEED * 0.1

def keyboard_wasd(key, x, y):
    """Handle WASD keys for player movement"""
    global player_lane, lane_switch_timer, is_jumping, is_sliding, slide_timer
    global player_velocity_y, target_x
    
    if game_over or game_paused:  # Don't move if game is over or paused
        return
    
    # Player movement controls - SWITCHED A AND D FUNCTIONALITY
    if key == b'a' or key == b'A':  # Move right (was left)
        if lane_switch_timer <= 0 and player_lane < 1:
            player_lane += 1
            target_x = player_lane * LANE_WIDTH
            lane_switch_timer = LANE_SWITCH_COOLDOWN
    elif key == b'd' or key == b'D':  # Move left (was right)
        if lane_switch_timer <= 0 and player_lane > -1:
            player_lane -= 1
            target_x = player_lane * LANE_WIDTH
            lane_switch_timer = LANE_SWITCH_COOLDOWN
    elif key == b'w' or key == b'W':  # Jump
        # Allow jumping even when sliding (remove is_sliding check)
        if not is_jumping and not is_flying:
            is_jumping = True
            player_velocity_y = JUMP_STRENGTH
            # End sliding when jumping
            if is_sliding:
                is_sliding = False
                slide_timer = 0.0
    elif key == b's' or key == b'S':  # Slide
        # Allow sliding even when jumping (remove is_jumping check)
        if not is_sliding and not is_flying:
            is_sliding = True
            slide_timer = 1.0
            # End jumping when sliding - land immediately
            if is_jumping:
                is_jumping = False
                player_velocity_y = 0.0
                player_y = 0.0  # Land on ground immediately

def activate_flight_mode():
    """Activate flight mode if powerup is available"""
    global is_flying, flight_timer, flight_target_height, flight_powerup_active
    
    if flight_powerup_active and not is_flying and not game_over:
        is_flying = True
        flight_timer = FLIGHT_DURATION
        flight_target_height = FLIGHT_HEIGHT
        flight_powerup_active = False  # Consume the powerup

def check_flight_powerup_collision():
    """Check collision with flight powerups"""
    global flight_powerup_active, flight_powerup_timer
    
    player_aabb = get_player_aabb()
    for powerup in flight_powerups:
        if not powerup.active:
            continue
        
        if player_aabb.intersects(powerup.aabb):
            powerup.active = False
            flight_powerup_active = True
            flight_powerup_timer = FLIGHT_POWERUP_LIFETIME
            break

def check_coin_multiplier_collision():
    """Check collision with coin multiplier powerups"""
    global coin_multiplier_active, coin_multiplier_timer, score
    
    player_aabb = get_player_aabb()
    for powerup in coin_multiplier_powerups:
        if not powerup.active:
            continue
        
        if player_aabb.intersects(powerup.aabb):
            powerup.active = False
            # Activate coin multiplier mode
            coin_multiplier_active = True
            coin_multiplier_timer = COIN_MULTIPLIER_DURATION
            
            # IMMEDIATELY double all existing coins on the track
            double_existing_coins()
            
            # Add a small bonus for collecting the powerup itself
            score += 5
            break

def double_existing_coins():
    """Double all existing coins on the track by creating duplicates"""
    new_coins = []
    
    # Go through all existing coins and create duplicates
    for coin in coins:
        if coin.active:  # Only duplicate active coins
            # Create a duplicate coin offset to the side
            coin2 = Coin(coin.lane, coin.z)
            coin2.x = coin.x + 0.8  # Offset to the right
            coin2.y = coin.y
            coin2.aabb.x = coin2.x  # Update AABB position
            coin2.aabb.y = coin2.y
            coin2.aabb.z = coin2.z
            new_coins.append(coin2)
    
    # Add all the new coins to the main coins list
    coins.extend(new_coins)

def check_magnet_powerup_collision():
    """Check collision with magnet powerups"""
    global magnet_mode_active, magnet_mode_timer, score
    
    player_aabb = get_player_aabb()
    for powerup in magnet_powerups:
        if not powerup.active:
            continue
        
        if player_aabb.intersects(powerup.aabb):
            powerup.active = False
            magnet_mode_active = True
            magnet_mode_timer = MAGNET_DURATION
            # Add a small score bonus for collecting the powerup
            score += 5  # Bonus points for collecting the powerup
            break

def update_magnet_attraction(delta_time):
    """Update coin attraction when magnet mode is active"""
    if not magnet_mode_active:
        return
    
    player_pos = (player_x, player_y, player_z)
    
    # Attract regular coins
    for coin in coins:
        if not coin.active:
            continue
        
        # Calculate distance to player
        dx = player_pos[0] - coin.x
        dy = player_pos[1] - coin.y
        dz = player_pos[2] - coin.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # If within magnet radius, move coin toward player
        if distance < MAGNET_RADIUS and distance > 0.5:  # Don't attract if too close
            # Normalize direction vector
            dx /= distance
            dy /= distance
            dz /= distance
            
            # Move coin toward player
            coin.x += dx * MAGNET_ATTRACTION_SPEED * delta_time
            coin.y += dy * MAGNET_ATTRACTION_SPEED * delta_time
            coin.z += dz * MAGNET_ATTRACTION_SPEED * delta_time
            
            # Update coin's AABB
            coin.aabb.x = coin.x
            coin.aabb.y = coin.y
            coin.aabb.z = coin.z
    
    # Attract aerial coins (only when flying)
    if is_flying:
        for coin in aerial_coins:
            if not coin.active:
                continue
            
            # Calculate distance to player
            dx = player_pos[0] - coin.x
            dy = player_pos[1] - coin.y
            dz = player_pos[2] - coin.z
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # If within magnet radius, move coin toward player
            if distance < MAGNET_RADIUS and distance > 0.5:
                # Normalize direction vector
                dx /= distance
                dy /= distance
                dz /= distance
                
                # Move coin toward player
                coin.x += dx * MAGNET_ATTRACTION_SPEED * delta_time
                coin.y += dy * MAGNET_ATTRACTION_SPEED * delta_time
                coin.z += dz * MAGNET_ATTRACTION_SPEED * delta_time
                
                # Update coin's AABB
                coin.aabb.x = coin.x
                coin.aabb.y = coin.y
                coin.aabb.z = coin.z

def spawn_aerial_coin():
    """Spawn aerial coins for flight mode"""
    # Check if we should spawn in this area (not in door safe zone)
    spawn_z_base = player_z + SPAWN_DISTANCE + 30
    if check_door_safe_zone(spawn_z_base):
        return  # Skip spawning if in door safe zone
    
    # Count how many aerial coins will actually be spawned
    coins_to_spawn = []
    for i in range(5):  # 5 aerial coins
        coin_lane = random.choice([-1, 0, 1])
        coin_z = spawn_z_base + 20 + (i * 10)  # Spread them out
        
        # Check if this coin's spawn location is safe
        if not check_door_safe_zone(coin_z):
            coin_height = random.uniform(12.5, FLIGHT_HEIGHT + 0.5)  # Height range 8.5-10.5
            coins_to_spawn.append((coin_lane, coin_z, coin_height))
    
    # Only spawn flight powerup if we actually have aerial coins to spawn
    if coins_to_spawn:  # Only spawn powerup if there are coins to collect
        powerup_lane = random.choice([-1, 0, 1])
        powerup_z = spawn_z_base  # Spawn ahead of aerial coins
        
        # Check if powerup spawn location is safe
        if not check_door_safe_zone(powerup_z):
            flight_powerups.append(FlightPowerup(powerup_lane, powerup_z))
        
        # Now spawn the actual aerial coins
        for coin_lane, coin_z, coin_height in coins_to_spawn:
            aerial_coins.append(AerialCoin(coin_lane, coin_z, coin_height))

def get_current_difficulty():
    """Calculate current difficulty based on time elapsed"""
    elapsed_time = time.time() - game_start_time
    
    # Base speed increases every 30 seconds
    speed_multiplier = 1.0 + (elapsed_time // 30) * 0.2
    speed_multiplier = min(speed_multiplier, 3.0)  # Cap at 3x speed
    
    # Spawn frequency increases every 45 seconds
    spawn_frequency = 1 + int(elapsed_time // 45)
    spawn_frequency = min(spawn_frequency, 3)  # Cap at 3 segments per spawn
    
    current_speed = FORWARD_SPEED * speed_multiplier
    
    return current_speed, spawn_frequency

# Add door collision check function
def check_door_collision():
    """Check collision with doors and trigger environment change"""
    global current_environment, next_environment, environment_transition_active, environment_transition_timer
    
    player_aabb = get_player_aabb()
    for door in doors:
        if not door.active:
            continue
        
        if player_aabb.intersects(door.aabb):
            door.active = False
            # Trigger environment transition
            next_environment = door.environment_type
            environment_transition_active = True
            environment_transition_timer = ENVIRONMENT_TRANSITION_TIME
            break

# Modify the update_environment function
def update_environment(delta_time):
    """Update environment transition and effects"""
    global environment_transition_active, environment_transition_timer, current_environment
    global weather_intensity, weather_timer
    
    # Handle environment transition
    if environment_transition_active:
        environment_transition_timer -= delta_time
        if environment_transition_timer <= 0:
            current_environment = next_environment
            environment_transition_active = False
            weather_intensity = 1.0  # Start weather effects for new environment
    
    # Update weather effects - keep them active for certain environments
    weather_timer += delta_time
    
    # Set weather intensity based on current environment instead of fading
    if current_environment in ["snow", "storm", "underwater", "night"]:
        weather_intensity = 1.0  # Keep weather active for these environments
    else:
        weather_intensity = 0.0  # No weather for other environments

# Add environment effects function
def draw_environment_effects():
    """Draw environment-specific visual effects"""
    if weather_intensity <= 0:
        return
    
    if current_environment == "snow":
        draw_snow_particles()
    elif current_environment == "storm":
        draw_rain_particles()
    elif current_environment == "underwater":
        draw_bubbles()
    elif current_environment == "night":
        draw_stars()

def draw_snow_particles():
    """Draw falling snow particles"""
    glColor4f(1.0, 1.0, 1.0, weather_intensity)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Simple snow particles
    for i in range(50):
        x = (i * 7.3) % 200 - 100  # Pseudo-random X
        y = 20 - ((i * 11.7 + weather_timer * 20) % 50)  # Falling Y - subtract from top
        z = player_z + ((i * 13.1) % 150) - 50  # Z spread
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glutSolidSphere(0.1, 4, 4)
        glPopMatrix()
    
    glDisable(GL_BLEND)

def draw_rain_particles():
    """Draw falling rain drops"""
    glColor4f(0.6, 0.8, 1.0, weather_intensity)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    
    for i in range(100):
        x = (i * 5.7) % 200 - 100
        y = 60 - ((i * 9.3 + weather_timer * 50) % 60) + 2  # Falling Y - subtract from top
        z = player_z + ((i * 7.1) % 150) - 50
        
        glVertex3f(x, y, z)
        glVertex3f(x, y - 1.5, z)  # Rain streak
    
    glEnd()

def draw_bubbles():
    """Draw underwater bubbles"""
    glColor4f(0.8, 0.9, 1.0, weather_intensity * 0.6)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    for i in range(20):
        x = (i * 8.7) % 100 - 50
        y = ((i * 6.1 + weather_timer * 10) % 30) + 2  # Rising bubbles
        z = player_z + ((i * 12.3) % 100) - 30
        
        glPushMatrix()
        glTranslatef(x, y, z)
        size = 0.2 + (i % 3) * 0.1
        glutSolidSphere(size, 6, 6)
        glPopMatrix()
    
    glDisable(GL_BLEND)

def draw_stars():
    """Draw night sky stars"""
    glColor3f(1.0, 1.0, 0.8)
    glPointSize(2.0)
    glBegin(GL_POINTS)
    
    for i in range(100):
        x = (i * 17.3) % 400 - 200
        y = 20 + (i * 3.7) % 20
        z = player_z + ((i * 23.1) % 300) - 100
        
        glVertex3f(x, y, z)
    
    glEnd()

def draw_railroad_ties():
    """Draw railroad ties with environment-appropriate colors"""
    tie_colors = {
        "snow": (0.3, 0.25, 0.2),     # Darker wood in snow
        "underwater": (0.2, 0.3, 0.2), # Seaweed-covered
        "default": (0.4, 0.3, 0.2)     # Normal brown wood
    }
    
    tie_color = tie_colors.get(current_environment, tie_colors["default"])
    glColor3f(*tie_color)
    
    tie_width = 0.3
    tie_height = 0.2
    tie_length = 14.0
    tie_spacing = 3.0
    animation_offset = (player_z % tie_spacing)
    
    z_start = int((player_z - 50) / tie_spacing) * tie_spacing - animation_offset
    z_end = player_z + 100
    
    z_pos = z_start
    while z_pos <= z_end:
        glPushMatrix()
        glTranslatef(0, 0.05, z_pos)
        glScalef(tie_length, tie_height, tie_width)
        glutSolidCube(1.0)
        glPopMatrix()
        z_pos += tie_spacing

def idle():
    global last_time
    
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    # Cap delta time to prevent huge jumps
    delta_time = min(delta_time, 1.0/30.0)  # Cap at 30 FPS minimum
    
    update(delta_time)
    glutPostRedisplay()

def main():
    global last_time
    
    # Initialize GLUT
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Runner3Lanes - 3D Train Track Runner")
    
    # Enable depth testing for 3D rendering
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    
    # Set background color (dark blue sky)
    glClearColor(0.1, 0.2, 0.5, 1.0)
    
    # Register callback functions
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)  # Add mouse callback
    glutIdleFunc(idle)
    
    # Initialize time tracking
    last_time = time.time()
    
    # Start the main loop
    glutMainLoop()

if __name__ == "__main__":
    main()