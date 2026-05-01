import pygame 
import math
import random
import time
from settings import *
from aura import draw_fighter_auras
from techniques import draw_special_techniques
from physics import update_fighter_physics

import json, os, base64
class AIMemory:
    def __init__(self):
        # Move storage to a hidden system folder
        appdata = os.getenv('APPDATA')
        save_dir = os.path.join(appdata, "GojoVsSukuna")
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        self.path = os.path.join(save_dir, "system_data.bin")
        
        self.patterns = {"punch": [0, 0, 0], "blue": [0, 0, 0], "red": [0, 0, 0], "purple": [0, 0, 0], "pb_blue": [0, 0, 0], "jump": [0, 0, 0], "dodge_left": [0, 0, 0], "dodge_right": [0, 0, 0], "domain": [0, 0, 0]}
        if os.path.exists(self.path):
            try:
                with open(self.path, "rb") as f:
                    # Decode the scrambled data
                    encoded_data = f.read()
                    decoded_data = base64.b64decode(encoded_data).decode('utf-8')
                    loaded = json.loads(decoded_data)
                    for k in self.patterns:
                        if k in loaded: self.patterns[k] = loaded[k]
            except: pass

    def save(self):
        try:
            # Scramble the JSON into Base64 gibberish
            json_string = json.dumps(self.patterns)
            encoded_data = base64.b64encode(json_string.encode('utf-8'))
            with open(self.path, "wb") as f:
                f.write(encoded_data)
        except: pass
        self.patterns = {"punch": [0, 0, 0], "blue": [0, 0, 0], "red": [0, 0, 0], "purple": [0, 0, 0], "pb_blue": [0, 0, 0], "jump": [0, 0, 0], "dodge_left": [0, 0, 0], "dodge_right": [0, 0, 0], "domain": [0, 0, 0]}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f: 
                    loaded = json.load(f)
                    for k in self.patterns:
                        if k in loaded: self.patterns[k] = loaded[k]
            except: pass
    def save(self):
        with open(self.path, "w") as f: json.dump(self.patterns, f)
    def record(self, mid, dist, hit=False):
        if mid not in self.patterns: return
        d = self.patterns[mid]
        d[0] += 10
        if hit: d[1] += 10
        d[2] = (d[2] * 0.1) + (dist * 0.9)
    def get_threat(self, mid, dist):
        d = self.patterns[mid]
        if d[0] == 0: return 0.0
        acc = d[1] / d[0]
        dr = 1.0 - min(1.0, abs(dist - d[2]) / 500)
        uf = min(1.0, d[0] / 10.0)
        return max(0.0, uf * dr * (0.4 + (acc * 0.6)))

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
        
        # --- RIGGING SYSTEM (BONE OFFSETS) ---
        self.rig = {
            "head": [0, 0],
            "l_shoulder": [10, 35],
            "r_shoulder": [60, 35],
            "l_elbow": [7, 60],
            "r_elbow": [63, 60],
            "l_hand": [5, 85],
            "r_hand": [65, 85],
            "torso_top": [5, 20],
            "torso_bottom": [15, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        if name == "Mahoraga":
            del self.rig["torso_top"]
            del self.rig["torso_bottom"]
            self.rig["l_shoulder"] = [1, 63]
            self.rig["r_shoulder"] = [139, 63]
            self.rig["l_elbow"] = [-1, 109]
            self.rig["r_elbow"] = [141, 109]
            self.rig["l_hand"] = [10, 160]
            self.rig["r_hand"] = [130, 160]
            self.rig["torso_top_l"] = [10, 40]
            self.rig["torso_top_r"] = [130, 40]
            self.rig["chest_l"] = [-5, 55]
            self.rig["chest_r"] = [145, 55]
            self.rig["waist_l"] = [25, 180]
            self.rig["waist_r"] = [115, 180]
            self.rig["torso_bottom"] = [30, 180] # Keep for leg logic
            self.rig["l_foot"] = [30, 310]
            self.rig["r_foot"] = [110, 310]

        self.maho_punch_poses = [
            # Pose before punching or when near
            {
                "head": [0, 0], "l_shoulder": [9, 52], "r_shoulder": [123, 56],
                "l_elbow": [-27, 82], "r_elbow": [165, 78], "l_hand": [-28, 127], "r_hand": [166, 126],
                "l_foot": [30, 310], "r_foot": [110, 310],
                "torso_top_l": [10, 40], "torso_top_r": [130, 40], "chest_l": [-5, 55], "chest_r": [145, 55],
                "waist_l": [25, 180], "waist_r": [115, 180], "torso_bottom": [30, 180]
            },
            # Punching animation 1
            {
                "head": [-5, 20], "l_shoulder": [28, 41], "r_shoulder": [105, 97],
                "l_elbow": [-21, 22], "r_elbow": [50, 143], "l_hand": [-38, 92], "r_hand": [-5, 190],
                "l_foot": [30, 310], "r_foot": [110, 310],
                "torso_top_l": [15, 27], "torso_top_r": [106, 47], "chest_l": [7, 79], "chest_r": [134, 75],
                "waist_l": [29, 183], "waist_r": [107, 185], "torso_bottom": [27, 183]
            },
            # Punching animation 2
            {
                "head": [-4, 13], "l_shoulder": [26, 64], "r_shoulder": [128, 34],
                "l_elbow": [-11, 116], "r_elbow": [183, 30], "l_hand": [-43, 162], "r_hand": [163, 97],
                "l_foot": [30, 310], "r_foot": [110, 310],
                "torso_top_l": [18, 47], "torso_top_r": [127, 19], "chest_l": [4, 74], "chest_r": [131, 77],
                "waist_l": [27, 182], "waist_r": [113, 178], "torso_bottom": [30, 180]
            }
        ]
            
        self.punch_poses = [
            # Preparing / Stance
            {
                "head": [0, 0], "l_shoulder": [10, 35], "r_shoulder": [60, 35],
                "l_elbow": [5, 59], "r_elbow": [82, 52], "l_hand": [40, 44], "r_hand": [111, 29],
                "torso_top": [5, 20], "torso_bottom": [15, 95], "l_foot": [15, 155], "r_foot": [55, 155]
            },
            # Punch Animation 1
            {
                "head": [0, 0], "l_shoulder": [10, 35], "r_shoulder": [67, 27],
                "l_elbow": [13, 60], "r_elbow": [102, 30], "l_hand": [46, 45], "r_hand": [134, 31],
                "torso_top": [5, 20], "torso_bottom": [15, 95], "l_foot": [15, 155], "r_foot": [55, 155]
            },
            # Punch Animation 2
            {
                "head": [0, 0], "l_shoulder": [10, 35], "r_shoulder": [64, 27],
                "l_elbow": [58, 37], "r_elbow": [75, 55], "l_hand": [113, 38], "r_hand": [87, 19],
                "torso_top": [5, 20], "torso_bottom": [15, 95], "l_foot": [15, 155], "r_foot": [55, 155]
            }
        ]
        
        self.grab_poses = [
            {
                "head": [0, 0], "l_shoulder": [11, 30], "r_shoulder": [62, 32],
                "l_elbow": [-21, 38], "r_elbow": [82, 40], "l_hand": [15, 51], "r_hand": [108, 34],
                "torso_top": [5, 20], "torso_bottom": [15, 95], "l_foot": [15, 155], "r_foot": [55, 155]
            },
            {
                "head": [0, 0], "l_shoulder": [11, 30], "r_shoulder": [62, 32],
                "l_elbow": [50, 29], "r_elbow": [77, 40], "l_hand": [90, 22], "r_hand": [104, 34],
                "torso_top": [5, 20], "torso_bottom": [15, 95], "l_foot": [15, 155], "r_foot": [55, 155]
            }
        ]
        
        self.block_pose = {
            "head": [1, -1],
            "l_shoulder": [10, 35],
            "r_shoulder": [60, 35],
            "l_elbow": [24, 49],
            "r_elbow": [45, 50],
            "l_hand": [23, 2],
            "r_hand": [46, 2],
            "torso_top": [5, 20],
            "torso_bottom": [15, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        
        self.summon_pose = {
            "head": [0, 0],
            "l_shoulder": [11, 34],
            "r_shoulder": [60, 35],
            "l_elbow": [-3, 53],
            "r_elbow": [54, 60],
            "l_hand": [-21, 44],
            "r_hand": [27, 38],
            "torso_top": [5, 20],
            "torso_bottom": [15, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        
        self.gojo_domain_pose = {
            "head": [0, 0],
            "l_shoulder": [10, 35],
            "r_shoulder": [60, 35],
            "l_elbow": [23, 60],
            "r_elbow": [63, 60],
            "l_hand": [36, 16],
            "r_hand": [65, 85],
            "torso_top": [5, 20],
            "torso_bottom": [15, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        
        self.sukuna_domain_pose = {
            "head": [0, 0],
            "l_shoulder": [10, 35],
            "r_shoulder": [60, 35],
            "l_elbow": [7, 60],
            "r_elbow": [63, 60],
            "l_hand": [32, 38],
            "r_hand": [38, 38],
            "torso_top": [5, 20],
            "torso_bottom": [15, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        
        self.hit_pose = {
            "head": [-2, 0],
            "l_shoulder": [8, 31],
            "r_shoulder": [62, 35],
            "l_elbow": [-3, 51],
            "r_elbow": [72, 50],
            "l_hand": [4, 74],
            "r_hand": [79, 69],
            "torso_top": [6, 20],
            "torso_bottom": [16, 95],
            "l_foot": [15, 155],
            "r_foot": [55, 155]
        }
        
        # --- REFACTOR: Combat Realism & Feedback ---
        self.hit_stop = 0
        self.particles = []
        self.active_hitbox = None
        self.stun_timer = 0
        self.is_blocking = False

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

    def draw_detailed(self, surface, is_punching=False, effect=None, is_amp=False, show_auras=True, forced_pose_index=None):
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
        
        if getattr(self, "stun_timer", 0) > 0:
            kb_offset = (self.stun_timer / 15.0) * 15 * -self.direction
            x += kb_offset
            mid_x += kb_offset

        if self.grab_timer > 0:
            if hasattr(self, "grabber") and self.grabber and hasattr(self.grabber, "last_active_rig"):
                g = self.grabber
                hand_pt = g.last_active_rig.get("r_hand", [0, 0])
                hx = g.rect.x + hand_pt[0] if g.direction == 1 else g.rect.x + g.rect.width - hand_pt[0]
                hy = g.rect.y + hand_pt[1]
                
                # Glue this fighter's neck to the grabbing hand
                my_neck_y = self.rig.get("torso_top", [5, 20])[1]
                x = hx - (self.rect.width // 2)
                y = hy - my_neck_y + 10
                mid_x = x + (self.rect.width // 2)
                
                # Sync underlying physics rect to visual lock
                self.rect.x = int(x)
                self.rect.y = int(y)

        ragdoll_angle = 0
                
        if self.hp <= 0 or getattr(self, "is_split", False):
            self.draw_death(surface)
            return

        t = self.anim_tick * 0.016 
        t_real = time.time()
        
        if self.black_flash_timer > 0:
            for _ in range(15):
                rx, ry = random.randint(int(x-40), int(x+110)), random.randint(int(y-40), int(y+200))
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
        if show_auras:
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
                visual_steps = total_turns // 4
                if visual_steps > self.last_turn_count:
                    self.last_turn_count = visual_steps
                    pygame.draw.circle(surface, WHITE, wheel_center, 60, 2)
                
                self.wheel_rotation = ((total_turns + turn_progress) * 45) / 4
            
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
        
        # Tail logic moved after head calculation for head-gluing
        pass

        active_rig = self.rig
        if forced_pose_index is not None:
            poses = self.maho_punch_poses if self.name == "Mahoraga" else self.punch_poses
            if 0 <= forced_pose_index < len(poses):
                active_rig = poses[forced_pose_index]
        elif getattr(self, "punch_timer", 0) > 0 and not self.is_paralyzed and self.stun_timer <= 0:
            phase = (20 - self.punch_timer) / 20.0
            poses = self.maho_punch_poses if self.name == "Mahoraga" else self.punch_poses
            
            if self.name == "Mahoraga":
                if phase < 0.12:
                    active_rig = poses[0]
                else:
                    active_rig = poses[1] if self.punch_count % 2 == 1 else poses[2]
            else:
                # Gojo/Sukuna also alternate between Strike 1 and Strike 2
                if getattr(self, "is_grabbing_attack", False):
                    active_rig = self.grab_poses[0] if phase < 0.4 else self.grab_poses[1]
                elif phase < 0.2:
                    active_rig = poses[0]
                else:
                    # Alternates based on punch count (Pose 1 then Pose 2)
                    active_rig = poses[1] if self.punch_count % 2 == 1 else poses[2]
        elif getattr(self, "domain_charge", 0) > 0:
            active_rig = self.gojo_domain_pose if self.name == "Gojo" else self.sukuna_domain_pose
        elif getattr(self, "summon_timer", 0) > 0 and self.name == "Sukuna":
            active_rig = self.summon_pose
        elif getattr(self, "stun_timer", 0) > 0 and self.name != "Mahoraga":
            active_rig = self.hit_pose
        elif self.is_blocking:
            active_rig = self.block_pose

        if getattr(self, "grab_timer", 0) > 0 and hasattr(self, "grabber") and self.grabber:
            rag_t = getattr(self, "anim_tick", 0) * 0.016
            sway = math.sin(rag_t * 6) * 0.08
            rag_angle = (0.25 + sway) * -self.grabber.direction
            
            rotated_rig = {}
            if "torso_top" in active_rig:
                neck_y = active_rig["torso_top"][1]
                t_top_l = active_rig["torso_top"]
                t_top_r = [w - active_rig["torso_top"][0], active_rig["torso_top"][1]]
                t_bot_l = active_rig["torso_bottom"]
                t_bot_r = [w - active_rig["torso_bottom"][0], active_rig["torso_bottom"][1]]
                base_points = list(active_rig.items()) + [("torso_top_l", t_top_l), ("torso_top_r", t_top_r), ("torso_bottom_l", t_bot_l), ("torso_bottom_r", t_bot_r)]
            else:
                neck_y = active_rig.get("torso_top_l", [10, 40])[1]
                base_points = list(active_rig.items())
                
            pivot_x = w / 2.0
            
            for k, v in base_points:
                if isinstance(v, list) and len(v) == 2:
                    if k in ["head", "torso_top", "torso_bottom", "torso_top_l", "torso_top_r", "torso_bottom_l", "torso_bottom_r", "chest_l", "chest_r", "waist_l", "waist_r", "l_shoulder", "r_shoulder"]:
                        rotated_rig[k] = v
                        continue
                        
                    if k in ["l_elbow", "l_hand"]:
                        p_x, p_y = active_rig.get("l_shoulder", [pivot_x, neck_y])
                    elif k in ["r_elbow", "r_hand"]:
                        p_x, p_y = active_rig.get("r_shoulder", [pivot_x, neck_y])
                    elif k == "l_foot":
                        p_x, p_y = active_rig.get("torso_bottom_l", active_rig.get("torso_bottom", [pivot_x, neck_y]))
                    elif k == "r_foot":
                        p_x, p_y = active_rig.get("torso_bottom_r", active_rig.get("torso_bottom", [pivot_x, neck_y]))
                    else:
                        p_x, p_y = pivot_x, neck_y
                        
                    true_x = v[0]
                    dx = true_x - p_x
                    dy = v[1] - p_y
                    nx = dx * math.cos(rag_angle) - dy * math.sin(rag_angle)
                    ny = dx * math.sin(rag_angle) + dy * math.cos(rag_angle)
                    rotated_rig[k] = [p_x + nx, p_y + ny]
                else:
                    rotated_rig[k] = v
            active_rig = rotated_rig

        self.last_active_rig = active_rig

        def get_pt(pt_name):
            lookup = pt_name
            if self.direction == -1:
                if pt_name.startswith("l_"): lookup = "r_" + pt_name[2:]
                elif pt_name.startswith("r_"): lookup = "l_" + pt_name[2:]
                elif pt_name.endswith("_l"): lookup = pt_name[:-2] + "_r"
                elif pt_name.endswith("_r"): lookup = pt_name[:-2] + "_l"
                
            px, py = active_rig.get(lookup, active_rig.get(pt_name, (0, 0)))
            if self.direction == -1:
                return (x + w - px, y + py)
            return (x + px, y + py)

        leg_off = math.sin(t * 12) * (15 * scale) if not self.on_ground and not self.is_paralyzed else 0
        thickness = 32 if self.name == "Mahoraga" else 12
        
        l_foot_pt = get_pt("l_foot")
        r_foot_pt = get_pt("r_foot")
        
        if getattr(self, "grab_timer", 0) > 0 and "torso_bottom_l" in active_rig:
            tb_l = get_pt("torso_bottom_l")
            tb_r = get_pt("torso_bottom_r")
            bot_mid_x = (tb_l[0] + tb_r[0]) / 2
            l_hip_x = bot_mid_x - 10
            r_hip_x = bot_mid_x + 10
        else:
            l_hip_x = mid_x - 10
            r_hip_x = mid_x + 10

        # DRAW TAIL FIRST (to be behind the body)
        if self.name == "Mahoraga":
            # Smoothly animate the tail direction when mirroring (reacts over time)
            if not hasattr(self, "tail_visual_dir"): self.tail_visual_dir = float(-self.direction)
            target_tail_dir = float(-self.direction)
            self.tail_visual_dir += (target_tail_dir - self.tail_visual_dir) * 0.1

            # Calculate head position early for tail gluing
            head_x_off = active_rig["head"][0]
            if self.direction == -1: head_x_off = -head_x_off
            hx_tail = mid_x + head_x_off
            hy_tail = y + active_rig["head"][1]

            tail_points = []
            tail_x = hx_tail 
            tail_y = hy_tail + 5
            
            wave_speed = 1.5
            wave_amount = 8
            
            for i in range(8):
                # Each segment waves with a slight delay for a "flowing" effect
                offset_x = math.sin(t * wave_speed + i * 0.4) * wave_amount
                offset_y = math.cos(t * wave_speed + i * 0.4) * (wave_amount * 0.6)
                
                # px: stretches out more horizontally, now uses visual_dir for smooth swing
                px = tail_x + (i * 22 * self.tail_visual_dir) + offset_x
                py = tail_y + (i * 12) + offset_y
                tail_points.append((int(px), int(py)))
                
            if len(tail_points) > 1:
                for i in range(len(tail_points) - 1):
                    t_thick = max(12, int(75 - (i * 7.5)))
                    inner_thick = max(1, t_thick - 12)
                    pygame.draw.line(surface, WHITE, tail_points[i], tail_points[i+1], t_thick)
                    pygame.draw.line(surface, (210, 210, 215), tail_points[i], tail_points[i+1], inner_thick)
        
        hip_y = y + active_rig.get("torso_bottom_l", active_rig.get("torso_bottom", [0, 95]))[1]
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (l_hip_x, hip_y), (l_foot_pt[0] - leg_off, l_foot_pt[1]), int(thickness))
        pygame.draw.line(surface, self.color if self.name != "Mahoraga" else (180, 180, 160), (r_hip_x, hip_y), (r_foot_pt[0] + leg_off, r_foot_pt[1]), int(thickness))
        
        if self.name == "Mahoraga": 
            body_rect = [
                get_pt("torso_top_l"),                        
                get_pt("torso_top_r"),                    
                get_pt("chest_r"),    
                get_pt("waist_r"),  
                get_pt("waist_l"),      
                get_pt("chest_l")         
            ]
        else:
            if "torso_top_l" in active_rig:
                body_rect = [
                    get_pt("torso_top_l"), 
                    get_pt("torso_top_r"), 
                    get_pt("torso_bottom_r"), 
                    get_pt("torso_bottom_l")
                ]
            else:
                body_rect = [
                    (x + active_rig["torso_top"][0], y + active_rig["torso_top"][1]), 
                    (x + w - active_rig["torso_top"][0], y + active_rig["torso_top"][1]), 
                    (x + w - active_rig["torso_bottom"][0], y + active_rig["torso_bottom"][1]), 
                    (x + active_rig["torso_bottom"][0], y + active_rig["torso_bottom"][1])
                ]
            
        pygame.draw.polygon(surface, self.color, body_rect)


        
        if self.name == "Mahoraga":
            # Chest highlight removed as requested
            pass

        if self.name == "Mahoraga":
            # Pants follow the waist joints
            w_l = get_pt("waist_l")
            w_r = get_pt("waist_r")
            pants_rect = [
                (w_l[0] - 15, w_l[1]), 
                (w_r[0] + 15, w_r[1]), 
                (w_r[0] + 25, w_r[1] + int(45*scale)), 
                ((w_l[0] + w_r[0])//2, w_l[1] + int(25*scale)), 
                (w_l[0] - 25, w_l[1] + int(45*scale))  
            ]
            pygame.draw.polygon(surface, BLACK, pants_rect)
        
        l_shoulder = get_pt("l_shoulder")
        r_shoulder = get_pt("r_shoulder")
        l_elbow = get_pt("l_elbow")
        r_elbow = get_pt("r_elbow")
        l_hand = get_pt("l_hand")
        r_hand = get_pt("r_hand")
        
        if self.name == "Mahoraga" and getattr(self, "punch_timer", 0) > 0:
            print(f"DEBUG [Mahoraga Punch]: Direction={self.direction} | R_HAND_RIG={active_rig['r_hand']} | DRAW_POS={r_hand}")
        
        if self.name == "Mahoraga" and getattr(self, "punch_timer", 0) > 0 and not self.is_paralyzed and self.stun_timer <= 0:
            # Legacy math extension removed to favor the new Rigging System
            pass
        
        arm_color = WHITE if self.name == "Mahoraga" else SKIN
        
        # Draw arms with direction-based Z-layering (Back arm first, Front arm last)
        def draw_l_arm():
            pygame.draw.line(surface, arm_color, l_shoulder, l_elbow, int(thickness - 2))
            pygame.draw.line(surface, arm_color, l_elbow, l_hand, int(thickness - 2))
        def draw_r_arm():
            pygame.draw.line(surface, arm_color, r_shoulder, r_elbow, int(thickness - 2))
            pygame.draw.line(surface, arm_color, r_elbow, r_hand, int(thickness - 2))

        if self.direction == 1:
            draw_l_arm()
            draw_r_arm()
        else:
            draw_r_arm()
            draw_l_arm()
        
        if self.name == "Mahoraga":
            blade_color = (180, 180, 195)
            blade_edge = WHITE
            
            wrist_x, wrist_y = l_hand
            
            arm_dx = l_hand[0] - l_elbow[0]
            arm_dy = l_hand[1] - l_elbow[1]
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

        head_x_off = active_rig["head"][0]
        if self.direction == -1: head_x_off = -head_x_off
        hx = mid_x + head_x_off
        hy = y + active_rig["head"][1]
        
        head_color = WHITE if self.name == "Mahoraga" else SKIN
        if self.name == "Mahoraga":
            # Rounded square head for a more monstrous/statue-like look
            h_rad = 30
            head_rect = pygame.Rect(hx - h_rad, hy - h_rad, h_rad * 2, h_rad * 2)
            pygame.draw.rect(surface, head_color, head_rect, border_radius=20)
        else:
            pygame.draw.circle(surface, head_color, (int(hx), int(hy)), 26)

        if self.name == "Sukuna":
            pygame.draw.line(surface, BLACK, (hx - 10, hy + 5), (hx - 5, hy + 15), 2)
            pygame.draw.line(surface, BLACK, (hx + 10, hy + 5), (hx + 5, hy + 15), 2)
            pygame.draw.circle(surface, BLACK, (int(hx), int(hy + 18)), 3) 
            
        if self.name == "Mahoraga":
            pygame.draw.polygon(surface, MAHO_COLOR, [(hx - int(12*scale), hy - int(8*scale)), (hx - int(48*scale), hy - int(36*scale)), (hx - int(4*scale), hy - int(14*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(hx - int(16*scale), hy - int(2*scale)), (hx - int(58*scale), hy - int(12*scale)), (hx - int(10*scale), hy + int(4*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(hx + int(12*scale), hy - int(8*scale)), (hx + int(48*scale), hy - int(36*scale)), (hx + int(4*scale), hy - int(14*scale))])
            pygame.draw.polygon(surface, MAHO_COLOR, [(hx + int(16*scale), hy - int(2*scale)), (hx + int(58*scale), hy - int(12*scale)), (hx + int(10*scale), hy + int(4*scale))])
            mouth_w = int(14*scale)
            mouth_h = int(7*scale)
            mouth_rect = pygame.Rect(hx - mouth_w//2, hy + int(8*scale), mouth_w, mouth_h)
            pygame.draw.ellipse(surface, (160, 190, 190), mouth_rect)
            pygame.draw.ellipse(surface, (30, 35, 40), mouth_rect, max(1, int(1.5*scale)))
            pygame.draw.line(surface, (30, 35, 40), (hx - mouth_w//2, hy + int(8*scale) + mouth_h//2), (hx + mouth_w//2, hy + int(8*scale) + mouth_h//2), max(1, int(1*scale)))
            for t_i in range(1, 5):
                t_x = (hx - mouth_w//2) + (t_i * (mouth_w // 5))
                pygame.draw.line(surface, (30, 35, 40), (t_x, hy + int(8*scale)), (t_x, hy + int(8*scale) + mouth_h), max(1, int(1*scale)))

        if self.name != "Mahoraga":
            h_color = WHITE if self.name == "Gojo" else (20, 20, 25)
            num_spikes = 5
            for i in range(num_spikes): 
                h_x = hx - int(25*scale) + i * 10
                pygame.draw.polygon(surface, h_color, [(h_x, hy-5), (h_x+5, hy-int(45*scale)), (h_x+10, hy-5)])

        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.9:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 12*scale), int(y + 30*scale)), int(4*scale))
        if hp_ratio < 0.8:
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 18*scale), int(y + 45*scale)), int(5*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x + 18*scale), int(y + 45*scale)), (int(mid_x + 10*scale), int(y + 55*scale)), int(3*scale))
        if hp_ratio < 0.7:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 10*scale), int(y + 40*scale)), int(8*scale))
        if hp_ratio < 0.6:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 22*scale), int(y + 60*scale)), int(6*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x - 22*scale), int(y + 60*scale)), (int(mid_x - 15*scale), int(y + 75*scale)), int(4*scale))
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 5*scale), int(y + 20*scale)), int(5*scale)) # head/neck
        if hp_ratio < 0.5:
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 25*scale), int(y + 80*scale)), int(9*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x + 5*scale), int(y + 20*scale)), (int(mid_x + 15*scale), int(y + 40*scale)), int(3*scale))
        if hp_ratio < 0.4:
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 15*scale), int(y + 60*scale)), int(12*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x), int(y + 30*scale)), (int(mid_x - 15*scale), int(y + 70*scale)), int(4*scale))
        if hp_ratio < 0.3:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 12*scale), int(y - 12*scale)), int(5*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x - 10*scale), int(y + 40*scale)), (int(mid_x - 15*scale), int(y + 70*scale)), int(6*scale))
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 10*scale), int(y - 15*scale)), int(4*scale))
        if hp_ratio < 0.2:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 5*scale), int(y + 80*scale)), int(15*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x + 10*scale), int(y + 80*scale)), (int(mid_x + 20*scale), int(y + 90*scale)), int(5*scale))
            pygame.draw.line(surface, BLOOD, (int(mid_x + 18*scale), int(y - 10*scale)), (int(mid_x + 20*scale), int(y + 15*scale)), int(3*scale)) # Drips down right cheek
        if hp_ratio < 0.1:
            pygame.draw.circle(surface, BLOOD, (int(mid_x - 12*scale), int(y + 8*scale)), int(8*scale)) # Covers left eye
            pygame.draw.line(surface, BLOOD, (int(mid_x - 12*scale), int(y + 8*scale)), (int(mid_x - 18*scale), int(y + 25*scale)), int(4*scale)) # Drips down left cheek
            pygame.draw.circle(surface, BLOOD, (int(mid_x + 5*scale), int(y - 18*scale)), int(6*scale)) # Forehead cut

    def draw_death(self, surface):
        mx, my = self.rect.centerx, self.rect.centery
        if self.name == "Gojo":
            pygame.draw.line(surface, CLOTHES, (mx-10, my+10), (mx-20, my+80), 14)
            pygame.draw.line(surface, CLOTHES, (mx+10, my+10), (mx+20, my+80), 14)
            pygame.draw.rect(surface, BLOOD, (mx-25, my-10, 50, 15))
            pygame.draw.circle(surface, SKIN, (mx + 90, my + 60), 26)
            pygame.draw.rect(surface, CLOTHES, (mx + 70, my + 70, 80, 45))
        elif self.name == "Sukuna":
            pygame.draw.circle(surface, BLOOD, (mx, my+20), 45)
            for _ in range(25):
                rx, ry = mx + random.randint(-80, 80), my + random.randint(-40, 100)
                pygame.draw.circle(surface, BLOOD, (rx, ry), random.randint(5, 18))
            pygame.draw.circle(surface, SKIN, (mx - 60, my + 80), 24)
            pygame.draw.line(surface, SKIN, (mx + 50, my + 80), (mx + 90, my + 90), 14)
            pygame.draw.line(surface, SKIN, (mx + 20, my + 110), (mx + 40, my + 130), 16)
        elif self.name == "Mahoraga":
            pygame.draw.circle(surface, BLOOD, (mx, my+20), 60)
            for _ in range(30):
                rx, ry = mx + random.randint(-100, 100), my + random.randint(-60, 120)
                pygame.draw.circle(surface, BLOOD, (rx, ry), random.randint(8, 22))
            pygame.draw.circle(surface, WHITE, (mx + 70, my + 80), 28) 
            for _ in range(8):
                pygame.draw.line(surface, (200, 200, 180), (mx + random.randint(-80, 80), my - random.randint(0, 100)), 
                                 (mx + random.randint(-80, 80), my - random.randint(0, 100)), random.randint(4, 10))