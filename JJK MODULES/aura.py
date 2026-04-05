import pygame # type: ignore
import math
import random
import time
from settings import *

def draw_fighter_auras(self, surface, t, t_real):
    x, y, mid_x = self.rect.centerx - (self.rect.width // 2), self.rect.y, self.rect.centerx

    # --- SIMPLE DOMAIN ---
    if self.simple_domain_active:
        self.sd_surf.fill((0,0,0,0)) 
        pygame.draw.circle(self.sd_surf, (200, 200, 255, 40), (90, 90), 90)
        pygame.draw.circle(self.sd_surf, (255, 255, 255, 120), (90, 90), 90, 3)
        pulse = (math.sin(t_real * 10) + 1) * 0.5 
        pygame.draw.circle(self.sd_surf, (200, 200, 255, int(100 * pulse)), (90, 90), 85, 1)
        surface.blit(self.sd_surf, (mid_x - 90, y + 80 - 90))

    # --- CE REINFORCEMENT AURA ---
    if self.aura_hit_timer > 0:
        aura_color = PURPLE if self.name == "Gojo" else BLUE if self.name == "Sukuna" else MAHO_COLOR
        self.aura_surf.fill((0,0,0,0))
        aura_w, aura_h = (180, 400) if self.name == "Mahoraga" else (85, 280)
        center_x, center_y = 300, 300
        points = []
        num_segments = 24 
        for i in range(num_segments):
            angle = (i / num_segments) * math.pi * 2
            base_x = math.cos(angle) * (aura_w / 2)
            base_y = math.sin(angle) * (aura_h / 2)
            h_ratio = abs(base_x) / (aura_w / 2)
            y_ratio = (base_y + (aura_h / 2)) / aura_h
            v_stabilizer = math.sin(y_ratio * math.pi) 
            sway_weight = h_ratio * v_stabilizer
            m_lag_x = -self.aura_sway_x * 3.5 
            is_front = (base_x > 0 and m_lag_x < 0) or (base_x < 0 and m_lag_x > 0)
            if is_front: m_lag_x *= 0.060 
            else: m_lag_x *= 0.30 
            edge_wiggle = math.sin(t * 6 + i * 0.8) * 7
            pulse = math.sin(t * 10 + i) * 5
            px = base_x + (base_x / (aura_w/2)) * pulse + edge_wiggle + (m_lag_x * sway_weight)
            py = base_y + (base_y / (aura_h/2)) * pulse + edge_wiggle + (-self.aura_sway_y * 1.2 * sway_weight)
            if py > self.rect.height // 2: py = self.rect.height // 2
            points.append((center_x + px, center_y + py))

        for _ in range(4):
            jitter_pts = [(p[0] + random.uniform(-3, 3), p[1] + random.uniform(-3, 3)) for p in points]
            pygame.draw.polygon(self.aura_surf, (0, 0, 0, 200), jitter_pts, random.randint(6, 12))

        pygame.draw.polygon(self.aura_surf, (*aura_color, 100), points)
        for layer in range(3):
            alpha = [220, 150, 90][layer] 
            thick = [1, 2, 4][layer]
            pygame.draw.polygon(self.aura_surf, (*aura_color, alpha), points, thick)
        surface.blit(self.aura_surf, (mid_x - 300, y + (self.rect.height // 2) - 300))

    # --- RCT MINI-AURA ---
    if self.rct_timer > 0:
        rct_color = (255, 255, 255)
        self.aura_surf.fill((0,0,0,0)) 
        soft_alpha = int(80 + math.sin(t_real * 25) * 30)
        aura_w, aura_h = (160, 250) if self.name == "Mahoraga" else (70, 260)
        center_x, center_y = 300, 300
        points = []
        num_segments = 20 
        for i in range(num_segments):
            angle = (i / num_segments) * math.pi * 2
            base_x = math.cos(angle) * (aura_w / 2)
            base_y = math.sin(angle) * (aura_h / 2)
            h_ratio = abs(base_x) / (aura_w / 2)
            y_ratio = (base_y + (aura_h / 2)) / aura_h
            v_stabilizer = math.sin(y_ratio * math.pi) 
            sway_weight = h_ratio * v_stabilizer
            m_lag_x = -self.aura_sway_x * 2.0 
            is_front = (base_x > 0 and m_lag_x < 0) or (base_x < 0 and m_lag_x > 0)
            if is_front: m_lag_x *= 0.05 
            else: m_lag_x *= 0.25 
            edge_wiggle = math.sin(t * 8 + i * 1.5) * 4
            pulse = math.sin(t * 12 + i) * 3
            px = base_x + (base_x / (aura_w/2)) * pulse + edge_wiggle + (m_lag_x * sway_weight)
            py = base_y + (base_y / (aura_h/2)) * pulse + edge_wiggle + (-self.aura_sway_y * 0.8 * sway_weight)
            if py > self.rect.height // 2: py = self.rect.height // 2
            points.append((center_x + px, center_y + py))

        for _ in range(3):
            jitter_pts = [(p[0] + random.uniform(-2, 2), p[1] + random.uniform(-2, 2)) for p in points]
            pygame.draw.polygon(self.aura_surf, (0, 0, 0, 220), jitter_pts, random.randint(4, 8))

        pygame.draw.polygon(self.aura_surf, (*rct_color, soft_alpha), points)
        pygame.draw.polygon(self.aura_surf, (*rct_color, min(255, soft_alpha + 40)), points, 2)
        pygame.draw.polygon(self.aura_surf, (255, 255, 255, soft_alpha), points, 1)
        surface.blit(self.aura_surf, (mid_x - 300, y + (self.rect.height // 2) - 300))

    # --- INFINITY AURA ---
    if self.name == "Gojo":
        has_active_infinity = self.infinity > 0 and self.technique_burnout == 0 and not getattr(self, "dev_disable_infinity", False)
        is_hit = self.hp < self.prev_hp or self.energy < self.prev_energy or self.grab_timer > 0 or self.inf_hit_timer > 0
        is_bypassed = (self.hp < self.prev_hp) and not (self.inf_hit_timer > 0)

        if has_active_infinity and (self.inf_hit_timer > 0 or (is_hit and not is_bypassed)):
            alpha_base = 150 
            pulse = math.sin(t * 20) * 8  
            self.inf_surf.fill((0,0,0,0)) 
            for i in reversed(range(2)): 
                layer_alpha = int(alpha_base / (i + 1))
                thickness = int(pulse + 4 + (i * 3)) 
                poly = [(70, 70), (150, 70), (145, 225), (75, 225)]
                pygame.draw.polygon(self.inf_surf, (140, 155, 175, layer_alpha), poly, thickness)
                pygame.draw.circle(self.inf_surf, (170, 185, 205, layer_alpha), (110, 45), 35 + (thickness//2), thickness)
            surface.blit(self.inf_surf, (x - 75, y - 55))