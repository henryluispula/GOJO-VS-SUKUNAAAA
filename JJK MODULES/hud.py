import pygame 
from settings import *

def draw_hud(self, render_surf, dt):
    time_mult = dt * 60.0
    
    if getattr(self, "clash_decision_timer", 0) > 0:
        prompt_text = "WAIT..." if self.clash_decision_timer > 8 else "SHRINK NOW!" 
        prompt_color = (255, 100, 100) if self.clash_decision_timer > 8 else (0, 255, 255) 
        
        if getattr(self, "clash_failed", False):
            prompt_text = "MISSED TIMING!"
            prompt_color = (150, 150, 150)
        
        shrink_txt = self.get_text(prompt_text, prompt_color) 
        render_surf.blit(shrink_txt, (WIDTH//2 - shrink_txt.get_width()//2, 80))

        bar_w, bar_h = 400, 25
        clash_window = 30 
        
        fill_w = int((self.clash_decision_timer / clash_window) * bar_w)
        bx, by = WIDTH//2 - bar_w//2, 120
        
        pygame.draw.rect(render_surf, (0, 0, 0), (bx - 4, by - 4, bar_w + 8, bar_h + 8))
        pygame.draw.rect(render_surf, (30, 30, 30), (bx, by, bar_w, bar_h))            
        
        sweet_spot_w = int((8 / clash_window) * bar_w) 
        pygame.draw.rect(render_surf, (0, 150, 150), (bx, by, sweet_spot_w, bar_h))

        if fill_w > 0:
            fill_color = (150, 150, 150) if getattr(self, "clash_failed", False) else (255, 255, 255)
            pygame.draw.rect(render_surf, fill_color, (bx, by, fill_w, bar_h))
            
    for fighter in [self.gojo, self.sukuna]:
        if fighter.domain_charge > 0:
            charge_progress = (60 - fighter.domain_charge) / 60.0
            
            domain_name = "UNLIMITED VOID" if fighter.name == "Gojo" else "MALEVOLENT SHRINE"
            base_txt = self.get_text(f"DOMAIN EXPANSION: {domain_name}", WHITE)
            
            scale_factor = 0.5 + (charge_progress * 0.5)
            new_w = int(base_txt.get_width() * scale_factor)
            new_h = int(base_txt.get_height() * scale_factor)
            scaled_txt = pygame.transform.scale(base_txt, (new_w, new_h))
            
            shadow_color = (200, 0, 0) if fighter.name == "Sukuna" else (0, 0, 200)
            shadow_txt = self.get_text(f"DOMAIN EXPANSION: {domain_name}", shadow_color)
            scaled_shadow = pygame.transform.scale(shadow_txt, (new_w, new_h))
            
            txt_x = WIDTH // 2 - scaled_txt.get_width() // 2
            
            y_offset_domain = -250 if fighter.name == "Gojo" else -100
            txt_y = HEIGHT // 2 + y_offset_domain - scaled_txt.get_height() // 2
            
            render_surf.blit(scaled_shadow, (txt_x + 4, txt_y + 4))
            render_surf.blit(scaled_txt, (txt_x, txt_y))

    if self.clash_msg_timer > 0:
        self.clash_msg_timer -= time_mult
        clash_txt = self.get_text(self.clash_winner, WHITE)
        bg_w, bg_h = clash_txt.get_width() + 40, clash_txt.get_height() + 20
        
        self.clash_msg_bg.fill((0, 0, 0, 0)) 
        pygame.draw.rect(self.clash_msg_bg, (0, 0, 0, 180), (0, 0, bg_w, bg_h))
        render_surf.blit(self.clash_msg_bg, (WIDTH//2 - bg_w//2, HEIGHT//2 - 100), (0, 0, bg_w, bg_h))
        render_surf.blit(clash_txt, (WIDTH//2 - clash_txt.get_width()//2, HEIGHT//2 - 90))

    if getattr(self, "clash_active_flag", False) and self.gojo.domain_active and self.sukuna.domain_active:
        clash_txt = self.get_text("DOMAIN CLASH!", (255, 255, 100))
        render_surf.blit(clash_txt, (WIDTH//2 - clash_txt.get_width()//2, 80))

    # --- GOJO HUD DASHBOARD (DYNAMIC WIDTH) ---
    is_clashing = getattr(self, "clash_active_flag", False) and self.gojo.domain_active and self.sukuna.domain_active
    
    # 1. PRE-CALCULATE ABILITIES
    is_burned_out = self.gojo.technique_burnout > 0 and self.gojo.domain_uses >= 5
    actual_domain_cooldown = max(self.gojo.domain_cd, self.gojo.technique_burnout)
    
    # Define Max CDs for Visual Wipe
    max_cds = {"BLUE": 300, "RED": 600, "PURPLE": 1800, "SIMPLE": 150, "VOID": 3000, "STANCE": 600}

    abilities = [
        {"name": "BLUE",   "key": "W",     "cd": self.gojo.blue_cd, "color": BLUE, "hits": None},
        {"name": "RED",    "key": "S",     "cd": self.gojo.red_cd, "color": RED, "hits": None},
        {"name": "PURPLE", "key": "R",     "cd": self.gojo.purple_cd, "color": (200, 100, 255), "hits": (int(self.gojo.tech_hits), self.gojo.max_tech_hits)},
        {"name": "SIMPLE", "key": "R-CLK", "cd": self.gojo.sd_broken_timer, "color": (0, 255, 255), "hits": (max(0, self.gojo.max_sd_hits - self.gojo.sd_hits), self.gojo.max_sd_hits)},
        {"name": "VOID",   "key": "V",     "cd": actual_domain_cooldown, "color": WHITE, "hits": (5 - self.gojo.domain_uses, 5)}
    ]
    if is_clashing:
        abilities.append({"name": "STANCE", "key": "CLASH", "cd": 0, "color": (200, 200, 255), "hits": (max(0, getattr(self.gojo, "stance", 300)), 600)})

    bw, bh = 100, 60
    spacing = 10
    slots_w = len(abilities) * (bw + spacing) - spacing
    
    # Dashboard Width: Stats Area (330) + Gap (10) + Abilities Slots
    dash_w, dash_h = 340 + slots_w + 10, 70
    dash_x = (WIDTH - dash_w) // 2
    dash_y = HEIGHT - dash_h - 4 
    
    # Dashboard Background
    pygame.draw.rect(render_surf, (0, 0, 10, 230), (dash_x - 5, dash_y - 12, dash_w + 10, dash_h + 16), border_radius=8)
    pygame.draw.rect(render_surf, (70, 70, 120), (dash_x - 5, dash_y - 12, dash_w + 10, dash_h + 16), 2, border_radius=8)

    # 1. STAT BARS
    bx, by = dash_x + 10, dash_y + 12
    self.draw_bar_on(render_surf, bx, by, self.gojo.hp, self.gojo.max_hp, RED, 310, 12, "SATORU GOJO")
    self.draw_bar_on(render_surf, bx, by + 28, self.gojo.energy, self.gojo.max_energy, PURPLE, 180, 6, "CE")
    self.draw_bar_on(render_surf, bx + 190, by + 28, self.gojo.infinity, self.gojo.max_infinity, INF_COLOR, 120, 6, "INF")
    stam_color = (255, 50, 50) if self.gojo.stamina < 10 else (50, 255, 100)
    self.draw_bar_on(render_surf, bx, by + 50, self.gojo.stamina, getattr(self.gojo, 'max_stamina', 100.0), stam_color, 310, 4, "STAMINA")

    # 2. ABILITY SLOTS
    if not hasattr(self.gojo, "sd_trig"): setattr(self.gojo, "sd_trig", False)
    if self.gojo.sd_broken_timer <= 0:
        if not self.gojo.sd_trig:
            setattr(self.gojo, "sd_fx", 25.0); setattr(self.gojo, "sd_trig", True)
    else: setattr(self.gojo, "sd_trig", False)
    
    fx_g = getattr(self.gojo, "sd_fx", 0)
    if fx_g > 0: setattr(self.gojo, "sd_fx", fx_g - time_mult)

    abilities_start_x = dash_x + 340
    if not hasattr(self, "micro_font"): self.micro_font = pygame.font.SysFont("Impact", 13)
    if not hasattr(self, "name_font"): self.name_font = pygame.font.SysFont("Impact", 16)
    if not hasattr(self, "cd_font"): self.cd_font = pygame.font.SysFont("Impact", 22)

    for i, abi in enumerate(abilities):
        x = abilities_start_x + i * (bw + spacing)
        y = dash_y + 4
        
        # Slot Background
        pygame.draw.rect(render_surf, (15, 15, 25), (x, y, bw, bh), border_radius=6)
        
        # Border
        border_color = (80, 80, 120)
        if abi["name"] == "SIMPLE" and fx_g > 0:
            flash_val = min(255, int((fx_g / 25.0) * 510)); border_color = (flash_val, flash_val, 255)
        pygame.draw.rect(render_surf, border_color, (x, y, bw, bh), 2, border_radius=6)
        
        # Hide VOID cooldown if active
        is_void_active = abi["name"] == "VOID" and self.gojo.domain_active
        effective_cd = 0 if is_void_active else abi["cd"]

        # Key hint
        key_txt = self.micro_font.render(abi["key"], True, (160, 160, 180))
        render_surf.blit(key_txt, (x + 5, y + 2))
        
        # Name (Larger)
        name_txt = self.name_font.render(abi["name"], True, WHITE)
        render_surf.blit(name_txt, (x + bw//2 - name_txt.get_width()//2, y + 18))
        
        # Charges / Hits / Stance / Void Bar (Drawn first so Dim covers it)
        if abi["hits"]:
            curr, mval = abi["hits"]
            bar_w = bw - 16
            bh_thick = 7 
            pygame.draw.rect(render_surf, (30, 30, 45), (x + 8, y + 40, bar_w, bh_thick), border_radius=2)
            if abi["name"] == "VOID":
                fill_w = int((curr / mval) * bar_w)
                pygame.draw.rect(render_surf, abi["color"], (x + 8, y + 40, fill_w, bh_thick), border_radius=2)
                for segment in range(1, 5):
                    lx = x + 8 + int((segment / 5.0) * bar_w)
                    pygame.draw.line(render_surf, (0, 0, 0), (lx, y + 40), (lx, y + 40 + bh_thick - 1), 1)
            else:
                fill_w = int((curr / mval) * bar_w)
                pygame.draw.rect(render_surf, abi["color"], (x + 8, y + 40, fill_w, bh_thick), border_radius=2)

        # Status / Cooldown (Now covers bars)
        if effective_cd > 0:
            # Static Dim Overlay
            dim_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            dim_surf.fill((0, 0, 0, 230))
            render_surf.blit(dim_surf, (x, y))
            
            # CD Seconds
            cd_s = f"{int(effective_cd // 60) + 1}s"
            cd_txt = self.cd_font.render(cd_s, True, (255, 255, 120))
            render_surf.blit(cd_txt, (x + bw//2 - cd_txt.get_width()//2, y + bh//2 - cd_txt.get_height()//2 + 5))
        else:
            # Status Text (Burnout only)
            status_str = ""
            status_color = RED
            if is_burned_out and abi["name"] not in ["SIMPLE", "STANCE"]:
                status_str = "BURNT" if abi["name"] == "VOID" else "BURN"
            
            if status_str:
                stat_txt = self.micro_font.render(status_str, True, status_color)
                render_surf.blit(stat_txt, (x + bw//2 - stat_txt.get_width()//2, y + 28))

    # CE Cost Popups
    if hasattr(self, "ce_hud_popups"):
        active_ce_popups = []
        for cp in self.ce_hud_popups:
            if cp.get("color") == BLUE: continue
            cp["y"] -= 1.0 * time_mult
            alpha = min(255, max(0, int(cp["timer"] * 8)))
            
            txt_surf = self.get_text(f"-{cp['val']} CE", cp["color"], font=self.mini_font)
            shadow = self.get_text(f"-{cp['val']} CE", BLACK, font=self.mini_font)
            
            fade_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
            fade_surf.blit(txt_surf, (0, 0))
            fade_surf.set_alpha(alpha)
            
            shadow_surf = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
            shadow_surf.blit(shadow, (0, 0))
            shadow_surf.set_alpha(alpha)
            
            render_surf.blit(shadow_surf, (cp["x"] - shadow.get_width()//2 + 1, int(cp["y"]) + 1))
            render_surf.blit(fade_surf, (cp["x"] - txt_surf.get_width()//2, int(cp["y"])))
            
            cp["timer"] -= time_mult
            if cp["timer"] > 0:
                active_ce_popups.append(cp)
        self.ce_hud_popups = active_ce_popups

    y_offset = 80  
    active_ann = []
    for ann in self.maho_announcements:
        text_str = ann["text"]
        
        if "VOW:" in text_str:
            base_color = (255, 80, 80)
        elif "ADAPTED" in text_str or "ACQUIRED" in text_str:
            base_color = (100, 255, 255)
        elif "SHATTERED" in text_str or "BURNED" in text_str:
            base_color = (255, 100, 255)
        else:
            base_color = (255, 220, 100)
        
        txt = self.get_text(text_str, base_color)
        shadow = self.get_text(text_str, BLACK)
        
        if txt.get_width() > 540:
            scale_ratio = 540.0 / txt.get_width()
            new_w = 540
            new_h = max(10, int(txt.get_height() * scale_ratio))
            txt = pygame.transform.scale(txt, (new_w, new_h))
            shadow = pygame.transform.scale(shadow, (new_w, new_h))
        
        banner_w = txt.get_width() + 40
        banner_h = txt.get_height() + 16
        
        ann_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        
        pygame.draw.rect(ann_surf, (5, 5, 10, 220), (0, 0, banner_w, banner_h), border_radius=8)
        
        line_thickness = max(1, min(3, int(ann["timer"]) // 10))
        pygame.draw.rect(ann_surf, base_color + (180,), (0, 0, banner_w, banner_h), line_thickness, border_radius=8)
        
        ann_surf.blit(shadow, (banner_w//2 - shadow.get_width()//2 + 2, 8 + 2))
        ann_surf.blit(txt, (banner_w//2 - txt.get_width()//2, 8))
        
        if ann["timer"] <= 20:
            ann_surf.set_alpha(int((max(0, ann["timer"]) / 20.0) * 255))
            
        render_surf.blit(ann_surf, (WIDTH//2 - banner_w//2, y_offset))
        
        ann["timer"] -= time_mult
        y_offset += banner_h + 8 
        
        if ann["timer"] > 0:
            active_ann.append(ann)
    self.maho_announcements = active_ann
    
    render_surf.blit(self.get_text("PRESS 'P' TO PAUSE / VIEW CONTROLS", (200, 200, 200), font=self.mini_font), (WIDTH//2 - 100, 20))
    
    # Paused Panel
    if self.paused:
        self.shared_ui_overlay.fill((0, 0, 0, 200))
        render_surf.blit(self.shared_ui_overlay, (0, 0))
        
        instr_bg = pygame.Rect(WIDTH//2 - 400, HEIGHT//2 - 300, 800, 600)
        pygame.draw.rect(render_surf, (15, 15, 25, 240), instr_bg, border_radius=20)
        pygame.draw.rect(render_surf, (100, 100, 255), instr_bg, 2, border_radius=20)
        
        title = self.get_text("CONTROLS & INSTRUCTIONS", WHITE)
        render_surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 280))
        
        # Controls Sections
        sections = [
            ("BASIC ACTIONS", [
                ("[A / D]", "Move Left/Right"),
                ("[SPACE]", "Jump / Double Jump"),
                ("[SHIFT]", "Dodge (I-frames)"),
                ("[F]", "BLOCK Stuns from Punches")
            ]),
            ("COMBAT & RECOVERY", [
                ("[CLICK]", "Standard Melee Punch"),
                ("[Q]", "Reverse Cursed Technique (Heal HP)")
            ]),
            ("SATORU GOJO: LIMITLESS", [
                ("[W]", "LAPSE BLUE (Pull enemies in)"),
                ("[S]", "REVERSAL RED (Push enemies away)"),
                ("[R]", "HOLLOW PURPLE (Massive Damage - Requires Tech Hits)")
            ]),
            ("DOMAIN TECHNIQUES", [
                ("[RIGHT CLICK]", "SIMPLE DOMAIN (Counters Sure-Hits)"),
                ("[V]", "DOMAIN EXPANSION: UNLIMITED VOID"),
                ("[Z + V]", "SHRINK DOMAIN (Mash during a Clash)")
            ]),
            ("ADVANCED COMBOS", [
                ("[E + W + CLICK]", "POINT-BLANK BLUE BEATDOWN"),
                ("[E + S]", "POINT-BLANK RED (Escape Cleave / Tech Refresh)")
            ])
        ]
        
        start_y = HEIGHT // 2 - 220 + self.menu_scroll_y
        
        # Clipping Area for Scrollable Content
        clip_rect = pygame.Rect(WIDTH//2 - 380, HEIGHT//2 - 230, 760, 460)
        old_clip = render_surf.get_clip()
        render_surf.set_clip(clip_rect)
        
        for section_title, controls in sections:
            # Section Header
            header_txt = self.get_text(section_title, (150, 180, 255), font=self.mini_font)
            render_surf.blit(header_txt, (WIDTH//2 - 370, start_y))
            pygame.draw.line(render_surf, (50, 50, 100), (WIDTH//2 - 370, start_y + 25), (WIDTH//2 + 370, start_y + 25), 1)
            start_y += 35
            
            for key, desc in controls:
                key_txt = self.get_text(key, (255, 255, 100), font=self.mini_font)
                desc_txt = self.get_text(f": {desc}", (200, 200, 200), font=self.mini_font)
                
                render_surf.blit(key_txt, (WIDTH//2 - 350, start_y))
                render_surf.blit(desc_txt, (WIDTH//2 - 350 + key_txt.get_width(), start_y))
                start_y += 28
            
            start_y += 15

        render_surf.set_clip(old_clip)
        
        # Scrollbar
        content_h = 650
        view_h = 460
        if content_h > view_h:
            bar_track_h = 460
            bar_w = 6
            bar_x = WIDTH//2 + 385
            bar_y = HEIGHT//2 - 230
            
            # Draw Track
            pygame.draw.rect(render_surf, (30, 30, 50), (bar_x, bar_y, bar_w, bar_track_h), border_radius=3)
            
            # Draw Handle
            handle_h = int((view_h / content_h) * bar_track_h)
            max_scroll = content_h - view_h
            scroll_ratio = max(0.0, min(1.0, -self.menu_scroll_y / max_scroll))
            handle_y = bar_y + int(scroll_ratio * (bar_track_h - handle_h))
            pygame.draw.rect(render_surf, (150, 150, 255), (bar_x, handle_y, bar_w, handle_h), border_radius=3)

        resume_txt = self.get_text("PRESS 'P' TO RESUME", (100, 255, 100), font=self.mini_font)
        render_surf.blit(resume_txt, (WIDTH//2 - resume_txt.get_width()//2, HEIGHT//2 + 245))

        menu_btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 265, 200, 30)
        mouse_pos = pygame.mouse.get_pos()
        color = (200, 80, 80) if menu_btn_rect.collidepoint(mouse_pos) else (150, 50, 50)
        pygame.draw.rect(render_surf, color, menu_btn_rect, border_radius=5)
        menu_txt = self.get_text("RETURN TO MENU", WHITE, font=self.mini_font)
        render_surf.blit(menu_txt, (menu_btn_rect.centerx - menu_txt.get_width()//2, menu_btn_rect.centery - menu_txt.get_height()//2))

    if self.game_over:
        self.shared_ui_overlay.fill((0, 0, 0, 230))
        render_surf.blit(self.shared_ui_overlay, (0,0))
        msg = "KING OF CURSES REIGNS" if self.gojo.is_split else "HONORED ONE PREVAILS"
        msg_surf = self.get_text(msg, WHITE)
        render_surf.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT//2 - 50))
        
        btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        pygame.draw.rect(render_surf, (60, 60, 80), btn_rect, border_radius=10)
        pygame.draw.rect(render_surf, WHITE, btn_rect, 2, border_radius=10)
        btn_txt = self.get_text("EXIT GAME", WHITE)
        render_surf.blit(btn_txt, (WIDTH//2 - btn_txt.get_width()//2, HEIGHT//2 + 80 - btn_txt.get_height()//2))