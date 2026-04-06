import pygame # type: ignore
import math
import random
import time
from settings import *
from aura import draw_fighter_auras
from techniques import draw_special_techniques
from physics import update_fighter_physics

import json, os
class AIMemory:
    def __init__(self):
        self.path = "sukuna_memory.json"
        self.patterns = {"punch": [0, 0, 0], "blue": [0, 0, 0], "red": [0, 0, 0], "purple": [0, 0, 0], "pb_blue": [0, 0, 0]}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f: self.patterns = json.load(f)
            except: pass
    def save(self):
        with open(self.path, "w") as f: json.dump(self.patterns, f)
    def record(self, mid, dist, hit=False):
        if mid not in self.patterns: return
        d = self.patterns[mid]
        d[0] += 1
        if hit: d[1] += 1
        d[2] = (d[2] * 0.9) + (dist * 0.1)
    def get_threat(self, mid, dist):
        d = self.patterns[mid]
        if d[0] == 0: return 0.02
        dr = 1.0 - min(1.0, abs(dist - d[2]) / 500)
        uf = d[0] / max(1, sum(p[0] for p in self.patterns.values()))
        return max(0.01, uf * dr)

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
        self.max_sd_hits = 300 if name == "Sukuna" else 152 
        self.max_stance = 600
        self.stance = 600
        
        # --- OPTIMIZATION: Surface Caching ---
        self.inf_surf = pygame.Surface((220, 320), pygame.SRCALPHA)
        self.aura_surf = pygame.Surface((600, 600), pygame.SRCALPHA)
        self.sd_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
        self.amp_surf = pygame.Surface((150, 250), pygame.SRCALPHA)
        self.aura_hit_timer = 0 
        
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
        self.rct_particles = []
        self.aura_sway_x = 0 
        self.aura_sway_y = 0 
        self.prev_x_aura = x
        self.prev_y_aura = y

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
        self.ce_loss_accum = 0.0  
        self.ce_exhausted = False 
        self.anim_tick = 0   
        self.inf_hit_timer = 0    
        if name == "Sukuna": self.memory = AIMemory()    

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
            self.domain_cd = 120 
            self.technique_burnout = 0
        else:
            self.domain_cd = 3000
            self.technique_burnout = 1800
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
        update_fighter_physics(self, dt)

    def trigger_adaptation(self, phenomenon, intensity=1.0):
        if self.name != "Mahoraga": return
        
        if self.adapting_to != phenomenon:
            self.adapting_to = phenomenon
            
        self.adaptation_points[phenomenon] += intensity

    def draw_detailed(self, surface, is_punching=False, effect=None, is_amp=False):
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

        t = self.anim_tick * 0.016 
        t_real = time.time()
        
        if self.black_flash_timer > 0:
            for _ in range(15):
                rx, ry = random.randint(x-40, x+110), random.randint(y-40, y+200)
                pygame.draw.line(surface, BLACK, (rx, ry), (rx+random.randint(-40,40), ry+random.randint(-40,40)), 6)
                pygame.draw.line(surface, (255, 0, 0), (rx, ry), (rx+random.randint(-20,20), ry+random.randint(-20,20)), 3)

        # DOMAIN CHARGE
        if getattr(self, "domain_charge", 0) > 0:
            ct = (60 - self.domain_charge) / 60.0
            burst = int(180 * ct)
            dom_color = (200, 200, 255) if self.name == "Gojo" else (255, 50, 50)
            pygame.draw.circle(surface, dom_color, (mid_x, y + 40), burst, max(1, int(15 * (1 - ct))))
            if ct > 0.8:
                pygame.draw.circle(surface, WHITE, (mid_x, y + 40), int(burst * 1.2), 3)

        # AURAS
        draw_fighter_auras(self, surface, t, t_real)

        # SPECIAL TECHNIQUES
        draw_special_techniques(self, surface, t)

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