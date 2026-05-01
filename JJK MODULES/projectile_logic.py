import random
import pygame 
from settings import *

def update_projectiles(self, dt):
    time_mult = dt * 60.0
    enemies = [self.sukuna]
    if self.mahoraga and self.mahoraga.hp > 0:
        enemies.append(self.mahoraga)

    active_projectiles = []
    for p in self.projectiles:
        if getattr(p, "is_grab_cleave", False):
            if self.gojo.grab_timer > 0:
                p.pos.x = self.gojo.rect.centerx
                p.pos.y = self.gojo.rect.centery
            else:
                p.active = False 
                
        if getattr(p, "is_sure_hit", False) and not self.sukuna.domain_active:
            p.active = False
                
        p.update(dt)
        if not p.active:
            continue
            
        p_target = min(enemies, key=lambda e: pygame.Vector2(e.rect.center).distance_to(p.pos))
        dist_to_orb = pygame.Vector2(p_target.rect.center).distance_to(p.pos)

        if p.type == "blue_orb":
            if dist_to_orb < 1000:
                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                    old_b_turns = int(p_target.adaptation_points["blue"] // 1000)
                    p_target.trigger_adaptation("blue", 1.0 * time_mult)
                    if int(p_target.adaptation_points["blue"] // 1000) > old_b_turns:
                        p_target.adapt_pulse_timer = 30
                    turns = p_target.adaptation_points["blue"] / 250.0
                    p_target.adaptation["blue"] = max(0, 1.0 - min(1.0, turns / 12.0))

                if not p_target.is_dodging:
                    if p_target.name == "Mahoraga" and p_target.adaptation["blue"] <= 0:
                        pull_factor = 0.0 
                    else:
                        pull_factor = .9 * (p_target.adaptation["blue"] if p_target.name == "Mahoraga" else 1.0)
                    
                    if pull_factor > 0:
                        pull_step = (p.pos.x - p_target.rect.centerx) * pull_factor * time_mult                        
                        p_target.rect.x += pull_step

                        if abs(p.pos.x - p_target.rect.centerx) < 10:
                            p_target.rect.centerx = p.pos.x
            
            if dist_to_orb < 450:
                if p.type == "blue_orb" and p.vel.length() > p.original_speed:
                    p.vel = p.vel.normalize() * p.original_speed
                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                    p_target.trigger_adaptation("blue", 2.0 * time_mult)
                    turns = p_target.adaptation_points["blue"] / 250.0
                    p_target.adaptation["blue"] = max(0, 1.0 - min(1.0, turns / 12.0))
                    
                orb_dmg = 1 * (p_target.adaptation["blue"] if p_target.name == "Mahoraga" else 1.0) * time_mult
                
                if p_target.name == "Sukuna":
                    if p_target.amp_duration > 0: orb_dmg *= 0.2 
                    
                    if p_target.energy > 0:
                        reduction_mult = random.uniform(0.15, 0.35) 
                        mitigated_dmg = orb_dmg * (1.0 - reduction_mult) 
                        orb_dmg *= reduction_mult 
                        p_target.energy = max(0, p_target.energy - (mitigated_dmg * 2.0) * p_target.cost_mult)
                        
                elif p_target.name == "Mahoraga":
                    orb_dmg *= 0.75
                    
                if not p_target.is_dodging:
                    p_target.hp -= orb_dmg
                    if p_target.name == "Sukuna": p_target.memory.record("blue", dist_to_orb, hit=True)
                    if p_target.name in ["Sukuna", "Mahoraga"]: self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 1 * time_mult)
            
            for slash in self.projectiles:
                if slash.type in ["dismantle", "cleave"]:
                    dist = p.pos.distance_to(slash.pos)
                    if 0 < dist < 400:
                        pull_dir = (p.pos - slash.pos).normalize()
                        current_speed = slash.vel.length()
                        
                        pull_force = current_speed * 0.65 
                        slash.vel += pull_dir * pull_force * time_mult
                        
                        if slash.vel.length() > 0:
                            slash.vel.scale_to_length(current_speed)

        elif p.type == "red_orb":
            if dist_to_orb < 600:
                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                    old_r_turns = int(p_target.adaptation_points["red"] // 1000)
                    p_target.trigger_adaptation("red", 1.0 * time_mult)
                    if int(p_target.adaptation_points["red"] // 1000) > old_r_turns:
                        p_target.adapt_pulse_timer = 30
                    turns = p_target.adaptation_points["red"] / 250.0
                    p_target.adaptation["red"] = max(0, 1.0 - min(1.0, turns / 12.0))

                if not p_target.is_dodging:
                    if p_target.name == "Mahoraga" and p_target.adaptation["red"] <= 0:
                        push_factor = 0.0 
                    else:
                        push_factor = 1.60 * (p_target.adaptation["red"] if p_target.name == "Mahoraga" else 1.0)
                    
                    if push_factor > 0:
                        p_target.rect.x -= (p.pos.x - p_target.rect.centerx) * push_factor * time_mult
            
            if dist_to_orb < 250:
                repel_dir = 1 if p_target.rect.centerx > p.pos.x else -1
                p_target.rect.x += repel_dir * (WORLD_WIDTH / 2)
                
                if p_target.rect.left < 0: p_target.rect.left = 0
                if p_target.rect.right > WORLD_WIDTH: p_target.rect.right = WORLD_WIDTH

                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                    p_target.trigger_adaptation("red", 2.0 * time_mult)
                    turns = p_target.adaptation_points["red"] / 250.0
                    p_target.adaptation["red"] = max(0, 1.0 - min(1.0, turns / 12.0))

                orb_dmg = 45.0 * (p_target.adaptation["red"] if p_target.name == "Mahoraga" else 1.0) 
                
                if p_target.name == "Sukuna":
                    if p_target.amp_duration > 0: orb_dmg *= 0.3 
                    if p_target.energy > 0:
                        reduction_mult = random.uniform(0.15, 0.35) 
                        mitigated_dmg = orb_dmg * (1.0 - reduction_mult) 
                        orb_dmg *= reduction_mult 
                        p_target.energy = max(0, p_target.energy - (mitigated_dmg * 2.0) * p_target.cost_mult)
                elif p_target.name == "Mahoraga":
                    orb_dmg *= 0.75
                    
                if not p_target.is_dodging:
                    p_target.hp -= orb_dmg
                    if p_target.name == "Sukuna": p_target.memory.record("red", dist_to_orb, hit=True)
                    if p_target.name in ["Sukuna", "Mahoraga"]: 
                        self.gojo.tech_hits = min(self.gojo.max_tech_hits, self.gojo.tech_hits + 10)
                
                p.active = False
                self.shake_timer = 15
                self.hit_stop = 8
            
            for slash in self.projectiles:
                if slash.type in ["dismantle", "cleave"]:
                    dist = p.pos.distance_to(slash.pos)
                    if 0 < dist < 450: 
                        push_dir = (slash.pos - p.pos).normalize()
                        current_speed = slash.vel.length()
                        
                        push_force = current_speed * 0.85 
                        slash.vel += push_dir * push_force * time_mult
                        
                        if slash.vel.length() > 0:
                            slash.vel.scale_to_length(current_speed)

        elif p.type == "purple_orb":
            dist_x = abs(p_target.rect.centerx - p.pos.x)
            if dist_x < 180: 
                if p_target.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                    old_pu_turns = int(p_target.adaptation_points["purple"] // 1000)
                    p_target.trigger_adaptation("purple", 400.0)
                    if int(p_target.adaptation_points["purple"] // 1000) > old_pu_turns:
                        p_target.adapt_pulse_timer = 30
                    turns = p_target.adaptation_points["purple"] / 250.0
                    p_target.adaptation["purple"] = max(0, 1.0 - min(1.0, turns / 13.0))

            if dist_x < 80: 
                purple_dmg = (p_target.max_hp * 1.0)
                
                if p_target.name == "Mahoraga":
                    purple_dmg *= p_target.adaptation["purple"] 
                elif p_target.name == "Sukuna" and p_target.amp_duration > 0:
                    purple_dmg *= 0.6 
                
                if p_target.energy > 0:
                    reduction_mult = random.uniform(0.5, 0.8)
                    mitigated_dmg = purple_dmg * (1.0 - reduction_mult) 
                    purple_dmg *= reduction_mult 
                    p_target.energy = max(0, p_target.energy - (mitigated_dmg * 8.5) * p_target.cost_mult)
                
                p_target.hp -= purple_dmg
                if p_target.name == "Sukuna": p_target.memory.record("purple", dist_x, hit=True)
                p.active = False 
                self.shake_timer = 20
                self.hit_stop = 30
    
        elif p.type == "fuga_arrow":
            dist_x = abs(self.gojo.rect.centerx - p.pos.x)
            dist_y = abs(self.gojo.rect.centery - p.pos.y)
            
            if dist_x < 350 and dist_y < 350: 
                
                if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout == 0:
                    fuga_ce_dmg = self.gojo.max_energy * 0.80 
                    self.gojo.energy = max(0, self.gojo.energy - fuga_ce_dmg)
                else:
                    fuga_hp_dmg = self.gojo.max_hp * 1.0
                    
                    if self.gojo.energy > 0: 
                        reduction_mult = random.uniform(0.15, 0.35) 
                        mitigated_dmg = fuga_hp_dmg * (1.0 - reduction_mult)
                        fuga_hp_dmg *= reduction_mult
                        self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) 
                
                    self.gojo.hp -= fuga_hp_dmg
                
                p.active = False 
                self.hit_stop = 30
    
        intercepted_by_sd = False
        
        is_domain_slash = getattr(p, "is_sure_hit", False)

        if self.gojo.simple_domain_active and is_domain_slash:
            dist_to_gojo = pygame.Vector2(self.gojo.rect.center).distance_to(p.pos)
            
            if dist_to_gojo < 100: 
                p.active = False 
                intercepted_by_sd = True
                
                self.gojo.sd_hits += 1
                
                if self.gojo.sd_hits >= self.gojo.max_sd_hits: 
                    self.gojo.simple_domain_active = False
                    self.gojo.sd_was_active = False
                    self.gojo.sd_broken_timer = 60 
                    self.popups.append({
                        "x": self.gojo.rect.centerx, 
                        "y": self.gojo.rect.centery - 100, 
                        "timer": 45, 
                        "text": "SD CRUMBLED!", 
                        "color": RED
                    })
                    self.shake_timer = 15
                    
        hit_radius = 50 * p.size_mult if p.type in ["dismantle", "cleave", "world_slash"] else 20
        dist_to_gojo_center = pygame.Vector2(self.gojo.rect.center).distance_to(p.pos)
        
        is_colliding = self.gojo.rect.collidepoint(p.pos) or dist_to_gojo_center < (hit_radius + 35)

        if not intercepted_by_sd and is_colliding and p.type in ["normal", "dismantle", "cleave", "world_slash"] and not getattr(p, "is_grab_cleave", False):
            if not self.gojo.is_dodging:
                
                if p.type == "world_slash":
                    self.gojo.hp -= 200 
                    p.active = False
                    self.shake_timer = 25
                    self.hit_stop = 15
                    
                elif getattr(p, "is_sure_hit", False):
                    proj_dmg = 80.0 if p.type == "cleave" else 32.0
                    if self.gojo.energy > 0: 
                        reduction_mult = random.uniform(0.15, 0.35) 
                        mitigated_dmg = proj_dmg * (1.0 - reduction_mult)
                        proj_dmg *= reduction_mult
                        self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) 
                
                    self.gojo.hp -= proj_dmg
                    p.active = False
                    if p.type == "cleave": self.hit_stop = 6
                    self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
                    
                else:
                    is_burned_out = (self.gojo.domain_uses >= 5 and self.gojo.technique_burnout > 0)
                    
                    if self.gojo.infinity > 0 and self.gojo.energy > 0 and not is_burned_out: 
                        self.gojo.energy = max(0, self.gojo.energy - 0.5 * self.gojo.cost_mult) 
                        p.active = False 
                    else: 
                        self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2) 
                        proj_dmg = 80.0 if p.type == "cleave" else 32.0
                        if self.gojo.energy > 0: 
                            reduction_mult = random.uniform(0.15, 0.35) 
                            mitigated_dmg = proj_dmg * (1.0 - reduction_mult)
                            proj_dmg *= reduction_mult
                            self.gojo.energy = max(0, self.gojo.energy - (mitigated_dmg * 3.5) * self.gojo.cost_mult) 
                    
                        self.gojo.hp -= proj_dmg
                        p.active = False
                        if p.type == "cleave": self.hit_stop = 6
                        self.blood_particles.append([self.gojo.rect.centerx, self.gojo.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])
        
        if p.active:
            active_projectiles.append(p)
    self.projectiles = active_projectiles