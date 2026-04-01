import pygame
import math
import random
import time
from settings import *

class Projectile:
    def __init__(self, x, y, target_x, target_y, speed, color, size_mult=1.0, type="normal", is_sure_hit=False):
        self.pos = pygame.Vector2(x, y)
        if target_x is not None:
            diff = pygame.Vector2(target_x - x, target_y - y)
            self.vel = diff.normalize() * speed if diff.length() != 0 else pygame.Vector2(-1, 0) * speed
        else:
            self.vel = pygame.Vector2(speed, 0)
            
        self.color = color
        self.active = True
        self.size_mult = size_mult
        self.type = type # "normal", "blue_orb", "red_orb", "purple_orb", "dismantle", "cleave", "fuga_arrow", "world_slash"
        self.is_sure_hit = is_sure_hit # Domain Expansion bypass modifier
        self.lifetime = 180 if type not in ["blue_orb", "red_orb", "purple_orb", "fuga_arrow", "world_slash"] else 1000
        if type in ["purple_orb", "fuga_arrow"]: self.lifetime = 300

    def update(self):
        self.pos += self.vel
        if self.type not in ["normal", "dismantle", "cleave", "world_slash"]:
            self.lifetime -= 1
            if self.lifetime <= 0: self.active = False
            
        if self.pos.x < -200 or self.pos.x > WORLD_WIDTH + 200 or self.pos.y < 0 or self.pos.y > WORLD_HEIGHT:
            self.active = False

    def draw(self, screen):
        if self.type == "normal":
            angle = math.atan2(self.vel.y, self.vel.x)
            p1 = self.pos + pygame.Vector2(0, -20 * self.size_mult).rotate(math.degrees(angle))
            p2 = self.pos + pygame.Vector2(40 * self.size_mult, 0).rotate(math.degrees(angle))
            p3 = self.pos + pygame.Vector2(0, 20 * self.size_mult).rotate(math.degrees(angle))
            pygame.draw.polygon(screen, self.color, [p1, p2, p3])
            
        elif self.type in ["dismantle", "cleave", "world_slash"]:
            poly_color = WHITE if self.type == "world_slash" else self.color
            base_color = BLACK if self.type == "world_slash" else (255, 100, 100)

            if getattr(self, "is_grab_cleave", False):
                # --- CLEAVE HOLD: MULTI-SLASH FLURRY VFX ---
                num_flurry_slashes = 2 # Spawns 8 slashes every single frame
                for _ in range(num_flurry_slashes):
                    # Random center point around the victim's body
                    cx = self.pos.x + random.uniform(-40, 40)
                    cy = self.pos.y + random.uniform(-60, 60)
                    
                    # Length ranges from 120 to 180 (Averaging Sukuna's exact height of 160!)
                    length = random.uniform(120, 180)
                    angle = random.uniform(0, 360)
                    
                    # Calculate end points of the slash
                    dx = math.cos(math.radians(angle)) * (length / 2)
                    dy = math.sin(math.radians(angle)) * (length / 2)
                    
                    p1 = (int(cx - dx), int(cy - dy))
                    p2 = (int(cx + dx), int(cy + dy))
                    
                    # Draw a thick dark red base and a bright white/red core
                    pygame.draw.line(screen, (150, 0, 0), p1, p2, 8)
                    pygame.draw.line(screen, (255, 100, 100), p1, p2, 3)
                    pygame.draw.line(screen, WHITE, p1, p2, 1)
                    
                    # Spark flashes where the blade bites into the target
                    if random.random() < 0.3:
                        pygame.draw.circle(screen, WHITE, (int(cx), int(cy)), random.randint(4, 8))
                        pygame.draw.circle(screen, (255, 50, 50), (int(cx), int(cy)), random.randint(8, 15), 2)
                        
            else:
                # --- STANDARD SLASH VFX ---
                angle = math.atan2(self.vel.y, self.vel.x)
                points = []
                num_segments = 10 
                arc_radius = 50 * self.size_mult
                arc_sweep = math.radians(120) 
                
                # 1. Generate Outer Curve
                for i in range(num_segments + 1):
                    theta = (i / num_segments - 0.5) * arc_sweep
                    rel_x = math.cos(theta) * arc_radius
                    rel_y = math.sin(theta) * arc_radius
                    p = self.pos + pygame.Vector2(rel_x, rel_y).rotate(math.degrees(angle))
                    points.append(p)

                # 2. Generate Inner Curve
                for i in range(num_segments, -1, -1):
                    theta = (i / num_segments - 0.5) * arc_sweep
                    t = (i / num_segments - 0.5) * 2.0 
                    thickness_curve = 1.0 - (t * t) 
                    
                    edge_thickness = 1.0  
                    center_thickness = 6.0 
                    current_thickness = (edge_thickness + (center_thickness * thickness_curve)) * self.size_mult
                    
                    rel_x = math.cos(theta) * (arc_radius - current_thickness)
                    rel_y = math.sin(theta) * (arc_radius - current_thickness)
                    p = self.pos + pygame.Vector2(rel_x, rel_y).rotate(math.degrees(angle))
                    points.append(p)

                # --- NEW: Speed Trail / Ghost Blade ---
                # This draws a darker blade trailing slightly behind to simulate immense velocity
                if self.vel.length() > 0:
                    trail_color = (120, 20, 20) if self.type != "world_slash" else (20, 50, 60)
                    trail_offset = self.vel.normalize() * -15 * self.size_mult
                    trail_points = [pt + trail_offset for pt in points]
                    pygame.draw.polygon(screen, trail_color, trail_points)

                # 3. Draw the main crescent body and glowing edge on top
                if self.type == "world_slash":
                    # Blinding Cyan/White interior representing the cut in space itself
                    pygame.draw.polygon(screen, (220, 255, 255), points)
                    # Massive thick black outline representing the void
                    pygame.draw.polygon(screen, BLACK, points, max(1, int(2.5 * self.size_mult)))
                    # Searing white inner edge
                    pygame.draw.polygon(screen, WHITE, points, max(1, int(1.0 * self.size_mult)))
                else:
                    pygame.draw.polygon(screen, base_color, points)
                    pygame.draw.polygon(screen, poly_color, points, 1)

        elif self.type == "fuga_arrow":
            # Big Flamy Arrow Visuals
            angle = math.atan2(self.vel.y, self.vel.x)
            
            # Arrow shaft
            p1 = self.pos + pygame.Vector2(-60 * self.size_mult, -5 * self.size_mult).rotate(math.degrees(angle))
            p2 = self.pos + pygame.Vector2(20 * self.size_mult, -5 * self.size_mult).rotate(math.degrees(angle))
            p3 = self.pos + pygame.Vector2(20 * self.size_mult, 5 * self.size_mult).rotate(math.degrees(angle))
            p4 = self.pos + pygame.Vector2(-60 * self.size_mult, 5 * self.size_mult).rotate(math.degrees(angle))
            pygame.draw.polygon(screen, (255, 150, 0), [p1, p2, p3, p4])
            
            # Arrow head
            h1 = self.pos + pygame.Vector2(20 * self.size_mult, -20 * self.size_mult).rotate(math.degrees(angle))
            h2 = self.pos + pygame.Vector2(60 * self.size_mult, 0).rotate(math.degrees(angle))
            h3 = self.pos + pygame.Vector2(20 * self.size_mult, 20 * self.size_mult).rotate(math.degrees(angle))
            pygame.draw.polygon(screen, (255, 50, 0), [h1, h2, h3])
            
            # Fire aura and particles
            for _ in range(int(12 * self.size_mult)):
                fx = self.pos.x + random.randint(-int(60*self.size_mult), int(40*self.size_mult))
                fy = self.pos.y + random.randint(-int(20*self.size_mult), int(20*self.size_mult))
                pygame.draw.circle(screen, random.choice([(255, 0, 0), (255, 120, 0), (255, 200, 0)]), (int(fx), int(fy)), random.randint(4, 12))
        else:
            # --- ANIME-ACCURATE GOJO ORBS ---
            # Create a pulsating effect using time
            t = time.time() * 15
            
            # Base size calculation
            base_radius = (50 if self.type == "purple_orb" else 22) * self.size_mult
            pulse = math.sin(t) * 4 * self.size_mult
            radius = int(max(5, base_radius + pulse))
            
            cx, cy = int(self.pos.x), int(self.pos.y)

            if self.type == "blue_orb":
                # LAPSE BLUE: Magnetic Black Hole
                # Outer gravitational pull (faint blue)
                pygame.draw.circle(screen, (0, 30, 100), (cx, cy), radius + int(12 * self.size_mult))
                # Main energy body
                pygame.draw.circle(screen, BLUE, (cx, cy), radius)
                # Absolute dense black hole core
                pygame.draw.circle(screen, (0, 0, 5), (cx, cy), int(radius * 0.6)) 
                
                # Swirling space debris/energy rings
                ring_r = radius + int(15 * self.size_mult)
                for i in range(3):
                    angle = (t * 0.4) + (i * (math.pi * 2 / 3))
                    px = int(cx + math.cos(angle) * ring_r)
                    py = int(cy + math.sin(angle) * ring_r)
                    pygame.draw.circle(screen, (150, 220, 255), (px, py), max(1, int(4 * self.size_mult)))

            elif self.type == "red_orb":
                # REVERSAL RED: White-hot explosive repel
                # Outer explosive heat wave
                pygame.draw.circle(screen, (150, 0, 0), (cx, cy), radius + int(10 * self.size_mult))
                # Main crimson energy body
                pygame.draw.circle(screen, RED, (cx, cy), radius)
                # Superheated white core
                pygame.draw.circle(screen, (255, 240, 240), (cx, cy), int(radius * 0.4)) 
                
                # Violent, erratic energy spikes shooting off it
                for _ in range(5):
                    sx = int(cx + random.uniform(-1.5, 1.5) * radius)
                    sy = int(cy + random.uniform(-1.5, 1.5) * radius)
                    pygame.draw.line(screen, (255, 100, 100), (cx, cy), (sx, sy), max(1, int(3 * self.size_mult)))

            elif self.type == "purple_orb":
                # HOLLOW PURPLE: Crackling sphere of erasing imaginary mass
                # Massive destructive outer aura
                pygame.draw.circle(screen, (90, 0, 140), (cx, cy), radius + int(20 * self.size_mult))
                # Main purple void
                pygame.draw.circle(screen, PURPLE, (cx, cy), radius)
                # Deep, dark inner void
                pygame.draw.circle(screen, (20, 0, 30), (cx, cy), int(radius * 0.75)) 
                # Tiny, blinding singularity at the exact center
                pygame.draw.circle(screen, WHITE, (cx, cy), int(radius * 0.15)) 
                
                # Intense, erratic plasma lightning tearing around the sphere
                for _ in range(8):
                    start_angle = random.uniform(0, math.pi * 2)
                    end_angle = start_angle + random.uniform(-0.8, 0.8)
                    r1 = radius * random.uniform(0.9, 1.4)
                    r2 = radius * random.uniform(0.9, 1.4)
                    
                    p1 = (int(cx + math.cos(start_angle) * r1), int(cy + math.sin(start_angle) * r1))
                    p2 = (int(cx + math.cos(end_angle) * r2), int(cy + math.sin(end_angle) * r2))
                    
                    # Draw lightning arcs
                    pygame.draw.line(screen, (220, 180, 255), p1, p2, max(2, int(4 * self.size_mult)))
                    # Bright flashes where the lightning arcs snap
                    if random.random() > 0.5:
                        pygame.draw.circle(screen, WHITE, p1, max(1, int(3 * self.size_mult)))