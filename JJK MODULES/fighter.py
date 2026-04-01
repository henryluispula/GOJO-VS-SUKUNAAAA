import pygame # type: ignore
import math
import random
import time
from settings import *

class Fighter:
    def __init__(self, x, y, name, color=CLOTHES):
        if name == "Mahoraga":
            self.rect = pygame.Rect(x, y, 140, 320)
        else:
            self.rect = pygame.Rect(x, y, 70, 160)
        self.name = name
        self.max_hp = 500 if name == "Sukuna" else (480 if name == "Mahoraga" else 200)
        self.hp = self.max_hp
        self.prev_hp = self.hp
        self.max_energy = 3000 if name == "Sukuna" else (2100 if name == "Gojo" else 2800)
        self.energy = self.max_energy
        self.max_infinity = 1000 if name == "Gojo" else 0 
        self.infinity = self.max_infinity
        self.max_tech_hits = 1000 
        self.max_sd_hits = 300 if name == "Sukuna" else 38 
        
        # --- OPTIMIZATION: Surface Caching ---
        self.inf_surf = pygame.Surface((220, 320), pygame.SRCALPHA)
        self.sd_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
        self.amp_surf = pygame.Surface((150, 250), pygame.SRCALPHA)
        
        # --- DODGE METER LOGIC ---
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.stamina_exhausted = False
        self.trail_points = [] 
        
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
        self.adapting_to = None 
        self.wheel_rotation = 0
        self.adapt_pulse_timer = 0 
        self.last_turn_count = 0
        self.is_split = False
        self.using_blue = False 
        self.purple_charge = 0 
        self.fuga_charge = 0
        self.world_slash_charge = 0 
        self.world_slash_cd = 0 
        self.domain_charge = 0 
        self.tech_hits = 0 
        self.slash_count = 0
        self.slash_delay = 0
        self.slash_type = "dismantle" 
        self.black_flash_timer = 0 
        self.potential_timer = 0 
        self.punch_timer = 0 
        self.punch_count = 0 
        self.world_slash_unlocked = False 
        self.grab_timer = 0
        self.grab_cd = 0

        # --- REFACTOR: Combat Realism & Feedback ---
        self.hit_stop = 0
        self.particles = []
        self.active_hitbox = None

        # --- DEV OPTIONS ---
        self.dev_immortal = False
        self.dev_inf_ce = False
        self.dev_inf_infinity = False
        
        # --- Domain Mechanics ---
        self.domain_active = False
        self.domain_timer = 0
        self.domain_cd = 0
        self.is_paralyzed = False
        self.domain_uses = 0
        self.technique_burnout = 0
        self.simple_domain_active = False 
        self.sd_hits = 0 
        self.sd_broken_timer = 0 
        self.prev_energy = self.energy
        self.ce_exhausted = False 

    @property
    def cost_mult(self):
        return 0.2 if self.potential_timer > 0 else 1.0

    def end_domain(self):
        if not self.domain_active:
            return

        self.domain_active = False 
        self.domain_timer = 0
        self.domain_uses += 1
        
        if self.domain_uses <= 5:
            self.domain_cd = 480 
            self.technique_burnout = 0
        else:
            self.domain_cd = 3000
            self.technique_burnout = 1200
            if self.name == "Gojo":
                self.infinity = 0                                          

    def jump(self):
        if self.on_ground and not self.is_paralyzed:
            self.vel_y = -55 if self.name == "Mahoraga" else -45
            self.on_ground = False

    def dodge(self):
        if self.dodge_timer <= 0 and not self.is_paralyzed and self.stamina >= 20 and not self.stamina_exhausted:
            self.is_dodging = True
            self.dodge_timer = 25 if self.name == "Gojo" else 20
            self.stamina -= 20

    def create_impact_particles(self, pos, color=WHITE):
        for _ in range(8):
            self.particles.append({
                "pos": list(pos),
                "vel": [random.uniform(-8, 8), random.uniform(-8, 8)],
                "life": 1.0,
                "color": color
            })

    def update_physics(self, dt):
        if self.is_split: return

        time_mult = dt * 60.0 

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
        
        if self.amp_duration > 0:
            self.amp_duration -= time_mult
            if self.amp_duration <= 0:
                self.amp_cd = 0
        else:
            self.amp_cd = max(0, self.amp_cd - time_mult)

    def trigger_adaptation(self, phenomenon, intensity=1.0):
        if self.name != "Mahoraga": return
        
        if self.adapting_to != phenomenon:
            self.adapting_to = phenomenon
            
        self.adaptation_points[phenomenon] += intensity

    def draw_detailed(self, surface, is_punching=False, effect=None, is_amp=False):
        # Particles Impact Feedback
        for p in self.particles:
            alpha = int(p["life"] * 255)
            p_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], alpha), (3, 3), 3)
            surface.blit(p_surf, (p["pos"][0]-3, p["pos"][1]-3))

        for pt in self.trail_points:
            streak_len = int((pt[2] / 10.0) * 80)
            if streak_len > 0:
                pygame.draw.line(surface, self.color, (pt[0], pt[1]), (pt[0] - self.direction * streak_len, pt[1]), 6)
                pygame.draw.line(surface, WHITE, (pt[0], pt[1] - 20), (pt[0] - self.direction * (streak_len - 15), pt[1] - 20), 2)
                pygame.draw.line(surface, WHITE, (pt[0], pt[1] + 20), (pt[0] - self.direction * (streak_len - 15), pt[1] + 20), 2)
                
        x, y, mid_x = self.rect.centerx - (self.rect.width // 2), self.rect.y, self.rect.centerx

        if self.name == "Sukuna" and self.grab_timer > 0 and getattr(self, "grab_type", "") != "gojo_beatdown":
            arm_color = (100, 0, 0)
            grab_x = mid_x + (60 * self.direction)
            pygame.draw.line(surface, SKIN, (mid_x, y + 50), (grab_x, y + 60), 18)
            for _ in range(5):
                pygame.draw.circle(surface, RED, (int(grab_x), int(y + 60 + random.randint(-10, 10))), 4)
                
        if self.is_split and self.name == "Gojo":
            self.draw_death(surface)
            return

        t = time.time()
        
        if self.black_flash_timer > 0:
            for _ in range(15):
                rx, ry = random.randint(x-40, x+110), random.randint(y-40, y+200)
                pygame.draw.line(surface, BLACK, (rx, ry), (rx+random.randint(-40,40), ry+random.randint(-40,40)), 6)
                pygame.draw.line(surface, (255, 0, 0), (rx, ry), (rx+random.randint(-20,20), ry+random.randint(-20,20)), 3)

        if getattr(self, "domain_charge", 0) > 0:
            ct = (60 - self.domain_charge) / 60.0
            burst = int(180 * ct)
            dom_color = (200, 200, 255) if self.name == "Gojo" else (255, 50, 50)
            pygame.draw.circle(surface, dom_color, (mid_x, y + 40), burst, max(1, int(15 * (1 - ct))))
            if ct > 0.8:
                pygame.draw.circle(surface, WHITE, (mid_x, y + 40), int(burst * 1.2), 3)

        if self.simple_domain_active:
            self.sd_surf.fill((0,0,0,0)) 
            pygame.draw.circle(self.sd_surf, (200, 200, 255, 40), (90, 90), 90)
            pygame.draw.circle(self.sd_surf, (255, 255, 255, 120), (90, 90), 90, 3)
            pulse = (math.sin(t * 10) + 1) * 0.5
            pygame.draw.circle(self.sd_surf, (200, 200, 255, int(100 * pulse)), (90, 90), 85, 1)
            surface.blit(self.sd_surf, (mid_x - 90, y + 80 - 90))

        if self.name == "Gojo":
            has_active_infinity = self.infinity > 0 and self.technique_burnout == 0 and not getattr(self, "dev_disable_infinity", False)
            
            is_hit = self.hp < self.prev_hp or self.energy < self.prev_energy or self.grab_timer > 0
            is_bypassed = (self.hp < self.prev_hp and self.energy >= self.prev_energy)

            if self.grab_timer > 0 and getattr(self, "grab_type", "") == "amp_punch":
                is_bypassed = True

            if has_active_infinity and is_hit and not is_bypassed:
                alpha_base = 180 
                pulse = math.sin(t * 20) * 15 
                
                self.inf_surf.fill((0,0,0,0)) 
                for i in range(2): 
                    layer_alpha = int(alpha_base / (i + 1))
                    thickness = int(pulse + 10 + (i * 5))
                    
                    poly = [(60, 70), (140, 70), (135, 240), (65, 240)]
                    
                    pygame.draw.polygon(self.inf_surf, (100, 200, 255, layer_alpha), poly, thickness)
                    pygame.draw.circle(self.inf_surf, (150, 230, 255, layer_alpha), (110, 45), 35 + (thickness//2), thickness)
                
                surface.blit(self.inf_surf, (x - 75, y - 55))

            if self.purple_charge > 0:
                ct = (120 - self.purple_charge) / 120.0
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

                if ct > 0.25:
                    for _ in range(int(6 * ct)):
                        lx = int(bx + random.randint(-12, 12))
                        ly = int(by + random.randint(-12, 12))
                        ex = int(rx + random.randint(-12, 12))
                        ey = int(ry + random.randint(-12, 12))
                        pygame.draw.line(surface, (220, 120, 255), (lx, ly), (ex, ey), 2)
                        pygame.draw.line(surface, WHITE, (lx, ly), (ex, ey), 1)

                if ct > 0.45:
                    for ri in range(4):
                        ring_r = int((30 + ri * 20) * ct)
                        alpha = max(1, 4 - ri)
                        pygame.draw.circle(surface, PURPLE, (mid_x, y + 40), ring_r, alpha)

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
            
            pull_r = int(250 * (1.0 - ct))
            core_size = int(60 * ct + math.sin(t * 30) * 10)
            pygame.draw.circle(surface, (5, 5, 10), (mid_x, y + 60), core_size)
            pygame.draw.circle(surface, (100, 255, 255), (mid_x, y + 60), core_size + 5, max(1, int(15 * ct)))
            
            for _ in range(int(20 * ct) + 5):
                ang = random.uniform(0, math.pi * 2)
                p1_x = mid_x + math.cos(ang) * pull_r
                p1_y = y + 60 + math.sin(ang) * pull_r
                p2_x = mid_x + math.cos(ang + random.uniform(-0.2, 0.2)) * (pull_r * 0.6)
                p2_y = y + 60 + math.sin(ang + random.uniform(-0.2, 0.2)) * (pull_r * 0.6)
                
                pygame.draw.line(surface, BLACK, (p1_x, p1_y), (p2_x, p2_y), max(2, int(8 * ct)))
                pygame.draw.line(surface, WHITE, (p1_x, p1_y), (p2_x, p2_y), max(1, int(3 * ct)))
                
            if ct > 0.4:
                grid_alpha = int(255 * ((ct - 0.4) / 0.6))
                grid_len = int(300 * ct)
                pygame.draw.line(surface, (255, 255, 255, grid_alpha), (mid_x - grid_len, y + 60), (mid_x + grid_len, y + 60), 1)
                pygame.draw.line(surface, (255, 255, 255, grid_alpha), (mid_x, y + 60 - grid_len), (mid_x, y + 60 + grid_len), 1)

            if ct > 0.6:
                slash_len = int(250 * ((ct - 0.6) / 0.4))
                pygame.draw.line(surface, (200, 255, 255), (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 15)
                pygame.draw.line(surface, BLACK, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 8)
                pygame.draw.line(surface, WHITE, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 2)
                
            if ct > 0.95:
                pygame.draw.circle(surface, BLACK, (mid_x, y + 60), 800)
                pygame.draw.circle(surface, WHITE, (mid_x, y + 60), int(1000 * ((ct - 0.95)/0.05)), 20)

        if self.name == "Sukuna" and self.fuga_charge > 0:
            ct = (120 - self.fuga_charge) / 120.0

            pillar_h = int(220 * ct)
            pillar_w = int(22 + 65 * ct)
            pygame.draw.ellipse(surface, (255, 55, 0),
                (mid_x - pillar_w // 2, y + 40 - pillar_h // 2, pillar_w, pillar_h),
                max(1, int(9 * ct)))
            pygame.draw.ellipse(surface, (255, 180, 0),
                (mid_x - pillar_w // 4, y + 40 - pillar_h // 4, pillar_w // 2, pillar_h // 2),
                max(1, int(5 * ct)))

            pulse_r = int(50 * ct + 6 * math.sin(t * 18))
            pygame.draw.circle(surface, (255, 100, 0), (mid_x, y + 40), pulse_r, max(1, int(14 * ct)))
            pygame.draw.circle(surface, (255, 220, 0), (mid_x, y + 40), max(1, pulse_r // 2), max(1, int(6 * ct)))

            n_parts = int(8 + 30 * ct)
            for _ in range(n_parts):
                px = mid_x + random.randint(-int(90 * ct), int(90 * ct))
                py = y + 40 + random.randint(-int(90 * ct), int(90 * ct))
                size = random.randint(3, int(7 + 15 * ct))
                pygame.draw.circle(surface, random.choice([(255, 0, 0), (255, 110, 0), (255, 200, 0), (255, 255, 50)]),
                    (int(px), int(py)), size)

            if ct > 0.35:
                for ri in range(4):
                    ring_r = int((35 + ri * 28) * ct)
                    pygame.draw.circle(surface, (255, 80, 0), (mid_x, y + 40), ring_r, max(1, 4 - ri))

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
            for i in range(3):
                amp_y = y + 160 - ((t * 120 + i * 50) % 160)
                pulse_x = math.sin(t * 8 + i) * 8
                pygame.draw.ellipse(surface, (100, 180, 255), (mid_x - 40 + pulse_x, amp_y - 15, 80, 30), 2)
            
            glow_rect = self.rect.inflate(15 + math.sin(t * 15) * 5, 15 + math.cos(t * 15) * 5)
            
            self.amp_surf.fill((0,0,0,0)) 
            temp_rect = pygame.Rect(0, 0, glow_rect.width, glow_rect.height)
            pygame.draw.rect(self.amp_surf, (100, 150, 255, 40), temp_rect, border_radius=15)
            surface.blit(self.amp_surf, glow_rect.topleft)

        if self.name == "Mahoraga" or (self.name == "Sukuna" and (effect == "summoning" or getattr(self, "adapt_pulse_timer", 0) > 0)):
            wheel_center = (mid_x, y - 65)
            wheel_color = (190, 170, 50)
            
            if getattr(self, "adapt_pulse_timer", 0) > 0:
                pulse_progress = (30 - self.adapt_pulse_timer) / 30.0
                pulse_scale = 1.0 + (math.sin(pulse_progress * math.pi) * 1.5)
                pulse_alpha = int(255 * (1.0 - pulse_progress))
                
                pulse_surf = pygame.Surface((150, 150), pygame.SRCALPHA)
                center_offset = 75
                
                pygame.draw.circle(pulse_surf, (255, 255, 150, pulse_alpha), (center_offset, center_offset), int(45 * pulse_scale), max(1, int(6 * pulse_scale)))
                pygame.draw.circle(pulse_surf, (255, 255, 200, pulse_alpha), (center_offset, center_offset), int(8 * pulse_scale))
                
                angle_offset = math.radians(self.wheel_rotation)
                for i in range(8):
                    rad = math.radians(i * 45) + angle_offset
                    spoke_end = (center_offset + math.cos(rad) * 45 * pulse_scale, center_offset + math.sin(rad) * 45 * pulse_scale)
                    pygame.draw.line(pulse_surf, (255, 255, 150, pulse_alpha), (center_offset, center_offset), spoke_end, max(1, int(4 * pulse_scale)))
                    pygame.draw.circle(pulse_surf, (255, 255, 200, pulse_alpha), spoke_end, int(6 * pulse_scale))
                
                surface.blit(pulse_surf, (int(wheel_center[0]) - center_offset, int(wheel_center[1]) - center_offset))

            if self.adapting_to:
                pts = self.adaptation_points[self.adapting_to]
                turn_progress = (pts % 250) / 250.0
                total_turns = int(pts // 250)
                if total_turns > self.last_turn_count:
                    self.last_turn_count = total_turns
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

        scale = 2.0 if self.name == "Mahoraga" else 1.0
        w = self.rect.width
        h = self.rect.height
        
        if self.name == "Mahoraga":
            tail_points = []
            tail_x = mid_x + (15 * -self.direction)
            tail_y = y - 10
            for i in range(8):
                px = tail_x + (i * 15 * -self.direction)
                py = tail_y + (i * 26) + (i * i * 0.4)
                tail_points.append((int(px), int(py)))
                
            if len(tail_points) > 1:
                for i in range(len(tail_points) - 1):
                    t_thick = max(12, int(75 - (i * 7.5)))
                    inner_thick = max(1, t_thick - 12)
                    pygame.draw.line(surface, WHITE, tail_points[i], tail_points[i+1], t_thick)
                    pygame.draw.line(surface, (210, 210, 215), tail_points[i], tail_points[i+1], inner_thick)

        leg_off = math.sin(t * 12) * (15 * scale) if not self.on_ground and not self.is_paralyzed else 0
        thickness = 32 if self.name == "Mahoraga" else 12
        
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (mid_x - int(10*scale), y + int(90*scale)), (mid_x - int(15*scale) - leg_off, y + int(160*scale)), int(thickness))
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (mid_x + int(10*scale), y + int(90*scale)), (mid_x + int(15*scale) + leg_off, y + int(160*scale)), int(thickness))
        
        if self.name == "Mahoraga": 
            body_rect = [
                (x + int(5*scale), y),                        
                (x + w - int(5*scale), y),                    
                (x + w + int(5*scale), y + int(15*scale)),    
                (x + w - int(25*scale), y + int(100*scale)),  
                (x + int(25*scale), y + int(100*scale)),      
                (x - int(5*scale), y + int(15*scale))         
            ]
        else:
            body_rect = [(x+5, y+20), (x+65, y+20), (x+55, y+95), (x+15, y+95)]
            
        pygame.draw.polygon(surface, self.color, body_rect)
        
        if self.name == "Mahoraga":
            pygame.draw.ellipse(surface, (190, 190, 175), (mid_x - int(15*scale), y - int(5*scale), int(30*scale), int(25*scale)))

        if self.name == "Mahoraga":
            pants_rect = [
                (x + 10, y + int(90*scale)), 
                (x + w - 10, y + int(90*scale)), 
                (x + w + 15, y + int(135*scale)), 
                (mid_x, y + int(115*scale)), 
                (x - 15, y + int(135*scale))  
            ]
            pygame.draw.polygon(surface, BLACK, pants_rect)
        
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.7:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 10*scale), int(y + 40*scale)), int(8*scale))
        if hp_ratio < 0.4:
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 15*scale), int(y + 60*scale)), int(12*scale))
            pygame.draw.line(surface, BLOOD, (mid_x, y + int(30*scale)), (mid_x - int(15*scale), y + int(70*scale)), int(4*scale))
        if hp_ratio < 0.2:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 5*scale), int(y + 80*scale)), int(15*scale))
            pygame.draw.line(surface, BLOOD, (mid_x + int(10*scale), y + int(80*scale)), (mid_x + int(20*scale), y + int(90*scale)), int(5*scale))
        
        l_shoulder = (x + int(10*scale), y + int(35*scale))
        r_shoulder = (x + w - int(10*scale), y + int(35*scale))
        l_hand = (x + int(5*scale), y + int(85*scale))
        r_hand = (x + w - int(5*scale), y + int(85*scale))
        
        if self.punch_timer > 0 and not self.is_paralyzed:
            phase = (20 - self.punch_timer) / 20.0
            arm_ext = 60 * scale * math.sin(phase * math.pi)
            
            if self.punch_count % 2 == 1: 
                l_hand = (x + int(5*scale) - arm_ext * self.direction, y + int(65*scale) - (arm_ext * 0.2))
            else: 
                r_hand = (x + w - int(5*scale) + arm_ext * self.direction, y + int(65*scale) - (arm_ext * 0.2))
        
        arm_color = WHITE if self.name == "Mahoraga" else SKIN
        pygame.draw.line(surface, arm_color, l_shoulder, l_hand, int(thickness - 2))
        pygame.draw.line(surface, arm_color, r_shoulder, r_hand, int(thickness - 2))
        
        if self.name == "Mahoraga":
            blade_color = (180, 180, 195)
            blade_edge = WHITE
            
            wrist_x, wrist_y = l_hand
            
            arm_dx = l_hand[0] - l_shoulder[0]
            arm_dy = l_hand[1] - l_shoulder[1]
            arm_angle = math.atan2(arm_dy, arm_dx)
            
            rot = arm_angle - (math.pi / 2)

            def rot_pt(px, py):
                nx = px * math.cos(rot) - py * math.sin(rot)
                ny = px * math.sin(rot) + py * math.cos(rot)
                return (int(wrist_x + nx), int(wrist_y + ny))

            blade_poly = [
                rot_pt(-5 * scale, -4 * scale),
                rot_pt(5 * scale, -4 * scale),
                rot_pt(10 * scale, 25 * scale),
                rot_pt(0, 42 * scale),
                rot_pt(-7 * scale, 25 * scale)
            ]
            
            pygame.draw.polygon(surface, blade_color, blade_poly)
            pygame.draw.polygon(surface, blade_edge, blade_poly, max(1, int(1*scale)))
            
            pygame.draw.line(surface, (30, 30, 30), rot_pt(-8 * scale, -2 * scale), rot_pt(8 * scale, -2 * scale), int(4*scale))
            pygame.draw.line(surface, (30, 30, 30), rot_pt(-8 * scale, 5 * scale), rot_pt(8 * scale, 5 * scale), int(4*scale))

        head_color = WHITE if self.name == "Mahoraga" else SKIN
        pygame.draw.circle(surface, head_color, (mid_x, y), 30 if self.name == "Mahoraga" else 26)
        
        if self.name == "Sukuna":
            pygame.draw.line(surface, BLACK, (mid_x - 10, y + 5), (mid_x - 5, y + 15), 2)
            pygame.draw.line(surface, BLACK, (mid_x + 10, y + 5), (mid_x + 5, y + 15), 2)
            pygame.draw.circle(surface, BLACK, (mid_x, y + 18), 3) 
            
        if self.name == "Mahoraga":
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x - int(12*scale), y - int(8*scale)), (mid_x - int(48*scale), y - int(36*scale)), (mid_x - int(4*scale), y - int(14*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x - int(16*scale), y - int(2*scale)), (mid_x - int(58*scale), y - int(12*scale)), (mid_x - int(10*scale), y + int(4*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x + int(12*scale), y - int(8*scale)), (mid_x + int(48*scale), y - int(36*scale)), (mid_x + int(4*scale), y - int(14*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(mid_x + int(16*scale), y - int(2*scale)), (mid_x + int(58*scale), y - int(12*scale)), (mid_x + int(10*scale), y + int(4*scale))])
            mouth_w = int(14*scale)
            mouth_h = int(7*scale)
            mouth_rect = pygame.Rect(mid_x - mouth_w//2, y + int(8*scale), mouth_w, mouth_h)
            pygame.draw.ellipse(surface, (160, 190, 190), mouth_rect)
            pygame.draw.ellipse(surface, (30, 35, 40), mouth_rect, max(1, int(1.5*scale)))
            pygame.draw.line(surface, (30, 35, 40), (mid_x - mouth_w//2, y + int(8*scale) + mouth_h//2), (mid_x + mouth_w//2, y + int(8*scale) + mouth_h//2), max(1, int(1*scale)))
            for t_i in range(1, 5):
                t_x = (mid_x - mouth_w//2) + (t_i * (mouth_w // 5))
                pygame.draw.line(surface, (30, 35, 40), (t_x, y + int(8*scale)), (t_x, y + int(8*scale) + mouth_h), max(1, int(1*scale)))

        if self.rct_timer > 0:
            offsets = [-35, 0, 35] 
            for j, x_off in enumerate(offsets):
                for i in range(5): 
                    sx = mid_x + x_off + math.sin(t * 5 + i + j) * 15
                    sy = (y + int(160*scale)) - ((t * 80 + i * 40 + j * 20) % int(150*scale))
                    
                    r_color = [(150, 255, 150), (255, 255, 200), (100, 255, 150)][(i+j) % 3]
                    pygame.draw.circle(surface, r_color, (int(sx), int(sy)), 3)

        if self.name != "Mahoraga":
            h_color = WHITE if self.name == "Gojo" else (20, 20, 25)
            num_spikes = 5
            for i in range(num_spikes): 
                h_x = mid_x - int(25*scale) + i * 10
                pygame.draw.polygon(surface, h_color, [(h_x, y-5), (h_x+5, y-int(45*scale)), (h_x+10, y-5)])

    def draw_death(self, surface):
        mx, my = self.rect.centerx, self.rect.centery
        pygame.draw.line(surface, CLOTHES, (mx-10, my+10), (mx-20, my+80), 14)
        pygame.draw.line(surface, CLOTHES, (mx+10, my+10), (mx+20, my+80), 14)
        pygame.draw.rect(surface, BLOOD, (mx-25, my-10, 50, 15))
        pygame.draw.circle(surface, SKIN, (mx + 90, my + 60), 26)
        pygame.draw.rect(surface, CLOTHES, (mx + 70, my + 70, 80, 45))