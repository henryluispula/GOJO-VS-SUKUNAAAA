import pygame # type: ignore
import random
import math
from settings import *

def draw_world(self, punching, dt):
    time_mult = dt * 60.0
    is_shrunk = getattr(self.gojo, "domain_shrunk", False)

    if not hasattr(self, "cached_shinjuku_bg"):
        self.cached_shinjuku_bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        
        M_SKY_TOP = (25, 27, 30)   
        M_SKY_BOT = (160, 165, 170) 
        M_WHITE = (245, 245, 250)   
        M_LIGHT = (110, 115, 120)   
        M_MID = (65, 68, 72)        
        M_DARK = (30, 32, 35)       
        M_INK = (5, 5, 8)           

        for y in range(WORLD_HEIGHT):
            ratio = y / WORLD_HEIGHT
            curve = ratio ** 1.8 
            r = int(M_SKY_TOP[0] * (1 - curve) + M_SKY_BOT[0] * curve)
            g = int(M_SKY_TOP[1] * (1 - curve) + M_SKY_BOT[1] * curve)
            b = int(M_SKY_TOP[2] * (1 - curve) + M_SKY_BOT[2] * curve)
            pygame.draw.line(self.cached_shinjuku_bg, (r, g, b), (0, y), (WORLD_WIDTH, y))
        
        sun_x, sun_y = WORLD_WIDTH - 700, WORLD_HEIGHT - 850
        pygame.draw.circle(self.cached_shinjuku_bg, (70, 75, 80), (sun_x, sun_y), 340) 
        pygame.draw.circle(self.cached_shinjuku_bg, (110, 115, 120), (sun_x, sun_y), 310) 
        pygame.draw.circle(self.cached_shinjuku_bg, (180, 185, 190), (sun_x, sun_y), 285) 
        pygame.draw.circle(self.cached_shinjuku_bg, M_WHITE, (sun_x, sun_y), 250) 
        
        for bg_x in range(-100, WORLD_WIDTH, 140):
            bg_x += random.randint(-30, 30)
            bg_w = random.randint(100, 180)
            bg_h = random.randint(400, 750) 
            
            pygame.draw.rect(self.cached_shinjuku_bg, M_MID, (bg_x, WORLD_HEIGHT - 100 - bg_h, bg_w, bg_h))
            pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (bg_x, WORLD_HEIGHT - 100 - bg_h, bg_w, bg_h), 3)                  
        
        sun_x = WORLD_WIDTH - 700 
        for bx in range(-100, WORLD_WIDTH, 380):
            bx += random.randint(-50, 50)
            bw = random.randint(200, 450)
            
            if abs((bx + bw // 2) - sun_x) < 400:
                if random.random() > 0.55: 
                    continue 
            
            bh = random.randint(800, 1500)
            
            pygame.draw.rect(self.cached_shinjuku_bg, M_LIGHT, (bx, WORLD_HEIGHT - 100 - bh, bw, bh))
            pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (bx, WORLD_HEIGHT - 100 - bh, bw, bh), 4) 
            
            for wy in range(WORLD_HEIGHT - 100 - bh + 40, WORLD_HEIGHT - 100, 60):
                pygame.draw.line(self.cached_shinjuku_bg, M_MID, (bx, wy), (bx + bw, wy), 3)
            for wx in range(bx + 30, bx + bw - 10, 40):
                pygame.draw.line(self.cached_shinjuku_bg, M_MID, (wx, WORLD_HEIGHT - 100 - bh), (wx, WORLD_HEIGHT - 100), 3)

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

        street_y = WORLD_HEIGHT - 100
        
        pygame.draw.rect(self.cached_shinjuku_bg, M_MID, (0, street_y - 40, WORLD_WIDTH, 40))
        pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 40), (WORLD_WIDTH, street_y - 40), 4)
        
        for gx in range(0, WORLD_WIDTH, 120):
            pygame.draw.rect(self.cached_shinjuku_bg, M_INK, (gx, street_y - 90, 15, 50))
        pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 80), (WORLD_WIDTH, street_y - 80), 8)
        pygame.draw.line(self.cached_shinjuku_bg, M_INK, (0, street_y - 55), (WORLD_WIDTH, street_y - 55), 6)

    if is_shrunk:
        self.world_surf.blit(self.cached_shinjuku_bg, (0, 0))
        
        if hasattr(self, 'shared_world_overlay'):
            self.shared_world_overlay.fill((0, 0, 0, 170)) 
            self.world_surf.blit(self.shared_world_overlay, (0, 0))

    # --- DOMAIN CLASH GLITCH LOGIC ---
    draw_gojo = self.gojo.domain_active
    draw_sukuna = self.sukuna.domain_active
    is_glitching = False

    if draw_gojo and draw_sukuna and is_shrunk:
        current_time = pygame.time.get_ticks()
        cycle_time = current_time % 2000
        
        if cycle_time > 1700:
            is_glitching = True
            if (current_time // 100) % 2 == 0:
                draw_gojo = False
            else:
                draw_sukuna = False
        else:
            if (current_time // 2000) % 2 == 0:
                draw_gojo = False
            else:
                draw_sukuna = False

    if draw_gojo:
        if is_shrunk and hasattr(self.gojo, "domain_center_x"):
            cx = self.gojo.domain_center_x
            cy = self.gojo.domain_center_y
            
            if self.cached_uv_bg_shrunk is None:
                self.cached_uv_bg_shrunk = pygame.Surface((800, 800), pygame.SRCALPHA)
                
                small_cx, small_cy = 400, 400
                
                self.cached_uv_bg_shrunk.fill((0, 0, 0, 0))
                
                pygame.draw.circle(self.cached_uv_bg_shrunk, (6, 6, 18, 255), (small_cx, small_cy), 405)
                
                bh_x, bh_y = small_cx, small_cy - 30
                scale = 0.67
                pygame.draw.circle(self.cached_uv_bg_shrunk, (80, 30, 160, 255), (bh_x, bh_y), int(520 * scale))
                pygame.draw.circle(self.cached_uv_bg_shrunk, (120, 60, 220, 255), (bh_x, bh_y), int(400 * scale))
                pygame.draw.circle(self.cached_uv_bg_shrunk, (200, 160, 255, 255), (bh_x, bh_y), int(290 * scale))
                pygame.draw.circle(self.cached_uv_bg_shrunk, (255, 255, 255, 255), (bh_x, bh_y), int(255 * scale))
                pygame.draw.circle(self.cached_uv_bg_shrunk, (0, 0, 0, 255), (bh_x, bh_y), int(230 * scale))
                
                pygame.draw.circle(self.cached_uv_bg_shrunk, (220, 240, 255, 255), (small_cx, small_cy), 400, width=8)
                
                for _ in range(90):
                    sx = small_cx + random.randint(-390, 390)
                    sy = small_cy + random.randint(-390, 390)
                    if math.hypot(sx - small_cx, sy - small_cy) < 395:
                        self.cached_uv_bg_shrunk.set_at((sx, sy), (255, 255, 255, 255))
            
            blit_x = int(cx - 400)
            blit_y = int(cy - 400)
            
            if is_glitching:
                ghost_surf = self.cached_uv_bg_shrunk.copy()
                ghost_surf.set_alpha(40) 
                self.world_surf.blit(self.cached_uv_bg_shrunk, (blit_x, blit_y))
                self.world_surf.blit(ghost_surf, (blit_x + random.randint(-8, 8), blit_y + random.randint(-8, 8)))
                
                for _ in range(random.randint(2, 4)): 
                    slice_y = random.randint(0, 750)
                    slice_h = random.randint(10, 25)
                    offset_x = random.randint(-12, 12) 
                    
                    strip = self.cached_uv_bg_shrunk.subsurface((0, slice_y, 800, slice_h))
                    self.world_surf.blit(strip, (blit_x + offset_x, blit_y + slice_y))
                    
                    if random.random() < 0.3: 
                        dark_neon = random.choice([(0, 100, 150), (50, 50, 80), (0, 50, 80)])
                        pygame.draw.line(self.world_surf, dark_neon, (blit_x + offset_x, blit_y + slice_y), (blit_x + offset_x + 800, blit_y + slice_y), 1)
            else:
                self.world_surf.blit(self.cached_uv_bg_shrunk, (blit_x, blit_y))
            
        else:
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
            
            self.world_surf.blit(self.star_layers[(pygame.time.get_ticks() // 200) % 3], (0, 0))

        if self.gojo.domain_timer > 880:
            flash_alpha = min(255, max(0, int(((self.gojo.domain_timer - 880) / 20.0) * 180)))
            self.shared_flash_surf.fill((150, 200, 255, flash_alpha))
            self.world_surf.blit(self.shared_flash_surf, (0, 0))
    
    elif draw_sukuna:
        if is_shrunk and hasattr(self.gojo, "domain_center_x"):
            cx = self.gojo.domain_center_x
            cy = self.gojo.domain_center_y
            
            if not hasattr(self, "cached_ms_bg_shrunk") or self.cached_ms_bg_shrunk is None:
                self.cached_ms_bg_shrunk = pygame.Surface((800, 800), pygame.SRCALPHA)
                self.cached_ms_bg_shrunk.fill((0, 0, 0, 0))
                small_cx, small_cy = 400, 400
                
                shrine_canvas = pygame.Surface((800, 800), pygame.SRCALPHA)
                shrine_x, shrine_y = small_cx, small_cy + 120
                scale = 0.65
                
                pygame.draw.circle(shrine_canvas, (150, 0, 0, 150), (shrine_x, int(shrine_y - 250 * scale)), int(450 * scale))
                pygame.draw.circle(shrine_canvas, (200, 30, 30, 200), (shrine_x, int(shrine_y - 250 * scale)), int(330 * scale))
                pygame.draw.circle(shrine_canvas, (255, 150, 150, 255), (shrine_x, int(shrine_y - 250 * scale)), int(240 * scale))
                
                shrine_color = (15, 5, 5) 
                pygame.draw.rect(shrine_canvas, shrine_color, (shrine_x - int(270*scale), shrine_y - int(150*scale), int(540*scale), int(750*scale)))
                pygame.draw.polygon(shrine_canvas, shrine_color, [(shrine_x - int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(270*scale), shrine_y - int(240*scale)), (shrine_x - int(270*scale), shrine_y - int(240*scale))])
                pygame.draw.polygon(shrine_canvas, shrine_color, [(shrine_x - int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(180*scale), shrine_y - int(345*scale)), (shrine_x - int(180*scale), shrine_y - int(345*scale))])
                pygame.draw.polygon(shrine_canvas, shrine_color, [(shrine_x - int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(90*scale), shrine_y - int(450*scale)), (shrine_x - int(90*scale), shrine_y - int(450*scale))])
                
                mouth_rect = (shrine_x - int(165*scale), shrine_y - int(20*scale), int(330*scale), int(420*scale))
                pygame.draw.ellipse(shrine_canvas, BLACK, mouth_rect)
                
                teeth_color = (220, 220, 200)
                for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                    pygame.draw.polygon(shrine_canvas, teeth_color, [(tx, shrine_y + int(25*scale)), (tx + int(35*scale), shrine_y + int(25*scale)), (tx + int(17*scale), shrine_y + int(115*scale))])
                for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                    pygame.draw.polygon(shrine_canvas, teeth_color, [(tx, shrine_y + int(360*scale)), (tx + int(35*scale), shrine_y + int(360*scale)), (tx + int(17*scale), shrine_y + int(270*scale))])
                for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                    pygame.draw.polygon(shrine_canvas, teeth_color, [(shrine_x - int(150*scale), ty), (shrine_x - int(150*scale), ty + int(35*scale)), (shrine_x - int(75*scale), ty + int(17*scale))])
                for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                    pygame.draw.polygon(shrine_canvas, teeth_color, [(shrine_x + int(150*scale), ty), (shrine_x + int(150*scale), ty + int(35*scale)), (shrine_x + int(75*scale), ty + int(17*scale))])

                mask = pygame.Surface((800, 800), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), (small_cx, small_cy), 400)
                
                shrine_canvas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                pygame.draw.circle(self.cached_ms_bg_shrunk, (20, 5, 5, 240), (small_cx, small_cy), 400)
                self.cached_ms_bg_shrunk.blit(shrine_canvas, (0, 0))
                pygame.draw.circle(self.cached_ms_bg_shrunk, RED, (small_cx, small_cy), 400, 4)

            blit_x = int(cx - 400)
            blit_y = int(cy - 400)
            
            if is_glitching:
                ghost_surf = self.cached_ms_bg_shrunk.copy()
                ghost_surf.set_alpha(40) 
                self.world_surf.blit(self.cached_ms_bg_shrunk, (blit_x, blit_y))
                self.world_surf.blit(ghost_surf, (blit_x + random.randint(-8, 8), blit_y + random.randint(-8, 8)))
                
                for _ in range(random.randint(2, 4)): 
                    slice_y = random.randint(0, 750)
                    slice_h = random.randint(10, 25)
                    offset_x = random.randint(-12, 12)
                    
                    strip = self.cached_ms_bg_shrunk.subsurface((0, slice_y, 800, slice_h))
                    self.world_surf.blit(strip, (blit_x + offset_x, blit_y + slice_y))
                    
                    if random.random() < 0.3: 
                        dark_neon = random.choice([(150, 0, 0), (80, 20, 20), (100, 0, 0)])
                        pygame.draw.line(self.world_surf, dark_neon, (blit_x + offset_x, blit_y + slice_y), (blit_x + offset_x + 800, blit_y + slice_y), 1)
            else:
                self.world_surf.blit(self.cached_ms_bg_shrunk, (blit_x, blit_y))

        else:
            if getattr(self, "cached_ms_bg", None) is None:
                self.cached_ms_bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
                
                num_steps = 50
                step_height = WORLD_HEIGHT / num_steps
                for i in range(num_steps):
                    color_val = max(0, 120 - (i * 2.4)) 
                    alpha_val = min(255, 150 + (i * 2))
                    pygame.draw.rect(self.cached_ms_bg, (int(color_val), 0, 0, int(alpha_val)), (0, int(i * step_height), WORLD_WIDTH, int(step_height) + 2))
            
                shrine_x, shrine_y = WORLD_WIDTH // 2, WORLD_HEIGHT - 400 
                scale = 1.0
                
                pygame.draw.circle(self.cached_ms_bg, (150, 0, 0, 150), (shrine_x, int(shrine_y - 250 * scale)), int(450 * scale))
                pygame.draw.circle(self.cached_ms_bg, (200, 30, 30, 200), (shrine_x, int(shrine_y - 250 * scale)), int(330 * scale))
                pygame.draw.circle(self.cached_ms_bg, (255, 150, 150, 255), (shrine_x, int(shrine_y - 250 * scale)), int(240 * scale))
                
                shrine_color = (15, 5, 5) 
                
                pygame.draw.rect(self.cached_ms_bg, shrine_color, (shrine_x - int(270*scale), shrine_y - int(150*scale), int(540*scale), int(750*scale)))
                
                pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(450*scale), shrine_y - int(120*scale)), (shrine_x + int(270*scale), shrine_y - int(240*scale)), (shrine_x - int(270*scale), shrine_y - int(240*scale))])
                pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(360*scale), shrine_y - int(240*scale)), (shrine_x + int(180*scale), shrine_y - int(345*scale)), (shrine_x - int(180*scale), shrine_y - int(345*scale))])
                pygame.draw.polygon(self.cached_ms_bg, shrine_color, [(shrine_x - int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(240*scale), shrine_y - int(345*scale)), (shrine_x + int(90*scale), shrine_y - int(450*scale)), (shrine_x - int(90*scale), shrine_y - int(450*scale))])
                
                mouth_rect = (shrine_x - int(165*scale), shrine_y - int(20*scale), int(330*scale), int(420*scale))
                pygame.draw.ellipse(self.cached_ms_bg, BLACK, mouth_rect)
                
                teeth_color = (220, 220, 200)
                
                for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                    pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(tx, shrine_y + int(25*scale)), (tx + int(35*scale), shrine_y + int(25*scale)), (tx + int(17*scale), shrine_y + int(115*scale))])
                
                for tx in range(int(shrine_x - 135*scale), int(shrine_x + 135*scale), int(35*scale)):
                    pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(tx, shrine_y + int(360*scale)), (tx + int(35*scale), shrine_y + int(360*scale)), (tx + int(17*scale), shrine_y + int(270*scale))])
                
                for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                    pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(shrine_x - int(150*scale), ty), (shrine_x - int(150*scale), ty + int(35*scale)), (shrine_x - int(75*scale), ty + int(17*scale))])
                
                for ty in range(int(shrine_y + 70*scale), int(shrine_y + 320*scale), int(45*scale)):
                    pygame.draw.polygon(self.cached_ms_bg, teeth_color, [(shrine_x + int(150*scale), ty), (shrine_x + int(150*scale), ty + int(35*scale)), (shrine_x + int(75*scale), ty + int(17*scale))])

            self.world_surf.blit(self.cached_ms_bg, (0, 0))
            
        if self.sukuna.domain_timer > 890: 
            self.world_surf.fill((200, 0, 0))
    
    else:
        self.world_surf.blit(self.cached_shinjuku_bg, (0, 0))

    if (self.gojo.domain_active and not is_shrunk) or (self.sukuna.domain_active and not is_shrunk):
        pygame.draw.rect(self.world_surf, (15, 15, 25), (0, WORLD_HEIGHT - 100, WORLD_WIDTH, 100))
    else:
        pygame.draw.rect(self.world_surf, (80, 85, 90), (0, WORLD_HEIGHT - 100, WORLD_WIDTH, 100))
        pygame.draw.line(self.world_surf, (10, 10, 12), (0, WORLD_HEIGHT - 100), (WORLD_WIDTH, WORLD_HEIGHT - 100), 6)
        
        for fx in range(0, WORLD_WIDTH, 180):
            pygame.draw.line(self.world_surf, (50, 50, 55), (fx, WORLD_HEIGHT - 80), (fx + 80, WORLD_HEIGHT - 80), 8)
    
    active_bf_words = []
    for bw in self.bf_words:
        scale_f = 1.0 + (45 - bw["timer"]) * 0.05
        txt = self.get_text("BLACK FLASH!", BLACK)
        out = self.get_text("BLACK FLASH!", RED)
        
        s_out = pygame.transform.scale(out, (int(out.get_width() * scale_f), int(out.get_height() * scale_f)))
        s_txt = pygame.transform.scale(txt, (int(txt.get_width() * scale_f), int(txt.get_height() * scale_f)))
        
        self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 - 2, bw["y"] - s_out.get_height()//2 - 2))
        self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 + 2, bw["y"] - s_out.get_height()//2 + 2))
        self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 - 2, bw["y"] - s_out.get_height()//2 + 2))
        self.world_surf.blit(s_out, (bw["x"] - s_out.get_width()//2 + 2, bw["y"] - s_out.get_height()//2 - 2))
        
        self.world_surf.blit(s_txt, (bw["x"] - s_txt.get_width()//2, bw["y"] - s_txt.get_height()//2))
        bw["timer"] -= time_mult
        if bw["timer"] > 0:
            active_bf_words.append(bw)
    self.bf_words = active_bf_words
    
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
        p_up["timer"] -= time_mult
        if p_up["timer"] > 0:
            active_popups.append(p_up)
    self.popups = active_popups
                
    
    if self.mahoraga and self.mahoraga.hp > 0: 
        self.mahoraga.draw_detailed(self.world_surf)

    if self.mahoraga_summon_timer > 0:
        self.shared_world_overlay.fill((0, 0, 0, 150))
        self.world_surf.blit(self.shared_world_overlay, (0,0))
        chants = ["With this treasure I summon...", "Eight-Handled Sword...", "Divergent Sila...", "Divine General Mahoraga!"]
        
        idx = 3 - (int(self.mahoraga_summon_timer) // 76) 
        idx = max(0, min(3, idx)) 
        
        txt = self.get_text(chants[idx], MAHO_COLOR)
        self.world_surf.blit(txt, (self.sukuna.rect.centerx - txt.get_width()//2, self.sukuna.rect.y - 120))
        self.sukuna.draw_detailed(self.world_surf, effect="summoning")
    else:
        maho_dead = getattr(self.sukuna, "mahoraga_is_dead", False)
        is_adapting_now = self.sukuna.adapting_to == "void" and self.sukuna.amp_duration <= 0 and self.gojo.domain_active and not maho_dead
        is_summoning = self.sukuna.is_paralyzed and self.gojo.domain_active and (self.mahoraga is None or self.mahoraga.hp <= 0) and not maho_dead
        
        eff = "summoning" if (is_summoning or is_adapting_now) else None
        self.sukuna.draw_detailed(self.world_surf, effect=eff, is_amp=(self.sukuna.amp_duration > 0))
    
    self.gojo.draw_detailed(self.world_surf, punching)

    for p in self.projectiles: p.draw(self.world_surf)

    active_blood = []
    if len(self.blood_particles) > 150:
        self.blood_particles = self.blood_particles[-150:]
    for bp in self.blood_particles:
        bp[0] += bp[2] * time_mult
        bp[1] += bp[3] * time_mult
        bp[3] += GRAVITY * time_mult
        bp[4] -= time_mult
        pygame.draw.circle(self.world_surf, BLOOD, (int(bp[0]), int(bp[1])), bp[5])
        if bp[4] > 0:
            active_blood.append(bp)
    self.blood_particles = active_blood

    active_sparks = []
    if len(self.hit_sparks) > 150:
        self.hit_sparks = self.hit_sparks[-150:]
    for spark in self.hit_sparks:
        spark[0] += spark[2] * time_mult
        spark[1] += spark[3] * time_mult
        spark[4] -= time_mult
        pygame.draw.circle(self.world_surf, spark[5], (int(spark[0]), int(spark[1])), max(1, int(spark[4] * 0.25)))
        if spark[4] > 0:
            active_sparks.append(spark)
    self.hit_sparks = active_sparks