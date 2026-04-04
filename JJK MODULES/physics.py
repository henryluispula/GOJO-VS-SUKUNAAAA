import pygame # type: ignore
import random
from settings import *

def update_fighter_physics(self, dt):
    if self.is_split: return

    time_mult = dt * 60.0 
    self.anim_tick += 1  

    # --- HIT STOP LOGIC ---
    if self.hit_stop > 0:
        self.hit_stop -= time_mult
        return

    # Particle Update
    for p in self.particles[:]:
        p["pos"][0] += p["vel"][0] * time_mult
        p["pos"][1] += p["vel"][1] * time_mult
        p["life"] -= 0.05 * time_mult
        if p["life"] <= 0:
            self.particles.remove(p)

    if self.name == "Gojo":
        if getattr(self, "dev_immortal", False):
            self.hp = self.max_hp
        if getattr(self, "dev_inf_ce", False):
            self.energy = self.max_energy
            self.ce_exhausted = False
        if getattr(self, "dev_disable_infinity", False):
            self.infinity = 0
    
    self.domain_cd = max(0, self.domain_cd - time_mult)
    self.technique_burnout = max(0, self.technique_burnout - time_mult)
    self.sd_broken_timer = max(0, self.sd_broken_timer - time_mult)

    if self.domain_timer > 0:
        self.domain_timer -= time_mult
        if self.domain_timer <= 0:
            self.end_domain()
            
    if self.name == "Gojo" and self.technique_burnout > 0 and self.domain_uses >= 5:
        self.infinity = 0

    if not hasattr(self, "y_remainder"): self.y_remainder = 0.0
    if not hasattr(self, "x_remainder"): self.x_remainder = 0.0

    if self.is_paralyzed or self.grab_timer > 0:
        self.is_dodging = False
        self.dodge_timer = 0
        self.vel_y = 0
        self.y_remainder = 0.0
        if self.grab_timer > 0: self.grab_timer -= time_mult
    else:
        self.vel_y += GRAVITY * time_mult
        
        move_y = (self.vel_y * time_mult) + self.y_remainder
        actual_move_y = int(move_y)
        self.y_remainder = move_y - actual_move_y
        self.rect.y += actual_move_y
        
        if self.rect.bottom >= WORLD_HEIGHT - 100:
            self.rect.bottom = WORLD_HEIGHT - 100
            self.vel_y = 0
            self.y_remainder = 0.0
            self.on_ground = True
        
        if self.rect.left < 10: self.rect.left = 10
        if self.rect.right > WORLD_WIDTH - 10: self.rect.right = WORLD_WIDTH - 10

        if self.dodge_timer > 0:
            self.dodge_timer -= time_mult
            dash_speed = 72 if self.name == "Gojo" else 45                
            move_x = (self.direction * dash_speed * time_mult) + self.x_remainder
            actual_move_x = int(move_x)
            self.x_remainder = move_x - actual_move_x
            self.rect.x += actual_move_x
        else: 
            self.is_dodging = False
            self.dodge_timer = 0 
                
    # Energy Regen
    base_regen = 25.0 if self.name == "Gojo" else 0.8 if self.name == "Mahoraga" else 1.0 
    regen_mult = 1.2 if self.potential_timer > 0 else 1.0
    
    if self.energy <= 0.5:
        self.ce_exhausted = True
        if self.name == "Gojo":
            self.infinity = 0
        
    if self.ce_exhausted:
        if self.name == "Sukuna":
            regen_mult *= 0.8 
            recovery_thresh = 80 
        else:
            regen_mult *= 0.4 
            recovery_thresh = 420 if self.name == "Gojo" else 30
            
        if self.energy >= recovery_thresh:
            self.ce_exhausted = False
    
    self.energy = min(self.max_energy, self.energy + base_regen * regen_mult * time_mult)
    
    stam_regen = 0.8 if self.name == "Gojo" else 0.6
    if self.stamina <= 0.5:
        self.stamina_exhausted = True
        
    if self.stamina_exhausted:
        stam_regen *= 0.1 
        if self.stamina >= 30:
            self.stamina_exhausted = False
            
    self.stamina = min(self.max_stamina, self.stamina + stam_regen * time_mult)
    
    if self.is_dodging:
        self.trail_points.append([self.rect.centerx, self.rect.centery, 10]) 
    
    active_trails = []
    for pt in self.trail_points:
        pt[2] -= time_mult
        if pt[2] > 0:
            active_trails.append(pt)
    self.trail_points = active_trails
    
    if self.name == "Gojo" and self.infinity < self.max_infinity and self.technique_burnout == 0 and not getattr(self, "dev_disable_infinity", False):
        cost = 0.1 * self.cost_mult * time_mult
        if self.energy >= cost:
            self.infinity = min(self.max_infinity, self.infinity + 3.5 * time_mult) 
            self.energy -= cost

    if self.name == "Sukuna" and self.hp > 0 and self.hp < self.max_hp and not self.ce_exhausted:
        if self.is_paralyzed and getattr(self, "mahoraga_is_dead", False):
            pass 
        else:
            heal_cost = 0.3 * self.cost_mult * time_mult
            
            if self.is_paralyzed:
                heal_cost *= 4.0 
                self.mahoraga_lockout = 900  
                
                if random.random() < (0.1 * time_mult):
                    self.black_flash_timer = 2 
            
            if self.energy >= heal_cost:
                self.hp = min(self.max_hp, self.hp + random.uniform(2.5, 3.5) * time_mult)
                self.energy -= heal_cost
                self.rct_timer = 5

    if self.name == "Mahoraga" and self.rct_timer > 0:
        self.hp = min(self.max_hp, self.hp + 1.2 * time_mult) 

    self.attack_cooldown = max(0, self.attack_cooldown - time_mult)
    self.dismantle_cd = max(0, self.dismantle_cd - time_mult)
    self.mahoraga_lockout = max(0, getattr(self, "mahoraga_lockout", 0) - time_mult)
    self.cleave_cd = max(0, self.cleave_cd - time_mult)
    self.grab_cd = max(0, self.grab_cd - time_mult)
    self.blue_cd = max(0, self.blue_cd - time_mult)
    self.red_cd = max(0, self.red_cd - time_mult)
    self.purple_cd = max(0, self.purple_cd - time_mult)
    self.fuga_cd = max(0, self.fuga_cd - time_mult)
    self.world_slash_cd = max(0, self.world_slash_cd - time_mult)
    self.dodge_cd = max(0, self.dodge_cd - time_mult)
    self.black_flash_timer = max(0, self.black_flash_timer - time_mult)
    self.potential_timer = max(0, self.potential_timer - time_mult)
    self.punch_timer = max(0, self.punch_timer - time_mult)        
    self.rct_timer = max(0, self.rct_timer - time_mult)
    self.adapt_pulse_timer = max(0, getattr(self, "adapt_pulse_timer", 0) - time_mult)
    self.inf_hit_timer = max(0, self.inf_hit_timer - time_mult)
    self.aura_hit_timer = max(0, self.aura_hit_timer - time_mult)

    # --- CE AURA MOVEMENT SWAY CALCULATION ---
    curr_vel_x = (self.rect.x - self.prev_x_aura)
    curr_vel_y = (self.rect.y - self.prev_y_aura)
    self.prev_x_aura = self.rect.x
    self.prev_y_aura = self.rect.y

    self.aura_sway_x += (curr_vel_x - self.aura_sway_x) * 0.2
    self.aura_sway_y += (curr_vel_y - self.aura_sway_y) * 0.2

    # --- RCT SWAY PHYSICS (CIRCULAR DOTS) ---
    if self.rct_timer > 0:
        if random.random() < 0.6 * time_mult: 
            px = self.rect.centerx + random.randint(-35, 35)
            py = self.rect.bottom - random.randint(0, 40)
            r_col = random.choice([(150, 255, 150), (255, 255, 200), (100, 255, 150)])
            self.rct_particles.append({
                "pos": [px, py], 
                "vel": [random.uniform(-1.6, 1.6), random.uniform(-4.0, -1.5)], 
                "color": r_col,
                "life": 255
            })

    for p in self.rct_particles[:]:
        p["pos"][0] += p["vel"][0] * time_mult 
        p["pos"][1] += p["vel"][1] * time_mult 
        p["life"] -= 6 * time_mult 
        if p["life"] <= 0:
            self.rct_particles.remove(p)
    
    if self.amp_duration > 0:
        self.amp_duration -= time_mult
        if self.amp_duration <= 0:
            self.amp_cd = 0
    else:
        self.amp_cd = max(0, self.amp_cd - time_mult)