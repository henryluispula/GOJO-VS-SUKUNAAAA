import pygame
import math
import random
import time

# --- Configuration ---
WIDTH, HEIGHT = 1280, 720
WORLD_WIDTH = 4480  # 30% smaller than 6400
WORLD_HEIGHT = 2520 # 30% smaller than 3600
FPS = 60
GRAVITY = 2.8 # Increased for heavy, realistic gravity

# Colors
WHITE, BLACK = (255, 255, 255), (10, 10, 15)
BLUE, RED, PURPLE = (20, 100, 255), (220, 20, 20), (160, 32, 240)
SKIN, CLOTHES = (255, 210, 190), (15, 15, 25)
MAHO_COLOR = (235, 235, 210)
BLOOD, HEAL_GREEN = (150, 0, 0), (50, 255, 50)
INF_COLOR = (100, 200, 255)

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

class Fighter:
    def __init__(self, x, y, name, color=CLOTHES):
        self.rect = pygame.Rect(x, y, 70, 160)
        self.name = name
        self.max_hp = 500 if name == "Sukuna" else (480 if name == "Mahoraga" else 200)
        self.hp = self.max_hp
        self.prev_hp = self.hp # Track for blood effects
        # Start the fight with appropriate max cursed energy levels
        self.max_energy = 3000 if name == "Sukuna" else (2100 if name == "Gojo" else 2800)
        self.energy = self.max_energy
        self.max_infinity = 1000 if name == "Gojo" else 0 
        self.infinity = self.max_infinity
        self.max_tech_hits = 1000 # INCREASED: Both Fuga and Hollow Purple now require 1000 points!
        self.max_sd_hits = 300 if name == "Sukuna" else 38 # NEW: Dynamic Simple Domain HP!
        
        # --- OPTIMIZATION: Surface Caching ---
        self.inf_surf = pygame.Surface((220, 320), pygame.SRCALPHA)
        self.sd_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
        self.amp_surf = pygame.Surface((150, 250), pygame.SRCALPHA)
        
        # --- NEW: DODGE METER LOGIC ---
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.stamina_exhausted = False
        self.trail_points = [] # For sleek dodge streak lines
        
        self.is_dodging = False
        self.dodge_timer = 0
        self.dodge_cd = 0 
        self.vel_y = 0
        self.on_ground = True
        self.direction = 1
        self.color = color
        self.attack_cooldown = 0
        self.dismantle_cd = 0
        self.cleave_cd = 0
        self.blue_cd = 0
        self.red_cd = 0
        self.purple_cd = 0
        self.fuga_cd = 0
        self.amp_cd = 0 
        self.amp_duration = 0 
        self.rct_timer = 0
        self.adaptation = {"blue": 1.0, "red": 1.0, "purple": 1.0, "punch": 1.0, "infinity": 0.0, "void": 1.0}
        self.adaptation_points = {"blue": 0, "red": 0, "purple": 0, "punch": 0, "infinity": 0, "void": 0}
        self.adapting_to = None # Current phenomenon being adapted
        self.wheel_rotation = 0
        self.last_turn_count = 0
        self.is_split = False
        self.using_blue = False 
        self.purple_charge = 0 
        self.fuga_charge = 0
        self.world_slash_charge = 0 # NEW: World Slash charge
        self.world_slash_cd = 0 # NEW: 30 sec cooldown
        self.domain_charge = 0 # NEW: Domain Expansion cast charge
        self.tech_hits = 0 
        self.slash_count = 0
        self.slash_delay = 0
        self.slash_type = "dismantle" 
        self.black_flash_timer = 0 
        self.potential_timer = 0 
        self.punch_timer = 0 
        self.punch_count = 0 # Track alternating arms
        self.world_slash_unlocked = False # LORE: Sukuna's ultimate counter to Infinity
        self.grab_timer = 0
        self.grab_cd = 0

        # --- NEW: DEV OPTIONS ---
        self.dev_immortal = False
        self.dev_inf_ce = False
        self.dev_inf_infinity = False
        
        # --- NEW: Domain Mechanics ---
        self.domain_active = False
        self.domain_timer = 0
        self.domain_cd = 0
        self.is_paralyzed = False
        self.domain_uses = 0
        self.technique_burnout = 0
        self.simple_domain_active = False # Negates domain sure-hit effects!
        self.sd_hits = 0 # NEW: Tracks hits for Simple Domain crumbling
        self.sd_broken_timer = 0 # NEW: Cooldown when Simple Domain crumbles
        self.prev_energy = self.energy
        self.ce_exhausted = False # CE Exhaustion/Burnout tracking

    @property
    def cost_mult(self):
        # 80% discount to all CE costs if they hit a black flash!
        return 0.2 if self.potential_timer > 0 else 1.0

    def end_domain(self):
        # 1. ADD THIS CHECK: If it's already off, don't count it again!
        if not self.domain_active:
            return

        # 2. Proceed with ending
        self.domain_active = False 
        self.domain_timer = 0
        self.domain_uses += 1
        
        # 5 times Domain Expansion 5 sec cooldowns, after 5 they get burnt out and heavy cooldowns apply
        if self.domain_uses <= 5:
            self.domain_cd = 300 # 5 second cooldown (300 frames)
            self.technique_burnout = 0
        else:
            self.domain_cd = 3000
            self.technique_burnout = 1200
            if self.name == "Gojo":
                self.infinity = 0                                         

    def jump(self):
        if self.on_ground and not self.is_paralyzed:
            # INCREASED JUMP HEIGHT: Stronger negative velocity shoots them higher!
            self.vel_y = -55 if self.name == "Mahoraga" else -45
            self.on_ground = False

    def dodge(self):
        if self.dodge_timer == 0 and not self.is_paralyzed and self.stamina >= 20 and not self.stamina_exhausted:
            self.is_dodging = True
            # REFINEMENT: Blue-infused dash timing for Gojo (faster execution & Enhanced i-frames)
            self.dodge_timer = 25 if self.name == "Gojo" else 20
            self.stamina -= 20

    def update_physics(self):
        if self.is_split: return

        # --- NEW: APPLY DEV OPTIONS (GOJO ONLY) ---
        if self.name == "Gojo":
            if getattr(self, "dev_immortal", False):
                self.hp = self.max_hp
            if getattr(self, "dev_inf_ce", False):
                self.energy = self.max_energy # Dynamically locks CE to maximum
                self.ce_exhausted = False
                
            # --- FIXED: FORCE INFINITY TO 0 WHEN TOGGLED OFF ---
            if getattr(self, "dev_disable_infinity", False):
                self.infinity = 0 # Strips his barrier completely!
        
        # --- NEW: Domain Cooldowns & Burnouts ---
        self.domain_cd = max(0, self.domain_cd - 1)
        self.technique_burnout = max(0, self.technique_burnout - 1)
        self.sd_broken_timer = max(0, self.sd_broken_timer - 1)

        if self.domain_timer > 0:
            self.domain_timer -= 1
            if self.domain_timer <= 0:
                self.end_domain()
                
        if self.name == "Gojo" and self.technique_burnout > 0 and self.domain_uses >= 5:
            self.infinity = 0

        # NEW: Freeze movement if grabbing or paralyzed
        if self.is_paralyzed or self.grab_timer > 0:
            self.is_dodging = False
            self.dodge_timer = 0
            self.vel_y = 0
            if self.grab_timer > 0: self.grab_timer -= 1
            # FIX: Removed the 'return' here so cooldowns and energy keep running!
        else:
            self.vel_y += GRAVITY
            self.rect.y += self.vel_y
            if self.rect.bottom >= WORLD_HEIGHT - 100:
                self.rect.bottom = WORLD_HEIGHT - 100
                self.vel_y = 0
                self.on_ground = True
            
            if self.rect.left < 10: self.rect.left = 10
            if self.rect.right > WORLD_WIDTH - 10: self.rect.right = WORLD_WIDTH - 10

            if self.dodge_timer > 0:
                self.dodge_timer -= 1
                # REFINEMENT: Gojo teleports (72). Sukuna and Mahoraga share the same heavy burst speed (45).
                dash_speed = 72 if self.name == "Gojo" else 45
                self.rect.x += self.direction * dash_speed
            else: self.is_dodging = False
            
        # === THESE NOW RUN EVEN WHEN GRABBED ===
        
        # Energy Regen
        base_regen = 25.0 if self.name == "Gojo" else 0.8 if self.name == "Mahoraga" else 1.0 # SIX EYES REGEN
        regen_mult = 1.2 if self.potential_timer > 0 else 1.0
        
        # --- CE EXHAUSTION LOGIC ---
        if self.energy <= 0.5:
            self.ce_exhausted = True
            if self.name == "Gojo":
                self.infinity = 0
            
        if self.ce_exhausted:
            if self.name == "Sukuna":
                regen_mult *= 0.8 # Less severe exhaustion for Sukuna
                recovery_thresh = 80 # Recovers faster
            else:
                regen_mult *= 0.4 # 10x slower regen when completely depleted!
                recovery_thresh = 420 if self.name == "Gojo" else 30
                
            if self.energy >= recovery_thresh:
                self.ce_exhausted = False
        
        # Cleaned up the old useless max_energy variable here!
        self.energy = min(self.max_energy, self.energy + base_regen * regen_mult)
        
        # --- STAMINA EXHAUSTION LOGIC (Dodge Meter) ---
        stam_regen = 0.8 if self.name == "Gojo" else 0.6
        if self.stamina <= 0.5:
            self.stamina_exhausted = True
            
        if self.stamina_exhausted:
            stam_regen *= 0.1 
            if self.stamina >= 30:
                self.stamina_exhausted = False
                
        self.stamina = min(self.max_stamina, self.stamina + stam_regen)
        
        # Sleek Dodge Trail Lines Update
        if self.is_dodging:
            self.trail_points.append([self.rect.centerx, self.rect.centery, 10]) # x, y, lifetime
        
        # OPTIMIZATION: List Comprehension for safe O(N) removal
        active_trails = []
        for pt in self.trail_points:
            pt[2] -= 1
            if pt[2] > 0:
                active_trails.append(pt)
        self.trail_points = active_trails
        
        # --- FIXED: Gojo Infinity regen (Now respects the Dev Toggle!) ---
        if self.name == "Gojo" and self.infinity < self.max_infinity and self.technique_burnout == 0 and not getattr(self, "dev_disable_infinity", False):
            cost = 0.1 * self.cost_mult
            if self.energy >= cost:
                self.infinity = min(self.max_infinity, self.infinity + 3.5) 
                self.energy -= cost

        # Sukuna Constant Auto-Heal & UV Survival Binding Vow
        if self.name == "Sukuna" and self.hp > 0 and self.hp < self.max_hp and not self.ce_exhausted:
            heal_cost = 0.3 * self.cost_mult
            
            # --- NEW: UNLIMITED VOID SURVIVAL VOW ---
            # If paralyzed (caught inside UV), he forces his brain to use RCT to survive!
            if self.is_paralyzed:
                heal_cost *= 4.0 # Massive CE tax for forcing RCT through a fried brain
                self.domain_cd = 600 # 10 seconds penalty to Domain Expansion
                self.mahoraga_lockout = 1800 # 30 seconds penalty to Mahoraga Summoning
                
                # Dark visual flare to show he's tanking it through pure willpower
                if random.random() < 0.1:
                    self.black_flash_timer = 2 
            
            if self.energy >= heal_cost:
                self.hp = min(self.max_hp, self.hp + random.uniform(2.5, 3.5))
                self.energy -= heal_cost
                self.rct_timer = 5
        # Mahoraga RCT Buff
        if self.name == "Mahoraga" and self.rct_timer > 0:
            self.hp = min(self.max_hp, self.hp + 1.2) 

        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        self.dismantle_cd = max(0, self.dismantle_cd - 1)
        self.mahoraga_lockout = max(0, getattr(self, "mahoraga_lockout", 0) - 1) # NEW: Vow Penalty Tracker
        self.cleave_cd = max(0, self.cleave_cd - 1)
        self.grab_cd = max(0, self.grab_cd - 1)
        self.blue_cd = max(0, self.blue_cd - 1)
        self.red_cd = max(0, self.red_cd - 1)
        self.purple_cd = max(0, self.purple_cd - 1)
        self.fuga_cd = max(0, self.fuga_cd - 1)
        self.world_slash_cd = max(0, self.world_slash_cd - 1)
        self.dodge_cd = max(0, self.dodge_cd - 1)
        self.black_flash_timer = max(0, self.black_flash_timer - 1)
        self.potential_timer = max(0, self.potential_timer - 1)
        self.punch_timer = max(0, self.punch_timer - 1)
        
        if self.amp_duration > 0:
            self.amp_duration -= 1
            if self.amp_duration <= 0:
                self.amp_cd = 0
        else:
            self.amp_cd = max(0, self.amp_cd - 1)

    def trigger_adaptation(self, phenomenon, intensity=1.0):
        if self.name != "Mahoraga": return
        
        # One phenomena at a time
        if self.adapting_to != phenomenon:
            self.adapting_to = phenomenon
            
        # Accelerate based on intensity (hits)
        self.adaptation_points[phenomenon] += intensity

    def draw_detailed(self, surface, is_punching=False, effect=None, is_amp=False):
        # Draw sleek stylized dash streak lines
        for pt in self.trail_points:
            streak_len = int((pt[2] / 10.0) * 80)
            if streak_len > 0:
                pygame.draw.line(surface, self.color, (pt[0], pt[1]), (pt[0] - self.direction * streak_len, pt[1]), 6)
                pygame.draw.line(surface, WHITE, (pt[0], pt[1] - 20), (pt[0] - self.direction * (streak_len - 15), pt[1] - 20), 2)
                pygame.draw.line(surface, WHITE, (pt[0], pt[1] + 20), (pt[0] - self.direction * (streak_len - 15), pt[1] + 20), 2)
                
        x, y, mid_x = self.rect.centerx - 35, self.rect.y, self.rect.centerx

        # Ensure we only draw Sukuna's grab arm if HE is the one attacking (not getting beaten up!)
        if self.name == "Sukuna" and self.grab_timer > 0 and getattr(self, "grab_type", "") != "gojo_beatdown":
            # Draw a thick, reinforced arm reaching out
            arm_color = (100, 0, 0) # Darkened for emphasis
            grab_x = mid_x + (60 * self.direction)
            pygame.draw.line(surface, SKIN, (mid_x, y + 50), (grab_x, y + 60), 18)
            # Add sparks/cinders at the palm
            for _ in range(5):
                pygame.draw.circle(surface, RED, (int(grab_x), int(y + 60 + random.randint(-10, 10))), 4)
                
        if self.is_split and self.name == "Gojo":
            self.draw_death(surface)
            return

        t = time.time()
        
        # Black Flash visual effect
        if self.black_flash_timer > 0:
            for _ in range(15):
                rx, ry = random.randint(x-40, x+110), random.randint(y-40, y+200)
                pygame.draw.line(surface, BLACK, (rx, ry), (rx+random.randint(-40,40), ry+random.randint(-40,40)), 6)
                pygame.draw.line(surface, (255, 0, 0), (rx, ry), (rx+random.randint(-20,20), ry+random.randint(-20,20)), 3)

        # Domain Expansion Cast Animation
        if getattr(self, "domain_charge", 0) > 0:
            ct = (60 - self.domain_charge) / 60.0
            burst = int(180 * ct)
            dom_color = (200, 200, 255) if self.name == "Gojo" else (255, 50, 50)
            pygame.draw.circle(surface, dom_color, (mid_x, y + 40), burst, max(1, int(15 * (1 - ct))))
            if ct > 0.8:
                pygame.draw.circle(surface, WHITE, (mid_x, y + 40), int(burst * 1.2), 3)

        # Draw Simple Domain barrier behind character visuals
        if self.simple_domain_active:
            self.sd_surf.fill((0,0,0,0)) # OPTIMIZATION: Clear and reuse Surface
            pygame.draw.circle(self.sd_surf, (200, 200, 255, 40), (90, 90), 90)
            pygame.draw.circle(self.sd_surf, (255, 255, 255, 120), (90, 90), 90, 3)
            # A slight pulse to show it actively draining
            pulse = (math.sin(t * 10) + 1) * 0.5
            pygame.draw.circle(self.sd_surf, (200, 200, 255, int(100 * pulse)), (90, 90), 85, 1)
            surface.blit(self.sd_surf, (mid_x - 90, y + 80 - 90))

        if self.name == "Gojo":
            # --- NEW: Check if Infinity is actually capable of being active right now ---
            has_active_infinity = self.infinity > 0 and self.technique_burnout == 0 and not getattr(self, "dev_disable_infinity", False)
            
            is_hit = self.hp < self.prev_hp or self.energy < self.prev_energy or self.grab_timer > 0
            is_bypassed = (self.hp < self.prev_hp and self.energy >= self.prev_energy)

            # Hide Infinity Aura during Domain Amplification holds!
            if self.grab_timer > 0 and getattr(self, "grab_type", "") == "amp_punch":
                is_bypassed = True # Force bypass state so the barrier doesn't draw

            # --- FIXED: Only draw the aura if he actually HAS Infinity up, got hit/grabbed, and it wasn't bypassed ---
            if has_active_infinity and is_hit and not is_bypassed:
                alpha_base = 180 
                pulse = math.sin(t * 20) * 15 
                
                self.inf_surf.fill((0,0,0,0)) # OPTIMIZATION: Clear and reuse Surface
                for i in range(2): 
                    layer_alpha = int(alpha_base / (i + 1))
                    thickness = int(pulse + 10 + (i * 5))
                    
                    # EXTENDED POLYGON: 
                    # Changed the last two points from 160 to 240 to reach the feet
                    poly = [(60, 70), (140, 70), (135, 240), (65, 240)]
                    
                    pygame.draw.polygon(self.inf_surf, (100, 200, 255, layer_alpha), poly, thickness)
                    pygame.draw.circle(self.inf_surf, (150, 230, 255, layer_alpha), (110, 45), 35 + (thickness//2), thickness)
                
                # Blit it slightly higher to account for the longer surface
                surface.blit(self.inf_surf, (x - 75, y - 55))

            if self.purple_charge > 0:
                ct = (120 - self.purple_charge) / 120.0
                # Orbs spiral inward on a shrinking radius
                spiral_r = 85 * (1.0 - ct)
                bx = mid_x + math.cos(t * 7 + ct * 22) * spiral_r
                by = y + 40 + math.sin(t * 7 + ct * 22) * spiral_r * 0.55
                rx = mid_x + math.cos(t * 7 + ct * 22 + math.pi) * spiral_r
                ry = y + 40 + math.sin(t * 7 + ct * 22 + math.pi) * spiral_r * 0.55

                orb_r = int(18 + 22 * ct)
                pygame.draw.circle(surface, (100, 180, 255), (int(bx), int(by)), orb_r + 6)
                pygame.draw.circle(surface, BLUE, (int(bx), int(by)), orb_r)
                pygame.draw.circle(surface, (255, 80, 80), (int(rx), int(ry)), orb_r + 6)
                pygame.draw.circle(surface, RED, (int(rx), int(ry)), orb_r)

                # Lightning arcs between orbs as they converge
                if ct > 0.25:
                    for _ in range(int(6 * ct)):
                        lx = int(bx + random.randint(-12, 12))
                        ly = int(by + random.randint(-12, 12))
                        ex = int(rx + random.randint(-12, 12))
                        ey = int(ry + random.randint(-12, 12))
                        pygame.draw.line(surface, (220, 120, 255), (lx, ly), (ex, ey), 2)
                        pygame.draw.line(surface, WHITE, (lx, ly), (ex, ey), 1)

                # Purple shockwave rings growing outward
                if ct > 0.45:
                    for ri in range(4):
                        ring_r = int((30 + ri * 20) * ct)
                        alpha = max(1, 4 - ri)
                        pygame.draw.circle(surface, PURPLE, (mid_x, y + 40), ring_r, alpha)

                # Final convergence burst — screaming purple explosion
                if ct > 0.80:
                    burst = int(140 * ((ct - 0.80) / 0.20))
                    pygame.draw.circle(surface, PURPLE, (mid_x, y + 40), burst, 8)
                    pygame.draw.circle(surface, (220, 180, 255), (mid_x, y + 40), burst // 2, 4)
                    pygame.draw.circle(surface, WHITE, (mid_x, y + 40), burst // 4, 3)
                    for _ in range(30):
                        fpx = mid_x + random.randint(-burst, burst)
                        fpy = y + 40 + random.randint(-burst, burst)
                        pygame.draw.circle(surface, PURPLE, (int(fpx), int(fpy)), random.randint(3, 12))
                    for _ in range(12):
                        fpx = mid_x + random.randint(-burst // 2, burst // 2)
                        fpy = y + 40 + random.randint(-burst // 2, burst // 2)
                        pygame.draw.circle(surface, WHITE, (int(fpx), int(fpy)), random.randint(2, 6))

        if self.name == "Sukuna" and getattr(self, "world_slash_charge", 0) > 0:
            ct = (120 - self.world_slash_charge) / 120.0
            
            # Violent, pulsing dark focal point
            pull_r = int(250 * (1.0 - ct))
            core_size = int(60 * ct + math.sin(t * 30) * 10)
            pygame.draw.circle(surface, (5, 5, 10), (mid_x, y + 60), core_size)
            pygame.draw.circle(surface, (100, 255, 255), (mid_x, y + 60), core_size + 5, max(1, int(15 * ct)))
            
            # Jagged, erratic reality tears pulling into his hands
            for _ in range(int(20 * ct) + 5):
                ang = random.uniform(0, math.pi * 2)
                p1_x = mid_x + math.cos(ang) * pull_r
                p1_y = y + 60 + math.sin(ang) * pull_r
                p2_x = mid_x + math.cos(ang + random.uniform(-0.2, 0.2)) * (pull_r * 0.6)
                p2_y = y + 60 + math.sin(ang + random.uniform(-0.2, 0.2)) * (pull_r * 0.6)
                
                # Tearing fabric of space effect
                pygame.draw.line(surface, BLACK, (p1_x, p1_y), (p2_x, p2_y), max(2, int(8 * ct)))
                pygame.draw.line(surface, WHITE, (p1_x, p1_y), (p2_x, p2_y), max(1, int(3 * ct)))
                
            # Giant inverted target grid mapping out the world
            if ct > 0.4:
                grid_alpha = int(255 * ((ct - 0.4) / 0.6))
                grid_len = int(300 * ct)
                pygame.draw.line(surface, (255, 255, 255, grid_alpha), (mid_x - grid_len, y + 60), (mid_x + grid_len, y + 60), 1)
                pygame.draw.line(surface, (255, 255, 255, grid_alpha), (mid_x, y + 60 - grid_len), (mid_x, y + 60 + grid_len), 1)

            # Massive screen-tearing cross building up
            if ct > 0.6:
                slash_len = int(250 * ((ct - 0.6) / 0.4))
                pygame.draw.line(surface, (200, 255, 255), (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 15)
                pygame.draw.line(surface, BLACK, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 8)
                pygame.draw.line(surface, WHITE, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 2)
                
            # Final blinding negative-color flash right before firing
            if ct > 0.95:
                pygame.draw.circle(surface, BLACK, (mid_x, y + 60), 800)
                pygame.draw.circle(surface, WHITE, (mid_x, y + 60), int(1000 * ((ct - 0.95)/0.05)), 20)

        if self.name == "Sukuna" and self.fuga_charge > 0:
            ct = (120 - self.fuga_charge) / 120.0

            # Rising fire pillar — grows taller and wider over time
            pillar_h = int(220 * ct)
            pillar_w = int(22 + 65 * ct)
            pygame.draw.ellipse(surface, (255, 55, 0),
                (mid_x - pillar_w // 2, y + 40 - pillar_h // 2, pillar_w, pillar_h),
                max(1, int(9 * ct)))
            pygame.draw.ellipse(surface, (255, 180, 0),
                (mid_x - pillar_w // 4, y + 40 - pillar_h // 4, pillar_w // 2, pillar_h // 2),
                max(1, int(5 * ct)))

            # Core pulsing ring
            pulse_r = int(50 * ct + 6 * math.sin(t * 18))
            pygame.draw.circle(surface, (255, 100, 0), (mid_x, y + 40), pulse_r, max(1, int(14 * ct)))
            pygame.draw.circle(surface, (255, 220, 0), (mid_x, y + 40), max(1, pulse_r // 2), max(1, int(6 * ct)))

            # Cascading fire particles — density scales with ct
            n_parts = int(8 + 30 * ct)
            for _ in range(n_parts):
                px = mid_x + random.randint(-int(90 * ct), int(90 * ct))
                py = y + 40 + random.randint(-int(90 * ct), int(90 * ct))
                size = random.randint(3, int(7 + 15 * ct))
                pygame.draw.circle(surface, random.choice([(255, 0, 0), (255, 110, 0), (255, 200, 0), (255, 255, 50)]),
                    (int(px), int(py)), size)

            # Expanding shockwave rings from torso
            if ct > 0.35:
                for ri in range(4):
                    ring_r = int((35 + ri * 28) * ct)
                    pygame.draw.circle(surface, (255, 80, 0), (mid_x, y + 40), ring_r, max(1, 4 - ri))

            # Final detonation — blinding fire burst
            if ct > 0.78:
                burst = int(160 * ((ct - 0.78) / 0.22))
                pygame.draw.circle(surface, (255, 140, 0), (mid_x, y + 40), burst, 8)
                pygame.draw.circle(surface, (255, 255, 100), (mid_x, y + 40), burst // 2, 5)
                pygame.draw.circle(surface, WHITE, (mid_x, y + 40), burst // 4, 3)
                for _ in range(35):
                    bpx = mid_x + random.randint(-burst, burst)
                    bpy = y + 40 + random.randint(-burst, burst)
                    pygame.draw.circle(surface, (255, random.randint(80, 255), 0),
                        (int(bpx), int(bpy)), random.randint(4, 16))
                for _ in range(10):
                    bpx = mid_x + random.randint(-burst // 2, burst // 2)
                    bpy = y + 40 + random.randint(-burst // 2, burst // 2)
                    pygame.draw.circle(surface, WHITE, (int(bpx), int(bpy)), random.randint(2, 7))
        if is_amp:
            # Domain Amplification: Fluid, shimmering water-like energy cloak
            for i in range(3):
                # Flowing energy layers moving up the body
                amp_y = y + 160 - ((t * 120 + i * 50) % 160)
                pulse_x = math.sin(t * 8 + i) * 8
                pygame.draw.ellipse(surface, (100, 180, 255), (mid_x - 40 + pulse_x, amp_y - 15, 80, 30), 2)
            
            # Outer shimmering cloak outline
            glow_rect = self.rect.inflate(15 + math.sin(t * 15) * 5, 15 + math.cos(t * 15) * 5)
            # --- CHANGED: Deleted the hard line border here! ---
            
            # Very faint inner fill to give it volume
            self.amp_surf.fill((0,0,0,0)) # OPTIMIZATION: Reuse surface
            temp_rect = pygame.Rect(0, 0, glow_rect.width, glow_rect.height)
            pygame.draw.rect(self.amp_surf, (100, 150, 255, 40), temp_rect, border_radius=15)
            surface.blit(self.amp_surf, glow_rect.topleft)

        # Draw Dharma Wheel for Mahoraga or Sukuna summoning
        if self.name == "Mahoraga" or (self.name == "Sukuna" and effect == "summoning"):
            wheel_center = (mid_x, y - 65)
            wheel_color = (190, 170, 50)
            
            # Spin wheel based on current adaptation progress
            if self.adapting_to:
                pts = self.adaptation_points[self.adapting_to]
                # Each 250 points is a 'turn'
                turn_progress = (pts % 250) / 250.0
                total_turns = int(pts // 250)
                if total_turns > self.last_turn_count:
                    self.last_turn_count = total_turns
                    # Visual 'ding' for wheel turn
                    pygame.draw.circle(surface, WHITE, wheel_center, 60, 2)
                
                self.wheel_rotation = (total_turns * 45) + (turn_progress * 45)
            
            angle_offset = math.radians(self.wheel_rotation)
            
            pygame.draw.circle(surface, wheel_color, wheel_center, 45, 6)
            pygame.draw.circle(surface, wheel_color, wheel_center, 8)
            for i in range(8):
                rad = math.radians(i * 45) + angle_offset
                spoke_end = (wheel_center[0] + math.cos(rad) * 45, wheel_center[1] + math.sin(rad) * 45)
                pygame.draw.line(surface, wheel_color, wheel_center, spoke_end, 4)
                pygame.draw.circle(surface, wheel_color, spoke_end, 6)

        # Character Rendering
        leg_off = math.sin(t * 12) * 15 if not self.on_ground and not self.is_paralyzed else 0
        thickness = 15 if self.name == "Mahoraga" else 12
        
        # Legs
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (mid_x - 10, y + 90), (mid_x - 15 - leg_off, y + 160), thickness)
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (mid_x + 10, y + 90), (mid_x + 15 + leg_off, y + 160), thickness)
        
        # Torso and Wounds
        body_rect = [(x+5, y+20), (x+65, y+20), (x+55, y+95), (x+15, y+95)]
        if self.name == "Mahoraga": body_rect = [(x-5, y+10), (x+75, y+10), (x+65, y+100), (x+5, y+100)]
        pygame.draw.polygon(surface, self.color, body_rect)
        
        # Dynamic bloody wounds/splatters mapped directly to character's HP
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.7:
            pygame.draw.circle(surface, BLOOD, (mid_x - 10, y + 40), 8)
        if hp_ratio < 0.4:
            pygame.draw.circle(surface, BLOOD, (mid_x + 15, y + 60), 12)
            pygame.draw.line(surface, BLOOD, (mid_x, y + 30), (mid_x - 15, y + 70), 4)
        if hp_ratio < 0.2:
            pygame.draw.circle(surface, BLOOD, (mid_x - 5, y + 80), 15)
            pygame.draw.line(surface, BLOOD, (mid_x + 10, y + 80), (mid_x + 20, y + 90), 5)
        
        # --- Alternating Punching Animation ---
        l_shoulder = (x + 10, y + 35)
        r_shoulder = (x + 60, y + 35)
        l_hand = (x + 5, y + 85)
        r_hand = (x + 65, y + 85)
        
        if self.punch_timer > 0 and not self.is_paralyzed:
            phase = (20 - self.punch_timer) / 20.0
            arm_ext = 60 * math.sin(phase * math.pi)
            
            # Use punch_count to alternate arms
            if self.punch_count % 2 == 1: # Left arm punches
                l_hand = (x + 5 - arm_ext * self.direction, y + 65 - (arm_ext * 0.2))
            else: # Right arm punches
                r_hand = (x + 65 + arm_ext * self.direction, y + 65 - (arm_ext * 0.2))
        
        pygame.draw.line(surface, SKIN, l_shoulder, l_hand, thickness - 2)
        pygame.draw.line(surface, SKIN, r_shoulder, r_hand, thickness - 2)
        
        # Head
        pygame.draw.circle(surface, SKIN, (mid_x, y), 26 + (4 if self.name == "Mahoraga" else 0))
        
        if self.name == "Sukuna":
            pygame.draw.line(surface, BLACK, (mid_x - 10, y + 5), (mid_x - 5, y + 15), 2)
            pygame.draw.line(surface, BLACK, (mid_x + 10, y + 5), (mid_x + 5, y + 15), 2)
            pygame.draw.circle(surface, BLACK, (mid_x, y + 18), 3) 
            
        if self.name == "Mahoraga":
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x - 20, y - 10), (mid_x - 50, y - 40), (mid_x - 20, y + 5)])
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x + 20, y - 10), (mid_x + 50, y - 40), (mid_x + 20, y + 5)])

        if self.rct_timer > 0:
            # Three distinct flowing streams: Left, Center, Right
            offsets = [-35, 0, 35] 
            for j, x_off in enumerate(offsets):
                for i in range(5): # 4 sparks per stream
                    # Smooth sine wave + upward modulo flow
                    sx = mid_x + x_off + math.sin(t * 5 + i + j) * 15
                    sy = (y + 160) - ((t * 80 + i * 40 + j * 20) % 150)
                    
                    r_color = [(150, 255, 150), (255, 255, 200), (100, 255, 150)][(i+j) % 3]
                    pygame.draw.circle(surface, r_color, (int(sx), int(sy)), 3)
            
            self.rct_timer -= 1

        # Hair
        h_color = WHITE if self.name == "Gojo" else (20, 20, 25) if self.name == "Sukuna" else (160, 160, 170)
        num_spikes = 7 if self.name == "Mahoraga" else 5
        for i in range(num_spikes): 
            h_x = mid_x - 25 + i * (10 if self.name != "Mahoraga" else 8)
            pygame.draw.polygon(surface, h_color, [(h_x, y-5), (h_x+5, y-45 if self.name != "Mahoraga" else y-30), (h_x+10, y-5)])

    def draw_death(self, surface):
        mx, my = self.rect.centerx, self.rect.centery
        pygame.draw.line(surface, CLOTHES, (mx-10, my+10), (mx-20, my+80), 14)
        pygame.draw.line(surface, CLOTHES, (mx+10, my+10), (mx+20, my+80), 14)
        pygame.draw.rect(surface, BLOOD, (mx-25, my-10, 50, 15))
        pygame.draw.circle(surface, SKIN, (mx + 90, my + 60), 26)
        pygame.draw.rect(surface, CLOTHES, (mx + 70, my + 70, 80, 45))

class Game:
    def __init__(self):
        pygame.init()
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.world_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT)).convert()
        self.cam_width = float(WIDTH)
        self.cam_height = float(HEIGHT)
        self.clock = pygame.time.Clock()
        self.prev_gojo_burnout = 0
        self.prev_sukuna_burnout = 0
        self.prev_world_slash_cd = 0
        self.gojo = Fighter(200, WORLD_HEIGHT - 300, "Gojo")
        
        # --- OPTIMIZATION: Fonts and Text Caching ---
        self.font = pygame.font.SysFont("Impact", 26)
        self.mini_font = pygame.font.SysFont("Impact", 16)
        self.text_cache = {}
        
        # New Tracking for Announcements
        self.prev_adaptations = {"blue": 1.0, "red": 1.0, "purple": 1.0, "punch": 1.0, "infinity": 0.0, "void": 1.0}
        self.maho_announcements = []        
        
        # --- OPTIMIZATION: Pre-rendered Domain Assets ---
        self.uv_stars = [(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT), random.randint(1, 4)) for _ in range(400)]
        self.star_layers = []
        for _ in range(3):
            star_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
            for sx, sy, r in self.uv_stars:
                pygame.draw.circle(star_surf, (255, 255, 255, random.randint(100, 255)), (sx, sy), r)
            self.star_layers.append(star_surf)
            
        self.cached_ms_bg = None
        self.cached_ms_shrunk = False
        self.cached_uv_bg = None
        self.cached_uv_bg_shrunk = None
        self.cached_uv_shrunk = False
        
        self.shared_flash_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
        self.shared_world_overlay = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
        self.shared_ui_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.shared_ui_overlay.fill((0, 0, 0, 200))
        
        # --- MEMORY ALLOCATION OPTIMIZATION ---
        # Moving all per-frame surface creations here so the CPU's Garbage Collector doesn't panic.
        self.micro_font = pygame.font.SysFont("Impact", 13)
        self.render_surf = pygame.Surface((WIDTH, HEIGHT)).convert()
        
        self.gojo_hud_bg = pygame.Surface((340, 210), pygame.SRCALPHA)
        self.gojo_hud_bg.fill((0, 0, 15, 180))
        pygame.draw.rect(self.gojo_hud_bg, (100, 150, 255), (0, 0, 340, 210), 2)
        
        self.sukuna_hud_bg_normal = pygame.Surface((340, 210), pygame.SRCALPHA)
        self.sukuna_hud_bg_normal.fill((20, 0, 0, 180))
        pygame.draw.rect(self.sukuna_hud_bg_normal, (255, 100, 100), (0, 0, 340, 210), 2)
        
        self.sukuna_hud_bg_maho = pygame.Surface((340, 290), pygame.SRCALPHA)
        self.sukuna_hud_bg_maho.fill((20, 0, 0, 180))
        pygame.draw.rect(self.sukuna_hud_bg_maho, (255, 100, 100), (0, 0, 340, 290), 2)
        
        self.clash_msg_bg = pygame.Surface((800, 100), pygame.SRCALPHA)
        
        # Sukuna initialized with WHITE to represent his Heian/Meguna robe aesthetic!
        self.sukuna = Fighter(1000, WORLD_HEIGHT - 300, "Sukuna", color=WHITE)
        self.mahoraga = None
        self.projectiles = []
        self.blood_particles = [] # Track blood splatters
        self.hit_sparks = [] # NEW: Track punch impact sparks
        self.bf_words = [] # Track Black Flash word popups
        self.popups = [] # Track Dodged text popups
        self.gojo_combo_buffer = [] # NEW: Combo input tracking buffer
        self.game_over = False
        self.paused = False
        self.mahoraga_summon_timer = 0 
        self.shake_timer = 0
        self.clash_msg_timer = 0
        self.clash_winner = ""
        
        # New Tracking for Announcements
        self.prev_adaptations = {"blue": 1.0, "red": 1.0, "purple": 1.0, "punch": 1.0, "infinity": 0.0, "void": 1.0}
        self.maho_announcements = []

    def get_text(self, text, color, font=None):
        if font is None:
            font = self.font
        key = (text, color, font)
        if key not in self.text_cache:
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    def draw_bar_on(self, surf, x, y, val, max_val, color, width, height, label):
        pygame.draw.rect(surf, (40, 40, 50), (x, y, width, height)) 
        fill_w = int((max(0, val) / max_val) * width)
        pygame.draw.rect(surf, color, (x, y, fill_w, height))
        pygame.draw.rect(surf, (120, 120, 150), (x, y, width, height), 1)
        if label:
            lbl = self.get_text(label, WHITE, self.mini_font)
            surf.blit(lbl, (x, y - 18))

    def run(self):
        running = True
        while running:
            self.screen.fill(BLACK)
            keys = pygame.key.get_pressed()
            mouse_click = pygame.mouse.get_pressed()
            
            # Reset Simple Domain Flags
            self.gojo.simple_domain_active = False
            self.sukuna.simple_domain_active = False
            
            # --- PB COMBO LATCHES ---
            if not hasattr(self, "pb_blue_ready"): self.pb_blue_ready = True
            if not hasattr(self, "pb_red_ready"): self.pb_red_ready = True
            
            if not (keys[pygame.K_e] and keys[pygame.K_w]): self.pb_blue_ready = True
            if not (keys[pygame.K_e] and keys[pygame.K_s]): self.pb_red_ready = True
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p: self.paused = not self.paused
                if not self.game_over:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE: self.gojo.jump()
                        if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: self.gojo.dodge()
                        
                        # # # --- NEW: GOJO DEV CONTROLS ---
                        # if event.key == pygame.K_1: 
                        #     self.gojo.dev_immortal = not self.gojo.dev_immortal
                        #     self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 120, "timer": 60, "text": f"IMMORTAL: {self.gojo.dev_immortal}", "color": HEAL_GREEN})
                        
                        # if event.key == pygame.K_2:
                        #     self.gojo.dev_inf_ce = not self.gojo.dev_inf_ce
                        #     self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 120, "timer": 60, "text": f"INF CE: {self.gojo.dev_inf_ce}", "color": BLUE})
                        
                        # if event.key == pygame.K_3:
                        #     # Toggles the state between True and False
                        #     self.gojo.dev_disable_infinity = not getattr(self.gojo, "dev_disable_infinity", False)
                            
                        #     # Give a clear popup so you know if it's OFF or NORMAL
                        #     state_text = "OFF" if self.gojo.dev_disable_infinity else "NORMAL"
                        #     self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 120, "timer": 60, "text": f"INFINITY: {state_text}", "color": INF_COLOR})
                        
                        # if event.key == pygame.K_4:
                        #     self.gojo.blue_cd = 0
                        #     self.gojo.red_cd = 0
                        #     self.gojo.purple_cd = 0
                        #     self.gojo.domain_cd = 0
                        #     self.gojo.technique_burnout = 0
                        #     self.gojo.sd_broken_timer = 0
                        #     self.gojo.attack_cooldown = 0
                        #     self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 120, "timer": 60, "text": "COOLDOWNS RESET!", "color": WHITE})
                        # # ------------------------------
                       
                        # Capture specific combo keys
                        if event.key == pygame.K_w: self.gojo_combo_buffer.append("W")
                        if event.key == pygame.K_s: self.gojo_combo_buffer.append("S")
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.gojo_combo_buffer.append("CLICK")
                    
                    # Keep combo buffer to the last 3 distinct required inputs
                    self.gojo_combo_buffer = self.gojo_combo_buffer[-3:]
                    
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if WIDTH//2 - 100 < event.pos[0] < WIDTH//2 + 100 and HEIGHT//2 + 50 < event.pos[1] < HEIGHT//2 + 110:
                            running = False

            if not self.game_over and not self.paused and self.mahoraga_summon_timer <= 0:
                # --- GOJO INPUTS ---
                
                # Simple Domain - Hold Right Click
                if mouse_click[2] and self.gojo.energy > 5 * self.gojo.cost_mult and not self.gojo.domain_active and self.gojo.sd_broken_timer <= 0:
                    # INITIAL COST: If it wasn't active last frame, take a big chunk
                    if not getattr(self.gojo, "sd_was_active", False):
                        self.gojo.energy -= 25.0 * self.gojo.cost_mult
                        self.gojo.sd_hits = 0 # Reset hit count on fresh activation
                    
                    self.gojo.simple_domain_active = True
                    self.gojo.sd_was_active = True # Track state for next frame
                    
                    # CONTINUOUS DRAIN: Increased from 0.5 to 1.5
                    if self.gojo.domain_charge == 0:
                        self.gojo.energy -= 1.5 * self.gojo.cost_mult
                else:
                    self.gojo.simple_domain_active = False
                    self.gojo.sd_was_active = False # Reset state
                
                # Domain Expansion Charge - 'V' 
                if keys[pygame.K_v] and self.gojo.domain_cd == 0 and self.gojo.technique_burnout == 0 and self.gojo.domain_charge == 0 and not self.gojo.domain_active and self.gojo.grab_timer <= 0:
                    if self.gojo.energy >= 190 * self.gojo.cost_mult:
                        self.gojo.domain_charge = 60
                        self.gojo.energy -= 190 * self.gojo.cost_mult 
                    else:
                        if self.gojo.attack_cooldown == 0:
                            self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 100, "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                            self.gojo.attack_cooldown = 20
                
                # --- COMBO EXECUTION LOGIC ---
                
                # 1. BLUE POINT-BLANK (Warped Punch)
                # Cost: 60 CE (3x Normal) | Cooldown: 120 frames (2 seconds) -> Shortened!
                # THE FIX: Added 'and self.gojo.technique_burnout == 0' to prevent usage during burnout
                if keys[pygame.K_e] and keys[pygame.K_w] and self.pb_blue_ready and self.gojo.energy >= 60 * self.gojo.cost_mult and self.gojo.blue_cd == 0 and self.gojo.grab_timer <= 0 and self.gojo.technique_burnout == 0 and self.gojo.domain_charge == 0:
                    self.pb_blue_ready = False
                    self.gojo.energy -= 60 * self.gojo.cost_mult
                    self.gojo.blue_cd = 480 # EQUALIZED: 8 second cooldown
                    
                    # Damage: 15.0 (3x Base Punch)
                    self.sukuna.rect.centerx = self.gojo.rect.centerx + (50 * self.gojo.direction)
                    
                    # Initial impact damage (reduced because the continuous beatdown handles the rest)
                    pb_blue_dmg = 30.0
                    if self.sukuna.amp_duration > 0: pb_blue_dmg *= 0.2 # DA absorbs 80%
                    
                    # --- 1:2 Final CE Drain based on Mitigation ---
                    if self.sukuna.energy > 0:
                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                        mitigated_dmg = pb_blue_dmg * (1.0 - reduction_mult) 
                        
                        pb_blue_dmg *= reduction_mult 
                        
                        # 2 CE spent for every 1 HP saved
                        self.sukuna.energy = max(0, self.sukuna.energy - (mitigated_dmg * 2.0) * self.sukuna.cost_mult)
                    
                    self.sukuna.hp -= pb_blue_dmg 
                    
                    self.sukuna.grab_timer = 180 # 3 SECOND BEATDOWN HOLD!
                    setattr(self.sukuna, "grab_type", "gojo_beatdown")
                    self.sukuna.fuga_charge = 0
                    self.sukuna.domain_charge = 0
                    self.sukuna.amp_duration = 0 
                    self.sukuna.attack_cooldown = 30 
                    self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 25) # Adds to Purple Pool
                    self.shake_timer = 10
                    
                    self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 80, "timer": 45, "text": "WARPED!", "color": BLUE})
                    
                    for _ in range(20):
                        self.hit_sparks.append([self.sukuna.rect.centerx, self.sukuna.rect.centery, random.uniform(-15, 15), random.uniform(-15, 15), random.randint(20, 40), BLUE])
                        
                    self.gojo_combo_buffer.clear()
                        
                # 2. RED POINT-BLANK (Cleave Escape / Beatdown Ender)
                # LORE FIX: Gojo CAN use PB Red while his technique is burned out (during/after MS) 
                # by performing a rapid Brain RCT Refresh! It instantly cures Burnout but costs extra CE!
                elif keys[pygame.K_e] and keys[pygame.K_s] and self.pb_red_ready and self.gojo.energy >= 100 * self.gojo.cost_mult and self.gojo.red_cd == 0 and (self.gojo.grab_timer > 0 or self.sukuna.grab_timer > 0) and self.gojo.domain_charge == 0:
                    self.pb_red_ready = False
                    self.gojo.grab_timer = 0
                    self.sukuna.grab_timer = 0
                    
                    # --- BRAIN RCT REFRESH ---
                    # LORE: If he is currently burned out, he destroys and heals his brain to instantly refresh his technique!
                    if self.gojo.technique_burnout > 0:
                        self.gojo.technique_burnout = 0
                        self.gojo.energy -= 150 * self.gojo.cost_mult # Extra heavy CE tax for the brain refresh!
                        self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 120, "timer": 60, "text": "BRAIN RCT REFRESH!", "color": HEAL_GREEN})
                        
                    self.gojo.energy -= 100 * self.gojo.cost_mult
                    self.gojo.red_cd = 240  
                    self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 25) # Adds to Purple Pool
                    
                    # --- NEW: Clear Sukuna's domain charge so he doesn't get a fake interrupt! ---
                    self.sukuna.domain_charge = 0
                    
                    # Damage: 30.0 (2x PB Blue)
                    pb_red_dmg = 150.0
                    if self.sukuna.amp_duration > 0: pb_red_dmg *= 0.3 # DA absorbs 70%
                    
                    # --- NEW: 1:2 Final CE Drain based on Mitigation ---
                    if self.sukuna.energy > 0:
                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                        mitigated_dmg = pb_red_dmg * (1.0 - reduction_mult) 
                        
                        pb_red_dmg *= reduction_mult 
                        
                        # 2 CE spent for every 1 HP saved
                        self.sukuna.energy = max(0, self.sukuna.energy - (mitigated_dmg * 2.0) * self.sukuna.cost_mult)
                        
                    self.sukuna.hp -= pb_red_dmg 
                    
                    # --- NEW: Apply hit-stun so Sukuna's AI doesn't instantly cast a domain while flying backward! ---
                    self.sukuna.attack_cooldown = 45
                    
                    # --- FIXED: PUSH BOTH FIGHTERS AWAY FROM EACH OTHER ---
                    push_force = 250
                    if self.sukuna.rect.centerx > self.gojo.rect.centerx:
                        self.sukuna.rect.x += push_force
                        self.gojo.rect.x -= push_force
                    else:
                        self.sukuna.rect.x -= push_force
                        self.gojo.rect.x += push_force
                    
                    self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 80, "timer": 45, "text": "REPELLED!", "color": RED})
                    
                    # --- FIXED: SPAWN ORB EXACTLY IN THE MIDDLE ---
                    mid_x = (self.gojo.rect.centerx + self.sukuna.rect.centerx) // 2
                    mid_y = (self.gojo.rect.centery + self.sukuna.rect.centery) // 2
                    
                    # Increased size_mult to 3.0 so it looks like a massive point-blank explosion
                    red_burst = Projectile(mid_x, mid_y, mid_x, mid_y, 0, RED, size_mult=3.0, type="red_orb")
                    red_burst.lifetime = 15 
                    self.projectiles.append(red_burst)
                    
                    self.shake_timer = 30
                    
                    for p in self.projectiles:
                        if getattr(p, "is_grab_cleave", False):
                            p.active = False
                            
                    self.gojo_combo_buffer.clear()

                if not self.gojo.is_paralyzed and self.gojo.grab_timer <= 0 and self.gojo.domain_charge == 0:
                    # Space compression movement speed: double normal rate
                    if keys[pygame.K_a]: self.gojo.rect.x -= 20; self.gojo.direction = -1
                    if keys[pygame.K_d]: self.gojo.rect.x += 20; self.gojo.direction = 1
                    
                    punching = False
                    
                    # --- PROXIMITY TARGETING SYSTEM ---
                    enemies = [self.sukuna]
                    if self.mahoraga and self.mahoraga.hp > 0:
                        enemies.append(self.mahoraga)
                    
                    # Target the one Gojo is closest to horizontally
                    target = min(enemies, key=lambda e: abs(self.gojo.rect.centerx - e.rect.centerx))
                    current_effect = None

                    # Hand to Hand (Gojo)
                    if mouse_click[0] and self.gojo.attack_cooldown == 0:
                        punching = True
                        self.gojo.punch_timer = 20 
                        self.gojo.punch_count += 1 
                        if abs(self.gojo.rect.centerx - target.rect.centerx) < 130:
                            dmg = 6.5 * (target.adaptation["punch"] if target.name == "Mahoraga" else 1.0)
                            
                            # --- CE IMBUE TO PUNCHES ---
                            imbue_cost = 2.0 * self.gojo.cost_mult
                            if self.gojo.energy >= imbue_cost:
                                self.gojo.energy -= imbue_cost
                                dmg *= 1.6 # CE Imbue Damage Boost!
                            
                            # Black Flash Trigger Logic (Base: 0.05-0.1%, Zone: 5-10%)
                            if self.gojo.potential_timer > 0:
                                bf_chance = random.uniform(0.05, 0.10) # 5% to 10% (The Zone)
                            else:
                                bf_chance = random.uniform(0.0005, 0.001) # SIGNIFICANTLY LOWERED: 0.05% to 0.1%
                                
                            if random.random() < bf_chance:
                                dmg *= math.pow(2.5, 2.5) 
                                self.gojo.black_flash_timer = 20
                                self.gojo.potential_timer = 600 # 10s duration
                                self.shake_timer = 15
                                self.gojo.energy = self.gojo.max_energy 
                                self.bf_words.append({"x": target.rect.centerx, "y": target.rect.centery - 60, "timer": 45})
                            
                            if not target.is_dodging:
                                # Sukuna's immense reinforcement gives him 20-50% passive damage reduction on normal attacks
                                if target.name == "Sukuna" and target.energy > 0:
                                    reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                    mitigated_dmg = dmg * (1.0 - reduction_mult) 
                                    
                                    dmg *= reduction_mult 
                                    
                                    # 2 CE spent for every 1 HP saved
                                    target.energy = max(0, target.energy - (mitigated_dmg * 2.0) * target.cost_mult)
                                elif target.name == "Mahoraga":
                                    dmg *= random.uniform(0.6, 0.85)
                                    
                                target.hp -= dmg
                                
                                # Spawn Punch Hit Sparks
                                spark_color = (255, 0, 0) if self.gojo.black_flash_timer > 0 else WHITE
                                for _ in range(12):
                                    self.hit_sparks.append([target.rect.centerx + random.randint(-15, 15), target.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), spark_color])
                                
                                # --- NEW: KNOCKBACK ---
                                kb_dir = 1 if target.rect.centerx > self.gojo.rect.centerx else -1
                                target.rect.x += kb_dir * 15
                                
                                if target.name == "Mahoraga": 
                                    if self.sukuna.amp_duration <= 0:
                                        target.trigger_adaptation("punch", 15.0)
                                        turns = target.adaptation_points["punch"] / 250.0
                                        target.adaptation["punch"] = max(0, 1.0 - min(1.0, turns))
                        self.gojo.attack_cooldown = 12

                    # RCT (Gojo)
                    if keys[pygame.K_q] and self.gojo.energy > 5 * self.gojo.cost_mult:
                        self.gojo.hp = min(self.gojo.max_hp, self.gojo.hp + 1.5)
                        self.gojo.energy -= 2 * self.gojo.cost_mult
                        self.gojo.rct_timer = 5

                   # --- GOJO TECHNIQUE ORBS ---
                    # Define a helper check to see if Gojo is REALLY burned out
                    is_actually_burned_out = (self.gojo.domain_uses >= 5 and self.gojo.technique_burnout > 0)

                    # Blue
                    if keys[pygame.K_w] and self.gojo.blue_cd == 0:
                        if self.gojo.energy >= 20 * self.gojo.cost_mult:
                            if not is_actually_burned_out:
                                self.projectiles.append(Projectile(self.gojo.rect.centerx, self.gojo.rect.centery, target.rect.centerx, target.rect.centery, 18, BLUE, size_mult=1.5, type="blue_orb"))
                                self.gojo.energy -= 20 * self.gojo.cost_mult
                                self.gojo.blue_cd = 60 
                        else:
                            if self.gojo.attack_cooldown == 0:
                                self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 100, "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                                self.gojo.attack_cooldown = 20
                        

                    # Red
                    if keys[pygame.K_s] and self.gojo.red_cd == 0:
                        if self.gojo.energy >= 40 * self.gojo.cost_mult:
                            if not is_actually_burned_out:
                                self.projectiles.append(Projectile(self.gojo.rect.centerx, self.gojo.rect.centery, target.rect.centerx, target.rect.centery, 30, RED, size_mult=1.8, type="red_orb"))
                                self.gojo.energy -= 40 * self.gojo.cost_mult
                                self.gojo.red_cd = 120
                        else:
                            if self.gojo.attack_cooldown == 0:
                                self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 100, "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                                self.gojo.attack_cooldown = 20

                    # Purple
                    # 1. Check if the 'R' key is pressed, not charging/on CD, AND not currently busy with a beatdown!
                    is_beatdown_active = self.sukuna.grab_timer > 0 and getattr(self.sukuna, "grab_type", "") == "gojo_beatdown"
                    
                    if keys[pygame.K_r] and self.gojo.purple_cd == 0 and self.gojo.purple_charge == 0 and not is_beatdown_active:
                        
                        # 2. Check for Energy (Cursed Energy) requirement
                        if self.gojo.energy >= 195 * self.gojo.cost_mult:
                            
                            # 3. Check for specific technique requirements (Burnout and Hits)
                            if not is_actually_burned_out and self.gojo.tech_hits >= self.gojo.max_tech_hits:
                                self.gojo.purple_charge = 120
                        
                        else:
                            # 4. Logic for when Energy is insufficient
                            # We use attack_cooldown to prevent the popup from spawning 60 times a second
                            if self.gojo.attack_cooldown == 0:
                                self.popups.append({
                                    "x": self.gojo.rect.centerx, 
                                    "y": self.gojo.rect.centery - 100, 
                                    "timer": 30, 
                                    "text": "NOT ENOUGH CE!", 
                                    "color": RED
                                })
                                self.gojo.attack_cooldown = 20

                    # 5. Handle the charging and firing logic (Independent of the key press trigger)
                    if self.gojo.purple_charge > 0:
                        self.gojo.purple_charge -= 1
                        if self.gojo.purple_charge == 1:
                            self.projectiles.append(Projectile(
                                self.gojo.rect.centerx, 
                                self.gojo.rect.centery, 
                                target.rect.centerx, 
                                target.rect.centery, 
                                20, PURPLE, size_mult=3.5, type="purple_orb"
                            ))
                            self.gojo.energy = max(0, self.gojo.energy - (195 * self.gojo.cost_mult))
                            self.gojo.purple_cd = 720
                            self.gojo.tech_hits = 0
                            
                # Gojo Domain Execution Timer
                if self.gojo.domain_charge > 0:
                    self.gojo.domain_charge -= 1
                    if self.gojo.domain_charge == 1:
                        self.gojo.domain_active = True
                        self.gojo.domain_timer = 400
                        self.gojo.domain_cd = 3000
                        self.gojo.infinity = self.gojo.max_infinity # Dynamically restores Infinity!
                        self.shake_timer = 30

                # --- SMART SUKUNA AI ---
                dist = abs(self.sukuna.rect.centerx - self.gojo.rect.centerx)
                fuga_priority = (self.sukuna.tech_hits >= self.sukuna.max_tech_hits and self.sukuna.fuga_cd == 0 and self.sukuna.energy >= 195 * self.sukuna.cost_mult) or self.sukuna.fuga_charge > 0
                gojo_has_inf = self.gojo.infinity > 0 and self.gojo.technique_burnout == 0
                
                # --- SUKUNA DOMAIN CLASH & SIMPLE DOMAIN LOGIC ---
                # --- FIXED: Added self.gojo.grab_timer <= 0 so he doesn't try to cast Domain while holding Gojo! ---
                # --- FIXED: Added attack_cooldown <= 0 so he doesn't cast Domain while reeling from PB Red! ---
                if self.sukuna.energy >= 200 * self.sukuna.cost_mult and self.sukuna.domain_cd == 0 and self.sukuna.technique_burnout == 0 and self.sukuna.domain_charge == 0 and not self.sukuna.domain_active and not self.sukuna.is_paralyzed and self.gojo.grab_timer <= 0 and self.sukuna.attack_cooldown <= 0:
                    
                    should_cast_domain = False
                    
                    # AI UPGRADE: Calculate overall combat readiness to see if clashing is favorable
                    sukuna_est_power = self.sukuna.hp + self.sukuna.energy
                    gojo_est_power = self.gojo.hp + self.gojo.energy
                    power_advantage = sukuna_est_power >= gojo_est_power
                    
                    # AI UPGRADE: Factor in Domain uses remaining (Max 5 uses)
                    sukuna_domains_left = 5 - self.sukuna.domain_uses
                    gojo_domains_left = 5 - self.gojo.domain_uses
                    domain_advantage = sukuna_domains_left >= gojo_domains_left
                    
                    if self.gojo.domain_active:
                        # Gojo's domain is already up! 
                        # SMART AI: If Sukuna is weak and out of uses, try stalling with Simple Domain if HP permits!
                        if not power_advantage and self.sukuna.sd_broken_timer <= 0 and self.sukuna.energy > 50:
                            should_cast_domain = False # Stall with Simple Domain to avoid a clash he calculates he'll lose!
                        else:
                            should_cast_domain = True # Pop ours to clash immediately!
                        
                    elif self.gojo.domain_charge > 0:
                        # Gojo is charging his domain! Calculate the best tactical response.
                        can_interrupt = False
                        
                        # 1. Guaranteed Interruption Checks (Must hit before domain_charge reaches 0)
                        if self.sukuna.world_slash_unlocked and self.sukuna.world_slash_cd <= 0 and getattr(self.sukuna, "world_slash_charge", 0) <= 0 and self.sukuna.energy >= 80 * self.sukuna.cost_mult:
                            can_interrupt = True # World Slash perfectly ignores Infinity
                        elif not gojo_has_inf and self.sukuna.dismantle_cd <= 0 and self.sukuna.energy >= 10 * self.sukuna.cost_mult:
                            can_interrupt = True # Normal slash only interrupts if Infinity is verified DOWN
                        elif dist <= 150 and self.sukuna.energy >= 15 * self.sukuna.cost_mult:
                            can_interrupt = True # Close enough to instantly DA punch him
                            
                        # 2. Survivability Calculation (If we fail to interrupt)
                        can_survive_uv = True
                        frames_unprotected = max(0, 400 - self.sukuna.max_sd_hits) if self.sukuna.sd_broken_timer <= 0 else 400
                        expected_uv_damage = frames_unprotected * 1.5
                        
                        if self.sukuna.hp <= expected_uv_damage or self.sukuna.energy < (400 * 1.0):
                            can_survive_uv = False # He calculates he will literally die or run out of CE if he gets caught
                            
                        # 3. Final Decision Logic
                        if not can_interrupt:
                            # If we can't interrupt, we MUST clash UNLESS we have a massive disadvantage and prefer stalling with SD
                            if not power_advantage and can_survive_uv and self.sukuna.sd_broken_timer <= 0:
                                should_cast_domain = False
                            else:
                                should_cast_domain = True 
                        elif can_interrupt and not can_survive_uv:
                            # Even if he thinks he can interrupt, if a single mistake means death, play it safe and clash!
                            should_cast_domain = True
                            
                    else:
                        # Strategic Offensive Domain (Gojo is vulnerable)
                        gojo_is_vulnerable = self.gojo.technique_burnout > 0 or self.gojo.domain_cd > 0 or self.gojo.energy < 150 * self.gojo.cost_mult
                        
                        # --- TACTICAL AI UPGRADE: ANTI-STALL & HOARDING DETECTION ---
                        # Sukuna calculates if Gojo is purposely withholding his Domain Expansion to trick Sukuna into wasting his 5 uses.
                        gojo_is_hoarding = gojo_domains_left > sukuna_domains_left
                        
                        # SMART AI: Only launch an offensive DE if Sukuna has a domain advantage, power advantage, or Gojo is highly vulnerable.
                        if gojo_is_vulnerable:
                            # If Gojo is genuinely vulnerable, strike without hesitation!
                            should_cast_domain = True
                        elif gojo_is_hoarding:
                            # SUKUNA IS SMART: He detects the stalling tactic.
                            # He refuses to cast an offensive domain to be baited. He will save his DE to answer Gojo, relying on DA or Fuga instead!
                            should_cast_domain = False
                        elif domain_advantage and power_advantage and (self.sukuna.hp > self.sukuna.max_hp * 0.5):
                            # Confident in his stats, force Gojo into a clash to burn Gojo's uses!
                            if random.random() < 0.01: # Small chance so he doesn't spam it instantly
                                should_cast_domain = True
                        elif (self.sukuna.hp < (self.sukuna.max_hp * 0.3) and random.random() < 0.005):
                            should_cast_domain = True # Desperation

                    if should_cast_domain:
                        self.sukuna.domain_charge = 60
                        de_cost = 200 * self.sukuna.cost_mult
                        self.sukuna.energy -= de_cost

                elif self.gojo.domain_active and not self.sukuna.domain_active:
                    # AI smartly maintains Simple Domain inside Gojo's domain
                    if self.sukuna.energy > 5 * self.sukuna.cost_mult and self.sukuna.sd_broken_timer <= 0:
                        
                        # INITIAL COST for AI (Only triggers on a fresh cast)
                        if not getattr(self.sukuna, "sd_was_active", False):
                            sd_init_cost = 25.0 * self.sukuna.cost_mult
                            self.sukuna.energy -= sd_init_cost
                            self.sukuna.sd_hits = 0 # Reset hits on fresh activation
                        
                        self.sukuna.simple_domain_active = True
                        self.sukuna.sd_was_active = True
                        
                        # CONTINUOUS DRAIN: (~60 CE per second)
                        sd_cont_cost = 1.0 * self.sukuna.cost_mult
                        self.sukuna.energy -= sd_cont_cost 
                    else:
                        self.sukuna.simple_domain_active = False
                        self.sukuna.sd_was_active = False
                else:
                    self.sukuna.simple_domain_active = False
                    self.sukuna.sd_was_active = False

                if not self.sukuna.is_paralyzed and self.sukuna.grab_timer <= 0 and self.sukuna.domain_charge == 0:
                    is_amp = self.sukuna.amp_duration > 0
                    
                    # --- NEW: ACTIVE DOMAIN & PURPLE INTERRUPT ---
                    purple_flying = any(p.type == "purple_orb" for p in self.projectiles)
                    is_purple_threat = self.gojo.purple_charge > 0 or purple_flying
                    
                    if self.gojo.domain_charge > 0 or is_purple_threat:
                        # --- HOLLOW PURPLE TACTICAL CALCULATION ---
                        can_tank_purple = True
                        if is_purple_threat:
                            # Calculate worst-case scenario for Purple (Base damage = max_hp = 500)
                            # DA absorbs 40% (remaining 300). Minimum CE mitigation is ~50% (remaining 150 HP damage).
                            # If he doesn't have at least 150 HP and ~300 CE, he CANNOT tank it safely.
                            safe_hp_threshold = 150
                            safe_ce_threshold = 300 * self.sukuna.cost_mult
                            
                            if self.sukuna.hp <= safe_hp_threshold or self.sukuna.energy <= safe_ce_threshold:
                                can_tank_purple = False

                        if is_purple_threat and not can_tank_purple:
                            # --- DESPERATE EVASION & BINDING VOW DEFENSE ---
                            # SMARTS: Run away to gain distance from the nuke!
                            run_dir = -1 if self.sukuna.rect.x < self.gojo.rect.x else 1
                            
                            # --- SMART CORNER DETECTION FOR PURPLE PANIC ---
                            if (self.sukuna.rect.left < 150 and run_dir == -1) or (self.sukuna.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                                # He realizes he is cornered against the wall! 
                                # Reverse direction to run PAST Gojo instead of dying trapped.
                                run_dir *= -1 
                                if self.sukuna.on_ground:
                                    self.sukuna.jump() # Force a jump to try and leap over Gojo/the incoming orb!
                            
                            self.sukuna.direction = run_dir
                            self.sukuna.rect.x += 28 * run_dir
                            
                            if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20:
                                self.sukuna.dodge()
                                self.sukuna.dodge_cd = 15 # Desperate faster dodges
                                
                            # BINDING VOW: Trade massive CE for hyper-reinforcement to survive the blast!
                            # Costs 60% of his Burst RCT cost (4.0 * 0.6 = 2.4)
                            vow_cost = 2.4 * self.sukuna.cost_mult
                            if self.sukuna.energy > vow_cost:
                                self.sukuna.energy -= vow_cost
                                # Rapidly fortify HP so he doesn't get one-shot by the incoming nuke!
                                self.sukuna.hp = min(self.sukuna.max_hp, self.sukuna.hp + 2.0)
                                self.sukuna.amp_duration = max(self.sukuna.amp_duration, 60) # Force DA on!
                                is_amp = True
                                
                                # --- ANNOUNCEMENT (Throttled to once every 5 seconds) ---
                                if pygame.time.get_ticks() - getattr(self, "last_purple_vow", 0) > 5000:
                                    self.maho_announcements.append({"text": "SUKUNA VOW: CE BURNED TO TANK PURPLE!", "timer": 120})
                                    self.last_purple_vow = pygame.time.get_ticks()
                        else:
                            # --- AGGRESSIVE INTERRUPT (Can Tank Purple OR it's a Domain Cast) ---
                            # SMARTS, NOT BUFFS: Immediately face the threat and stop wasting time
                            self.sukuna.direction = 1 if self.sukuna.rect.x < self.gojo.rect.x else -1
                            
                            # Priority 1: World Slash (Targets space, bypassing Infinity directly)
                            if self.sukuna.world_slash_unlocked and self.sukuna.world_slash_cd <= 0 and getattr(self.sukuna, "world_slash_charge", 0) <= 0 and self.sukuna.energy >= 80 * self.sukuna.cost_mult:
                                self.sukuna.world_slash_charge = 120
                                
                            # Priority 2: Tactical Rush to interrupt
                            elif dist > 100:
                                # Use his standard existing lunge speed (28), no artificial speed buffs!
                                self.sukuna.rect.x += 28 * self.sukuna.direction
                                
                                # Sequence his STANDARD dodge perfectly without buffing cooldowns or stamina costs
                                if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20:
                                    self.sukuna.dodge()
                                    self.sukuna.dodge_cd = 20 # Restored to strict base cooldown!
                    
                    # LORE ACCURACY: Actively detect incoming Orbs and dodge THROUGH them to close the gap!
                    incoming_orbs = [p for p in self.projectiles if p.type in ["blue_orb", "red_orb", "purple_orb"] and abs(p.pos.x - self.sukuna.rect.centerx) < 250]
                    if incoming_orbs:
                        closest_orb = min(incoming_orbs, key=lambda p: abs(p.pos.x - self.sukuna.rect.centerx))
                        
                        # Smart Jump: Jump over the orb to avoid the center of mass
                        if self.sukuna.on_ground and abs(closest_orb.pos.x - self.sukuna.rect.centerx) < 180:
                            self.sukuna.jump()
                            
                        if self.sukuna.dodge_cd == 0:
                            # Smart i-frame Dash: if trapped, dash towards the center to escape edge. 
                            # Otherwise, aggressively dash straight through the orb towards Gojo!
                            if self.sukuna.rect.centerx < 100: self.sukuna.direction = 1
                            elif self.sukuna.rect.centerx > WORLD_WIDTH - 100: self.sukuna.direction = -1
                            else: self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                            
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 40
                    
                    # LORE ACCURACY: Sukuna flickers DA! If he gets pushed away (> 150) and has slashes ready, instantly turn DA off.
                    if is_amp and dist > 150 and (self.sukuna.dismantle_cd == 0 or self.sukuna.cleave_cd == 0):
                        self.sukuna.amp_duration = 0
                        is_amp = False
                    
                    # Turn DA on only if he is very close, not about to Fuga, and slashes are unavailable
                    if dist <= 150 and self.sukuna.energy > 30 * self.sukuna.cost_mult and not fuga_priority and not self.sukuna.ce_exhausted and self.gojo.grab_timer <= 0:
                        # --- MODIFIED: Force DA to stay on if Gojo's Infinity is active so he can punch! ---
                        if self.gojo.infinity > 0:
                            # Continuously refresh the duration so it never drops while punching Gojo's Infinity
                            self.sukuna.amp_duration = max(self.sukuna.amp_duration, 60) 
                            is_amp = True
                        elif self.sukuna.amp_cd == 0 and self.sukuna.amp_duration == 0:
                            if self.sukuna.grab_cd > 0 or self.gojo.domain_active:
                                self.sukuna.amp_duration = 600 
                                is_amp = True
                    
                    if is_amp: 
                        da_cost = 0.25 * self.sukuna.cost_mult
                        self.sukuna.energy -= da_cost # Yes, Domain Amp drains 1.8 CE per frame!
                       
                    # --- FIX: ALLOW SUKUNA TO MOVE WHILE GRABBING ---
                    # STRATEGIC AI: If Gojo's domain is active, Sukuna frantically stays in point-blank contact!
                    rush_distance = 40 if self.gojo.domain_active else 110
                    
                    # --- NEW: SMARTER SUKUNA AI (CE CONSERVATION & BINDING VOW) ---
                    # Sukuna refuses to let his CE drop recklessly from tanking hits.
                    is_draining_ce = self.sukuna.energy < (self.sukuna.max_energy * 0.65) # Lost 35% CE
                    
                    if getattr(self.sukuna, "tactical_eval_timer", 0) > 0:
                        self.sukuna.tactical_eval_timer -= 1
                    
                    is_tactical_eval = getattr(self.sukuna, "tactical_eval_timer", 0) > 0
                    
                    if is_draining_ce and not self.sukuna.ce_exhausted and self.gojo.grab_timer <= 0:
                        # 1. CALCULATE THE ODDS (Flesh for Cursed Energy Binding Vow)
                        # He evaluates if trading HP for CE benefits him right now.
                        vow_hp_cost = self.sukuna.max_hp * 0.80 # BUFF: Costs a massive 80% of Max HP (400 HP)!
                        vow_ce_gain = self.sukuna.max_energy * 0.40 # Restores 1200 CE
                        
                        # The Math: Will he survive the HP drop? (Needs at least a 20 HP buffer to not instantly die)
                        can_afford_flesh_vow = self.sukuna.hp > (vow_hp_cost + 20)
                        # Does he actually need the CE badly enough to justify the pain?
                        desperate_for_ce = self.sukuna.energy < (self.sukuna.max_energy * 0.40)
                        
                        if can_afford_flesh_vow and desperate_for_ce:
                            self.sukuna.hp -= vow_hp_cost
                            self.sukuna.energy = min(self.sukuna.max_energy, self.sukuna.energy + vow_ce_gain)
                            self.shake_timer = 20
                            
                            # --- TACTICAL VOW PENALTY: DA LOST ---
                            self.sukuna.amp_duration = 0 
                            self.sukuna.amp_cd = 600 # 10 SECONDS DA LOCKOUT (60 fps * 10s)
                            self.sukuna.tactical_eval_timer = 600 # 10 SECONDS OF TACTICAL AI
                            is_amp = False
                            is_tactical_eval = True
                            
                            # --- UPGRADED ANNOUNCEMENT ---
                            self.maho_announcements.append({"text": "SUKUNA VOW: 80% HP FOR CE! (DA LOST 10s)", "timer": 120})
                            for _ in range(30): # Massive blood burst from the sacrifice
                                bx, by = self.sukuna.rect.center
                                self.blood_particles.append([bx, by, random.uniform(-8, 8), random.uniform(-10, -2), 50, random.randint(4, 7)])
                        
                        # 2. CHANGE TACTICS: STOP TANKING!
                        # If he is losing CE, he stops walking forward into punches and actively evades!
                        elif dist < 180 and self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20 and not self.gojo.domain_active:
                            # Smart Backstep: Dodge AWAY from Gojo instead of through him!
                            self.sukuna.direction = 1 if self.sukuna.rect.x > self.gojo.rect.x else -1
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 25 # Fast evasion cooldown

                    # --- TACTICAL HEALING, CE REGEN & CALCULATION RETREAT ---
                    # Retreat if HP is below 40%, if CE drops below 30%, OR if he is in Tactical Evaluation mode (no DA)
                    needs_healing = self.sukuna.hp < (self.sukuna.max_hp * 0.4) and self.sukuna.energy > 50 and not self.sukuna.ce_exhausted
                    needs_energy = self.sukuna.energy < (self.sukuna.max_energy * 0.3)
                    
                    # If in tactical evaluation, his primary goal is maintaining distance to calculate odds and use ranged/heavy attacks
                    retreating = (needs_healing or needs_energy or is_tactical_eval) and not self.gojo.domain_active
                    
                    if retreating and self.gojo.grab_timer <= 0:
                        
                        # --- TACTICAL EVALUATION LOGIC: Calculating odds and capabilities ---
                        if is_tactical_eval:
                            # He calculates Gojo's CE and Infinity state
                            gojo_vulnerable = self.gojo.infinity <= 0 or self.gojo.ce_exhausted
                            can_survive_counter = self.sukuna.hp > (self.sukuna.max_hp * 0.25) # Is he healthy enough to fight?
                            
                            # Calculation 1: Can he just end it with a Domain Expansion safely?
                            if self.sukuna.energy >= 200 * self.sukuna.cost_mult and self.sukuna.domain_cd == 0 and self.sukuna.technique_burnout == 0 and not self.sukuna.domain_active:
                                self.sukuna.domain_charge = 60
                                self.sukuna.energy -= 200 * self.sukuna.cost_mult
                            
                            # Calculation 2: Can he use Fuga to bypass or shred Gojo's CE completely?
                            elif self.sukuna.tech_hits >= self.sukuna.max_tech_hits and self.sukuna.fuga_cd == 0 and self.sukuna.energy >= 195 * self.sukuna.cost_mult and self.sukuna.technique_burnout == 0:
                                vow_hp_cost = self.sukuna.max_hp * 0.50
                                if self.sukuna.hp > (vow_hp_cost + 40): # Calculate odds: MUST survive the Fuga vow with a healthy buffer
                                    self.sukuna.fuga_charge = 120
                            
                            # Calculation 3: Tactical Harassment & CE Drain
                            # If he has the CE, aggressively spam slashes from afar to chip away at Gojo's Infinity and drain his CE
                            elif dist > 250 and self.sukuna.dismantle_cd <= 0 and self.sukuna.energy >= 30 * self.sukuna.cost_mult and self.sukuna.technique_burnout == 0 and can_survive_counter:
                                self.sukuna.slash_count = 3 # Controlled tactical burst
                                self.sukuna.slash_type = "dismantle"
                                self.sukuna.energy -= 10 * self.sukuna.cost_mult
                                self.sukuna.dismantle_cd = 40
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1 # Face Gojo to fire
                        
                        # --- ACTIVE RCT BURST ---
                        # Sukuna checks if he has a very safe CE buffer (> 1000 CE) AND actually needs healing.
                        # If so, he dramatically speeds up healing at a heavy CE cost!
                        if needs_healing and self.sukuna.energy > 1000 * self.sukuna.cost_mult:
                            active_heal_cost = 4.0 * self.sukuna.cost_mult
                            self.sukuna.energy -= active_heal_cost
                            self.sukuna.hp = min(self.sukuna.max_hp, self.sukuna.hp + 5.0) # THE FIX: Doubled burst heal speed!
                            self.sukuna.rct_timer = 5 # Keep particles flowing
                            
                        # Note: If energy is <= 1000, he skips this burst and relies on his 0.3 CE passive RCT to save energy!

                        # --- MODIFIED: Attempt Domain Expansion as a defensive counter-measure while retreating! ---
                        # Only do this if he has a safe amount of CE, since his goal might be to regen CE! (Skip if in pure tactical evaluation)
                        if not needs_energy and not is_tactical_eval and self.sukuna.energy >= 200 * self.sukuna.cost_mult and self.sukuna.domain_cd == 0 and self.sukuna.technique_burnout == 0 and self.sukuna.domain_charge == 0 and not self.sukuna.domain_active and self.sukuna.attack_cooldown <= 0:
                            # --- TACTICAL AI UPGRADE: ANTI-STALL CHECK ---
                            # If Gojo is hoarding domains, Sukuna won't be baited into a panic domain cast just because he's retreating!
                            if (5 - self.gojo.domain_uses) <= (5 - self.sukuna.domain_uses):
                                self.sukuna.domain_charge = 60
                                de_cost = 200 * self.sukuna.cost_mult
                                self.sukuna.energy -= de_cost

                        # --- EVASIVE SHADOW STEPPING ---
                        speed = 18 if not is_tactical_eval else 24 
                        
                        # Base movement: Back away if too close, close in if too far, otherwise Dash Dance!
                        if dist < 250:
                            run_dir = 1 if self.sukuna.rect.x > self.gojo.rect.x else -1
                        elif dist > 550:
                            run_dir = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1 # Dart back in!
                        else:
                            # The "Dash Dance": Rapidly switch directions to confuse Gojo while regenerating
                            if getattr(self.sukuna, "dash_dance_timer", 0) <= 0:
                                self.sukuna.dash_dance_dir = random.choice([-1, 1])
                                self.sukuna.dash_dance_timer = random.randint(15, 35)
                            else:
                                self.sukuna.dash_dance_timer -= 1
                            run_dir = getattr(self.sukuna, "dash_dance_dir", 1)

                        # Smart corner logic so he bounces off walls dynamically
                        if (self.sukuna.rect.left < 150 and run_dir == -1) or (self.sukuna.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                            run_dir *= -1 
                            if self.sukuna.on_ground: self.sukuna.jump()
                        else:
                            # Highly evasive jumps while shadow stepping
                            jump_chance = 0.08 if needs_energy else 0.04
                            if self.sukuna.on_ground and random.random() < jump_chance:
                                self.sukuna.jump()
                                
                        # Apply the smart movement
                        self.sukuna.rect.x += speed * run_dir
                            
                        # Aggressively spam dodge to dash around!
                        if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20 and not self.sukuna.stamina_exhausted:
                            # If dashing, give it a 30% chance to forcefully cross-up THROUGH Gojo to look menacing
                            if dist < 350 and random.random() < 0.3:
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                            else:
                                self.sukuna.direction = run_dir
                                
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 20 if needs_energy or is_tactical_eval else 25
                        # --- NEW: ANTI-BLUE DEFENSES ---
                        # 1. Covering Fire: Throw a quick Dismantle backward to interrupt Gojo's pursuit!
                        if not is_tactical_eval and self.sukuna.dismantle_cd <= 0 and self.sukuna.energy >= 10 * self.sukuna.cost_mult and random.random() < 0.04 and self.sukuna.technique_burnout == 0 and not gojo_has_inf:
                            self.sukuna.slash_count = 1
                            self.sukuna.slash_type = "dismantle"
                            self.sukuna.energy -= 10 * self.sukuna.cost_mult
                            self.sukuna.dismantle_cd = 80 # Longer cooldown so he doesn't spam it while running
                            self.sukuna.direction = -run_dir # Face backwards at Gojo to fire!
                            
                        # 2. Defensive Aura: Turn on Domain Amplification while healing to tank ALL incoming damage!
                        # Explicitly disabled during Tactical Evaluation because of the Vow Penalty!
                        if not is_tactical_eval and self.sukuna.energy > 15 * self.sukuna.cost_mult and self.sukuna.amp_cd <= 0:
                            # max() ensures the duration is constantly refreshed so the shield doesn't flicker off!
                            self.sukuna.amp_duration = max(self.sukuna.amp_duration, 60) 
                            is_amp = True

                    # --- NEW: ABSOLUTE VERTICAL TETHERING ---
                    elif self.gojo.domain_active and not self.sukuna.domain_active and self.gojo.rect.bottom < self.sukuna.rect.top - 20 and self.sukuna.on_ground:
                        self.sukuna.jump()

                    elif dist > rush_distance or self.gojo.grab_timer > 0:
                        # Magnetic Lunge to trigger Cleave Hold (speed 28) or normal relentless walking (speed 9)
                        # AI FIX: If exhausted or surviving UV, aggressively rush at high speed!
                        speed = 35 if (self.sukuna.ce_exhausted or self.gojo.domain_active) else (28 if (self.sukuna.cleave_cd <= 0 and dist < 600 and self.gojo.grab_timer <= 0) else 9)
                        
                        if self.gojo.grab_timer > 0:
                            # Sukuna actively drags Gojo around while grinding him with Cleave!
                            self.sukuna.rect.x += speed * self.sukuna.direction
                            if random.random() < 0.02: self.sukuna.direction *= -1 # Periodically switches drag direction
                        else:
                            self.sukuna.rect.x += -speed if self.sukuna.rect.x > self.gojo.rect.x else speed
                            
                        # --- THE STRUGGLE PHASE: SMARTER TETHERING ---
                        if self.gojo.domain_active and not self.sukuna.domain_active:
                            # Desperately dash to close the distance quickly (Jump moved outside)
                            if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20 and not self.sukuna.stamina_exhausted:
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                                self.sukuna.dodge()
                                self.sukuna.dodge_cd = 25
                        else:
                            # --- SMARTER PURSUIT: JUMP-DASH BLITZ COMBO ---
                            if self.sukuna.dodge_cd == 0 and random.random() < 0.04 and self.gojo.grab_timer <= 0:
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                                self.sukuna.dodge()
                                if self.sukuna.on_ground:
                                    self.sukuna.jump() # Air Blitz combo!
                                self.sukuna.dodge_cd = 70
                            elif self.sukuna.on_ground and random.random() < 0.02:
                                self.sukuna.jump()

                    # --- SMARTER FUGA AI ---
                    # With the 50% HP Binding Vow, Fuga is extremely dangerous to Sukuna. He must calculate!
                    if self.sukuna.energy >= 195 * self.sukuna.cost_mult and self.sukuna.fuga_cd == 0 and self.sukuna.fuga_charge == 0 and self.sukuna.technique_burnout == 0:
                        if self.sukuna.tech_hits >= self.sukuna.max_tech_hits:
                            # 1. Calculate HP Cost Survivability (Needs at least 50% + 20 HP buffer)
                            vow_hp_cost = self.sukuna.max_hp * 0.50
                            can_survive_vow = self.sukuna.hp > (vow_hp_cost + 20)
                            
                            # 2. Tactical Benefit Checks
                            gojo_is_vulnerable = self.gojo.infinity <= 0 or self.gojo.technique_burnout > 0 or self.gojo.ce_exhausted
                            is_guaranteed_kill = self.gojo.hp < 150 and gojo_is_vulnerable # Fuga will definitively end it
                            
                            # 3. Decision
                            # Pop Fuga IF he can survive it AND (Gojo is vulnerable to it OR it's a guaranteed kill OR Sukuna is very healthy and wants to strip Gojo's CE)
                            if can_survive_vow and (gojo_is_vulnerable or is_guaranteed_kill or self.sukuna.hp > self.sukuna.max_hp * 0.7):
                                self.sukuna.fuga_charge = 120
                    
                    if getattr(self.sukuna, "world_slash_charge", 0) > 0:
                        self.sukuna.world_slash_charge -= 1
                        if self.sukuna.world_slash_charge == 1:
                            # Speed reduced to 55 to provide a tight 5-frame dodge window across mid-range!
                            self.projectiles.append(Projectile(self.sukuna.rect.centerx, self.sukuna.rect.centery, self.gojo.rect.centerx, self.gojo.rect.centery, 55, BLACK, size_mult=12.0, type="world_slash"))
                            ws_cost = 80 * self.sukuna.cost_mult
                            self.sukuna.energy = max(0, self.sukuna.energy - ws_cost)
                            self.sukuna.world_slash_cd = 1800 # 30 seconds cooldown
                            self.shake_timer = 40 # Double screen shake!

                    if self.sukuna.fuga_charge > 0:
                        self.sukuna.fuga_charge -= 1
                        if self.sukuna.fuga_charge == 1:
                            # SCALED VFX: size_mult increased to 5.8 to accurately reflect the 350-radius blast zone!
                            self.projectiles.append(Projectile(self.sukuna.rect.centerx, self.sukuna.rect.centery, self.gojo.rect.centerx, self.gojo.rect.centery, 28, (255, 100, 0), size_mult=5.8, type="fuga_arrow"))
                            
                            # --- FIXED: Now matches Purple's 195 CE cost! ---
                            fuga_cost = 195 * self.sukuna.cost_mult
                            self.sukuna.energy = max(0, self.sukuna.energy - fuga_cost)
                            
                            # --- NEW BINDING VOW: Costs 50% Max HP! ---
                            vow_hp_cost = self.sukuna.max_hp * 0.50
                            self.sukuna.hp -= vow_hp_cost
                            self.shake_timer = 35 # Increased screen shake for the massive offering!
                            for _ in range(30): # Spawns a massive burst of blood from Sukuna for the vow
                                bx, by = self.sukuna.rect.center
                                self.blood_particles.append([bx, by, random.uniform(-8, 8), random.uniform(-10, 0), 50, random.randint(4, 7)])
                            
                            # --- ANNOUNCEMENT UPGRADE ---
                            self.maho_announcements.append({"text": "SUKUNA VOW: 50% HP OFFERED FOR FUGA!", "timer": 120})
                            
                            self.sukuna.fuga_cd = 720
                            self.sukuna.tech_hits = 0

                    # --- NEW: PRIORITY 1 - TACTICAL HOLD DECISION ---
                    # We evaluate this REGARDLESS of is_amp because Sukuna forces DA on when Infinity is active!
                    if self.sukuna.technique_burnout == 0 and not fuga_priority and self.gojo.grab_timer <= 0:
                        
                        if self.sukuna.rect.colliderect(self.gojo.rect) and self.sukuna.grab_cd <= 0:
                            is_burned_out = (self.gojo.domain_uses >= 5 and self.gojo.technique_burnout > 0)
                            has_infinity = self.gojo.infinity > 0 and self.gojo.energy > 0 and not is_burned_out
                            
                            if has_infinity:
                                # HOLD 1: Domain Amp Beatdown (Infinity is UP)
                                # THE FIX: Sukuna CANNOT bypass his Binding Vow penalty to grab Gojo!
                                is_da_locked_out = getattr(self.sukuna, "tactical_eval_timer", 0) > 0
                                
                                if self.sukuna.energy >= 15 * self.sukuna.cost_mult and not is_da_locked_out:
                                    self.sukuna.amp_duration = max(self.sukuna.amp_duration, 300) 
                                    is_amp = True
                                    
                                    self.gojo.grab_timer = 300
                                    self.gojo.grab_type = "amp_punch" 
                                    self.gojo.purple_charge = 0
                                    self.gojo.domain_charge = 0
                                    
                                    self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 80, "timer": 45, "text": "DOM AMP BEATDOWN!", "color": (255, 255, 0)})
                                    
                                    self.gojo.rect.centerx = self.sukuna.rect.centerx + (40 * self.sukuna.direction)
                                    self.gojo.rect.centery = self.sukuna.rect.centery
                                    
                                    self.sukuna.energy -= 15 * self.sukuna.cost_mult
                                    self.sukuna.grab_cd = 480 # 8 seconds cooldown
                            else:
                                # HOLD 2: Cleave Dismemberment (Infinity is DOWN)
                                if self.sukuna.energy >= 30 * self.sukuna.cost_mult and self.sukuna.cleave_cd <= 0: 
                                    self.sukuna.amp_duration = 0 
                                    is_amp = False
                                    
                                    self.gojo.grab_timer = 300
                                    self.gojo.grab_type = "cleave" 
                                    self.gojo.purple_charge = 0
                                    self.gojo.domain_charge = 0
                                    
                                    self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 80, "timer": 45, "text": "CLEAVE!", "color": RED})
                                    
                                    self.gojo.rect.centerx = self.sukuna.rect.centerx + (40 * self.sukuna.direction)
                                    self.gojo.rect.centery = self.sukuna.rect.centery
                                    
                                    # Spawn Visual Cleave strictly on Gojo
                                    p = Projectile(self.gojo.rect.centerx, self.gojo.rect.centery, self.gojo.rect.centerx, self.gojo.rect.centery, 1, RED, size_mult=4.0, type="cleave")
                                    p.vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 0.1
                                    p.lifetime = 300
                                    p.is_grab_cleave = True 
                                    self.projectiles.append(p)

                                    cleave_cost_1 = 15 * self.sukuna.cost_mult
                                    self.sukuna.energy -= cleave_cost_1
                                    self.sukuna.cleave_cd = 600 # Increased
                                    
                                    # 3. Apply Conceptual Attrition burst (The rest of the stun is purely CC for Fuga setup)
                                    if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                                        self.gojo.energy = max(0, self.gojo.energy - 0.5 * self.gojo.cost_mult) 
                                        self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 20)
                                    else:
                                        self.gojo.hp -= 120.0
                                        self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 20)
                                        self.shake_timer = 40
                                        
                                        for _ in range(50):
                                            bx, by = self.gojo.rect.center
                                            self.blood_particles.append([bx, by, random.uniform(-10, 10), random.uniform(-10, 10), 60, random.randint(4, 8)])

                                    cleave_cost_2 = 15 * self.sukuna.cost_mult
                                    self.sukuna.energy -= cleave_cost_2
                                    self.sukuna.cleave_cd = 600 # Increased
                                    self.sukuna.grab_cd = 600

                    # --- PRIORITY 2: RANGED SLASHES ---
                    # LORE ACCURACY: Expanded slash zones so he never stands completely still
                    # Slashes cannot be used while Domain Amplification is active (is_amp == True)
                    if not is_amp and self.sukuna.energy > 40 * self.sukuna.cost_mult and not fuga_priority and self.sukuna.technique_burnout == 0 and self.gojo.grab_timer <= 0:
                        
                        # Priority 2: The World Cutting Slash
                        if self.sukuna.world_slash_unlocked and self.sukuna.energy > 80 * self.sukuna.cost_mult and self.sukuna.world_slash_cd <= 0 and getattr(self.sukuna, "world_slash_charge", 0) <= 0:
                            self.sukuna.world_slash_charge = 120 
                            
                        # Priority 3: Standard Dismantle Spacing (Only if Infinity is down!)
                        elif dist > 180 and self.sukuna.dismantle_cd == 0 and not gojo_has_inf:
                            self.sukuna.slash_count = 6
                            self.sukuna.slash_type = "dismantle"
                            dismantle_cost = 10 * self.sukuna.cost_mult
                            self.sukuna.energy -= dismantle_cost
                            self.sukuna.dismantle_cd = 40
                            
                        # Priority 4: If Infinity is UP and dist > 180, rely on DA punch rush instead of slashes!
                        elif dist > 180 and gojo_has_inf and self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20:
                            self.sukuna.direction = 1 if self.sukuna.rect.x < self.gojo.rect.x else -1
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 40

                    if self.sukuna.slash_count > 0 and self.sukuna.slash_type != "cleave": # Add this check
                        if self.sukuna.slash_delay <= 0:
                            if self.sukuna.slash_type == "world_slash":
                                self.sukuna.slash_count -= 1 # Handled by charge logic instead
                            else:
                                offset_y = (self.sukuna.slash_count - 2.5) * 45
                                size = 2.5 if self.sukuna.slash_type == "dismantle" else 4.2
                                self.projectiles.append(Projectile(self.sukuna.rect.centerx, self.sukuna.rect.centery + offset_y, self.gojo.rect.centerx, self.gojo.rect.centery, 110, RED, size_mult=size, type=self.sukuna.slash_type))
                                self.sukuna.slash_count -= 1
                                self.sukuna.slash_delay = 2 
                        else:
                            self.sukuna.slash_delay -= 1

                    if dist < 120 and self.sukuna.attack_cooldown <= 90 and not fuga_priority:
                        if self.sukuna.attack_cooldown == 0: 
                            self.sukuna.punch_timer = 20 
                            self.sukuna.punch_count += 1
                            melee_dmg = 7.5
                            
                            # --- CE IMBUE TO PUNCHES ---
                            imbue_cost = 2.0 * self.sukuna.cost_mult
                            if self.sukuna.energy >= imbue_cost:
                                self.sukuna.energy -= imbue_cost
                                melee_dmg *= 1.6 # CE Imbue Damage Boost!
                            
                            # Black Flash Trigger Logic (Base: 0.05-0.1%, Zone: 5-10%)
                            if self.sukuna.potential_timer > 0:
                                bf_chance = random.uniform(0.05, 0.10) # 5% to 10% (The Zone)
                            else:
                                bf_chance = random.uniform(0.0005, 0.001) # SIGNIFICANTLY LOWERED: 0.05% to 0.1%
                                
                            if random.random() < bf_chance:
                                melee_dmg *= math.pow(2.5, 2.5) 
                                self.sukuna.black_flash_timer = 20
                                self.sukuna.potential_timer = 600 # 10s duration
                                self.shake_timer = 15
                                
                                # --- FIXED: Sukuna Black Flash fully restores CE pool! ---
                                self.sukuna.energy = self.sukuna.max_energy 
                                
                                self.bf_words.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 60, "timer": 45})
                                
                            if is_amp:
                                # LORE ACCURACY: Domain Amplification Bypass ignores Infinity.
                                # CE Imbue still buffs damage since DA doesn't stop CE output!
                                if not self.gojo.is_dodging: 
                                    actual_dmg = melee_dmg
                                    # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                                    if self.gojo.energy > 0:
                                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                        mitigated_dmg = actual_dmg * (1.0 - reduction_mult)
                                        actual_dmg *= reduction_mult
                                        # Six Eyes Efficiency: 1 CE per 1 HP saved
                                        self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                        
                                    self.gojo.hp -= actual_dmg
                                    
                                    # Spawn Punch Hit Sparks
                                    spark_color = (255, 0, 0) if self.sukuna.black_flash_timer > 0 else RED
                                    for _ in range(12):
                                        self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-15, 15), self.gojo.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), spark_color])
                                        
                                    # --- NEW: KNOCKBACK ---
                                    kb_dir = 1 if self.gojo.rect.centerx > self.sukuna.rect.centerx else -1
                                    self.gojo.rect.x += kb_dir * 15
                            else:
                                if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                                    # LORE FIX: Infinity blocks seamlessly and efficiently using only 0.5 CE
                                    self.gojo.energy = max(0, self.gojo.energy - 0.5 * self.gojo.cost_mult)
                                    # --- NEW: SLIGHT KNOCKBACK FOR BLOCKED HIT ---
                                    kb_dir = 1 if self.gojo.rect.centerx > self.sukuna.rect.centerx else -1
                                    self.gojo.rect.x += kb_dir * 5
                                else:
                                    if not self.gojo.is_dodging: 
                                        actual_dmg = melee_dmg
                                        # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                                        if self.gojo.energy > 0:
                                            reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                            mitigated_dmg = actual_dmg * (1.0 - reduction_mult)
                                            actual_dmg *= reduction_mult
                                            # Six Eyes Efficiency: 1 CE per 1 HP saved
                                            self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                            
                                        self.gojo.hp -= actual_dmg 
                                        
                                        # Spawn Punch Hit Sparks
                                        spark_color = (255, 0, 0) if self.sukuna.black_flash_timer > 0 else RED
                                        for _ in range(12):
                                            self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-15, 15), self.gojo.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), spark_color])
                                            
                                        # --- NEW: KNOCKBACK ---
                                        kb_dir = 1 if self.gojo.rect.centerx > self.sukuna.rect.centerx else -1
                                        self.gojo.rect.x += kb_dir * 15
                            # Spams punches more than twice as fast (12 frames instead of 30) when exhausted to fish for a Black Flash!
                            self.sukuna.attack_cooldown = 12 

                    purple_active = any(p.type == "purple_orb" for p in self.projectiles)
                    if (purple_active or self.gojo.purple_charge > 0) and self.sukuna.on_ground:
                        if random.random() < 0.15: self.sukuna.jump()

                    # LORE ACCURACY: If Sukuna drops below 50% HP and hasn't unlocked the World Slash yet, bring out Big Raga!
                    # NEW CONDITION: Sukuna will wait until Gojo's Domain Expansion completely ends so Mahoraga doesn't instantly die paralyzed!
                    if self.sukuna.hp < (self.sukuna.max_hp * 0.5) and self.mahoraga is None and not self.sukuna.world_slash_unlocked and self.gojo.domain_cd > 0 and getattr(self, "clash_decision_timer", 0) == 0 and self.gojo.domain_charge == 0 and self.sukuna.domain_charge == 0 and not self.gojo.domain_active:
                        if getattr(self.sukuna, "mahoraga_lockout", 0) <= 0:
                            self.mahoraga_summon_timer = 210
                        
                    # NEW TACTIC: If Megumi's soul has fully adapted to Unlimited Void, instantly summon Mahoraga to shatter it!
                    if self.mahoraga is None and self.sukuna.adaptation["void"] <= 0.0 and self.mahoraga_summon_timer <= 0:
                        if getattr(self.sukuna, "mahoraga_lockout", 0) <= 0:
                            self.mahoraga_summon_timer = 210

                # Sukuna Domain Execution Timer
                if self.sukuna.domain_charge > 0:
                    self.sukuna.domain_charge -= 1
                    if self.sukuna.domain_charge == 1:
                        self.sukuna.domain_active = True
                        self.sukuna.domain_timer = 400
                        self.sukuna.domain_cd = 3000
                        self.shake_timer = 30

                # --- DOMAIN SHRINK LOGIC ---
                if self.gojo.domain_active and getattr(self.gojo, "domain_shrunk", False):
                    if not hasattr(self.gojo, "domain_center_x"):
                        safe_pad_x = 750
                        safe_pad_y = 450
                        self.gojo.domain_center_x = max(safe_pad_x, min(WORLD_WIDTH - safe_pad_x, self.gojo.rect.centerx))
                        self.gojo.domain_center_y = max(safe_pad_y, min(WORLD_HEIGHT - safe_pad_y, self.gojo.rect.centery))
                else:
                    self.gojo.domain_shrunk = False
                    if hasattr(self.gojo, "domain_center_x"):
                        del self.gojo.domain_center_x
                        del self.gojo.domain_center_y

                # === CIRCULAR DOMAIN PHYSICS ===
                # This pushes fighters back if they try to leave the circular boundary
                if self.gojo.domain_active and getattr(self.gojo, "domain_shrunk", False) and hasattr(self.gojo, "domain_center_x"):
                    cx = self.gojo.domain_center_x
                    cy = self.gojo.domain_center_y
                    radius = 400
                    
                    for f in [self.gojo, self.sukuna]:
                        if f and f.hp > 0:
                            dx = f.rect.centerx - cx
                            dy = f.rect.centery - cy
                            dist = math.hypot(dx, dy)
                            
                            if dist > radius - 35:   # keep fighters nicely inside the circle
                                if dist > 0:
                                    push = (radius - 35 - dist) * 0.8   # stronger push
                                    f.rect.x += (dx / dist) * push
                                    f.rect.y += (dy / dist) * push       

                # --- CINEMATIC TIME STOP ---
                # Check if anyone is currently charging their Domain
                is_cinematic = self.gojo.domain_charge > 0 or self.sukuna.domain_charge > 0 or getattr(self, "clash_decision_timer", 0) > 0
                active_fighters = [self.gojo, self.sukuna]
                if self.mahoraga: active_fighters.append(self.mahoraga)
                
                if is_cinematic:
                    self.gojo.vel_y = 0
                    self.sukuna.vel_y = 0
                    if self.mahoraga: self.mahoraga.vel_y = 0

                    for f in active_fighters:
                        if f is None: continue
                        f.prev_energy = f.energy # Capture before change
                        
                        # REGEN LOGIC
                        base_regen = 25.0 if f.name == "Gojo" else 0.8 if f.name == "Mahoraga" else 1.0 # SIX EYES REGEN
                        regen_mult = 1.2 if f.potential_timer > 0 else 1.0
                        
                        # --- CE EXHAUSTION LOGIC (During Cinematic Stop) ---
                        if f.energy <= 0.5:
                            f.ce_exhausted = True
                            if f.name == "Gojo":
                                f.infinity = 0
                        if f.ce_exhausted:
                            if f.name == "Sukuna":
                                regen_mult *= 0.8
                                recovery_thresh = 80
                            else:
                                regen_mult *= 0.4
                                recovery_thresh = 420 if f.name == "Gojo" else 30 # Updated to 420
                            if f.energy >= recovery_thresh:
                                f.ce_exhausted = False
                                
                        f.energy = min(f.max_energy, f.energy + base_regen * regen_mult)
                        
                            
                        # INFINITY REGEN (Gojo only)
                        if f.name == "Gojo" and f.infinity < f.max_infinity and f.technique_burnout == 0:
                            inf_cost = 0.1 * f.cost_mult
                            if f.energy >= inf_cost:
                                f.prev_energy = f.energy
                                f.infinity = min(f.max_infinity, f.infinity + 3.5)
                                f.energy -= inf_cost                    
                else:
                    # Normal Physics Loop
                    for f in active_fighters:
                        if f: f.prev_energy = f.energy
                    
                    # --- NEW: CONTINUOUS GRAB DAMAGE & DRAGGING ---
                    if self.sukuna.grab_timer > 0 and getattr(self.sukuna, "grab_type", "") == "gojo_beatdown":
                        
                        # --- TACTICAL AI: SUKUNA'S BEATDOWN COUNTER & ESCAPE ---
                        escaped = False
                        # Sukuna has a small chance each frame to process a counter-attack, making it feel organic rather than instant.
                        if self.sukuna.attack_cooldown <= 0 and random.random() < 0.08:
                            is_burned_out = (self.gojo.domain_uses >= 5 and self.gojo.technique_burnout > 0)
                            has_infinity = self.gojo.infinity > 0 and self.gojo.energy > 0 and not is_burned_out
                            is_da_locked_out = getattr(self.sukuna, "tactical_eval_timer", 0) > 0
                            
                            can_da_counter = has_infinity and self.sukuna.grab_cd <= 0 and self.sukuna.energy >= 15 * self.sukuna.cost_mult and not is_da_locked_out
                            can_cleave_counter = not has_infinity and self.sukuna.grab_cd <= 0 and self.sukuna.energy >= 30 * self.sukuna.cost_mult and self.sukuna.cleave_cd <= 0
                            can_da_escape = (self.sukuna.amp_cd <= 0 or self.sukuna.amp_duration > 0) and self.sukuna.energy >= 10 * self.sukuna.cost_mult and not is_da_locked_out

                            # 1. The Counter-Beatdown
                            if can_da_counter or can_cleave_counter:
                                self.sukuna.grab_timer = 0 # Break Gojo's hold
                                self.gojo.grab_timer = 300 # Take control of the duration!
                                self.gojo.purple_charge = 0
                                self.gojo.domain_charge = 0
                                self.sukuna.attack_cooldown = 30
                                escaped = True
                                
                                if can_da_counter:
                                    self.gojo.grab_type = "amp_punch"
                                    self.sukuna.amp_duration = max(self.sukuna.amp_duration, 300)
                                    self.sukuna.energy -= 15 * self.sukuna.cost_mult
                                    self.sukuna.grab_cd = 480
                                    self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 80, "timer": 45, "text": "COUNTER: DA BEATDOWN!", "color": (255, 255, 0)})
                                else:
                                    self.gojo.grab_type = "cleave"
                                    self.sukuna.amp_duration = 0
                                    self.sukuna.energy -= 30 * self.sukuna.cost_mult
                                    self.sukuna.cleave_cd = 600
                                    self.sukuna.grab_cd = 600
                                    self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 80, "timer": 45, "text": "COUNTER: CLEAVE!", "color": RED})
                                    
                                    # Visual Cleave setup
                                    p = Projectile(self.gojo.rect.centerx, self.gojo.rect.centery, self.gojo.rect.centerx, self.gojo.rect.centery, 1, RED, size_mult=4.0, type="cleave")
                                    p.vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 0.1
                                    p.lifetime = 300
                                    p.is_grab_cleave = True 
                                    self.projectiles.append(p)
                                    
                            # 2. The DA Burst Escape (If countering is unavailable or unwise)
                            elif can_da_escape and self.sukuna.hp < self.sukuna.max_hp * 0.65:
                                self.sukuna.grab_timer = 0
                                self.sukuna.amp_duration = max(self.sukuna.amp_duration, 60)
                                self.sukuna.energy -= 10 * self.sukuna.cost_mult
                                self.sukuna.attack_cooldown = 20
                                escaped = True
                                
                                kb_dir = 1 if self.sukuna.rect.centerx > self.gojo.rect.centerx else -1
                                self.sukuna.rect.x += kb_dir * 180
                                self.gojo.rect.x -= kb_dir * 180
                                self.shake_timer = 15
                                self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 80, "timer": 45, "text": "DA BURST ESCAPE!", "color": WHITE})
                                
                        if not escaped:
                            # Gojo locks Sukuna in place and unleashes a rapid melee beatdown!
                            self.sukuna.rect.centerx = self.gojo.rect.centerx + (40 * self.gojo.direction)
                            self.sukuna.rect.centery = self.gojo.rect.centery
                            
                            beatdown_dmg = 1.2
                            
                            # CE Imbue for Gojo's beatdown punches
                        imbue_cost = 2.0 * self.gojo.cost_mult
                        if self.gojo.energy >= imbue_cost:
                            self.gojo.energy -= imbue_cost
                            beatdown_dmg *= 1.6
                            
                        # Sukuna's Reinforcement Defense
                        if self.sukuna.energy > 0:
                            reduction_mult = random.uniform(0.15, 0.35)
                            mitigated_dmg = beatdown_dmg * (1.0 - reduction_mult)
                            beatdown_dmg *= reduction_mult
                            self.sukuna.energy = max(0, self.sukuna.energy - (mitigated_dmg * 2.0) * self.sukuna.cost_mult)
                            
                        self.sukuna.hp -= beatdown_dmg
                        self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + beatdown_dmg)
                        
                        # Visuals: Flurry of fast punches
                        if self.sukuna.grab_timer % 6 == 0:
                            self.shake_timer = 3
                            spark_color = WHITE if random.random() < 0.5 else BLUE
                            for _ in range(6):
                                self.hit_sparks.append([self.sukuna.rect.centerx + random.randint(-20, 20), self.sukuna.rect.centery + random.randint(-30, 30), random.uniform(-10, 10), random.uniform(-10, 10), random.randint(15, 30), spark_color])

                    if self.gojo.grab_timer > 0:
                        # Force Gojo to follow Sukuna's hand, dragging him across the map
                        self.gojo.rect.centerx = self.sukuna.rect.centerx + (40 * self.sukuna.direction)
                        self.gojo.rect.centery = self.sukuna.rect.centery
                        
                        # Identify which hold is currently active
                        grab_type = getattr(self.gojo, "grab_type", "cleave")
                        
                        if grab_type == "amp_punch":
                            # LORE MECHANIC: Domain Amplification neutralizes Infinity.
                            # Sukuna violently pummels Gojo. Damage comes strictly from base + CE Imbue!
                            self.sukuna.amp_duration = max(self.sukuna.amp_duration, 10) # Ensure DA stays locked ON
                            
                            beatdown_dmg = 0.2
                            
                            # --- CE IMBUE FOR BEATDOWN PUNCHES ---
                            imbue_cost = 2.0 * self.sukuna.cost_mult
                            if self.sukuna.energy >= imbue_cost:
                                self.sukuna.energy -= imbue_cost
                                beatdown_dmg *= 1.6 # CE Imbue Damage Boost!
                                
                            # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                            if self.gojo.energy > 0:
                                reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                mitigated_dmg = beatdown_dmg * (1.0 - reduction_mult)
                                beatdown_dmg *= reduction_mult
                                self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE

                            # Deal steady melee damage directly to HP
                            self.gojo.hp -= beatdown_dmg 
                            self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + beatdown_dmg)
                            
                            # Visual: Rapid brutal punches and hit sparks!
                            if self.gojo.grab_timer % 8 == 0:
                                self.shake_timer = 4
                                spark_color = WHITE if random.random() < 0.5 else RED
                                for _ in range(5):
                                    self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-15, 15), self.gojo.rect.centery + random.randint(-20, 20), random.uniform(-8, 8), random.uniform(-8, 8), random.randint(15, 30), spark_color])
                                    
                        elif grab_type == "cleave":
                            # LORE MECHANIC: Infinity is down, but Gojo reinforces his body with CE!
                            cleave_dmg = 0.4
                            
                            # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                            if self.gojo.energy > 0:
                                reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                mitigated_dmg = cleave_dmg * (1.0 - reduction_mult)
                                cleave_dmg *= reduction_mult
                                self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                
                            self.gojo.hp -= cleave_dmg # Adds up to ~60-96 damage over 300 frames with CE, or 120 without
                            self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 0.5) 
                            
                            if self.gojo.grab_timer % 10 == 0:
                                self.shake_timer = 5
                                self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
                        
                        # LORE MECHANIC: Because Sukuna dropped DA, Infinity is active. 
                        # Cleave grinds against the spatial barrier, violently shredding Gojo's CE reserves!
                        if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                            self.gojo.energy = max(0, self.gojo.energy - 1.5 * self.gojo.cost_mult) 
                            self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 0.5)
                            
                            # Visual: Blue sparks where Cleave strikes the Infinity barrier
                            if random.random() < 0.3:
                                self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-20, 20), self.gojo.rect.centery + random.randint(-30, 30), random.uniform(-5, 5), random.uniform(-5, 5), random.randint(15, 25), INF_COLOR])
                        else:
                            # If Infinity drops (CE exhausted), Cleave directly targets flesh!
                            cleave_dmg = 0.4
                            
                            # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                            if self.gojo.energy > 0:
                                reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                mitigated_dmg = cleave_dmg * (1.0 - reduction_mult)
                                cleave_dmg *= reduction_mult
                                self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                
                            self.gojo.hp -= cleave_dmg 
                            self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 0.5) 
                            if self.gojo.grab_timer % 10 == 0:
                                self.shake_timer = 5
                                self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
                    
                    self.gojo.update_physics()
                    self.sukuna.update_physics()
                    if self.mahoraga and self.mahoraga.hp > 0: 
                        self.mahoraga.update_physics()
                        
                    # --- NEW: ANNOUNCE THE UV SURVIVAL VOW ---
                    if self.sukuna.is_paralyzed and self.sukuna.rct_timer > 0 and getattr(self.sukuna, "mahoraga_lockout", 0) > 1798:
                        if pygame.time.get_ticks() - getattr(self, "last_uv_vow", 0) > 5000:
                            self.maho_announcements.append({"text": "SUKUNA VOW: FORCED RCT IN UV! (MS 10s / MAHO 30s LOCKED)", "timer": 150})
                            self.last_uv_vow = pygame.time.get_ticks()
                    
                    # Log normal regen from update_physics
                    for f in active_fighters:
                        if f and f.energy != f.prev_energy:
                            change = f.energy - f.prev_energy
                            tag = "REGEN" if change > 0 else "DRAIN"
                                            
                # --- DOMAIN CLASH ARBITRATION ---
                gojo_can_clash = self.gojo.technique_burnout == 0 and self.gojo.infinity > 0 and self.gojo.energy >= 50

                if self.gojo.domain_active and self.sukuna.domain_active and gojo_can_clash:
                    clash_window = 20
                    
                    if getattr(self, "clash_decision_timer", 0) == 0 and not getattr(self, "clash_resolved", False):
                        self.clash_decision_timer = clash_window
                        self.clash_failed = False # NEW: Track if they mashed too early!

                    if getattr(self, "clash_decision_timer", 0) > 0:
                        self.clash_decision_timer -= 1
                        
                        # --- SWEET SPOT LOGIC ---
                        # The window is only open when the timer is between 1 and 5 frames remaining.
                        is_sweet_spot = 1 <= self.clash_decision_timer <= 5
                        
                        # Check inputs, but ONLY if they haven't already failed this clash!
                        if keys[pygame.K_z] and keys[pygame.K_v] and not getattr(self, "clash_failed", False):
                            if is_sweet_spot and not getattr(self.gojo, "domain_shrunk", False):
                                self.gojo.domain_shrunk = True
                                self.shake_timer = 20
                                self.popups.append({
                                    "x": self.gojo.rect.centerx, 
                                    "y": self.gojo.rect.centery - 100, 
                                    "timer": 60, 
                                    "text": "CRITICAL SHRINK!", 
                                    "color": (0, 255, 255) 
                                })
                            elif self.clash_decision_timer > 5: # <--- CHANGE THIS TO 5
                                # They pressed too early! Lock them out of the sweet spot for this clash.
                                self.clash_failed = True
                                self.popups.append({
                                    "x": self.gojo.rect.centerx, 
                                    "y": self.gojo.rect.centery - 50, 
                                    "timer": 30, 
                                    "text": "TOO EARLY!", 
                                    "color": RED
                                })

                        # Resolve the clash when the timer hits zero
                        if self.clash_decision_timer == 0:
                            self.clash_resolved = True
                            
                            # Power calculation logic
                            # Gojo gets a massive but RANDOM boost for shrinking the domain (no guaranteed win!)
                            # SCALED: Lowered the bonus by 1900 to compensate for his new 2100 CE pool!
                            shrink_bonus = random.randint(100, 1500) if getattr(self.gojo, "domain_shrunk", False) else 0
                            gojo_power = self.gojo.hp + self.gojo.energy + shrink_bonus
                            
                            # Sukuna's raw power, plus a tiny random variance to keep clashes unpredictable
                            sukuna_power = self.sukuna.hp + self.sukuna.energy + random.randint(0, 500)
                            
                            # --- NEW: SAVE POWERS FOR THE HUD ---
                            self.gojo_clash_power = int(gojo_power)
                            self.sukuna_clash_power = int(sukuna_power)
                            self.clash_power_timer = 120 # Keeps the numbers on the HUD for 2 seconds
                            
                            if gojo_power >= sukuna_power:
                                self.clash_winner = "GOJO WINS CLASH!"
                                self.sukuna.end_domain()
                                self.gojo.domain_shrunk = True # FIX: Force the visual shrink if he wins!
                            else: 
                                self.clash_winner = "SUKUNA WINS CLASH!"
                                self.gojo.end_domain()
                                self.gojo.domain_shrunk = False 
                                
                            self.clash_msg_timer = 90
                            self.shake_timer = 30
                else:
                    self.clash_resolved = False 
                    self.clash_decision_timer = 0
                    self.clash_failed = False

                if self.mahoraga and self.mahoraga.hp > 0:
                    self.mahoraga.update_physics()
                    if not self.mahoraga.is_paralyzed:
                        # --- RELENTLESS PROTECTION AI ---
                        ideal_x = self.gojo.rect.centerx # Default chase target
                        
                        # Find dangerous projectiles aimed at Sukuna
                        threats = [p for p in self.projectiles if p.type in ["blue_orb", "red_orb", "purple_orb"] and p.active]
                        if threats:
                            # Intercept the closest dangerous projectile
                            closest_threat = min(threats, key=lambda p: abs(p.pos.x - self.sukuna.rect.centerx))
                            if closest_threat.pos.x < self.sukuna.rect.centerx:
                                ideal_x = self.sukuna.rect.centerx - 70
                            else:
                                ideal_x = self.sukuna.rect.centerx + 70
                        elif abs(self.gojo.rect.centerx - self.sukuna.rect.centerx) < 8000:
                            # Gojo is getting close to Sukuna, rush him to attack!
                            ideal_x = self.gojo.rect.centerx
                        else:
                            # Stand guard actively between Sukuna and Gojo
                            if self.gojo.rect.centerx < self.sukuna.rect.centerx:
                                ideal_x = self.sukuna.rect.centerx - 120
                            else:
                                ideal_x = self.sukuna.rect.centerx + 120

                        # Move relentlessly towards the ideal protection position
                        if abs(self.mahoraga.rect.centerx - ideal_x) > 42:
                            self.mahoraga.rect.x += -42 if self.mahoraga.rect.centerx > ideal_x else 42
                        # ------------------------------------
                        
                        if abs(self.mahoraga.rect.centerx - self.gojo.rect.centerx) > 150:
                            # --- SMARTER PURSUIT: JUMP-DASH BLITZ COMBO ---
                            if self.mahoraga.dodge_cd == 0 and random.random() < 0.05:
                                self.mahoraga.direction = -1 if self.mahoraga.rect.x > self.gojo.rect.x else 1
                                self.mahoraga.dodge()
                                if self.mahoraga.on_ground:
                                    self.mahoraga.jump() # Combos dodge and jump to launch horizontally!
                                self.mahoraga.dodge_cd = 60
                            elif self.mahoraga.on_ground and random.random() < 0.025:
                                self.mahoraga.jump()

                        m_dist = abs(self.mahoraga.rect.centerx - self.gojo.rect.centerx)
                        if m_dist < 150:
                            # Complex phenomena: 5 turns to adapt (1250 pts)
                            # Limitation: If Sukuna uses Domain Amplification, it interrupts the process of Mahoraga adapting.
                            if self.sukuna.amp_duration <= 0:
                                self.mahoraga.trigger_adaptation("infinity", 1.5)
                                turns = self.mahoraga.adaptation_points["infinity"] / 250.0
                                self.mahoraga.adaptation["infinity"] = min(1.0, turns / 5.0)

                        if self.gojo.rect.colliderect(self.mahoraga.rect) and self.mahoraga.attack_cooldown == 0:
                            self.mahoraga.punch_timer = 20 
                            self.mahoraga.punch_count += 1
                            base_dmg = 4.5

                            # --- CE IMBUE TO PUNCHES ---
                            imbue_cost = 2.0 * self.mahoraga.cost_mult
                            if self.mahoraga.energy >= imbue_cost:
                                self.mahoraga.energy -= imbue_cost
                                base_dmg *= 1.6 # CE Imbue Damage Boost!

                            # Black Flash Trigger Logic 
                            # Mahoraga Scale (Base: 0.01%, Zone: 1-2%)
                            if self.mahoraga.potential_timer > 0:
                                bf_chance = random.uniform(0.01, 0.02) # 1% to 2% (The Zone)
                            else:
                                bf_chance = 0.0001 # SIGNIFICANTLY LOWERED: 0.01% flat base
                                
                            if random.random() < bf_chance:
                                base_dmg *= math.pow(2.5, 2.5)
                                self.mahoraga.black_flash_timer = 20
                                self.shake_timer = 15
                                
                                ce_recovery = self.mahoraga.max_energy * 0.20
                                self.mahoraga.energy = min(self.mahoraga.max_energy, self.mahoraga.energy + ce_recovery)
                                
                                self.bf_words.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 60, "timer": 45})
                            
                            if not self.gojo.is_dodging:
                                inf_adapt_ratio = self.mahoraga.adaptation["infinity"]
                                to_hp = base_dmg * inf_adapt_ratio
                                to_inf = base_dmg * (1.0 - inf_adapt_ratio)
                                
                                hit_connected = False
                                if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                                    self.gojo.infinity -= to_inf * 0.5 
                                    
                                    # --- GOJO'S CE REINFORCEMENT DEFENSE ---
                                    if self.gojo.energy > 0: 
                                        to_hp *= random.uniform(0.15, 0.35)
                                        self.gojo.energy -= (base_dmg * inf_adapt_ratio * 0.75) * 3.5 # Drain CE for block
                                    
                                    self.gojo.hp -= to_hp 
                                    if to_hp > 0: hit_connected = True
                                else:
                                    # --- GOJO'S CE REINFORCEMENT DEFENSE ---
                                    actual_dmg = base_dmg
                                    if self.gojo.energy > 0: 
                                        actual_dmg *= random.uniform(0.15, 0.35)
                                        self.gojo.energy -= (base_dmg * 0.75) * 3.5 # Drain CE for block
                                        
                                    self.gojo.hp -= actual_dmg
                                    hit_connected = True
                                    
                                if hit_connected:
                                    spark_color = (255, 0, 0) if self.mahoraga.black_flash_timer > 0 else MAHO_COLOR
                                    for _ in range(12):
                                        self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-15, 15), self.gojo.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), spark_color])
                                    
                                # --- NEW: MAHORAGA KNOCKBACK (Protecting Sukuna!) ---
                                kb_dir = 1 if self.gojo.rect.centerx > self.mahoraga.rect.centerx else -1
                                self.gojo.rect.x += kb_dir * 40
                                
                            self.mahoraga.attack_cooldown = 12
                            
                        # LORE ACCURACY: Mahoraga's intense passive regeneration
                        # 300 is 62.5% of his base 480 HP. This scales it dynamically!
                        if self.mahoraga.hp < (self.mahoraga.max_hp * 0.625) and self.mahoraga.energy > 5 * self.mahoraga.cost_mult and not self.mahoraga.ce_exhausted:
                            self.mahoraga.hp = min(self.mahoraga.max_hp, self.mahoraga.hp + 1.8) # Further increased for massive survivability
                            self.mahoraga.energy -= 1.0 * self.mahoraga.cost_mult
                            self.mahoraga.rct_timer = 5

                    pass # Adaptation tracking moved globally to support Megumi's soul

                # --- Universal Adaptation Announcements Tracking (Handles Sukuna's Secret Timer too) ---
                tracker_source = self.mahoraga if (self.mahoraga and self.mahoraga.hp > 0) else self.sukuna
                for key in tracker_source.adaptation:
                    val = tracker_source.adaptation[key]
                    prev = self.prev_adaptations[key]
                    is_adapted = val <= 0.0 if key != "infinity" else val >= 1.0
                    was_adapted = prev <= 0.0 if key != "infinity" else prev >= 1.0

                    if is_adapted and not was_adapted:
                        if key == "void" and (self.mahoraga is None or self.mahoraga.hp <= 0):
                            self.maho_announcements.append({"text": "MEGUMI'S SOUL ADAPTED TO UNLIMITED VOID!", "timer": 180})
                        else:
                            self.maho_announcements.append({"text": f"MAHORAGA HAS FULLY ADAPTED TO {key.upper()}!", "timer": 180})
                        
                        if key == "infinity" and not self.sukuna.world_slash_unlocked:
                            self.sukuna.world_slash_unlocked = True
                            self.maho_announcements.append({"text": "SUKUNA HAS ACQUIRED THE WORLD CUTTING SLASH!", "timer": 240})
                            
                    self.prev_adaptations[key] = val

                # --- World Slash Cooldown Announcement ---
                if self.sukuna.world_slash_cd == 0 and self.prev_world_slash_cd == 1:
                    self.maho_announcements.append({"text": "WORLD CUTTING SLASH IS READY!", "timer": 120})
                self.prev_world_slash_cd = self.sukuna.world_slash_cd

                # --- BURNOUT ANNOUNCEMENTS ---
                # Ensuring announcement happens strictly AFTER the domain duration drops!
                if not self.gojo.domain_active and self.gojo.technique_burnout > 0 and self.prev_gojo_burnout == 0:
                    # STRICT LIMIT: Only pop up every 5th domain use!
                    if self.gojo.domain_uses > 0 and self.gojo.domain_uses % 5 == 0:
                        self.maho_announcements.append({"text": "GOJO'S CURSED TECHNIQUE HAS BURNED OUT!", "timer": 90})
                        
                if not self.sukuna.domain_active and self.sukuna.technique_burnout > 0 and self.prev_sukuna_burnout == 0:
                    if self.sukuna.domain_uses > 0 and self.sukuna.domain_uses % 5 == 0:
                        self.maho_announcements.append({"text": "SUKUNA'S CURSED TECHNIQUE HAS BURNED OUT!", "timer": 90})
                
                self.prev_gojo_burnout = self.gojo.technique_burnout
                self.prev_sukuna_burnout = self.sukuna.technique_burnout        

                # --- DOMAIN EXPANSION EFFECTS & SIMPLE DOMAIN COUNTER ---
                # 1. Unlimited Void: Paralysis and Brain Damage (Constant CE/HP drain)
                if self.gojo.domain_active:
                    # --- THE PAYOFF: MAHORAGA INSTANT SHATTER ---
                    if self.mahoraga and self.mahoraga.hp > 0 and self.mahoraga.adaptation["void"] <= 0:
                        self.gojo.end_domain()
                        self.gojo.domain_cd = 3000
                        # THE FIX: Removed hardcoded 720 burnout! It now strictly obeys the 3-use rule in end_domain().
                        self.shake_timer = 30
                        # CHANGED: Now uses the central HUD announcement system instead of a popup
                        self.maho_announcements.append({"text": "MAHORAGA SHATTERED UNLIMITED VOID!", "timer": 180})
                        self.sukuna.is_paralyzed = False
                        self.mahoraga.is_paralyzed = False
                    else:
                        for enemy in [self.sukuna, self.mahoraga]:
                            if enemy and enemy.hp > 0:
                                # LORE: Gojo's Infinity prevents Unlimited Void from hitting him directly
                                is_touching_gojo = enemy.rect.colliderect(self.gojo.rect)
                                
                                # --- SMARTER SUKUNA AI: THE SACRIFICIAL GAMBIT ---
                                if enemy.name == "Sukuna" and getattr(enemy, "simple_domain_active", False) and not is_touching_gojo and self.mahoraga is None:
                                    
                                    # --- NEW: HOLLOW PURPLE THREAT ASSESSMENT ---
                                    # Sukuna checks if Gojo has Purple ready OR is dangerously close to unlocking it (800+ hits).
                                    # If Gojo is that close, paralyzing himself to tank UV is a massive risk!
                                    gojo_purple_danger = (self.gojo.tech_hits >= 800) and (self.gojo.purple_cd == 0) and (self.gojo.energy >= 195 * self.gojo.cost_mult)
                                    
                                    # Also verify there isn't one already flying or charging!
                                    purple_flying = any(p.type == "purple_orb" for p in self.projectiles)
                                    is_purple_threat = gojo_purple_danger or self.gojo.purple_charge > 0 or purple_flying
                                    
                                    # AI UPGRADE: Check if it's worth taking the brain damage based on domain uses left.
                                    # If Gojo has exhausted his 4 domains, there is less immediate pressure to adapt to UV.
                                    gojo_domains_exhausted = self.gojo.domain_uses >= 4
                                    
                                    # He will ONLY attempt the gambit if Purple is completely off the board and not close to ready!
                                    if not is_purple_threat:
                                        # LORE FIX: Increased by 50%! He now needs 1500 points to fully adapt. 
                                        # NEW TACTIC: He tanks it in chunks! As long as his HP is safely above 45%, he drops the shield!
                                        points_needed = 1500.0 - enemy.adaptation_points["void"]
                                        if points_needed > 0:
                                            # SMART TANKING: If Gojo has no domains left, don't sacrifice HP as willingly.
                                            min_hp_threshold = 0.65 if gojo_domains_exhausted else 0.45 
                                            
                                            if enemy.hp > (enemy.max_hp * min_hp_threshold): 
                                                enemy.simple_domain_active = False
                                                enemy.sd_was_active = False
                                                self.popups.append({"x": enemy.rect.centerx, "y": enemy.rect.centery - 100, "timer": 45, "text": "GAMBIT: TANKING UV!", "color": MAHO_COLOR})
                                if getattr(enemy, "simple_domain_active", False) and not is_touching_gojo:
                                    enemy.is_paralyzed = False # Protected by Simple Domain!
                                    # UV sure-hit continuously grinds down the Simple Domain
                                    enemy.sd_hits += 1
                                    if enemy.sd_hits >= enemy.max_sd_hits: # THE DYNAMIC BREAK POINT
                                        enemy.simple_domain_active = False
                                        enemy.sd_was_active = False
                                        enemy.sd_broken_timer = 120 # Reduced to 2 seconds cooldown
                                        self.popups.append({"x": enemy.rect.centerx, "y": enemy.rect.centery - 100, "timer": 45, "text": "SD CRUMBLED!", "color": RED})
                                        self.shake_timer = 15
                                        enemy.is_paralyzed = True
                                elif is_touching_gojo:
                                    enemy.is_paralyzed = False # Protected by Contact!
                                else:
                                    if enemy.name == "Mahoraga" and enemy.adaptation["void"] <= 0:
                                        enemy.is_paralyzed = False # Fully adapted, ignores effects completely!
                                    else:
                                        enemy.is_paralyzed = True
                                        uv_dmg = 1.5 * (enemy.adaptation["void"] if enemy.name == "Mahoraga" else 1.0)
                                        enemy.hp -= uv_dmg
                                        
                                        # LORE: Without a barrier, the brain information overflow is 3x more taxing
                                        brain_drain = 4.5 if not getattr(enemy, "simple_domain_active", False) else 1.5
                                        enemy.energy = max(0, enemy.energy - brain_drain)

                                # --- THE PENALTY & SECRET TIMER (Sukuna Only) ---
                                if enemy.name == "Sukuna" and enemy.is_paralyzed:
                                    # The Penalty: Lose access to all active skills
                                    enemy.dismantle_cd = 2
                                    enemy.cleave_cd = 2
                                    enemy.amp_cd = 2
                                    enemy.amp_duration = 0
                                    enemy.sd_broken_timer = 2
                                    enemy.rct_timer = 0
                                    enemy.fuga_cd = 2
                                    enemy.attack_cooldown = 2
                                    
                                    # The Secret Timer: Megumi's Soul / Wheel triggers
                                    if self.mahoraga is None or self.mahoraga.hp <= 0:
                                        enemy.adapting_to = "void"
                                        enemy.adaptation_points["void"] += 2.0
                                        turns = enemy.adaptation_points["void"] / 250.0
                                        enemy.adaptation["void"] = max(0, 1.0 - min(1.0, turns / 6.0)) # Increased to 6 turns (1500 pts)

                                if enemy.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                    enemy.adapting_to = "void"
                                    enemy.adaptation_points["void"] += 2.0
                                    turns = enemy.adaptation_points["void"] / 250.0
                                    enemy.adaptation["void"] = max(0, 1.0 - min(1.0, turns / 6.0)) # Increased to 6 turns (1500 pts)
                else:
                    self.sukuna.is_paralyzed = False
                    if self.mahoraga: self.mahoraga.is_paralyzed = False
                
                if self.sukuna.domain_active and not self.sukuna.is_paralyzed:
                    # --- NEW: Rapidly auto-charge Fuga pool inside Domain! ---
                    self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2)
                    
                    # Relentless slashes spawned instantly around Gojo
                    if self.sukuna.domain_timer % 8 == 0:
                        self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2)
                        
                        # --- FIX: Spawn sure-hits directly ON Gojo with low speed so they can't clip through him! ---
                        sx = self.gojo.rect.centerx + random.randint(-40, 40)
                        sy = self.gojo.rect.centery + random.randint(-60, 60)
                        stype = "cleave" if abs(self.sukuna.rect.centerx - self.gojo.rect.centerx) < 150 else "dismantle"
                        
                        # Speed reduced to 5 so it persists for at least 1 frame inside the collision box
                        self.projectiles.append(Projectile(sx, sy, self.gojo.rect.centerx, self.gojo.rect.centery, 5, RED, size_mult=3.0, type=stype, is_sure_hit=True))

                # OPTIMIZATION: Use list comprehension for projectiles
                active_projectiles = []
                for p in self.projectiles:
                    # Make the grab visual explicitly track Gojo while he is held
                    if getattr(p, "is_grab_cleave", False):
                        if self.gojo.grab_timer > 0:
                            p.pos.x = self.gojo.rect.centerx
                            p.pos.y = self.gojo.rect.centery
                        else:
                            p.active = False # Kill it instantly when grab ends/goes on cooldown
                            
                    # BUG FIX: Remove sure-hit slashes if Sukuna's domain ends
                    if getattr(p, "is_sure_hit", False) and not self.sukuna.domain_active:
                        p.active = False
                            
                    p.update()
                    if not p.active:
                        continue
                        
                    # Recalculate target for projectiles to hit closest
                    p_target = min(enemies, key=lambda e: pygame.Vector2(e.rect.center).distance_to(p.pos))
                    
                    dist_to_orb = pygame.Vector2(p_target.rect.center).distance_to(p.pos)

                    if p.type == "blue_orb":
                        if dist_to_orb < 600:
                            # --- NEW: Mahoraga actively adapts to the pull force! ---
                            if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                p_target.trigger_adaptation("blue", 1.0)
                                turns = p_target.adaptation_points["blue"] / 250.0
                                p_target.adaptation["blue"] = max(0, 1.0 - min(1.0, turns / 4.0))

                            if not p_target.is_dodging:
                                # --- THE FIX: Absolute Pull Immunity for Mahoraga! ---
                                if p_target.name == "Mahoraga" and p_target.adaptation["blue"] <= 0:
                                    pull_factor = 0.0 # He is fully adapted, Blue cannot move him!
                                else:
                                    # Sukuna (or partially adapted Mahoraga) still gets pulled
                                    pull_factor = 0.85 * (p_target.adaptation["blue"] if p_target.name == "Mahoraga" else 1.0)
                                
                                # Only apply the movement if the pull factor is actively greater than 0
                                if pull_factor > 0:
                                    p_target.rect.x += (p.pos.x - p_target.rect.centerx) * pull_factor
                            
                            if dist_to_orb < 250:
                                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                    p_target.trigger_adaptation("blue", 2.0)
                                    turns = p_target.adaptation_points["blue"] / 250.0
                                    p_target.adaptation["blue"] = max(0, 1.0 - min(1.0, turns / 4.0))
                                    
                                orb_dmg = 1 * (p_target.adaptation["blue"] if p_target.name == "Mahoraga" else 1.0)
                                
                                if p_target.name == "Sukuna":
                                    if p_target.amp_duration > 0: orb_dmg *= 0.2 
                                    
                                    # --- NEW: 1:2 Final CE Drain based on Mitigation ---
                                    if p_target.energy > 0:
                                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                        mitigated_dmg = orb_dmg * (1.0 - reduction_mult) 
                                        
                                        orb_dmg *= reduction_mult 
                                        
                                        # 2 CE spent for every 1 HP saved
                                        p_target.energy = max(0, p_target.energy - (mitigated_dmg * 2.0) * p_target.cost_mult)
                                        
                                elif p_target.name == "Mahoraga":
                                    orb_dmg *= 0.75
                                    
                                if not p_target.is_dodging:
                                    p_target.hp -= orb_dmg
                                    if p_target.name in ["Sukuna", "Mahoraga"]: self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 1)
                        
                        # --- NEW: Blue Pulls Sukuna's Slashes ---
                        for slash in self.projectiles:
                            if slash.type in ["dismantle", "cleave"]:
                                dist = p.pos.distance_to(slash.pos)
                                if 0 < dist < 400:
                                    pull_dir = (p.pos - slash.pos).normalize()
                                    current_speed = slash.vel.length()
                                    
                                    pull_force = current_speed * 0.65 
                                    slash.vel += pull_dir * pull_force
                                    
                                    if slash.vel.length() > 0:
                                        slash.vel.scale_to_length(current_speed)

                    elif p.type == "red_orb":
                        if dist_to_orb < 600:
                            # --- NEW: Mahoraga actively adapts to the push force! ---
                            if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                p_target.trigger_adaptation("red", 1.0)
                                turns = p_target.adaptation_points["red"] / 250.0
                                p_target.adaptation["red"] = max(0, 1.0 - min(1.0, turns / 4.0))

                            if not p_target.is_dodging:
                                # --- THE FIX: Absolute Push Immunity for Mahoraga! ---
                                if p_target.name == "Mahoraga" and p_target.adaptation["red"] <= 0:
                                    push_factor = 0.0 # He is fully adapted, Red cannot move him!
                                else:
                                    # Sukuna (or partially adapted Mahoraga) still gets pushed
                                    push_factor = 1.60 * (p_target.adaptation["red"] if p_target.name == "Mahoraga" else 1.0)
                                
                                # Only apply the movement if the push factor is actively greater than 0
                                if push_factor > 0:
                                    p_target.rect.x -= (p.pos.x - p_target.rect.centerx) * push_factor
                            
                            if dist_to_orb < 250:
                                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                    p_target.trigger_adaptation("red", 2.0)
                                    turns = p_target.adaptation_points["red"] / 250.0
                                    p_target.adaptation["red"] = max(0, 1.0 - min(1.0, turns / 4.0))

                                orb_dmg = 1.5 * (p_target.adaptation["red"] if p_target.name == "Mahoraga" else 1.0)
                                
                                if p_target.name == "Sukuna":
                                    if p_target.amp_duration > 0: orb_dmg *= 0.3 
                                    
                                    # --- NEW: 1:2 Final CE Drain based on Mitigation ---
                                    if p_target.energy > 0:
                                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                        mitigated_dmg = orb_dmg * (1.0 - reduction_mult) 
                                        
                                        orb_dmg *= reduction_mult 
                                        
                                        # 2 CE spent for every 1 HP saved
                                        p_target.energy = max(0, p_target.energy - (mitigated_dmg * 2.0) * p_target.cost_mult)
                                        
                                elif p_target.name == "Mahoraga":
                                    orb_dmg *= 0.75
                                    
                                if not p_target.is_dodging:
                                    p_target.hp -= orb_dmg
                                    if p_target.name in ["Sukuna", "Mahoraga"]: self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 1)
                        
                        for slash in self.projectiles:
                            if slash.type in ["dismantle", "cleave"]:
                                dist = p.pos.distance_to(slash.pos)
                                if 0 < dist < 450: 
                                    push_dir = (slash.pos - p.pos).normalize()
                                    current_speed = slash.vel.length()
                                    
                                    push_force = current_speed * 0.85 
                                    slash.vel += push_dir * push_force
                                    
                                    if slash.vel.length() > 0:
                                        slash.vel.scale_to_length(current_speed)

                    elif p.type == "purple_orb":
                        dist_x = abs(p_target.rect.centerx - p.pos.x)
                        if dist_x < 180: # Must physically escape this radius
                            if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                p_target.trigger_adaptation("purple", 400.0)
                                turns = p_target.adaptation_points["purple"] / 250.0
                                p_target.adaptation["purple"] = max(0, 1.0 - min(1.0, turns / 5.0))

                            # Hollow Purple ignores I-frames (is_dodging is ignored here)
                            if dist_x < 80: # Direct hit: 100% MAX HEALTH
                                dmg_perc = 1.0
                            else: # Realistic hit: 100% MAX HEALTH
                                dmg_perc = 1.0
                                
                            purple_dmg = (p_target.max_hp * dmg_perc)
                            
                            if p_target.name == "Mahoraga":
                                purple_dmg *= p_target.adaptation["purple"] 
                            elif p_target.name == "Sukuna" and p_target.amp_duration > 0:
                                # DA partially absorbs Purple (40% reduction, less than Red/Blue because Purple is imaginary mass)
                                purple_dmg *= 0.6 
                            
                            # --- NEW: CE REINFORCEMENT DEFENSE FOR PURPLE ---
                            if p_target.energy > 0:
                                # They use their raw CE to tank the imaginary mass
                                reduction_mult = random.uniform(0.5, 0.8)
                                mitigated_dmg = purple_dmg * (1.0 - reduction_mult) 
                                
                                purple_dmg *= reduction_mult 
                                
                                # TAX: Hollow Purple obliterates CE! Costs a massive 8.5x CE per HP saved!
                                p_target.energy = max(0, p_target.energy - (mitigated_dmg * 8.5) * p_target.cost_mult)
                            
                            p_target.hp -= purple_dmg
                            p.active = False # Hit confirmed, remove projectile
                    
                    elif p.type == "fuga_arrow":
                        dist_x = abs(self.gojo.rect.centerx - p.pos.x)
                        dist_y = abs(self.gojo.rect.centery - p.pos.y)
                        
                        # --- CHANGED: Massively increased the blast radius from 180 to 350! ---
                        if dist_x < 350 and dist_y < 350: 
                            
                            # --- THE FIX: INFINITY CHECK MOVED TO THE TOP ---
                            # Infinity must be checked BEFORE physical CE reinforcement to prevent the double-tax bug!
                            if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                                # Infinity catches the nuke. Gojo takes NO physical HP damage, but the thermal energy shreds his CE!
                                # Adjusted drain to 80% of Max CE so it's devastating but doesn't instantly zero out a full bar.
                                fuga_ce_dmg = self.gojo.max_energy * 0.80 
                                self.gojo.energy = max(0, self.gojo.energy - fuga_ce_dmg)
                            else:
                                # Infinity is DOWN. The nuke hits his physical body!
                                fuga_hp_dmg = self.gojo.max_hp * 1.0
                                
                                # --- GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                                # He only braces for physical impact if Infinity fails!
                                if self.gojo.energy > 0: 
                                    reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                    mitigated_dmg = fuga_hp_dmg * (1.0 - reduction_mult)
                                    fuga_hp_dmg *= reduction_mult
                                    self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                
                                self.gojo.hp -= fuga_hp_dmg
                                
                            p.active = False # Hit confirmed, remove projectile
                    
                    # --- FIXED: LORE-ACCURATE SIMPLE DOMAIN ---
                    # Simple Domain ONLY neutralizes sure-hits. Manual slashes pass right through!
                    intercepted_by_sd = False
                    if self.gojo.simple_domain_active and getattr(p, "is_sure_hit", False):
                        dist_to_gojo = pygame.Vector2(self.gojo.rect.center).distance_to(p.pos)
                        if dist_to_gojo < 100: # Simple Domain Barrier Radius
                            p.active = False
                            intercepted_by_sd = True
                            
                            self.gojo.sd_hits += 1
                            if self.gojo.sd_hits >= self.gojo.max_sd_hits: # DYNAMIC BREAK POINT
                                self.gojo.simple_domain_active = False
                                self.gojo.sd_was_active = False
                                self.gojo.sd_broken_timer = 120 # 2 seconds cooldown
                                self.popups.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 100, "timer": 45, "text": "SD CRUMBLED!", "color": RED})
                                self.shake_timer = 15
                                
                    # --- FIXED: MASSIVE HITBOX SCALING ---
                    # Instead of checking just the 1x1 center pixel, we calculate a dynamic collision radius mapped perfectly to the size multiplier!
                    hit_radius = 50 * p.size_mult if p.type in ["dismantle", "cleave", "world_slash"] else 20
                    dist_to_gojo_center = pygame.Vector2(self.gojo.rect.center).distance_to(p.pos)
                    
                    # Collides if the center hits, OR if the radius overlaps Gojo's collision box (35 is half Gojo's width)
                    is_colliding = self.gojo.rect.collidepoint(p.pos) or dist_to_gojo_center < (hit_radius + 35)

                    # Only apply physical body damage if SD didn't intercept it
                    if not intercepted_by_sd and is_colliding and p.type in ["normal", "dismantle", "cleave", "world_slash"] and not getattr(p, "is_grab_cleave", False):
                        if not self.gojo.is_dodging:
                            
                            # 1. World Cutting Slash (Always damages HP!)
                            if p.type == "world_slash":
                                self.gojo.hp -= 200 
                                p.active = False
                                
                            # 2. Domain Expansion Sure-Hits (If SD is down)
                            elif getattr(p, "is_sure_hit", False):
                                proj_dmg = 80.0 if p.type == "cleave" else 32.0
                                # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                                if self.gojo.energy > 0: 
                                    reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                    mitigated_dmg = proj_dmg * (1.0 - reduction_mult)
                                    proj_dmg *= reduction_mult
                                    self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                
                                self.gojo.hp -= proj_dmg
                                p.active = False
                                self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
                                
                            # 3. Manual Slashes
                            else:
                                is_burned_out = (self.gojo.domain_uses >= 5 and self.gojo.technique_burnout > 0)
                                
                                if self.gojo.infinity > 0 and self.gojo.energy > 0 and not is_burned_out: 
                                    # --- CHANGED: Removed the tech_hits increase here! Slashes blocked by Infinity give NO Fuga progress. ---
                                    self.gojo.energy = max(0, self.gojo.energy - 0.5 * self.gojo.cost_mult) 
                                    p.active = False 
                                else: 
                                    # Direct HP hit also counts!
                                    self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2) 
                                    proj_dmg = 80.0 if p.type == "cleave" else 32.0
                                    # --- NEW: GOJO'S 1:1 CE REINFORCEMENT DEFENSE ---
                                    if self.gojo.energy > 0: 
                                        reduction_mult = random.uniform(0.15, 0.35) # BUFF: Takes only 15-35% damage
                                        mitigated_dmg = proj_dmg * (1.0 - reduction_mult)
                                        proj_dmg *= reduction_mult
                                        self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) # TAX: Costs 3.5x CE
                                    
                                    self.gojo.hp -= proj_dmg
                                    p.active = False
                                    self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
                    
                    if p.active:
                        active_projectiles.append(p)
                self.projectiles = active_projectiles

                # --- DESPERATION & LINKED DEATH LOGIC ---
                # When Sukuna is critically low on HP, he drops all pride to survive!
                if self.sukuna.hp <= (self.sukuna.max_hp * 0.24) and self.sukuna.hp > 0:
                    
                    # 1. BINDING VOW: EMERGENCY CE REINFORCEMENT
                    # He trades a colossal amount of CE to rapidly heal and shield his body up to 50% HP.
                    if self.sukuna.energy > 40 * self.sukuna.cost_mult and not self.sukuna.ce_exhausted:
                        self.sukuna.energy -= 12.0 * self.sukuna.cost_mult # Monstrous CE drain!
                        self.sukuna.hp = min((self.sukuna.max_hp * 0.5), self.sukuna.hp + 3.5) # Fast emergency recovery
                        self.sukuna.rct_timer = 5
                        
                        # --- ANNOUNCEMENT (Throttled to once every 4 seconds) ---
                        if pygame.time.get_ticks() - getattr(self, "last_desp_vow", 0) > 4000:
                            self.maho_announcements.append({"text": "SUKUNA VOW: MASSIVE CE BURNED FOR SURVIVAL!", "timer": 120})
                            self.last_desp_vow = pygame.time.get_ticks()
                    
                    # 2. DESPERATE DOMAIN EXPANSION: Ignore standard tactical pacing and instantly pop DE if he can!
                    # FIX: Added 'and self.mahoraga_summon_timer <= 0' to prevent overlapping animations
                    if self.sukuna.energy >= 200 * self.sukuna.cost_mult and self.sukuna.domain_cd == 0 and self.sukuna.technique_burnout == 0 and self.sukuna.domain_charge == 0 and not self.sukuna.domain_active and self.gojo.grab_timer <= 0 and self.mahoraga_summon_timer <= 0:
                        self.sukuna.domain_charge = 60
                        self.sukuna.energy -= 200 * self.sukuna.cost_mult
                        self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 100, "timer": 60, "text": "DESPERATE DOMAIN!", "color": RED})
                        
                    # 3. PHANTOM BLITZ EVASION 
                    # Instead of cowardly running, he zips furiously around the arena!
                    if self.gojo.grab_timer <= 0 and not self.gojo.domain_active and not self.sukuna.domain_active and self.mahoraga_summon_timer <= 0:
                        
                        # If he's far away, he darts back IN to maintain pressure, otherwise backs off slightly
                        if dist > 450:
                            run_dir = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                        else:
                            run_dir = 1 if self.sukuna.rect.x > self.gojo.rect.x else -1
                        
                        # Smart corner escape
                        if (self.sukuna.rect.left < 150 and run_dir == -1) or (self.sukuna.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                            run_dir *= -1
                            if self.sukuna.on_ground: self.sukuna.jump()
                        
                        # CE-Reinforced Speed
                        if self.sukuna.energy > 2.0 * self.sukuna.cost_mult and not self.sukuna.ce_exhausted:
                            self.sukuna.rect.x += 22 * run_dir
                            self.sukuna.energy -= 2.0 * self.sukuna.cost_mult
                        else:
                            self.sukuna.rect.x += 18 * run_dir 
                        
                        # Aggressive phantom dodges
                        if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20:
                            # 50% chance to furiously dash straight through Gojo if close enough!
                            if dist < 300 and random.random() < 0.5:
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                            else:
                                self.sukuna.direction = run_dir
                                
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 15 # Frenzied evasion

                # Actual Death Logic (Immortality completely removed!)
                if self.sukuna.hp <= 0:
                    self.sukuna.hp = 0
                    if self.mahoraga and self.mahoraga.hp > 0: 
                        self.mahoraga.hp = 0 # Mahoraga dies if Sukuna dies
                    self.game_over = True
                if self.gojo.hp <= 0: self.gojo.is_split, self.game_over = True, True

            # --- SUMMONING LOGIC ---
            if self.mahoraga_summon_timer > 0:
                self.mahoraga_summon_timer -= 1
                if self.mahoraga_summon_timer == 1:
                    self.mahoraga = Fighter(self.sukuna.rect.x - 100, WORLD_HEIGHT - 300, "Mahoraga", MAHO_COLOR)
                    self.mahoraga.hp = self.mahoraga.max_hp # Dynamic Initialization!
                    # NEW: Transfer the wheel's adaptation progress from Sukuna to Mahoraga!
                    self.mahoraga.adaptation_points = self.sukuna.adaptation_points.copy()
                    self.mahoraga.adaptation = self.sukuna.adaptation.copy()

            # --- SCREEN SHAKE ---
            display_offset = (0,0)
            if self.shake_timer > 0:
                self.shake_timer -= 1
                display_offset = (random.randint(-10, 10), random.randint(-10, 10))

            # --- EFFECTS GENERATORS ---
            # Detects if anyone lost HP this frame and sprays blood dynamically!
            for fighter in [self.gojo, self.sukuna, self.mahoraga]:
                if fighter is not None and fighter.hp < fighter.prev_hp:
                    damage = fighter.prev_hp - fighter.hp
                    
                    # --- NEW: INTERUPTABLE DOMAIN EXPANSION CASTING ANIMATION ---
                    if fighter.domain_charge > 0:
                        fighter.domain_charge = 0
                        
                        # --- NEW FIX: Apply a cooldown penalty so AI/Players can't instantly spam it again! ---
                        fighter.domain_cd = 300 # 5-second lockout from trying to cast Domain again
                        
                        self.popups.append({"x": fighter.rect.centerx, "y": fighter.rect.centery - 100, "timer": 45, "text": "DOMAIN INTERRUPTED!", "color": WHITE})
                    
                    # --- SUKUNA DOMAIN COLLAPSE MECHANIC ---
                    # Upgraded: Sukuna is extremely resilient. It now takes at least 60 damage 
                    # in a single frame to even risk breaking his concentration!
                    if fighter.name == "Sukuna" and damage >= 60: 
                        if fighter.domain_active:
                            # Lore Accuracy: 
                            # If damage is utterly catastrophic (like PB Red > 120), 75% chance his domain breaks.
                            # If it's a heavy hit (like PB Blue > 60), only a 30% chance it breaks.
                            break_chance = 0.75 if damage >= 120 else 0.30 
                            
                            # Roll the dice to see if he loses focus!
                            if random.random() < break_chance:
                                fighter.end_domain()
                                self.shake_timer = 20 # Screen shakes as domain shatters
                                # Let's add a visual popup so you know exactly when it breaks!
                                self.popups.append({"x": fighter.rect.centerx, "y": fighter.rect.centery - 100, "timer": 60, "text": "DOMAIN SHATTERED!", "color": WHITE})
                    
                    num_drops = min(int(damage * 1.5), 40) # Scale amount of blood to damage taken, capped at 40
                    for _ in range(num_drops):
                        bx = fighter.rect.centerx + random.randint(-30, 30)
                        by = fighter.rect.centery + random.randint(-50, 50)
                        vx = random.uniform(-6, 6)
                        vy = random.uniform(-10, -2)
                        self.blood_particles.append([bx, by, vx, vy, random.randint(20, 45), random.randint(2, 6)])
                if fighter is not None:
                    fighter.prev_hp = fighter.hp

            # --- RENDERING (World Surf handling) ---
            if not hasattr(self, "cached_shinjuku_bg"):
                self.cached_shinjuku_bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
                
                # DIMMER, HIGH-CONTRAST DUSK PALETTE
                M_SKY_TOP = (25, 27, 30)   # Deep, moody upper sky
                M_SKY_BOT = (160, 165, 170) # Glowing lower horizon
                M_WHITE = (245, 245, 250)   # Piercing light elements (Sun)
                M_LIGHT = (110, 115, 120)   # Dimmer highlights
                M_MID = (65, 68, 72)        # Heavy midtones
                M_DARK = (30, 32, 35)       # Deep shadows
                M_INK = (5, 5, 8)           # Almost pitch black for harsh contrast

                # 1. Sky Background (High-Contrast Gradient Curve)
                for y in range(WORLD_HEIGHT):
                    ratio = y / WORLD_HEIGHT
                    curve = ratio ** 1.8 
                    r = int(M_SKY_TOP[0] * (1 - curve) + M_SKY_BOT[0] * curve)
                    g = int(M_SKY_TOP[1] * (1 - curve) + M_SKY_BOT[1] * curve)
                    b = int(M_SKY_TOP[2] * (1 - curve) + M_SKY_BOT[2] * curve)
                    pygame.draw.line(self.cached_shinjuku_bg, (r, g, b), (0, y), (WORLD_WIDTH, y))
                
                # Setting Sun (Low on the horizon with layered glowing halos)
                sun_x, sun_y = WORLD_WIDTH - 700, WORLD_HEIGHT - 850
                pygame.draw.circle(self.cached_shinjuku_bg, (70, 75, 80), (sun_x, sun_y), 340) # Outer glow
                pygame.draw.circle(self.cached_shinjuku_bg, (110, 115, 120), (sun_x, sun_y), 310) # Mid glow
                pygame.draw.circle(self.cached_shinjuku_bg, (180, 185, 190), (sun_x, sun_y), 285) # Inner glow
                pygame.draw.circle(self.cached_shinjuku_bg, M_WHITE, (sun_x, sun_y), 250) # Core
                
                # 2. Distant Cityscape (Grid Buildings)
                # --- NEW: Far-Distant Filler Buildings (Smaller sizes to fill gaps) ---
                for bg_x in range(-100, WORLD_WIDTH, 140):
                    bg_x += random.randint(-30, 30)
                    bg_w = random.randint(100, 180)
                    bg_h = random.randint(400, 750) # Smaller heights
                    
                    # Drawing them slightly darker (M_MID) to push them into the background
                    pygame.draw.rect(self.cached_shinjuku_bg, M_MID, (bg_x, WORLD_HEIGHT - 100 - bg_h, bg_w, bg_h))
                    pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (bg_x, WORLD_HEIGHT - 100 - bg_h, bg_w, bg_h), 3)                  
                
                # Original Large Distant Buildings
                sun_x = WORLD_WIDTH - 700 # The horizontal center of your sun
                for bx in range(-100, WORLD_WIDTH, 380):
                    bx += random.randint(-50, 50)
                    bw = random.randint(200, 450)
                    
                    # --- NEW: Make huge buildings rare in front of the sun ---
                    # If the building's center is within 400 pixels of the sun's center...
                    if abs((bx + bw // 2) - sun_x) < 400:
                        if random.random() > 0.55: # % chance to SKIP drawing this building!
                            continue # Skip the rest of this loop and leave a gap for the sun
                    
                    bh = random.randint(800, 1500)
                    
                    pygame.draw.rect(self.cached_shinjuku_bg, M_LIGHT, (bx, WORLD_HEIGHT - 100 - bh, bw, bh))
                    pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (bx, WORLD_HEIGHT - 100 - bh, bw, bh), 4) 
                    
                    # Window Grid Lines
                    for wy in range(WORLD_HEIGHT - 100 - bh + 40, WORLD_HEIGHT - 100, 60):
                        pygame.draw.line(self.cached_shinjuku_bg, M_MID, (bx, wy), (bx + bw, wy), 3)
                    for wx in range(bx + 30, bx + bw - 10, 40):
                        pygame.draw.line(self.cached_shinjuku_bg, M_MID, (wx, WORLD_HEIGHT - 100 - bh), (wx, WORLD_HEIGHT - 100), 3)

                # 3. The Massive Overpass Bridge 
                bridge_y = WORLD_HEIGHT - 650
                bridge_h = 160
                
                pygame.draw.rect(self.cached_shinjuku_bg, M_MID, (0, bridge_y, WORLD_WIDTH, bridge_h))
                pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (0, bridge_y, WORLD_WIDTH, bridge_h), 6)
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, bridge_y + 40), (WORLD_WIDTH, bridge_y + 40), 4)
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, bridge_y + 50), (WORLD_WIDTH, bridge_y + 50), 10) 
                
                under_y = bridge_y + bridge_h
                pygame.draw.rect(self.cached_shinjuku_bg, M_DARK, (0, under_y, WORLD_WIDTH, 80))
                pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (0, under_y, WORLD_WIDTH, 80), 5)
                for gx in range(0, WORLD_WIDTH, 60):
                    pygame.draw.line(self.cached_shinjuku_bg, M_INK, (gx, under_y), (gx, under_y + 80), 5)
                    if gx % 180 == 0:
                        pygame.draw.line(self.cached_shinjuku_bg, M_INK, (gx, under_y), (gx + 120, under_y + 80), 8)

                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, bridge_y - 80), (WORLD_WIDTH, bridge_y - 80), 5)
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, bridge_y - 40), (WORLD_WIDTH, bridge_y - 40), 4)
                for rx in range(0, WORLD_WIDTH, 40):
                    pygame.draw.line(self.cached_shinjuku_bg, M_INK, (rx, bridge_y), (rx, bridge_y - 80), 3)

                # 4. Heavy Concrete Support Pillars 
                for px in range(200, WORLD_WIDTH, 1000):
                    pil_w = 180
                    
                    pygame.draw.polygon(self.cached_shinjuku_bg, M_MID, [(px - 30, under_y + 80), (px + pil_w + 30, under_y + 80), (px + pil_w, under_y + 180), (px, under_y + 180)])
                    pygame.draw.polygon(self.cached_shinjuku_bg, M_INK, [(px - 30, under_y + 80), (px + pil_w + 30, under_y + 80), (px + pil_w, under_y + 180), (px, under_y + 180)], 5)
                    
                    pygame.draw.rect(self.cached_shinjuku_bg, M_LIGHT, (px, under_y + 180, pil_w, WORLD_HEIGHT))
                    pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (px, under_y + 180, pil_w, WORLD_HEIGHT), 6)
                    
                    pygame.draw.rect(self.cached_shinjuku_bg, M_DARK, (px + pil_w - 50, under_y + 180, 50, WORLD_HEIGHT))
                    pygame.draw.line(self.cached_shinjuku_bg, M_INK, (px + pil_w - 50, under_y + 180), (px + pil_w - 50, WORLD_HEIGHT), 4)
                    
                    for dy in range(int(under_y) + 300, WORLD_HEIGHT - 100, 150):
                        pygame.draw.line(self.cached_shinjuku_bg, M_INK, (px, dy), (px + pil_w, dy), 3)
                
                # 5. Midground Silhouettes (Trees & Street details)
                for tx in range(150, WORLD_WIDTH, 400):
                    if random.random() > 0.45:
                        pygame.draw.circle(self.cached_shinjuku_bg, M_DARK, (tx, WORLD_HEIGHT - 250), 70)
                        pygame.draw.circle(self.cached_shinjuku_bg, M_INK, (tx, WORLD_HEIGHT - 250), 70, 3)
                        pygame.draw.circle(self.cached_shinjuku_bg, M_DARK, (tx - 40, WORLD_HEIGHT - 180), 50)
                        pygame.draw.circle(self.cached_shinjuku_bg, M_INK, (tx - 40, WORLD_HEIGHT - 180), 50, 3)
                        pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (tx - 10, WORLD_HEIGHT - 250, 20, 150))
                    
                    if random.random() > 0.1:
                        px = tx + 180
                        pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (px, WORLD_HEIGHT - 450, 8, 350))
                        pygame.draw.circle(self.cached_shinjuku_bg, M_INK, (px - 20, WORLD_HEIGHT - 400), 20)
                        pygame.draw.circle(self.cached_shinjuku_bg, (255, 220, 100), (px - 20, WORLD_HEIGHT - 400), 12)

                # 6. Street Level Foreground (Guardrails & Road)
                street_y = WORLD_HEIGHT - 100
                
                pygame.draw.rect(self.cached_shinjuku_bg, M_MID, (0, street_y - 40, WORLD_WIDTH, 40))
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 40), (WORLD_WIDTH, street_y - 40), 4)
                
                for gx in range(0, WORLD_WIDTH, 120):
                    pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (gx, street_y - 90, 15, 50))
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 80), (WORLD_WIDTH, street_y - 80), 8)
                pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 55), (WORLD_WIDTH, street_y - 55), 6)
            # --- DOMAIN BACKGROUND VISUALS ---
            is_shrunk = getattr(self.gojo, "domain_shrunk", False)

            # 1. Draw Shinjuku background first (city outside the sphere)
            if is_shrunk:
                self.world_surf.blit(self.cached_shinjuku_bg, (0, 0))

            if self.gojo.domain_active:
                if is_shrunk and hasattr(self.gojo, "domain_center_x"):
                    cx = self.gojo.domain_center_x
                    cy = self.gojo.domain_center_y
                    
                    # Create the small 800x800 surface ONLY ONCE when we first shrink
                    if self.cached_uv_bg_shrunk is None:
                        # 800x800 is enough for the circle (radius 400)
                        self.cached_uv_bg_shrunk = pygame.Surface((800, 800), pygame.SRCALPHA)
                        
                        # Center of the small surface
                        small_cx, small_cy = 400, 400
                        
                        self.cached_uv_bg_shrunk.fill((0, 0, 0, 0))
                        
                        # HARD OPAQUE VOID (covers everything inside the circle)
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (6, 6, 18, 255), (small_cx, small_cy), 405)
                        
                        # Accretion Disk + Black Hole
                        bh_x, bh_y = small_cx, small_cy - 30
                        scale = 0.67
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (80, 30, 160, 255), (bh_x, bh_y), int(520 * scale))
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (120, 60, 220, 255), (bh_x, bh_y), int(400 * scale))
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (200, 160, 255, 255), (bh_x, bh_y), int(290 * scale))
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (255, 255, 255, 255), (bh_x, bh_y), int(255 * scale))
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (0, 0, 0, 255), (bh_x, bh_y), int(230 * scale))
                        
                        # Bright glowing barrier ring
                        pygame.draw.circle(self.cached_uv_bg_shrunk, (220, 240, 255, 255), (small_cx, small_cy), 400, width=8)
                        
                        # Stars inside domain
                        for _ in range(90):
                            sx = small_cx + random.randint(-390, 390)
                            sy = small_cy + random.randint(-390, 390)
                            if math.hypot(sx - small_cx, sy - small_cy) < 395:
                                self.cached_uv_bg_shrunk.set_at((sx, sy), (255, 255, 255, 255))
                    
                    # Blit the small surface at the correct world position
                    blit_x = int(cx - 400)
                    blit_y = int(cy - 400)
                    self.world_surf.blit(self.cached_uv_bg_shrunk, (blit_x, blit_y))
                    
                else:
                    # Normal full-screen Unlimited Void (unchanged)
                    if self.cached_uv_bg is None:
                        self.cached_uv_bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
                        self.cached_uv_bg.fill((5, 5, 18, 235))
                        bh_x, bh_y = WORLD_WIDTH // 2, WORLD_HEIGHT // 2 - 300
                        scale = 1.0
                        pygame.draw.circle(self.cached_uv_bg, (100, 50, 200, 80), (bh_x, bh_y), int(500 * scale))
                        pygame.draw.circle(self.cached_uv_bg, (150, 100, 255, 120), (bh_x, bh_y), int(380 * scale))
                        pygame.draw.circle(self.cached_uv_bg, (220, 200, 255, 180), (bh_x, bh_y), int(280 * scale))
                        pygame.draw.circle(self.cached_uv_bg, (255, 255, 255, 255), (bh_x, bh_y), int(250 * scale))
                        pygame.draw.circle(self.cached_uv_bg, (0, 0, 0, 255), (bh_x, bh_y), int(240 * scale))
                    
                    self.world_surf.blit(self.cached_uv_bg, (0, 0))
                    
                    # Animated stars for full domain
                    self.world_surf.blit(self.star_layers[(pygame.time.get_ticks() // 200) % 3], (0, 0))

                # Fade effect
                if self.gojo.domain_timer > 380:
                    flash_alpha = int(((self.gojo.domain_timer - 380) / 20.0) * 180)
                    self.shared_flash_surf.fill((150, 200, 255, flash_alpha))
                    self.world_surf.blit(self.shared_flash_surf, (0, 0))
            
            elif self.sukuna.domain_active:
                if self.cached_ms_bg is None or self.cached_ms_shrunk != is_shrunk:
                    self.cached_ms_bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
                    
                    if is_shrunk and hasattr(self.gojo, "domain_center_x"):
                        cx, cy = self.gojo.domain_center_x, self.gojo.domain_center_y
                        
                        # Draw the circular sphere boundary for the Shrunken Domain (Malevolent Shrine version)
                        pygame.draw.circle(self.cached_ms_bg, (20, 5, 5, 240), (cx, cy), 400)
                        
                        # Lower the shrine so it sits on the bottom of the circle
                        shrine_x, shrine_y = cx, cy + 180
                        scale = 0.65
                        
                        # Shrunken Domain Barrier Outer Shell
                        pygame.draw.circle(self.cached_ms_bg, RED, (cx, cy), 400, 4)
                    else:
                        # Normal Full-Screen Domain
                        num_steps = 50
                        step_height = WORLD_HEIGHT / num_steps
                        for i in range(num_steps):
                            color_val = max(0, 120 - (i * 2.4)) 
                            alpha_val = min(255, 150 + (i * 2))
                            pygame.draw.rect(self.cached_ms_bg, (int(color_val), 0, 0, int(alpha_val)), (0, int(i * step_height), WORLD_WIDTH, int(step_height) + 2))
                        
                        shrine_x, shrine_y = WORLD_WIDTH // 2, WORLD_HEIGHT - 400 
                        scale = 1.0
                        
                    # Draw Blood Moon
                    pygame.draw.circle(self.cached_ms_bg, (150, 0, 0, 150), (shrine_x, int(shrine_y - 250 * scale)), int(450 * scale))
                    pygame.draw.circle(self.cached_ms_bg, (200, 30, 30, 200), (shrine_x, int(shrine_y - 250 * scale)), int(330 * scale))
                    pygame.draw.circle(self.cached_ms_bg, (255, 150, 150, 255), (shrine_x, int(shrine_y - 250 * scale)), int(240 * scale))
                    
                    # Draw the BIGGER Malevolent Shrine (Responsive to scale)
                    shrine_color = (15, 5, 5) 
                    
                    # Main base structure
                    pygame.draw.rect(self.cached_ms_bg, shrine_color, (shrine_x - int(270*scale), shrine_y - int(150*scale), int(540*scale), int(750*scale)))
                    
                    # Roof Tiers
                    pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(270*scale), shrine_y - int(240*scale)), (shrine_x - int(270*scale), shrine_y - int(240*scale))])
                    pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(180*scale), shrine_y - int(345*scale)), (shrine_x - int(180*scale), shrine_y - int(345*scale))])
                    pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(90*scale), shrine_y - int(450*scale)), (shrine_x - int(90*scale), shrine_y - int(450*scale))])
                    
                    # Gaping Open Mouth
                    mouth_rect = (shrine_x - int(165*scale), shrine_y - int(20*scale), int(330*scale), int(420*scale))
                    pygame.draw.ellipse(self.cached_ms_bg, BLACK, mouth_rect)
                    
                    teeth_color = (220, 220, 200)
                    
                    # Top teeth
                    for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                        pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(tx, shrine_y + int(25*scale)), (tx + int(35*scale), shrine_y + int(25*scale)), (tx + int(17*scale), shrine_y + int(115*scale))])
                    
                    # Bottom teeth
                    for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                        pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(tx, shrine_y + int(360*scale)), (tx + int(35*scale), shrine_y + int(360*scale)), (tx + int(17*scale), shrine_y + int(270*scale))])
                    
                    # Side teeth (left)
                    for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                        pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(shrine_x - int(150*scale), ty), (shrine_x - int(150*scale), ty + int(35*scale)), (shrine_x - int(75*scale), ty + int(17*scale))])
                    
                    # Side teeth (right)
                    for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                        pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(shrine_x + int(150*scale), ty), (shrine_x + int(150*scale), ty + int(35*scale)), (shrine_x + int(75*scale), ty + int(17*scale))])

                    self.cached_ms_shrunk = is_shrunk

                self.world_surf.blit(self.cached_ms_bg, (0, 0))
                
                # Initial Flash Effect
                if self.sukuna.domain_timer > 390: self.world_surf.fill((200, 0, 0))
            
            else:
                self.world_surf.blit(self.cached_shinjuku_bg, (0, 0))

            # --- DYNAMIC MANGA FLOOR (HIGH CONTRAST DUSK) ---
            if (self.gojo.domain_active and not is_shrunk) or (self.sukuna.domain_active and not is_shrunk):
                # Full screen domains overwrite the floor entirely
                pygame.draw.rect(self.world_surf, (15, 15, 25), (0, WORLD_HEIGHT - 100, WORLD_WIDTH, 100))
            else:
                # Normal Manga Street Ground (Also visible during Shrunken Domains!)
                pygame.draw.rect(self.world_surf, (80, 85, 90), (0, WORLD_HEIGHT - 100, WORLD_WIDTH, 100))
                pygame.draw.line(self.world_surf, (10, 10, 12), (0, WORLD_HEIGHT - 100), (WORLD_WIDTH, WORLD_HEIGHT - 100), 6)
                
                # Darker speed lines trailing off
                for fx in range(0, WORLD_WIDTH, 180):
                    pygame.draw.line(self.world_surf, (50, 50, 55), (fx, WORLD_HEIGHT - 80), (fx + 80, WORLD_HEIGHT - 80), 8)
            
            # Draw Black Flash Popups behind the characters
            active_bf_words = []
            for bw in self.bf_words:
                scale_f = 1.0 + (45 - bw["timer"]) * 0.05
                txt = self.get_text("BLACK FLASH!", BLACK)
                out = self.get_text("BLACK FLASH!", RED)
                
                s_out = pygame.transform.scale(out, (int(out.get_width() * scale_f), int(out.get_height() * scale_f)))
                s_txt = pygame.transform.scale(txt, (int(txt.get_width() * scale_f), int(txt.get_height() * scale_f)))
                
                # Outer shadow layout to emphasize text
                self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 - 2, bw["y"] - s_out.get_height()//2 - 2))
                self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 + 2, bw["y"] - s_out.get_height()//2 + 2))
                self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 - 2, bw["y"] - s_out.get_height()//2 + 2))
                self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 + 2, bw["y"] - s_out.get_height()//2 - 2))
                
                self.world_surf.blit(s_txt, (bw["x"] - s_txt.get_width()//2, bw["y"] - s_txt.get_height()//2))
                bw["timer"] -= 1
                if bw["timer"] > 0:
                    active_bf_words.append(bw)
            self.bf_words = active_bf_words
            
            # Draw Dodged Popups
            active_popups = []
            for p_up in self.popups:
                scale_f = 1.0 + (45 - p_up["timer"]) * 0.02
                txt = self.get_text(p_up["text"], BLACK)
                out = self.get_text(p_up["text"], p_up["color"])
                
                s_out = pygame.transform.scale(out, (int(out.get_width() * scale_f), int(out.get_height() * scale_f)))
                s_txt = pygame.transform.scale(txt, (int(txt.get_width() * scale_f), int(txt.get_height() * scale_f)))
                
                self.world_surf.blit(s_out, (p_up["x"] - s_out.get_width()//2 - 2, p_up["y"] - s_out.get_height()//2 - 2))
                self.world_surf.blit(s_out, (p_up["x"] - s_out.get_width()//2 + 2, p_up["y"] - s_out.get_height()//2 + 2))
                self.world_surf.blit(s_out, (p_up["x"] - s_out.get_width()//2 - 2, p_up["y"] - s_out.get_height()//2 + 2))
                self.world_surf.blit(s_out, (p_up["x"] - s_out.get_width()//2 + 2, p_up["y"] - s_out.get_height()//2 - 2))
                
                self.world_surf.blit(s_txt, (p_up["x"] - s_txt.get_width()//2, p_up["y"] - s_txt.get_height()//2))
                p_up["timer"] -= 1
                if p_up["timer"] > 0:
                    active_popups.append(p_up)
            self.popups = active_popups
                        
            
            if self.mahoraga_summon_timer > 0:
                self.shared_world_overlay.fill((0, 0, 0, 150))
                self.world_surf.blit(self.shared_world_overlay, (0,0))
                chants = ["With this treasure I summon...", "Eight-Handled Sword...", "Divergent Sila...", "Divine General Mahoraga!"]
                
                # Math updated for 84 frames. 84 / 4 parts = 21 frames per chant.
                idx = 3 - (self.mahoraga_summon_timer // 22) 
                idx = max(0, min(3, idx)) # Safety clamp so the list index never goes out of bounds
                
                txt = self.get_text(chants[idx], MAHO_COLOR)
                self.world_surf.blit(txt, (self.sukuna.rect.centerx - txt.get_width()//2, self.sukuna.rect.y - 120))
                self.sukuna.draw_detailed(self.world_surf, effect="summoning")
            else:
                # NEW: Secret Timer visual - Draw the wheel on Sukuna if he is stunned by UV and Mahoraga isn't out!
                eff = "summoning" if (self.sukuna.is_paralyzed and self.gojo.domain_active and (self.mahoraga is None or self.mahoraga.hp <= 0)) else None
                self.sukuna.draw_detailed(self.world_surf, effect=eff, is_amp=(self.sukuna.amp_duration > 0))
            
            self.gojo.draw_detailed(self.world_surf, punching)
            if self.mahoraga and self.mahoraga.hp > 0: self.mahoraga.draw_detailed(self.world_surf)

            for p in self.projectiles: p.draw(self.world_surf)

            # Draw Blood Particles (Optimized O(N) Loop)
            active_blood = []
            if len(self.blood_particles) > 150:
                self.blood_particles = self.blood_particles[-150:]
            for bp in self.blood_particles:
                bp[0] += bp[2] # x + vx
                bp[1] += bp[3] # y + vy
                bp[3] += GRAVITY # Apply gravity to blood
                bp[4] -= 1 # Reduce lifetime
                pygame.draw.circle(self.world_surf, BLOOD, (int(bp[0]), int(bp[1])), bp[5])
                if bp[4] > 0:
                    active_blood.append(bp)
            self.blood_particles = active_blood

            # Draw Hit Sparks (Optimized O(N) Loop)
            active_sparks = []
            if len(self.hit_sparks) > 150:
                self.hit_sparks = self.hit_sparks[-150:]
            for spark in self.hit_sparks:
                spark[0] += spark[2] # x + vx
                spark[1] += spark[3] # y + vy
                spark[4] -= 1 # lifetime
                pygame.draw.circle(self.world_surf, spark[5], (int(spark[0]), int(spark[1])), max(1, int(spark[4] * 0.25)))
                if spark[4] > 0:
                    active_sparks.append(spark)
            self.hit_sparks = active_sparks

            # --- CAMERA SYSTEM AND WORLD ZOOM ---
            active_f = [self.gojo, self.sukuna]
            if self.mahoraga and self.mahoraga.hp > 0: active_f.append(self.mahoraga)
            
            # 1. Determine Camera Focus and Zoom Target
            if self.gojo.domain_active and getattr(self.gojo, "domain_shrunk", False) and hasattr(self.gojo, "domain_center_x"):
                # Smoothly transition to the shrunken domain dimensions
                target_cam_height = 800.0
                target_cam_width = target_cam_height * (WIDTH / HEIGHT)
                
                # Aim for the exact safe center we calculated in the shrink logic
                target_center_x = self.gojo.domain_center_x
                target_center_y = self.gojo.domain_center_y
            else:
                # Standard Dynamic Camera Logic
                min_x = min(f.rect.centerx for f in active_f)
                max_x = max(f.rect.centerx for f in active_f)
                min_y = min(f.rect.centery for f in active_f)
                max_y = max(f.rect.centery for f in active_f)
                
                dist_x = max_x - min_x + 600
                dist_y = max_y - min_y + 400

                # Maintain 16:9 ratio for standard view
                if dist_x / WIDTH > dist_y / HEIGHT:
                    target_cam_width = max(WIDTH, dist_x)
                    target_cam_height = target_cam_width * (HEIGHT / WIDTH)
                else:
                    target_cam_height = max(HEIGHT, dist_y)
                    target_cam_width = target_cam_height * (WIDTH / HEIGHT)
                    
                target_center_x = (min_x + max_x) / 2
                target_center_y = (min_y + max_y) / 2
            
            # 2. Smoothly Interpolate Camera Dimensions & Position
            self.cam_width += (target_cam_width - self.cam_width) * 0.1 
            self.cam_height += (target_cam_height - self.cam_height) * 0.1
            
            # Initialize persistent camera tracking variables if they don't exist
            if not hasattr(self, "cam_x"):
                self.cam_x = target_center_x
                self.cam_y = target_center_y
                
            # Smoothly pan the camera towards the target center!
            self.cam_x += (target_center_x - self.cam_x) * 0.1
            self.cam_y += (target_center_y - self.cam_y) * 0.1
            
            # Boundary Clamping
            self.cam_width = max(WIDTH * 0.5, min(WORLD_WIDTH, self.cam_width))
            self.cam_height = max(HEIGHT * 0.5, min(WORLD_HEIGHT, self.cam_height))
            
            # 3. Calculate Viewport Position based on our smooth panning camera
            cam_left = self.cam_x - self.cam_width / 2
            cam_top = self.cam_y - self.cam_height / 2

            # Keep camera strictly inside world bounds to prevent crashing
            c_left = int(max(0, min(WORLD_WIDTH - self.cam_width, cam_left)))
            c_top = int(max(0, min(WORLD_HEIGHT - self.cam_height, cam_top)))
            c_width = int(self.cam_width)
            c_height = int(self.cam_height)

            # 4. Final Render Scale
            visible_world = self.world_surf.subsurface((c_left, c_top, c_width, c_height))
            scaled_visible = pygame.transform.scale(visible_world, (WIDTH, HEIGHT))
            
            # OPTIMIZATION: Reuse pre-allocated surface. Do not spawn a new one 60x a second!
            render_surf = self.render_surf 
            render_surf.blit(scaled_visible, (0, 0)) 
            # --- HUD: CLASH TIMER & SHRINK PROMPT ---
            if getattr(self, "clash_decision_timer", 0) > 0:
                # 1. Draw Prompt (Changes text and color based on the sweet spot!)
                prompt_text = "WAIT..." if self.clash_decision_timer > 5 else "SHRINK NOW!" # <--- CHANGE TO 5
                prompt_color = (255, 100, 100) if self.clash_decision_timer > 5 else (0, 255, 255) # <--- CHANGE TO 5
                
                # If they failed, display a locked out message
                if getattr(self, "clash_failed", False):
                    prompt_text = "MISSED TIMING!"
                    prompt_color = (150, 150, 150)
                
                shrink_txt = self.get_text(prompt_text, prompt_color) 
                render_surf.blit(shrink_txt, (WIDTH//2 - shrink_txt.get_width()//2, 80))

                # 2. Draw the Progress Bar directly into the HUD
                bar_w, bar_h = 400, 25
                clash_window = 20 
                
                fill_w = int((self.clash_decision_timer / clash_window) * bar_w)
                bx, by = WIDTH//2 - bar_w//2, 120
                
                # Black Border & Inner Background
                pygame.draw.rect(render_surf, (0, 0, 0), (bx - 4, by - 4, bar_w + 8, bar_h + 8))
                pygame.draw.rect(render_surf, (30, 30, 30), (bx, by, bar_w, bar_h))            
                
                # Draw the "Sweet Spot" Zone visually on the bar (The last 5 frames)
                sweet_spot_w = int((5 / clash_window) * bar_w) # <--- CHANGE THIS TO 5
                pygame.draw.rect(render_surf, (0, 150, 150), (bx, by, sweet_spot_w, bar_h))

                # White Fill (The shrinking timer)
                if fill_w > 0:
                    fill_color = (150, 150, 150) if getattr(self, "clash_failed", False) else (255, 255, 255)
                    pygame.draw.rect(render_surf, fill_color, (bx, by, fill_w, bar_h))
            # --- ANIMATED DOMAIN EXPANSION TEXT ---
            for fighter in [self.gojo, self.sukuna]:
                if fighter.domain_charge > 0:
                    # Calculate how far along the charge is (0.0 to 1.0)
                    charge_progress = (60 - fighter.domain_charge) / 60.0
                    
                    # Create the base text
                    domain_name = "UNLIMITED VOID" if fighter.name == "Gojo" else "MALEVOLENT SHRINE"
                    base_txt = self.get_text(f"DOMAIN EXPANSION: {domain_name}", WHITE)
                    
                    # ADJUSTMENT: Scale it up over time (starts at 0.5x, ends at 1.0x instead of 1.8x)
                    scale_factor = 0.5 + (charge_progress * 0.5)
                    new_w = int(base_txt.get_width() * scale_factor)
                    new_h = int(base_txt.get_height() * scale_factor)
                    scaled_txt = pygame.transform.scale(base_txt, (new_w, new_h))
                    
                    # Set color based on the caster for a cool drop shadow
                    shadow_color = (200, 0, 0) if fighter.name == "Sukuna" else (0, 0, 200)
                    shadow_txt = self.get_text(f"DOMAIN EXPANSION: {domain_name}", shadow_color)
                    scaled_shadow = pygame.transform.scale(shadow_txt, (new_w, new_h))
                    
                    # Center the text dynamically on screen
                    txt_x = WIDTH // 2 - scaled_txt.get_width() // 2
                    
                    # Adjust Y position to avoid overlap during clashes
                    y_offset_domain = -250 if fighter.name == "Gojo" else -100
                    txt_y = HEIGHT // 2 + y_offset_domain - scaled_txt.get_height() // 2
                    
                    # Draw shadow, then white text on top
                    render_surf.blit(scaled_shadow, (txt_x + 4, txt_y + 4))
                    render_surf.blit(scaled_txt, (txt_x, txt_y))

            # --- DOMAIN CLASH VISUAL & POWER ANNOUNCEMENT ---
            # 1. Draw the "Who Wins" text
            if self.clash_msg_timer > 0:
                self.clash_msg_timer -= 1
                clash_txt = self.get_text(self.clash_winner, WHITE)
                bg_w, bg_h = clash_txt.get_width() + 40, clash_txt.get_height() + 20
                
                # OPTIMIZATION: Reuse pre-allocated background surface
                self.clash_msg_bg.fill((0, 0, 0, 0)) # Clear previous pixels
                pygame.draw.rect(self.clash_msg_bg, (0, 0, 0, 180), (0, 0, bg_w, bg_h))
                render_surf.blit(self.clash_msg_bg, (WIDTH//2 - bg_w//2, HEIGHT//2 - 100), (0, 0, bg_w, bg_h))
                render_surf.blit(clash_txt, (WIDTH//2 - clash_txt.get_width()//2, HEIGHT//2 - 90))

            # 2. Draw the Exact Power Numbers in the upper HUD
            if getattr(self, "clash_power_timer", 0) > 0:
                self.clash_power_timer -= 1
                
                # Colors based on who had the higher number
                g_color = (0, 255, 255) if self.gojo_clash_power >= self.sukuna_clash_power else (150, 150, 150)
                s_color = RED if self.sukuna_clash_power > self.gojo_clash_power else (150, 150, 150)
                
                g_txt = self.get_text(f"GOJO: {self.gojo_clash_power}", g_color)
                vs_txt = self.get_text(" VS ", WHITE)
                s_txt = self.get_text(f"SUKUNA: {self.sukuna_clash_power}", s_color)
                
                # Calculate positions to center them dynamically
                total_w = g_txt.get_width() + vs_txt.get_width() + s_txt.get_width() + 40
                start_x = WIDTH // 2 - total_w // 2
                
                # Draw a sleek background box at Y=80 (Right where the rhythm bar was!)
                bg_rect = pygame.Rect(start_x - 20, 80, total_w + 40, 50)
                pygame.draw.rect(render_surf, (20, 20, 25), bg_rect, border_radius=10)
                pygame.draw.rect(render_surf, WHITE, bg_rect, 2, border_radius=10)
                
                # Blit the text inside the box
                render_surf.blit(g_txt, (start_x, 90))
                render_surf.blit(vs_txt, (start_x + g_txt.get_width() + 20, 90))
                render_surf.blit(s_txt, (start_x + g_txt.get_width() + vs_txt.get_width() + 40, 90))

            # --- HUD: REVERTED TO CLEANER BOX STYLE ---
            # 1. Gojo HUD (Top Left)
            # OPTIMIZATION: Reuse cached HUD background to prevent memory trashing
            render_surf.blit(self.gojo_hud_bg, (10, 10))
            
            render_surf.blit(self.get_text("SATORU GOJO", (200, 230, 255)), (25, 15))
            if self.gojo.potential_timer > 0:
                render_surf.blit(self.get_text("120% POT", (255, 215, 0), font=self.mini_font), (260, 20))

            self.draw_bar_on(render_surf, 25, 60, self.gojo.hp, self.gojo.max_hp, RED, 310, 10, "HEALTH")
            self.draw_bar_on(render_surf, 25, 95, self.gojo.energy, self.gojo.max_energy, PURPLE, 145, 8, "CURSE ENERGY")
            self.draw_bar_on(render_surf, 190, 95, self.gojo.infinity, self.gojo.max_infinity, INF_COLOR, 145, 8, "INFINITY")          
            self.draw_bar_on(render_surf, 25, 125, self.gojo.tech_hits, self.gojo.max_tech_hits, (180, 0, 255), 310, 2, "")

            # --- NEW: GOJO SIMPLE DOMAIN BAR ---
            sd_label_g = f"SIMPLE DOMAIN (CD: {self.gojo.sd_broken_timer//60 + 1}s)" if self.gojo.sd_broken_timer > 0 else "SIMPLE DOMAIN"
            sd_color_g = (0, 255, 255) if self.gojo.sd_broken_timer == 0 else (100, 100, 100)
            self.draw_bar_on(render_surf, 25, 145, max(0, self.gojo.max_sd_hits - self.gojo.sd_hits), self.gojo.max_sd_hits, sd_color_g, 310, 6, sd_label_g)

            # --- GOJO HUD LOGIC ---
            # Define burnout state first so we can apply it to all techniques
            is_burned_out = self.gojo.technique_burnout > 0 and self.gojo.domain_uses >= 5
            
            # THE FIX: Apply the 'BURN' state to Blue and Red text displays
            b_cd = f"BLUE: {'BURN' if is_burned_out else 'RDY' if self.gojo.blue_cd==0 else str(self.gojo.blue_cd//60)+'s'}"
            r_cd = f"RED: {'BURN' if is_burned_out else 'RDY' if self.gojo.red_cd==0 else str(self.gojo.red_cd//60)+'s'}"
            
            # --- FANCY PURPLE STATUS ---
            p_status = "BURN" if is_burned_out else ("RDY" if self.gojo.purple_cd == 0 else f"{self.gojo.purple_cd//60}s")
            if self.gojo.tech_hits < self.gojo.max_tech_hits:
                p_label = f"PRPLE: LOCKED ({int(self.gojo.tech_hits)}/{self.gojo.max_tech_hits})"
                p_color = (150, 150, 150) # Grey when locked
            else:
                p_label = f"PRPLE: {p_status}"
                # If burned out, make it red to indicate an error state, otherwise bright purple
                p_color = RED if is_burned_out else (200, 100, 255) 

            # Domain Burnout logic (Void)
            d_cd = f"VOID: {'BURN' if is_burned_out else 'ACT' if self.gojo.domain_active else 'RDY' if self.gojo.domain_cd==0 else str(self.gojo.domain_cd//60)+'s'}"
            use_txt = f"USES: {self.gojo.domain_uses}/5"

            # --- RENDERING (Shifted down) ---
            render_surf.blit(self.get_text(f"{b_cd} | {r_cd} | ", (200, 220, 255), font=self.mini_font), (25, 170))
            render_surf.blit(self.get_text(p_label, p_color, font=self.mini_font), (180, 170)) 
            render_surf.blit(self.get_text(f"{d_cd} | {use_txt}", WHITE, font=self.mini_font), (25, 190))

            # 2. Sukuna HUD (Top Right)
            # OPTIMIZATION: Reuse cached HUD background
            if self.mahoraga and self.mahoraga.hp > 0:
                render_surf.blit(self.sukuna_hud_bg_maho, (WIDTH - 350, 10))
            else:
                render_surf.blit(self.sukuna_hud_bg_normal, (WIDTH - 350, 10))
            
            s_label = self.get_text("RYOMEN SUKUNA", (255, 100, 100))
            render_surf.blit(s_label, (WIDTH - 335, 15))
            if self.sukuna.potential_timer > 0:
                render_surf.blit(self.get_text("120% POT", (255, 215, 0), font=self.mini_font), (WIDTH - 100, 20))

            self.draw_bar_on(render_surf, WIDTH - 335, 60, self.sukuna.hp, self.sukuna.max_hp, RED, 310, 10, "HEALTH")
            self.draw_bar_on(render_surf, WIDTH - 335, 95, self.sukuna.energy, self.sukuna.max_energy, BLUE, 310, 8, "CURSE ENERGY")
            self.draw_bar_on(render_surf, WIDTH - 335, 125, self.sukuna.tech_hits, self.sukuna.max_tech_hits, (255, 100, 0), 310, 2, "")

            # --- NEW: SUKUNA SIMPLE DOMAIN BAR ---
            sd_label_s = f"SIMPLE DOMAIN (CD: {self.sukuna.sd_broken_timer//60 + 1}s)" if self.sukuna.sd_broken_timer > 0 else "SIMPLE DOMAIN"
            sd_color_s = (0, 255, 255) if self.sukuna.sd_broken_timer == 0 else (100, 100, 100)
            self.draw_bar_on(render_surf, WIDTH - 335, 145, max(0, self.sukuna.max_sd_hits - self.sukuna.sd_hits), self.sukuna.max_sd_hits, sd_color_s, 310, 6, sd_label_s)

            # --- SUKUNA HUD LOGIC ---
            # THE FIX: Ensure Sukuna's HUD strictly obeys the 5-use rule!
            sukuna_is_burned_out = self.sukuna.technique_burnout > 0 and self.sukuna.domain_uses >= 5
            
            # Domain Amp can be used even during burnout in lore, so we leave it alone!
            is_da_locked_out = getattr(self.sukuna, "tactical_eval_timer", 0) > 0
            if self.sukuna.amp_duration > 0:
                da_status = "ACT"
            elif is_da_locked_out:
                da_status = f"{self.sukuna.amp_cd // 60}s"
            else:
                da_status = "RDY"
            da_cd = f"DOMAIN AMP: {da_status}"
            
            # Apply BURN status to his innate techniques
            di_cd = f"DISMANTLE: {'BRN' if sukuna_is_burned_out else 'RDY' if self.sukuna.dismantle_cd == 0 else str(self.sukuna.dismantle_cd//60)+'s'}"
            cl_cd = f"CLEAVE: {'BRN' if sukuna_is_burned_out else 'RDY' if self.sukuna.cleave_cd == 0 else str(self.sukuna.cleave_cd//60)+'s'}"
            
            # --- FANCY FUGA STATUS (Matches Gojo's Purple) ---
            fu_status = "BURN" if sukuna_is_burned_out else ("RDY" if self.sukuna.fuga_cd == 0 else f"{self.sukuna.fuga_cd//60}s")
            if self.sukuna.tech_hits < self.sukuna.max_tech_hits:
                fu_label = f"FUGA: LOCKED ({int(self.sukuna.tech_hits)}/{self.sukuna.max_tech_hits})"
                fu_color = (150, 150, 150) # Grey when locked
            else:
                fu_label = f"FUGA: {fu_status}"
                # If burned out, make it red, otherwise bright orange
                fu_color = RED if sukuna_is_burned_out else (255, 150, 50)
                
            sd_cd = f"SHRINE: {'BURN' if sukuna_is_burned_out else 'ACT' if self.sukuna.domain_active else 'RDY' if self.sukuna.domain_cd==0 else str(self.sukuna.domain_cd//60)+'s'}"

            # Render Domain Amp (Shifted down)
            da_txt = self.get_text(da_cd, (150, 220, 255), font=self.mini_font)
            render_surf.blit(da_txt, (WIDTH - 335, 170))
            
            # Render the rest of the slashes next to it
            slash_str = f" | {di_cd} | {cl_cd}"
            slash_txt = self.get_text(slash_str, (255, 150, 150), font=self.mini_font)
            render_surf.blit(slash_txt, (WIDTH - 335 + da_txt.get_width(), 170))

            # --- RENDER FUGA AND SHRINE ---
            # Split Fuga and Shrine so Fuga can have dynamic colors like Purple!
            fu_txt = self.get_text(f"{fu_label} | ", fu_color, font=self.mini_font)
            render_surf.blit(fu_txt, (WIDTH - 335, 190))
            render_surf.blit(self.get_text(sd_cd, WHITE, font=self.mini_font), (WIDTH - 335 + fu_txt.get_width(), 190))

            # 3. Mahoraga HUD (Extension of Sukuna's Box)
            if self.mahoraga and self.mahoraga.hp > 0:
                self.draw_bar_on(render_surf, WIDTH - 335, 235, self.mahoraga.hp, self.mahoraga.max_hp, MAHO_COLOR, 310, 8, "MAHORAGA")
                
                # --- NEW: Check if Domain Amp is pausing adaptation ---
                if self.sukuna.amp_duration > 0:
                    ad_txt = "ADAPT: PAUSED (DOMAIN AMP)"
                    ad_color = (255, 100, 100) # Red to show it's unable
                else:
                    ad_txt = f"ADAPT: {self.mahoraga.adapting_to.upper() if self.mahoraga.adapting_to else 'NONE'}"
                    ad_color = (255, 255, 150)
                    
                if self.sukuna.world_slash_unlocked: 
                    ad_txt = "WORLD SLASH BLUEPRINT ACQUIRED!"
                    ad_color = (255, 255, 150)
                    
                render_surf.blit(self.get_text(ad_txt, ad_color, font=self.mini_font), (WIDTH - 335, 250))
                
                # Tiny text for adaptation percentages to avoid overlap
                p_p = int((1.0 - self.mahoraga.adaptation["punch"]) * 100)
                b_p = int((1.0 - self.mahoraga.adaptation["blue"]) * 100)
                r_p = int((1.0 - self.mahoraga.adaptation["red"]) * 100)
                pu_p = int((1.0 - self.mahoraga.adaptation["purple"]) * 100)
                i_p = int(self.mahoraga.adaptation["infinity"] * 100)
                v_p = int((1.0 - self.mahoraga.adaptation["void"]) * 100)
                sm_txt = f"PN:{p_p}% BL:{b_p}% RD:{r_p}% PR:{pu_p}% IN:{i_p}% VD:{v_p}%"
                
                # OPTIMIZATION: Use the pre-loaded micro_font. Calling SysFont here reads from the hard drive 60x a second!
                render_surf.blit(self.get_text(sm_txt, WHITE, font=self.micro_font), (WIDTH - 335, 270))

            # 4. Center Announcements (Mahoraga Full Adaptations)
            y_offset = HEIGHT // 2 - 150
            active_ann = []
            for ann in self.maho_announcements:
                txt = self.get_text(ann["text"], MAHO_COLOR)
                render_surf.blit(self.get_text(ann["text"], BLACK), (WIDTH//2 - txt.get_width()//2 + 2, y_offset + 2))
                render_surf.blit(txt, (WIDTH//2 - txt.get_width()//2, y_offset))
                ann["timer"] -= 1
                y_offset += 40
                if ann["timer"] > 0:
                    active_ann.append(ann)
            self.maho_announcements = active_ann
            
            render_surf.blit(self.get_text("PRESS 'P' TO PAUSE / VIEW CONTROLS", (200, 200, 200), font=self.mini_font), (WIDTH//2 - 100, 20))
            
            if self.paused:
                self.shared_ui_overlay.fill((0, 0, 0, 200))
                render_surf.blit(self.shared_ui_overlay, (0, 0))
                
                instr_bg = pygame.Rect(WIDTH//2 - 320, HEIGHT//2 - 250, 640, 500)
                pygame.draw.rect(render_surf, (30, 30, 60), instr_bg, border_radius=20)
                pygame.draw.rect(render_surf, (200, 200, 255), instr_bg, 3, border_radius=20)
                
                title = self.get_text("CONTROLS & INSTRUCTIONS", (255, 255, 255))
                render_surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 230))
                
                lines = [
                    "[A/D]: Move  |  [SPACE]: Jump  |  [SHIFT]: Dodge (I-frames)",
                    "[Q]: RCT Heal (Consumes CE)  |  [CLICK]: Melee Attack",
                    "",
                    "--- SATORU GOJO: LIMITLESS ---",
                    "[W]: LAPSE BLUE (Pulls)   |  [S]: REVERSAL RED (Pushes)",
                    "[R]: HOLLOW PURPLE (Requires Max Hits - HP Wipe!)",
                    "[RIGHT CLICK HOLD]: SIMPLE DOMAIN (Counters Sure-hits)",
                    "[V]: DOMAIN EXPANSION (Ultimate Clash & Paralyze)",
                    "[Z + V]: SHRINK DOMAIN (Mash during a Domain Clash!)",
                    "",
                    "--- POINT-BLANK COMBOS (Needs 0 Burnout) ---",
                    "[E + W + HOLD CLICK]: POINT-BLANK BLUE (Warped Punch BEATDOWN)",
                    "[E + S]: POINT-BLANK RED (Cleave Escape -> Massive Blast)",
                    "   * If Burned Out, [E + S] costs 150 extra CE to do a",
                    "     Brain RCT Refresh and instantly restore your technique!",
                    "",
                    "[P]: Resume Game"
                ]
                
                for i, line in enumerate(lines):
                    text = self.get_text(line, (200, 220, 255), font=self.mini_font)
                    render_surf.blit(text, (WIDTH//2 - 290, HEIGHT//2 - 180 + i*25))
            
            if self.game_over:
                self.shared_ui_overlay.fill((0, 0, 0, 230))
                render_surf.blit(self.shared_ui_overlay, (0,0))
                msg = "THE KING REIGNS" if self.gojo.is_split else "THE STRONGEST SURVIVED"
                msg_surf = self.get_text(msg, WHITE)
                render_surf.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT//2 - 50))
                
                btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
                pygame.draw.rect(render_surf, (60, 60, 80), btn_rect, border_radius=10)
                pygame.draw.rect(render_surf, WHITE, btn_rect, 2, border_radius=10)
                btn_txt = self.get_text("EXIT GAME", WHITE)
                render_surf.blit(btn_txt, (WIDTH//2 - btn_txt.get_width()//2, HEIGHT//2 + 80 - btn_txt.get_height()//2))
            
            self.screen.blit(render_surf, display_offset)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    Game().run()