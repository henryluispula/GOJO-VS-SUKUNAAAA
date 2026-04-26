import random
import math
import pygame 
from settings import *

def update_mahoraga_ai(self, dt):
    time_mult = dt * 60.0
    self.mahoraga.update_physics(dt)
    if not self.mahoraga.is_paralyzed:
        ideal_x = self.gojo.rect.centerx 
        
        threats = [p for p in self.projectiles if p.type in ["blue_orb", "red_orb", "purple_orb"] and p.active]
        if threats:
            closest_threat = min(threats, key=lambda p: abs(p.pos.x - self.sukuna.rect.centerx))
            if closest_threat.pos.x < self.sukuna.rect.centerx:
                ideal_x = self.sukuna.rect.centerx - 70
            else:
                ideal_x = self.sukuna.rect.centerx + 70
        elif abs(self.gojo.rect.centerx - self.sukuna.rect.centerx) < 8000:
            ideal_x = self.gojo.rect.centerx
        else:
            if self.gojo.rect.centerx < self.sukuna.rect.centerx:
                ideal_x = self.sukuna.rect.centerx - 120
            else:
                ideal_x = self.sukuna.rect.centerx + 120

        if abs(self.mahoraga.rect.centerx - ideal_x) > 42:
            self.mahoraga.rect.x += (-42 if self.mahoraga.rect.centerx > ideal_x else 42) * time_mult
        
        if abs(self.mahoraga.rect.centerx - self.gojo.rect.centerx) > 150:
            if self.mahoraga.dodge_cd <= 0 and random.random() < 0.05:
                self.mahoraga.direction = -1 if self.mahoraga.rect.x > self.gojo.rect.x else 1
                self.mahoraga.dodge()
                if self.mahoraga.on_ground:
                    self.mahoraga.jump() 
                self.mahoraga.dodge_cd = 60
            elif self.mahoraga.on_ground and random.random() < 0.025:
                self.mahoraga.jump()

        m_dist = abs(self.mahoraga.rect.centerx - self.gojo.rect.centerx)
        if m_dist < 150:
            if self.sukuna.amp_duration <= 0:
                old_inf_turns = int(self.mahoraga.adaptation_points["infinity"] // 1000)
                self.mahoraga.trigger_adaptation("infinity", 1.5 * time_mult)
                if int(self.mahoraga.adaptation_points["infinity"] // 1000) > old_inf_turns:
                    self.mahoraga.adapt_pulse_timer = 30
                turns = self.mahoraga.adaptation_points["infinity"] / 250.0
                self.mahoraga.adaptation["infinity"] = min(1.0, turns / 13.0)

        if self.gojo.rect.colliderect(self.mahoraga.rect) and self.mahoraga.attack_cooldown <= 0:
            self.mahoraga.punch_timer = 20 
            self.mahoraga.punch_count += 1
            base_dmg = 4.5

            imbue_cost = 2.0 * self.mahoraga.cost_mult
            if self.mahoraga.energy >= imbue_cost:
                self.mahoraga.energy -= imbue_cost
                base_dmg *= 1.6 

            if self.mahoraga.potential_timer > 0:
                bf_chance = random.uniform(0.01, 0.02) 
            else:
                bf_chance = 0.0001 
                
            is_black_flash = random.random() < bf_chance
            if is_black_flash:
                self.bf_zoom_timer = 45
                self.bf_zoom_pos = (self.gojo.rect.centerx, self.gojo.rect.centery)
                    
                base_dmg *= math.pow(2.5, 2.5)
                self.mahoraga.black_flash_timer = 20
                self.mahoraga.potential_timer = 600 
                self.shake_timer = 15
                
                ce_recovery = self.mahoraga.max_energy * 0.20
                self.mahoraga.energy = min(self.mahoraga.max_energy, self.mahoraga.energy + ce_recovery)
                
                self.bf_words.append({"x": self.gojo.rect.centerx, "y": self.gojo.rect.centery - 60, "timer": 45})
            
            if not self.gojo.is_dodging:
                inf_adapt_ratio = self.mahoraga.adaptation["infinity"]
                to_hp = base_dmg * inf_adapt_ratio
                to_inf = base_dmg * (1.0 - inf_adapt_ratio)
                
                hit_connected = False
                if self.gojo.infinity > 0 and self.gojo.energy > 0 and self.gojo.technique_burnout <= 0:
                    self.gojo.inf_hit_timer = 20  
                    self.gojo.infinity -= to_inf * 0.5 
                    
                    if self.gojo.energy > 0 and not is_black_flash: 
                        to_hp *= random.uniform(0.15, 0.35)
                        self.gojo.energy -= (base_dmg * inf_adapt_ratio * 0.75) * 3.5 
                    
                    self.gojo.hp -= to_hp 
                    if to_hp > 0: hit_connected = True
                else:
                    actual_dmg = base_dmg
                    if self.gojo.energy > 0 and not is_black_flash: 
                        actual_dmg *= random.uniform(0.15, 0.35)
                        self.gojo.energy -= (base_dmg * 0.75) * 3.5 
                        
                    self.gojo.hp -= actual_dmg
                    hit_connected = True
                    
                if hit_connected:
                    spark_color = (255, 0, 0) if self.mahoraga.black_flash_timer > 0 else MAHO_COLOR
                    for _ in range(12):
                        self.hit_sparks.append([self.gojo.rect.centerx + random.randint(-15, 15), self.gojo.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), spark_color])
                    
                kb_dir = 1 if self.gojo.rect.centerx > self.mahoraga.rect.centerx else -1
                kb_dist = 1200 if is_black_flash else 40
                self.gojo.rect.x += kb_dir * kb_dist
                
            self.mahoraga.attack_cooldown = 12
            
        if self.mahoraga.hp < (self.mahoraga.max_hp * 0.625) and self.mahoraga.energy > 5 * self.mahoraga.cost_mult and not self.mahoraga.ce_exhausted:
            self.mahoraga.hp = min(self.mahoraga.max_hp, self.mahoraga.hp + 1.8 * time_mult) 
            self.mahoraga.energy -= 1.0 * self.mahoraga.cost_mult * time_mult
            self.mahoraga.rct_timer = 5