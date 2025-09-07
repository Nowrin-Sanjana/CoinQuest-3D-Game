from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time
import math
import random


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
LANE_WIDTH = 4.0
FORWARD_SPEED = 20.0
LANE_SWITCH_COOLDOWN = 0.25
LANE_TRANSITION_SPEED = 8.0 
JUMP_STRENGTH = 15.0
GRAVITY = 50.0
SLIDE_HEIGHT_REDUCTION = 0.5


SEGMENT_LENGTH = 20.0
SPAWN_DISTANCE = 100.0
CLEANUP_DISTANCE = -50.0


CAMERA_DISTANCE_BEHIND = 10.0
CAMERA_HEIGHT = 6.0
CAMERA_LOOK_AHEAD = 8.0
CAMERA_MIN_HEIGHT = 2.0
CAMERA_MAX_HEIGHT = 15.0
CAMERA_MIN_DISTANCE = 5.0
CAMERA_MAX_DISTANCE = 25.0
CAMERA_MOVE_SPEED = 5.0


MAX_AMMO = 5  
BULLET_SPEED = 70.0
BULLET_LIFETIME = 2.0
RELOAD_PICKUP_LIFETIME = 10.0


ENEMY_SPAWN_CHANCE = 0.3  
ENEMY_SPAWN_DELAY = 10.0
OBSTACLE_PASS_DISTANCE = 15.0


FLIGHT_DURATION = 5.0
FLIGHT_HEIGHT = 10.0 
FLIGHT_TRANSITION_SPEED = 15.0  
AERIAL_COIN_SPAWN_INTERVAL = 7.0  
FLIGHT_POWERUP_LIFETIME = 15.0  

COIN_MULTIPLIER_DURATION = 5.0  
COIN_MULTIPLIER_SPAWN_CHANCE = 0.002  
COIN_MULTIPLIER_COOLDOWN = 60.0  


MAGNET_DURATION = 8.0  
MAGNET_RADIUS = 15.0  
MAGNET_ATTRACTION_SPEED = 25.0  
MAGNET_POWERUP_SPAWN_CHANCE = 0.001  
MAGNET_POWERUP_COOLDOWN = 45.0  


DOOR_SPAWN_INTERVAL = 200.0  
DOOR_WIDTH = 6.0
DOOR_HEIGHT = 8.0
DOOR_DEPTH = 2.0
ENVIRONMENT_TRANSITION_TIME = 0.5 
DOOR_SPAWN_CHANCE = 0.0005  
DOOR_MIN_DISTANCE = 500.0


ENVIRONMENTS = [
    "forest",
    "desert",
    "snow",
    "night",
    "storm",
    "underwater"
]


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
ammo = MAX_AMMO
lives = 3  


leg_angle = 0.0
arm_angle = 0.0


god_mode = False
infinite_ammo = False
coin_multiplier_cheat = False  


obstacles = []
coins = []
enemies = []
bullets = []
reload_pickups = []
aerial_coins = []
flight_powerups = []
coin_multiplier_powerups = []  
magnet_powerups = []  
segments_spawned = 0

last_obstacle_z = -1000.0
enemy_cooldown_timer = 0.0
reload_spawn_cooldown = 0.0

last_time = time.time()
fps_counter = 0
fps_time = 0.0
last_aerial_coin_spawn = time.time()  
game_start_time = time.time()  

camera_mode = "third_person"  
camera_manual_height = CAMERA_HEIGHT
camera_manual_distance = CAMERA_DISTANCE_BEHIND
camera_manual_x_offset = 0.0

flight_powerup_active = False
flight_powerup_timer = 0.0

coin_multiplier_active = False
coin_multiplier_timer = 0.0
coin_multiplier_spawn_cooldown = 0.0

magnet_mode_active = False
magnet_mode_timer = 0.0
magnet_powerup_spawn_cooldown = 0.0

infinite_ammo_timer = 0.0  

current_environment = "default"
environment_transition_active = False
environment_transition_timer = 0.0
next_environment = "default"
last_door_spawn = 0.0
doors = []
weather_intensity = 0.0
weather_timer = 0.0
god_mode_timer = 0.0  

door_spawn_cooldown = 0.0  

game_paused = False  

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
        self.type = obstacle_type  
        self.active = True
        
        if obstacle_type == 'jumpable':
            self.height = 1.5
            self.color = (1.0, 0.5, 0.0)  

        elif obstacle_type == 'slidable':
            self.height = 3.0
            self.y = 3.5  
            self.color = (0.8, 0.2, 0.2)  

        else:  
            self.height = 4.0
            self.color = (0.5, 0.5, 0.5)  
        
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
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)  
        
        glColor3f(1.0, 0.95, 0.1)  
        
        glutSolidSphere(0.25, 12, 24)  
        
        glColor3f(1.0, 1.0, 0.3)  

        glutSolidSphere(0.32, 8, 16)  

        glPopMatrix()

class Enemy:
    def __init__(self, lane, z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 0.0
        self.z = z
        self.active = True
        self.width = 2.2  
        self.height = 3.5  
        self.depth = 2.2  
        self.aabb = AABB(self.x, self.y + self.height/2, self.z, self.width, self.height, self.depth)
        self.bob_timer = 0.0  
        self.speed = 8.0  
        self.target_lane = lane  
        self.lane_switch_timer = 0.0  
        self.lane_switch_cooldown = 2.0  
    
    def update(self):
        self.z -= self.speed * 0.016  
        
        if self.lane_switch_timer <= 0:
            if self.lane < player_lane:
                self.target_lane = min(self.lane + 1, 1)  
            elif self.lane > player_lane:
                self.target_lane = max(self.lane - 1, -1)  
            
            if self.target_lane != self.lane:
                self.lane = self.target_lane
                self.lane_switch_timer = self.lane_switch_cooldown
        else:
            self.lane_switch_timer -= 0.016  
        
        target_x = self.lane * LANE_WIDTH
        if abs(self.x - target_x) > 0.1:
            direction = 1 if target_x > self.x else -1
            self.x += direction * 8.0 * 0.016  
            if direction > 0 and self.x >= target_x:
                self.x = target_x
            elif direction < 0 and self.x <= target_x:
                self.x = target_x
        
        self.aabb.x = self.x
        self.aabb.y = self.y + self.height/2
        self.aabb.z = self.z
        
        self.bob_timer += 0.05  
        
        if self.z < player_z - 30:
            self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        bob_offset = math.sin(self.bob_timer) * 0.1
        glTranslatef(0, bob_offset, 0)
        
        glColor3f(1.0, 0.0, 0.0)  
        glPushMatrix()
        glTranslatef(0, 1.2, 0)  
        glutSolidSphere(1.5, 20, 20)  
        glPopMatrix()
        
        glColor3f(0.1, 0.1, 0.1)  
        glPushMatrix()
        glTranslatef(0, 3.0, 0)  
        glutSolidSphere(0.9, 15, 15)  
        glPopMatrix()
        
        glColor3f(1.0, 0.0, 0.0)  
        glPushMatrix()
        glTranslatef(-0.3, 3.2, 0.8)  
        glutSolidSphere(0.1, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.3, 3.2, 0.8)  
        glutSolidSphere(0.1, 8, 8)
        glPopMatrix()
        
        glPopMatrix()

class Bullet:
    def __init__(self, lane, start_z):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = 3.5 
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
        glColor3f(0.2, 0.1, 0.05)
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
        glColor3f(0.0, 1.0, 1.0)  
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(0.5, 16, 16)
        glPopMatrix()

class AerialCoin:
    def __init__(self, lane, z, height):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.y = height  
        self.z = z
        self.active = True
        self.rotation = 0.0
        self.bob_timer = 0.0  
        self.base_height = height  
        self.aabb = AABB(self.x, self.y, self.z, 1.0, 1.0, 1.0)
    
    def update(self, delta_time):
        self.rotation += 240.0 * delta_time  
        self.bob_timer += delta_time * 1.5
        self.y = self.base_height + math.sin(self.bob_timer) * 0.2  
        
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)  
        
        glColor3f(1.0, 0.95, 0.1)  
        
        glutSolidSphere(0.25, 12, 24)  
        
        glColor3f(1.0, 1.0, 0.3)  
        
        glutSolidSphere(0.32, 8, 16)  
        
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
        self.rotation += 120.0 * delta_time  
        self.bob_timer += delta_time * 3.0
        self.y = 1.0 + math.sin(self.bob_timer) * 0.3  
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glColor3f(0.0, 1.0, 1.0)
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glRotatef(45, 1, 0, 0)  
        
        glScalef(1.2, 0.3, 1.2)
        glutSolidCube(1.0)
        
        glColor3f(0.5, 1.0, 1.0)
        glScalef(1.3, 1.3, 1.3)
        glutSolidCube(1.0)
        glPopMatrix()

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
        self.rotation += 200.0 * delta_time  
        self.pulse_timer += delta_time * 4.0
        self.scale = 1.0 + math.sin(self.pulse_timer) * 0.3  
        self.aabb.x = self.x
        self.aabb.y = self.y
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glColor3f(1.0, 0.8, 0.0)
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glRotatef(45, 1, 0, 1)  
        
        glScalef(self.scale, self.scale * 0.3, self.scale)
        
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
        
        glColor3f(1.0, 1.0, 0.0)
        glScalef(1.5, 1.5, 1.5)
        
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
        glColor3f(0.6, 0.7, 0.8)  
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        
        glScalef(self.scale, self.scale, self.scale)
        
        glPushMatrix()
        glTranslatef(-0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        glScalef(1.1, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glColor3f(0.7, 0.8, 0.9)  
        glScalef(1.2, 1.2, 1.2)
        
        glPushMatrix()
        glTranslatef(-0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.4, 0, 0)
        glScalef(0.3, 1.0, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        glScalef(1.1, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPopMatrix()

class Door:
    def __init__(self, lane, z, environment_type):
        self.lane = lane
        self.x = lane * LANE_WIDTH  
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
        
        self.colors = {
            "forest": (0.2, 0.8, 0.2),    
            "desert": (1.0, 0.8, 0.2),    
            "snow": (0.8, 0.9, 1.0),      
            "night": (0.3, 0.2, 0.6),     
            "storm": (0.4, 0.4, 0.4),     
            "underwater": (0.2, 0.6, 1.0) 
        }
    
    def update(self, delta_time):
        self.rotation += 30.0 * delta_time  
        self.glow_timer += delta_time * 2.0
        self.aabb.x = self.x
        self.aabb.y = self.y + self.height/2
        self.aabb.z = self.z
    
    def draw(self):
        if not self.active:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y + self.height/2, self.z)
        
        color = self.colors.get(self.environment_type, (0.5, 0.5, 0.5))
        
        glColor3f(0.5, 0.2, 0.3)  
        glPushMatrix()
        glScalef(self.width + 1.0, self.height + 0.8, 0.2)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glColor3f(1.0, 0.7, 0.8)  
        glPushMatrix()
        glScalef(self.width + 0.3, self.height + 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glow = 0.3 + 0.2 * math.sin(self.glow_timer)
        glColor3f(color[0] + glow, color[1] + glow, color[2] + glow)
        glPushMatrix()
        glScalef(self.width, self.height, 0.1)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glRotatef(self.rotation, 0, 0, 1)
        for i in range(8):
            angle = i * 45.0
            glPushMatrix()
            glRotatef(angle, 0, 0, 1)
            glTranslatef(self.width/3, 0, 0.2)
            glColor3f(color[0], color[1], color[2])
            glutSolidSphere(0.2, 8, 8)
            glPopMatrix()
        glPopMatrix()
        
        self.draw_label()
        
        glPopMatrix()
    
    def draw_label(self):
        glPushMatrix()
        glTranslatef(0, self.height/2 + 1.0, 0.5)
        glColor3f(1.0, 1.0, 1.0)
        glPopMatrix()

def get_player_aabb():
    base_height = 4.0
    height = base_height * (SLIDE_HEIGHT_REDUCTION if is_sliding else 1.0)
    y_center = player_y + height / 2.0
    
    return AABB(player_x, y_center, player_z, 1.0, height, 1.0)

def spawn_segment():
    global segments_spawned
    spawn_z = segments_spawned * SEGMENT_LENGTH
    
    if segments_spawned < 3:
        segments_spawned += 1
        return
    
    door_safe_zone = check_door_safe_zone(spawn_z)
    
    _, current_spawn_freq = get_current_difficulty()
    
    for _ in range(current_spawn_freq):
        current_z = spawn_z + (_ * SEGMENT_LENGTH)
        
        if door_safe_zone:
            continue  
        
        segment_type = random.choice(['obstacles', 'coins', 'mixed'])
        
        if segment_type == 'obstacles':
            occupied_lanes = random.sample([-1, 0, 1], random.randint(1, 2))
            
            for lane in occupied_lanes:
                obstacle_type = random.choice(['solid', 'jumpable', 'slidable'])
                obstacle = Obstacle(lane, current_z, obstacle_type)
                obstacles.append(obstacle)
        
        elif segment_type == 'coins':
            coin_lane = random.choice([-1, 0, 1])  
            
            for i in range(3):  
                coin_z = current_z + i * 2.0
                coin = Coin(coin_lane, coin_z)
                coins.append(coin)
                
                if coin_multiplier_active or coin_multiplier_cheat:
                    coin2 = Coin(coin_lane, coin_z)
                    coin2.x = coin_lane * LANE_WIDTH + 0.8  
                    coin2.aabb.x = coin2.x  
                    coins.append(coin2)
        
        elif segment_type == 'mixed':
            safe_lane = random.choice([-1, 0, 1])
            
            for lane in [-1, 0, 1]:
                if lane != safe_lane and random.random() < 0.7:
                    obstacle_type = random.choice(['jumpable', 'slidable'])
                    obstacle = Obstacle(lane, current_z, obstacle_type)
                    obstacles.append(obstacle)
            
            if random.random() < 0.5:
                coin = Coin(safe_lane, current_z + 5.0)
                coins.append(coin)
                
                if coin_multiplier_active or coin_multiplier_cheat:
                    coin2 = Coin(safe_lane, current_z + 5.0)
                    coin2.x = safe_lane * LANE_WIDTH + 0.8  
                    coin2.aabb.x = coin2.x  
                    coins.append(coin2)
    
    segments_spawned += current_spawn_freq

def check_door_safe_zone(spawn_z):
    safe_zone_distance = 50.0  
    
    for door in doors:
        if door.active:
            if abs(spawn_z - door.z) <= safe_zone_distance:
                return True
    
    return False

def spawn_door():
    door_lane = random.choice([-1, 0, 1])  
    door_z = player_z + SPAWN_DISTANCE + 100  
    
    available_environments = [env for env in ENVIRONMENTS if env != current_environment]
    environment_type = random.choice(available_environments)
    
    door = Door(door_lane, door_z, environment_type)
    doors.append(door)

def clear_obstacles_around_door(door_z):
    safe_zone_distance = 30.0  
    
    global obstacles, coins, reload_pickups, flight_powerups, coin_multiplier_powerups, magnet_powerups, aerial_coins
    
    obstacles[:] = [obs for obs in obstacles if abs(obs.z - door_z) > safe_zone_distance]
    coins[:] = [coin for coin in coins if abs(coin.z - door_z) > safe_zone_distance]
    reload_pickups[:] = [rp for rp in reload_pickups if abs(rp.z - door_z) > safe_zone_distance]
    flight_powerups[:] = [fp for fp in flight_powerups if abs(fp.z - door_z) > safe_zone_distance]
    coin_multiplier_powerups[:] = [cmp for cmp in coin_multiplier_powerups if abs(cmp.z - door_z) > safe_zone_distance]
    magnet_powerups[:] = [mp for mp in magnet_powerups if abs(mp.z - door_z) > safe_zone_distance]
    aerial_coins[:] = [ac for ac in aerial_coins if abs(ac.z - door_z) > safe_zone_distance]

def check_obstacle_pass_and_spawn_enemies():
    global last_obstacle_z, enemy_cooldown_timer
    
    if game_over:
        return
    
    furthest_passed_obstacle = -1000.0
    for obs in obstacles:
        if obs.active and obs.z < player_z and obs.z > last_obstacle_z:
            if obs.z > furthest_passed_obstacle:
                furthest_passed_obstacle = obs.z
    
    if (furthest_passed_obstacle > last_obstacle_z and 
        player_z - furthest_passed_obstacle > OBSTACLE_PASS_DISTANCE and 
        enemy_cooldown_timer <= 0):
        
        if random.random() < ENEMY_SPAWN_CHANCE:
            enemy_z = player_z + SPAWN_DISTANCE + 40  
            enemy_lane = random.choice([-1, 0, 1])
            enemy = Enemy(enemy_lane, enemy_z)
            enemies.append(enemy)
            enemy_cooldown_timer = ENEMY_SPAWN_DELAY
        
        last_obstacle_z = furthest_passed_obstacle
    
    if enemy_cooldown_timer > 0:
        enemy_cooldown_timer -= 0.1

def update_spawner():
    global reload_spawn_cooldown, last_aerial_coin_spawn, coin_multiplier_spawn_cooldown
    global magnet_powerup_spawn_cooldown, last_door_spawn, door_spawn_cooldown
    global obstacles, coins, enemies, bullets, reload_pickups, aerial_coins, flight_powerups, coin_multiplier_powerups
    global magnet_powerups, doors
    
    while (segments_spawned * SEGMENT_LENGTH) < (player_z + SPAWN_DISTANCE):
        spawn_segment()
    
    if door_spawn_cooldown <= 0:
        if random.random() < DOOR_SPAWN_CHANCE:
            if player_z - last_door_spawn > DOOR_MIN_DISTANCE:
                spawn_door()
                last_door_spawn = player_z
                door_spawn_cooldown = random.uniform(300.0, 800.0)
    else:
        door_spawn_cooldown -= 1.0  
    
    check_obstacle_pass_and_spawn_enemies()
    
    if time.time() - last_aerial_coin_spawn > AERIAL_COIN_SPAWN_INTERVAL:
        spawn_aerial_coin()
        last_aerial_coin_spawn = time.time()
    
    if reload_spawn_cooldown <= 0:
        if random.random() < 0.005:
            pickup_lane = random.choice([-1, 0, 1])
            pickup_z = player_z + SPAWN_DISTANCE + random.uniform(10, 30)  
            
            if not check_door_safe_zone(pickup_z):
                reload_pickups.append(ReloadPickup(pickup_lane, pickup_z))
            
            reload_spawn_cooldown = random.uniform(40.0, 80.0)  
    else:
        reload_spawn_cooldown -= 0.1
    
    if coin_multiplier_spawn_cooldown <= 0:
        if random.random() < COIN_MULTIPLIER_SPAWN_CHANCE:
            powerup_lane = random.choice([-1, 0, 1])
            powerup_z = player_z + SPAWN_DISTANCE + random.uniform(20, 50)
            
            if not check_door_safe_zone(powerup_z):
                coin_multiplier_powerups.append(CoinMultiplierPowerup(powerup_lane, powerup_z))
            
            coin_multiplier_spawn_cooldown = COIN_MULTIPLIER_COOLDOWN
    else:
        coin_multiplier_spawn_cooldown -= 0.1
    
    if magnet_powerup_spawn_cooldown <= 0:
        if random.random() < MAGNET_POWERUP_SPAWN_CHANCE:
            powerup_lane = random.choice([-1, 0, 1])
            powerup_z = player_z + SPAWN_DISTANCE + random.uniform(25, 60)
            
            if not check_door_safe_zone(powerup_z):
                magnet_powerups.append(MagnetPowerup(powerup_lane, powerup_z))
            
            magnet_powerup_spawn_cooldown = MAGNET_POWERUP_COOLDOWN
    else:
        magnet_powerup_spawn_cooldown -= 0.1
    
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
    
    temp_flight_powerups = []
    for powerup in flight_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_flight_powerups.append(powerup)
    flight_powerups[:] = temp_flight_powerups
    
    temp_coin_multiplier_powerups = []
    for powerup in coin_multiplier_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_coin_multiplier_powerups.append(powerup)
    coin_multiplier_powerups[:] = temp_coin_multiplier_powerups
    
    temp_magnet_powerups = []
    for powerup in magnet_powerups:
        if powerup.z > player_z + CLEANUP_DISTANCE:
            temp_magnet_powerups.append(powerup)
    magnet_powerups[:] = temp_magnet_powerups
    
    temp_doors = []
    for door in doors:
        if door.z > player_z + CLEANUP_DISTANCE:
            temp_doors.append(door)
    doors[:] = temp_doors

def check_collisions():
    global score, game_over, lives  

    player_aabb = get_player_aabb()

    for obstacle in obstacles:
        if not obstacle.active:
            continue

        if player_aabb.intersects(obstacle.aabb):
            if obstacle.type == 'jumpable' and is_jumping and player_y > 1.0:
                continue  
            elif obstacle.type == 'slidable' and is_sliding and player_y < 3.0:
                continue  
            elif is_flying:
                continue  
            else:
                if obstacle.type == 'solid':
                    if not god_mode:
                        game_over = True
                    obstacle.active = False
                
                else:
                    if not god_mode:
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                    obstacle.active = False

    for coin in coins:
        if not coin.active:
            continue

        if player_aabb.intersects(coin.aabb):
            score += 1
            coin.active = False

    for coin in aerial_coins:
        if not coin.active:
            continue

        if is_flying and player_aabb.intersects(coin.aabb):
            score += 2
            coin.active = False

    for enemy in enemies:
        if not enemy.active:
            continue

        if player_aabb.intersects(enemy.aabb):
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
                score += 5  
                break

def check_reload_pickup_collision():
    global ammo
    
    player_aabb = get_player_aabb()
    for rp in reload_pickups:
        if not rp.active:
            continue
        if player_aabb.intersects(rp.aabb):
            rp.active = False
            ammo = MAX_AMMO  

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
        title = f"CoinQuest 3D - FPS: {fps:.1f}"
        glutSetWindowTitle(title.encode('ascii'))
        fps_counter = 0
        fps_time = current_time

def draw_player():
    global leg_angle, arm_angle
    
    glPushMatrix()
    
    slide_offset = -1.5 if is_sliding else 0.0  
    glTranslatef(player_x, player_y + 1.5 + slide_offset, player_z)
    
    glRotatef(-90, 1, 0, 0)  
    glRotatef(180, 0, 0, 1)  
    
    scale = 0.02
    glScalef(scale, scale, scale)
    
    if god_mode:
        glColor3f(1.0, 1.0, 1.0)  
    
    running_speed = 8.0 if not game_over else 0.0
    leg_swing = math.sin(leg_angle * running_speed) * 25.0  
    arm_swing = math.sin(arm_angle * running_speed) * 20.0  
    
    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.0, 1.0)
    glTranslatef(-22, 0, 50)
    glRotatef(leg_swing, 1, 0, 0)  
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 50, 8, 1)
    glPopMatrix()

    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.0, 1.0)
    glTranslatef(22, 0, 50)
    glRotatef(-leg_swing, 1, 0, 0)  
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 50, 8, 1)
    glPopMatrix()

    glPushMatrix()
    if not god_mode:
        glColor3f(0.0, 0.6, 0.0)
    glTranslatef(0, 0, 75)
    glScalef(1.5, 1.0, 1.5)
    glutSolidCube(40)
    glPopMatrix()

    head_bob = math.sin(leg_angle * running_speed * 2) * 2.0  
    glPushMatrix()
    if not god_mode:
        glColor3f(0.1, 0.1, 0.1)
    glTranslatef(0, 0, 130 + head_bob)
    gluSphere(gluNewQuadric(), 25, 16, 16)
    glPopMatrix()

    glPushMatrix()
    if not god_mode:
        glColor3f(1.0, 0.8, 0.6)
    glTranslatef(-22, 20, 100)
    glRotatef(-arm_swing - 90, 1, 0, 0)  
    gluCylinder(gluNewQuadric(), 8, 4, 50, 8, 1)
    glPopMatrix()
    
    glPushMatrix()
    if not god_mode:
        glColor3f(1.0, 0.8, 0.6)
    glTranslatef(22, 20, 100)
    glRotatef(arm_swing - 90, 1, 0, 0)  
    gluCylinder(gluNewQuadric(), 8, 4, 50, 8, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 100)
    glTranslatef(0, 20, 0)
    glRotatef(-90, 1, 0, 0)
    if not god_mode:
        glColor3f(0.2, 0.2, 0.2)
    gluCylinder(gluNewQuadric(), 12, 4, 60, 10, 10)
    glPopMatrix()

    glPopMatrix()

def draw_ground():
    ground_colors = {
        "forest": (0.2, 0.4, 0.1),    
        "desert": (0.8, 0.6, 0.3),    
        "snow": (0.9, 0.9, 1.0),      
        "night": (0.1, 0.1, 0.2),     
        "storm": (0.3, 0.3, 0.3),     
        "underwater": (0.1, 0.3, 0.6) 
    }
    
    base_color = ground_colors.get(current_environment, (0.3, 0.25, 0.15))
    
    glColor3f(*base_color)
    glBegin(GL_QUADS)
    ground_size = 100.0
    glVertex3f(-ground_size, -1.0, player_z - 50.0)
    glVertex3f(ground_size, -1.0, player_z - 50.0)
    glVertex3f(ground_size, -1.0, player_z + 100.0)
    glVertex3f(-ground_size, -1.0, player_z + 100.0)
    glEnd()
    
    side_colors = {
        "forest": (0.1, 0.6, 0.1),    
        "desert": (0.9, 0.7, 0.4),    
        "snow": (0.95, 0.95, 1.0),    
        "night": (0.2, 0.2, 0.3),     
        "storm": (0.4, 0.4, 0.4),     
        "underwater": (0.2, 0.4, 0.8) 
    }
    
    side_color = side_colors.get(current_environment, (0.4, 0.8, 0.3))
    glColor3f(*side_color)
    
    glBegin(GL_QUADS)
    glVertex3f(-ground_size, -0.8, player_z - 50.0)
    glVertex3f(-8.0, -0.8, player_z - 50.0)
    glVertex3f(-8.0, -0.8, player_z + 100.0)
    glVertex3f(-ground_size, -0.8, player_z + 100.0)
    
    glVertex3f(8.0, -0.8, player_z - 50.0)
    glVertex3f(ground_size, -0.8, player_z - 50.0)
    glVertex3f(ground_size, -0.8, player_z + 100.0)
    glVertex3f(8.0, -0.8, player_z + 100.0)
    glEnd()
    
    glColor3f(0.4, 0.35, 0.25)  
    glBegin(GL_QUADS)
    foundation_height = -0.9
    glVertex3f(-8.0, foundation_height, player_z - 50.0)
    glVertex3f(8.0, foundation_height, player_z - 50.0)
    glVertex3f(8.0, foundation_height, player_z + 100.0)
    glVertex3f(-8.0, foundation_height, player_z + 100.0)
    glEnd()
    
    draw_environment_effects()
    
    draw_railroad_ties()
    draw_environment_objects()

def draw_tree(x, z):
    glPushMatrix()
    glTranslatef(x, -0.8, z)  
    
    glColor3f(0.4, 0.2, 0.1)  
    glPushMatrix()
    glTranslatef(0, 1.5, 0)  
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.3, 0.2, 3.0, 8, 1)
    glPopMatrix()
    
    glColor3f(0.1, 0.6, 0.1)  
    for j in range(3):
        glPushMatrix()
        glTranslatef(0, 2.7 + j * 0.8, 0)  
        glutSolidSphere(1.2 - j * 0.2, 12, 12)
        glPopMatrix()
    
    glPopMatrix()

def draw_tunnel_structure(z):
    glPushMatrix()
    glTranslatef(0, -0.8, z)  
    
    glColor3f(0.4, 0.4, 0.5)  
    
    glPushMatrix()
    glTranslatef(-10.0, 3.8, 0)  
    glScalef(2.0, 6.0, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(10.0, 3.8, 0)  
    glScalef(2.0, 6.0, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 7.3, 0)  
    glScalef(22.0, 1.5, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glColor3f(0.35, 0.35, 0.45)
    for angle in range(-90, 91, 15):
        glPushMatrix()
        rad = math.radians(angle)
        arch_x = 8.0 * math.sin(rad)
        arch_y = 6.8 + 2.0 * math.cos(rad)  
        glTranslatef(arch_x, arch_y, 0)
        glutSolidSphere(0.8, 8, 8)
        glPopMatrix()
    
    glPopMatrix()

def draw_signal_pole(x, z):
    glPushMatrix()
    glTranslatef(x, -0.8, z)  
    
    glColor3f(0.6, 0.6, 0.6)  
    glPushMatrix()
    glTranslatef(0, 2.5, 0)  
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.15, 0.15, 5.0, 8, 1)
    glPopMatrix()
    
    signal_color = (1.0, 0.0, 0.0) if abs(z - player_z) < 30 else (0.0, 1.0, 0.0)
    glColor3f(*signal_color)
    glPushMatrix()
    glTranslatef(0, 4.0, 0)  
    glutSolidSphere(0.3, 12, 12)
    glPopMatrix()
    
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(-1.0, 3.7, 0)  
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), 0.08, 0.08, 2.0, 6, 1)
    glPopMatrix()
    
    glPopMatrix()

def draw_environment_objects():
    pole_spacing = 40.0
    pole_offset = int(player_z / pole_spacing) * pole_spacing
    
    for i in range(-1, 4):  
        pole_z = pole_offset + (i * pole_spacing)
        if abs(pole_z - player_z) < 80:  
            draw_signal_pole(-12.0, pole_z)
            draw_signal_pole(12.0, pole_z)
    
    tunnel_spacing = 200.0
    tunnel_offset = int(player_z / tunnel_spacing) * tunnel_spacing
    
    for i in range(-1, 2):
        tunnel_z = tunnel_offset + (i * tunnel_spacing)
        if abs(tunnel_z - player_z) < 120:
            draw_tunnel_structure(tunnel_z)
    
    draw_background_scenery()

def draw_background_scenery():
    glColor3f(0.3, 0.4, 0.6)  
    
    mountain_distance = 200.0
    for i in range(-5, 6):
        mountain_x = i * 40.0
        mountain_z = player_z + mountain_distance
        mountain_height = 15.0 + abs(i * 3.0)
        
        glPushMatrix()
        glTranslatef(mountain_x, (mountain_height/2) - 1.0, mountain_z)  
        glScalef(30.0, mountain_height, 20.0)
        glutSolidCube(1.0)
        glPopMatrix()
    
    glColor3f(0.9, 0.9, 1.0)  
    cloud_distance = 150.0
    cloud_height = 25.0
    
    for i in range(-3, 4):
        cloud_x = i * 60.0 + math.sin(player_z * 0.01) * 10.0  
        cloud_z = player_z + cloud_distance + (i % 2) * 20.0
        
        for j in range(3):
            glPushMatrix()
            glTranslatef(cloud_x + j * 4.0, cloud_height + j * 1.0, cloud_z)
            glutSolidSphere(3.0 + j * 0.5, 12, 12)
            glPopMatrix()
    
    draw_side_trees()

def draw_side_trees():
    tree_spacing = 25.0
    tree_offset = int(player_z / tree_spacing) * tree_spacing
    
    for i in range(-2, 5):
        tree_z = tree_offset + (i * tree_spacing) + (i % 3) * 5.0  
        if abs(tree_z - player_z) < 60:
            tree_x = -15.0 + (i % 3) * 3.0
            draw_tree(tree_x, tree_z)
            
            tree_x = 15.0 + (i % 3) * 3.0
            draw_tree(tree_x, tree_z)
            
def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    if game_paused:
        glColor3f(1.0, 1.0, 0.0)  
        paused_text = "PAUSED"
        
        text_width = len(paused_text) * 18  
        text_x = (WINDOW_WIDTH - text_width) // 2
        text_y = WINDOW_HEIGHT // 2 + 50
        
        glRasterPos2f(text_x, text_y)
        for c in paused_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        
        unpause_text = "Press SPACE to continue"
        unpause_width = len(unpause_text) * 18  
        unpause_x = (WINDOW_WIDTH - unpause_width) // 2
        unpause_y = text_y - 40
        
        glColor3f(1.0, 1.0, 1.0)  
        glRasterPos2f(unpause_x, unpause_y)
        for c in unpause_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))  
    
    if game_over:
        glColor3f(1.0, 0.0, 0.0)  
        game_over_text = "GAME OVER"
        
        text_width = len(game_over_text) * 18  
        text_x = (WINDOW_WIDTH - text_width) // 2
        text_y = WINDOW_HEIGHT // 2 + 50
        
        glRasterPos2f(text_x, text_y)
        for c in game_over_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        
        restart_text = "Press 'R' to restart"
        restart_width = len(restart_text) * 18  
        restart_x = (WINDOW_WIDTH - restart_width) // 2
        restart_y = text_y - 40
        
        glColor3f(1.0, 1.0, 1.0)  
        glRasterPos2f(restart_x, restart_y)
        for c in restart_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))  
        
        final_score_text = f"Final Score: {score}"
        score_width = len(final_score_text) * 18  
        score_x = (WINDOW_WIDTH - score_width) // 2
        score_y = restart_y - 30
        
        glColor3f(1.0, 1.0, 0.0)  
        glRasterPos2f(score_x, score_y)
        for c in final_score_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))  
    
    glColor3f(1.0, 1.0, 1.0)
    
    if coin_multiplier_active or coin_multiplier_cheat:
        if coin_multiplier_active:
            score_text = f"Score: {score} (x10 MULTIPLIER - {coin_multiplier_timer:.1f}s)"
        else:
            score_text = f"Score: {score} (x10 MULTIPLIER CHEAT)"
        glColor3f(1.0, 1.0, 0.0)  
    else:
        score_text = f"Score: {score}"
        glColor3f(1.0, 1.0, 1.0)  
    
    glRasterPos2f(10, WINDOW_HEIGHT - 30)
    for c in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)  
    
    distance = int(player_z / 10.0)
    distance_text = f"Distance: {distance}m"
    glRasterPos2f(10, WINDOW_HEIGHT - 60)
    for c in distance_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    env_text = f"Environment: {current_environment.upper()}"
    glRasterPos2f(10, WINDOW_HEIGHT - 90)
    for c in env_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    lives_text = f"Lives: {lives}"
    glColor3f(1.0, 0.5, 0.5)
    glRasterPos2f(10, WINDOW_HEIGHT - 120)
    for c in lives_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)
    
    if infinite_ammo and infinite_ammo_timer > 0:
        ammo_text = f"Ammo: ∞ ({infinite_ammo_timer:.1f}s) / {MAX_AMMO}"
        glColor3f(0.0, 1.0, 0.0)
    else:
        ammo_text = f"Ammo: {ammo} / {MAX_AMMO}"
        if ammo == 0:
            glColor3f(1.0, 0.0, 0.0)
        elif ammo <= 2:
            glColor3f(1.0, 1.0, 0.0)
        else:
            glColor3f(1.0, 1.0, 1.0)
    
    glRasterPos2f(10, WINDOW_HEIGHT - 150)
    for c in ammo_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glColor3f(1.0, 1.0, 1.0)
    
    if god_mode and god_mode_timer > 0:
        god_mode_text = f"GOD MODE: {god_mode_timer:.1f}s"
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(10, WINDOW_HEIGHT - 180)
        for c in god_mode_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)
        status_offset = 30
    else:
        status_offset = 0
    
    camera_text = f"Camera: {camera_mode.upper()} (Press C to switch)"
    glRasterPos2f(10, WINDOW_HEIGHT - 180 - status_offset)
    for c in camera_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    if camera_mode == "third_person":
        controls_text = "Arrows: Move Camera | A/D: Move Player Left/Right"
        glRasterPos2f(10, WINDOW_HEIGHT - 210 - status_offset)
        for c in controls_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    else:
        controls_text = "D/A: Move Left/Right | W: Jump | S: Slide"
        glRasterPos2f(10, WINDOW_HEIGHT - 210 - status_offset)
        for c in controls_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    if camera_mode == "first_person":
        lane_names = {-1: "LEFT", 0: "CENTER", 1: "RIGHT"}
        lane_text = f"Lane: {lane_names[player_lane]}"
        glRasterPos2f(10, WINDOW_HEIGHT - 240 - status_offset)
        for c in lane_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    
    status_y = WINDOW_HEIGHT - 270 - status_offset
    if environment_transition_active:
        transition_text = f"ENTERING {next_environment.upper()}... ({environment_transition_timer:.1f}s)"
        glColor3f(0.0, 1.0, 1.0)
        glRasterPos2f(10, status_y)
        for c in transition_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)
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
        glColor3f(1.0, 0.0, 1.0)
        glRasterPos2f(10, status_y)
        for c in magnet_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        glColor3f(1.0, 1.0, 1.0)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_player(delta_time):
    global player_y, player_z, player_velocity_y, is_jumping, is_sliding, slide_timer, lane_switch_timer
    global is_flying, flight_timer, flight_target_height, player_x, target_x
    
    if game_over:
        return
    
    current_speed, _ = get_current_difficulty()
    
    player_z += current_speed * delta_time
    
    if abs(player_x - target_x) > 0.1:
        direction = 1 if target_x > player_x else -1
        player_x += direction * LANE_TRANSITION_SPEED * delta_time
        if direction > 0 and player_x >= target_x:
            player_x = target_x
        elif direction < 0 and player_x <= target_x:
            player_x = target_x
    
    if lane_switch_timer > 0:
        lane_switch_timer -= delta_time
    if is_sliding and slide_timer > 0:
        slide_timer -= delta_time
        if slide_timer <= 0:
            is_sliding = False
    
    if is_flying:
        flight_timer -= delta_time
        
        height_diff = flight_target_height - player_y
        if abs(height_diff) > 0.1:
            if height_diff > 0:
                player_y += FLIGHT_TRANSITION_SPEED * delta_time
            else:
                player_y -= FLIGHT_TRANSITION_SPEED * delta_time
        if flight_timer <= 0:
            is_flying = False
            flight_target_height = 0.0
    elif player_y > 0 and not is_jumping:
        player_y -= FLIGHT_TRANSITION_SPEED * delta_time
        if player_y <= 0:
            player_y = 0.0
    
    elif is_jumping:
        player_y += player_velocity_y * delta_time
        player_velocity_y -= GRAVITY * delta_time
        
        if player_y <= 0.0:
            player_y = 0.0
            player_velocity_y = 0.0
            is_jumping = False

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
    global lives, game_paused, camera_mode
    camera_mode = "third_person"
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
    game_paused = False
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
    lives = 3

    current_environment = "default"
    last_door_spawn = 0.0
    environment_transition_active = False
    weather_intensity = 0.0
    
    game_start_time = time.time()
    
    camera_manual_height = CAMERA_HEIGHT
    camera_manual_distance = CAMERA_DISTANCE_BEHIND
    camera_manual_x_offset = 0.0
    
    flight_powerup_active = False
    flight_powerup_timer = 0.0
    coin_multiplier_active = False
    coin_multiplier_timer = 0.0
    coin_multiplier_spawn_cooldown = random.uniform(30.0, 60.0)
    magnet_mode_active = False
    magnet_mode_timer = 0.0
    magnet_powerup_spawn_cooldown = random.uniform(20.0, 40.0)
    
    obstacles[:] = []
    coins[:] = []
    enemies[:] = []
    bullets[:] = []
    reload_pickups[:] = []
    aerial_coins[:] = []
    flight_powerups[:] = []
    coin_multiplier_powerups[:] = []
    magnet_powerups[:] = []
    doors[:] = []

    last_door_spawn = -1000.0
    door_spawn_cooldown = random.uniform(200.0, 400.0)

def setup_camera():
    global camera_manual_height, camera_manual_distance, camera_manual_x_offset
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(65.0, float(WINDOW_WIDTH)/float(WINDOW_HEIGHT), 0.1, 1000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if camera_mode == "first_person":
        camera_x = player_x
        base_camera_height = player_y + 1.8
        if is_sliding:
            base_camera_height = player_y + 0.8
        camera_y = base_camera_height
        camera_z = player_z
        
        look_x = player_x
        look_y = base_camera_height
        look_z = player_z + 10.0
        
        gluLookAt(camera_x, camera_y, camera_z,
                  look_x, look_y, look_z,
                  0.0, 1.0, 0.0)
    
    else:
        camera_x = camera_manual_x_offset
        camera_y = camera_manual_height + player_y * 0.3
        camera_z = player_z - camera_manual_distance
        
        look_x = 0.0
        look_y = player_y + 1.0
        look_z = player_z + CAMERA_LOOK_AHEAD
        
        gluLookAt(camera_x, camera_y, camera_z,
                  look_x, look_y, look_z,
                  0.0, 1.0, 0.0)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    setup_camera()
    
    draw_ground()
    draw_player()
    
    for obstacle in obstacles:
        obstacle.draw()
    
    for coin in coins:
        coin.draw()
    
    for coin in aerial_coins:
        coin.draw()
    
    for powerup in flight_powerups:
        powerup.draw()
    
    for powerup in coin_multiplier_powerups:
        powerup.draw()
    
    for powerup in magnet_powerups:
        powerup.draw()
    
    for door in doors:
        door.draw()
    
    for enemy in enemies:
        enemy.draw()
    
    for bullet in bullets:
        bullet.draw()
    
    for pickup in reload_pickups:
        pickup.draw()
    
    draw_hud()
    
    glutSwapBuffers()
    update_fps()

def update(delta_time):
    global leg_angle, arm_angle, flight_powerup_timer, flight_powerup_active
    global coin_multiplier_timer, coin_multiplier_active, magnet_mode_timer, magnet_mode_active
    global god_mode, god_mode_timer, infinite_ammo, infinite_ammo_timer
    
    if game_paused:
        return
    
    if not game_over:
        update_player(delta_time)
        update_spawner()
        update_environment(delta_time)
        
        if god_mode and god_mode_timer > 0:
            god_mode_timer -= delta_time
            if god_mode_timer <= 0:
                god_mode = False
                god_mode_timer = 0.0
        
        if infinite_ammo and infinite_ammo_timer > 0:
            infinite_ammo_timer -= delta_time
            if infinite_ammo_timer <= 0:
                infinite_ammo = False
                infinite_ammo_timer = 0.0
        
        if flight_powerup_active:
            flight_powerup_timer -= delta_time
            if flight_powerup_timer <= 0:
                flight_powerup_active = False
        
        if coin_multiplier_active:
            coin_multiplier_timer -= delta_time
            if coin_multiplier_timer <= 0:
                coin_multiplier_active = False
        
        if magnet_mode_active:
            magnet_mode_timer -= delta_time
            if magnet_mode_timer <= 0:
                magnet_mode_active = False
        
        update_magnet_attraction(delta_time)
        
        for coin in coins:
            coin.update(delta_time)
        
        for coin in aerial_coins:
            coin.update(delta_time)
        
        for powerup in flight_powerups:
            powerup.update(delta_time)
        
        for powerup in coin_multiplier_powerups:
            powerup.update(delta_time)
        
        for powerup in magnet_powerups:
            powerup.update(delta_time)
        
        for door in doors:
            door.update(delta_time)
        
        for obstacle in obstacles:
            obstacle.update()
        
        for enemy in enemies:
            enemy.update()
        
        for bullet in bullets:
            bullet.update(delta_time)
        
        for pickup in reload_pickups:
            pickup.update(delta_time)
        
        check_collisions()
        check_bullet_enemy_collision()
        check_reload_pickup_collision()
        check_flight_powerup_collision()
        check_coin_multiplier_collision()
        check_magnet_powerup_collision()
        check_door_collision()
    
    leg_angle += delta_time
    arm_angle += delta_time

def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not game_paused:
            shoot()

def keyboard(key, x, y):
    global god_mode, infinite_ammo, camera_mode, coin_multiplier_cheat, god_mode_timer, infinite_ammo_timer
    global game_paused

    if key == b'g' or key == b'G':
        if not god_mode:
            god_mode = True
            god_mode_timer = 10.0
    elif key == b'r' or key == b'R':
        reset_game()
    elif key == b'i' or key == b'I':
        if not infinite_ammo:
            infinite_ammo = True
            infinite_ammo_timer = 10.0
    elif key == b'c' or key == b'C':
        if camera_mode == "third_person":
            camera_mode = "first_person"
        else:
            camera_mode = "third_person"
    elif key == b'f' or key == b'F':
        activate_flight_mode()
    elif key == b' ':
        if game_over:
            return
        
        game_paused = not game_paused
        return
    
    if not game_paused:
        keyboard_wasd(key, x, y)

def special_keys(key, x, y):
    global camera_manual_height, camera_manual_distance, camera_manual_x_offset
    
    if camera_mode == "third_person":
        if key == GLUT_KEY_UP:
            camera_manual_height = min(camera_manual_height + CAMERA_MOVE_SPEED * 0.1, CAMERA_MAX_HEIGHT)
        elif key == GLUT_KEY_DOWN:
            camera_manual_height = max(camera_manual_height - CAMERA_MOVE_SPEED * 0.1, CAMERA_MIN_HEIGHT)
        elif key == GLUT_KEY_LEFT:
            camera_manual_x_offset += CAMERA_MOVE_SPEED * 0.1
        elif key == GLUT_KEY_RIGHT:
            camera_manual_x_offset -= CAMERA_MOVE_SPEED * 0.1

def keyboard_wasd(key, x, y):
    global player_lane, lane_switch_timer, is_jumping, is_sliding, slide_timer
    global player_velocity_y, target_x
    
    if game_over or game_paused:
        return
    
    if key == b'a' or key == b'A':
        if lane_switch_timer <= 0 and player_lane < 1:
            player_lane += 1
            target_x = player_lane * LANE_WIDTH
            lane_switch_timer = LANE_SWITCH_COOLDOWN
    elif key == b'd' or key == b'D':
        if lane_switch_timer <= 0 and player_lane > -1:
            player_lane -= 1
            target_x = player_lane * LANE_WIDTH
            lane_switch_timer = LANE_SWITCH_COOLDOWN
    elif key == b'w' or key == b'W':
        if not is_jumping and not is_flying:
            is_jumping = True
            player_velocity_y = JUMP_STRENGTH
            if is_sliding:
                is_sliding = False
                slide_timer = 0.0
    elif key == b's' or key == b'S':
        if not is_sliding and not is_flying:
            is_sliding = True
            slide_timer = 1.0
            if is_jumping:
                is_jumping = False
                player_velocity_y = 0.0
                player_y = 0.0

def activate_flight_mode():
    global is_flying, flight_timer, flight_target_height, flight_powerup_active
    
    if flight_powerup_active and not is_flying and not game_over:
        is_flying = True
        flight_timer = FLIGHT_DURATION
        flight_target_height = FLIGHT_HEIGHT
        flight_powerup_active = False

def check_flight_powerup_collision():
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
    global coin_multiplier_active, coin_multiplier_timer, score
    
    player_aabb = get_player_aabb()
    for powerup in coin_multiplier_powerups:
        if not powerup.active:
            continue
        
        if player_aabb.intersects(powerup.aabb):
            powerup.active = False
            coin_multiplier_active = True
            coin_multiplier_timer = COIN_MULTIPLIER_DURATION
            
            double_existing_coins()
            
            score += 5
            break

def double_existing_coins():
    new_coins = []
    
    for coin in coins:
        if coin.active:
            coin2 = Coin(coin.lane, coin.z)
            coin2.x = coin.x + 0.8
            coin2.y = coin.y
            coin2.aabb.x = coin2.x
            coin2.aabb.y = coin2.y
            coin2.aabb.z = coin2.z
            new_coins.append(coin2)
    
    coins.extend(new_coins)

def check_magnet_powerup_collision():
    global magnet_mode_active, magnet_mode_timer, score
    
    player_aabb = get_player_aabb()
    for powerup in magnet_powerups:
        if not powerup.active:
            continue
        
        if player_aabb.intersects(powerup.aabb):
            powerup.active = False
            magnet_mode_active = True
            magnet_mode_timer = MAGNET_DURATION
            score += 5
            break

def update_magnet_attraction(delta_time):
    if not magnet_mode_active:
        return
    
    player_pos = (player_x, player_y, player_z)
    
    for coin in coins:
        if not coin.active:
            continue
        
        dx = player_pos[0] - coin.x
        dy = player_pos[1] - coin.y
        dz = player_pos[2] - coin.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if distance < MAGNET_RADIUS and distance > 0.5:
            dx /= distance
            dy /= distance
            dz /= distance
            
            coin.x += dx * MAGNET_ATTRACTION_SPEED * delta_time
            coin.y += dy * MAGNET_ATTRACTION_SPEED * delta_time
            coin.z += dz * MAGNET_ATTRACTION_SPEED * delta_time
            
            coin.aabb.x = coin.x
            coin.aabb.y = coin.y
            coin.aabb.z = coin.z
    
    if is_flying:
        for coin in aerial_coins:
            if not coin.active:
                continue
            
            dx = player_pos[0] - coin.x
            dy = player_pos[1] - coin.y
            dz = player_pos[2] - coin.z
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            if distance < MAGNET_RADIUS and distance > 0.5:
                dx /= distance
                dy /= distance
                dz /= distance
                
                coin.x += dx * MAGNET_ATTRACTION_SPEED * delta_time
                coin.y += dy * MAGNET_ATTRACTION_SPEED * delta_time
                coin.z += dz * MAGNET_ATTRACTION_SPEED * delta_time
                
                coin.aabb.x = coin.x
                coin.aabb.y = coin.y
                coin.aabb.z = coin.z

def spawn_aerial_coin():
    spawn_z_base = player_z + SPAWN_DISTANCE + 30
    if check_door_safe_zone(spawn_z_base):
        return
    
    coins_to_spawn = []
    for i in range(5):
        coin_lane = random.choice([-1, 0, 1])
        coin_z = spawn_z_base + 20 + (i * 10)
        
        if not check_door_safe_zone(coin_z):
            coin_height = random.uniform(12.5, FLIGHT_HEIGHT + 0.5)
            coins_to_spawn.append((coin_lane, coin_z, coin_height))
    
    if coins_to_spawn:
        powerup_lane = random.choice([-1, 0, 1])
        powerup_z = spawn_z_base
        
        if not check_door_safe_zone(powerup_z):
            flight_powerups.append(FlightPowerup(powerup_lane, powerup_z))
        
        for coin_lane, coin_z, coin_height in coins_to_spawn:
            aerial_coins.append(AerialCoin(coin_lane, coin_z, coin_height))

def get_current_difficulty():
    elapsed_time = time.time() - game_start_time
    
    speed_multiplier = 1.0 + (elapsed_time // 30) * 0.2
    speed_multiplier = min(speed_multiplier, 3.0)
    
    spawn_frequency = 1 + int(elapsed_time // 45)
    spawn_frequency = min(spawn_frequency, 3)
    
    current_speed = FORWARD_SPEED * speed_multiplier
    
    return current_speed, spawn_frequency

def check_door_collision():
    global current_environment, next_environment, environment_transition_active, environment_transition_timer
    
    player_aabb = get_player_aabb()
    for door in doors:
        if not door.active:
            continue
        
        if player_aabb.intersects(door.aabb):
            door.active = False
            next_environment = door.environment_type
            environment_transition_active = True
            environment_transition_timer = ENVIRONMENT_TRANSITION_TIME
            break

def update_environment(delta_time):
    global environment_transition_active, environment_transition_timer, current_environment
    global weather_intensity, weather_timer
    
    if environment_transition_active:
        environment_transition_timer -= delta_time
        if environment_transition_timer <= 0:
            current_environment = next_environment
            environment_transition_active = False
            weather_intensity = 1.0
    
    weather_timer += delta_time
    
    if current_environment in ["snow", "storm", "underwater", "night"]:
        weather_intensity = 1.0
    else:
        weather_intensity = 0.0

def draw_environment_effects():
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
    glColor3f(1.0, 1.0, 1.0)
    
    for i in range(50):
        x = (i * 7.3) % 200 - 100
        y = 20 - ((i * 11.7 + weather_timer * 20) % 50)
        z = player_z + ((i * 13.1) % 150) - 50
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glutSolidSphere(0.1, 4, 4)
        glPopMatrix()

def draw_rain_particles():
    glColor3f(0.6, 0.8, 1.0)
    
    for i in range(100):
        x = (i * 5.7) % 200 - 100
        y = 60 - ((i * 9.3 + weather_timer * 50) % 60) + 2
        z = player_z + ((i * 7.1) % 150) - 50
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 0.02, 0.02, 1.5, 4, 1)
        glPopMatrix()

def draw_bubbles():
    glColor3f(0.8, 0.9, 1.0)

    
    for i in range(20):
        x = (i * 8.7) % 100 - 50
        y = ((i * 6.1 + weather_timer * 10) % 30) + 2
        z = player_z + ((i * 12.3) % 100) - 30
        
        glPushMatrix()
        glTranslatef(x, y, z)
        size = 0.2 + (i % 3) * 0.1
        glutSolidSphere(size, 6, 6)
        glPopMatrix()
    
def draw_stars():
    glColor3f(1.0, 1.0, 0.8)
    
    for i in range(100):
        x = (i * 17.3) % 400 - 200
        y = 20 + (i * 3.7) % 20
        z = player_z + ((i * 23.1) % 300) - 100
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glutSolidSphere(0.1, 6, 6)
        glPopMatrix()

def draw_railroad_ties():
    tie_colors = {
        "snow": (0.3, 0.25, 0.2),
        "underwater": (0.2, 0.3, 0.2),
        "default": (0.4, 0.3, 0.2)
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
    
    delta_time = min(delta_time, 1.0/30.0)
    
    update(delta_time)
    glutPostRedisplay()

def main():
    global last_time
    
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"CoinQuest 3D")
    
    glClearColor(0.1, 0.2, 0.5, 1.0)
    

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)  
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    
    last_time = time.time()
    
    glutMainLoop()

if __name__ == "__main__":
    main()