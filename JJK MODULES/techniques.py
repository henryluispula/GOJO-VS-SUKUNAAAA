import pygame # type: ignore
import math
import random
from settings import *

def draw_special_techniques(self, surface, t):
    x, y, mid_x = self.rect.centerx - (self.rect.width // 2), self.rect.y, self.rect.centerx

    # --- HOLLOW PURPLE ---
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
                lx, ly = int(bx + random.randint(-12, 12)), int(by + random.randint(-12, 12))
                ex, ey = int(rx + random.randint(-12, 12)), int(ry + random.randint(-12, 12))
                pygame.draw.line(surface, (220, 120, 255), (lx, ly), (ex, ey), 2)
                pygame.draw.line(surface, WHITE, (lx, ly), (ex, ey), 1)

        if ct > 0.45:
            for ri in range(4):
                ring_r = int((30 + ri * 20) * ct)
                pygame.draw.circle(surface, PURPLE, (mid_x, y + 40), ring_r, max(1, 4 - ri))

        if ct > 0.80:
            burst = int(140 * ((ct - 0.80) / 0.20))
            pygame.draw.circle(surface, PURPLE, (mid_x, y + 40), burst, 8)
            pygame.draw.circle(surface, (220, 180, 255), (mid_x, y + 40), burst // 2, 4)
            pygame.draw.circle(surface, WHITE, (mid_x, y + 40), burst // 4, 3)
            for _ in range(30):
                fpx, fpy = mid_x + random.randint(-burst, burst), y + 40 + random.randint(-burst, burst)
                pygame.draw.circle(surface, PURPLE, (int(fpx), int(fpy)), random.randint(3, 12))

    # --- WORLD SLASH ---
    if self.name == "Sukuna" and getattr(self, "world_slash_charge", 0) > 0:
        ct = (120 - self.world_slash_charge) / 120.0
        pull_r = int(250 * (1.0 - ct))
        core_size = int(60 * ct + math.sin(t * 30) * 10)
        pygame.draw.circle(surface, (5, 5, 10), (mid_x, y + 60), core_size)
        pygame.draw.circle(surface, (100, 255, 255), (mid_x, y + 60), core_size + 5, max(1, int(15 * ct)))
        
        for _ in range(int(20 * ct) + 5):
            ang = random.uniform(0, math.pi * 2)
            p1_x, p1_y = mid_x + math.cos(ang) * pull_r, y + 60 + math.sin(ang) * pull_r
            p2_x, p2_y = mid_x + math.cos(ang) * (pull_r * 0.6), y + 60 + math.sin(ang) * (pull_r * 0.6)
            pygame.draw.line(surface, BLACK, (p1_x, p1_y), (p2_x, p2_y), max(2, int(8 * ct)))

        if ct > 0.6:
            slash_len = int(250 * ((ct - 0.6) / 0.4))
            pygame.draw.line(surface, (200, 255, 255), (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 15)
            pygame.draw.line(surface, BLACK, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 8)
            pygame.draw.line(surface, WHITE, (mid_x - slash_len, y + 60 - slash_len//3), (mid_x + slash_len, y + 60 + slash_len//3), 2)

    # --- FUGA ---
    if self.name == "Sukuna" and self.fuga_charge > 0:
        ct = (120 - self.fuga_charge) / 120.0
        pillar_h, pillar_w = int(220 * ct), int(22 + 65 * ct)
        pygame.draw.ellipse(surface, (255, 55, 0), (mid_x - pillar_w // 2, y + 40 - pillar_h // 2, pillar_w, pillar_h), max(1, int(9 * ct)))
        
        pulse_r = int(50 * ct + 6 * math.sin(t * 18))
        pygame.draw.circle(surface, (255, 100, 0), (mid_x, y + 40), pulse_r, max(1, int(14 * ct)))

        if ct > 0.78:
            burst = int(160 * ((ct - 0.78) / 0.22))
            pygame.draw.circle(surface, (255, 140, 0), (mid_x, y + 40), burst, 8)
            pygame.draw.circle(surface, WHITE, (mid_x, y + 40), burst // 4, 3)