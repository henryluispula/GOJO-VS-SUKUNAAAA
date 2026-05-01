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

    if getattr(self, "clash_active_flag", False):
        clash_txt = self.get_text("DOMAIN CLASH!", (255, 255, 100))
        render_surf.blit(clash_txt, (WIDTH//2 - clash_txt.get_width()//2, 80))

    render_surf.blit(self.gojo_hud_bg, (10, 10))
    
    render_surf.blit(self.get_text("SATORU GOJO", (200, 230, 255)), (25, 15))
    self.draw_bar_on(render_surf, 25, 60, self.gojo.hp, self.gojo.max_hp, RED, 310, 10, "HEALTH")
    
    threshold_x = 25 + int(310 * 0.7)
    pygame.draw.line(render_surf, (255, 255, 255), (threshold_x, 58), (threshold_x, 72), 2)
    if self.gojo.hp > self.gojo.max_hp * 0.7:
        render_surf.blit(self.get_text("TANK STUN", (200, 200, 200), font=self.mini_font), (260, 30))
        
    self.draw_bar_on(render_surf, 25, 95, self.gojo.energy, self.gojo.max_energy, PURPLE, 145, 8, "CURSE ENERGY")
    self.draw_bar_on(render_surf, 190, 95, self.gojo.infinity, self.gojo.max_infinity, INF_COLOR, 145, 8, "INFINITY")
    
    stam_color = (255, 50, 50) if self.gojo.stamina < 10 else (50, 255, 100)
    self.draw_bar_on(render_surf, 25, 120, self.gojo.stamina, getattr(self.gojo, 'max_stamina', 100.0), stam_color, 310, 6, "STAMINA")

    # SD_READY_LOGIC_GOJO
    if not hasattr(self.gojo, "sd_trig"): setattr(self.gojo, "sd_trig", False)
    if self.gojo.sd_broken_timer <= 0:
        if not self.gojo.sd_trig:
            setattr(self.gojo, "sd_fx", 25.0)
            setattr(self.gojo, "sd_trig", True)
    else: setattr(self.gojo, "sd_trig", False)
    
    fx_g = getattr(self.gojo, "sd_fx", 0)
    sd_label_g = f"SIMPLE DOMAIN (CD: {int(self.gojo.sd_broken_timer)//60 + 1}s)" if self.gojo.sd_broken_timer > 0 else "SIMPLE DOMAIN"
    sd_color_g = (0, 255, 255) if self.gojo.sd_broken_timer <= 0 else (100, 100, 100)
    
    # SD_FX_DRAW_GOJO
    if fx_g > 0:
        setattr(self.gojo, "sd_fx", fx_g - time_mult)
        y_bnc = -8 if fx_g > 15 else 0 # CARTOON_BOUNCE
        flash_val = min(255, int((fx_g / 25.0) * 510))
        fx_color = (max(sd_color_g[0], flash_val), max(sd_color_g[1], flash_val), max(sd_color_g[2], flash_val))
        self.draw_bar_on(render_surf, 25, 145 + y_bnc, max(0, self.gojo.max_sd_hits - self.gojo.sd_hits), self.gojo.max_sd_hits, fx_color, 310, 6, sd_label_g)
        # CYAN_STREAK
        streak_x = 25 + (310 * (1.0 - fx_g / 25.0))
        pygame.draw.rect(render_surf, (255, 255, 255), (streak_x, 145 + y_bnc, 20, 8))
    else:
        self.draw_bar_on(render_surf, 25, 145, max(0, self.gojo.max_sd_hits - self.gojo.sd_hits), self.gojo.max_sd_hits, sd_color_g, 310, 6, sd_label_g)

    is_burned_out = self.gojo.technique_burnout > 0 and self.gojo.domain_uses >= 5
    
    b_cd = f"BLUE: {'BURN' if is_burned_out else 'RDY' if self.gojo.blue_cd<=0 else str(int(self.gojo.blue_cd)//60)+'s'}"
    r_cd = f"RED: {'BURN' if is_burned_out else 'RDY' if self.gojo.red_cd<=0 else str(int(self.gojo.red_cd)//60)+'s'}"
    
    p_status = "BURN" if is_burned_out else ("RDY" if self.gojo.purple_cd <= 0 else f"{int(self.gojo.purple_cd)//60}s")
    if self.gojo.tech_hits < self.gojo.max_tech_hits:
        p_label = f"PRPLE: LOCKED ({int(self.gojo.tech_hits)}/{self.gojo.max_tech_hits})"
        p_color = (150, 150, 150) 
    else:
        p_label = f"PRPLE: {p_status}"
        p_color = RED if is_burned_out else (200, 100, 255) 

    actual_domain_cooldown = max(self.gojo.domain_cd, self.gojo.technique_burnout)
    d_cd = f"VOID: {'BURN' if is_burned_out else 'ACT' if self.gojo.domain_active else 'RDY' if actual_domain_cooldown<=0 else str(int(actual_domain_cooldown)//60)+'s'}"
    use_txt = f"USES: {self.gojo.domain_uses}/5"

    render_surf.blit(self.get_text(f"{b_cd} | {r_cd} | ", (200, 220, 255), font=self.mini_font), (25, 170))
    render_surf.blit(self.get_text(p_label, p_color, font=self.mini_font), (180, 170)) 
    render_surf.blit(self.get_text(f"{d_cd} | {use_txt}", WHITE, font=self.mini_font), (25, 190))

    # if self.mahoraga and self.mahoraga.hp > 0:
    #     render_surf.blit(self.sukuna_hud_bg_maho, (WIDTH - 350, 10))
    # else:
    #     render_surf.blit(self.sukuna_hud_bg_normal, (WIDTH - 350, 10))
    
    # s_label = self.get_text("RYOMEN SUKUNA", (255, 100, 100))
    # render_surf.blit(s_label, (WIDTH - 335, 15))
    # if self.sukuna.potential_timer > 0:
    #     render_surf.blit(self.get_text("120% POT", (255, 215, 0), font=self.mini_font), (WIDTH - 100, 20))

    # self.draw_bar_on(render_surf, WIDTH - 335, 60, self.sukuna.hp, self.sukuna.max_hp, RED, 310, 10, "HEALTH")
    # self.draw_bar_on(render_surf, WIDTH - 335, 95, self.sukuna.energy, self.sukuna.max_energy, BLUE, 310, 8, "CURSE ENERGY")

    # sd_label_s = f"SIMPLE DOMAIN (CD: {int(self.sukuna.sd_broken_timer)//60 + 1}s)" if self.sukuna.sd_broken_timer > 0 else "SIMPLE DOMAIN"
    # sd_color_s = (0, 255, 255) if self.sukuna.sd_broken_timer <= 0 else (100, 100, 100)
    # self.draw_bar_on(render_surf, WIDTH - 335, 145, max(0, self.sukuna.max_sd_hits - self.sukuna.sd_hits), self.sukuna.max_sd_hits, sd_color_s, 310, 6, sd_label_s)

    # sukuna_is_burned_out = self.sukuna.technique_burnout > 0 and self.sukuna.domain_uses >= 5
    
    # is_da_locked_out = getattr(self.sukuna, "tactical_eval_timer", 0) > 0
    # if self.sukuna.amp_duration > 0:
    #     da_status = "ACT"
    # elif is_da_locked_out:
    #     da_status = f"{int(self.sukuna.amp_cd) // 60}s"
    # else:
    #     da_status = "RDY"
    # da_cd = f"DOMAIN AMP: {da_status}"
    
    # di_cd = f"DISMANTLE: {'BRN' if sukuna_is_burned_out else 'RDY' if self.sukuna.dismantle_cd <= 0 else str(int(self.sukuna.dismantle_cd)//60)+'s'}"
    # cl_cd = f"CLEAVE: {'BRN' if sukuna_is_burned_out else 'RDY' if self.sukuna.cleave_cd <= 0 else str(int(self.sukuna.cleave_cd)//60)+'s'}"
    
    # fu_status = "BURN" if sukuna_is_burned_out else ("RDY" if self.sukuna.fuga_cd <= 0 else f"{int(self.sukuna.fuga_cd)//60}s")
    # if self.sukuna.tech_hits < self.sukuna.max_tech_hits:
    #     fu_label = f"FUGA: LOCKED ({int(self.sukuna.tech_hits)}/{self.sukuna.max_tech_hits})"
    #     fu_color = (150, 150, 150) 
    # else:
    #     fu_label = f"FUGA: {fu_status}"
    #     fu_color = RED if sukuna_is_burned_out else (255, 150, 50)
        
    # sukuna_actual_domain_cooldown = max(self.sukuna.domain_cd, self.sukuna.technique_burnout)
    # sd_cd = f"SHRINE: {'BURN' if sukuna_is_burned_out else 'ACT' if self.sukuna.domain_active else 'RDY' if sukuna_actual_domain_cooldown<=0 else str(int(sukuna_actual_domain_cooldown)//60)+'s'}"

    # da_txt = self.get_text(da_cd, (150, 220, 255), font=self.mini_font)
    # render_surf.blit(da_txt, (WIDTH - 335, 170))
    
    # slash_str = f" | {di_cd} | {cl_cd}"
    # slash_txt = self.get_text(slash_str, (255, 150, 150), font=self.mini_font)
    # render_surf.blit(slash_txt, (WIDTH - 335 + da_txt.get_width(), 170))

    # fu_txt = self.get_text(f"{fu_label} | ", fu_color, font=self.mini_font)
    # render_surf.blit(fu_txt, (WIDTH - 335, 190))
    # render_surf.blit(self.get_text(sd_cd, WHITE, font=self.mini_font), (WIDTH - 335 + fu_txt.get_width(), 190))

    # if self.mahoraga and self.mahoraga.hp > 0:
    #     self.draw_bar_on(render_surf, WIDTH - 335, 235, self.mahoraga.hp, self.mahoraga.max_hp, MAHO_COLOR, 310, 8, "MAHORAGA")
        
    #     if self.sukuna.amp_duration > 0:
    #         ad_txt = "ADAPT: PAUSED (DOMAIN AMP)"
    #         ad_color = (255, 100, 100) 
    #     else:
    #         ad_txt = f"ADAPT: {self.mahoraga.adapting_to.upper() if self.mahoraga.adapting_to else 'NONE'}"
    #         ad_color = (255, 255, 150)
            
    #     if self.sukuna.world_slash_unlocked: 
    #         ad_txt = "WORLD SLASH BLUEPRINT ACQUIRED!"
    #         ad_color = (255, 255, 150)
            
    #     render_surf.blit(self.get_text(ad_txt, ad_color, font=self.mini_font), (WIDTH - 335, 250))
        
    #     p_p = int((1.0 - self.mahoraga.adaptation["punch"]) * 100)
    #     b_p = int((1.0 - self.mahoraga.adaptation["blue"]) * 100)
    #     r_p = int((1.0 - self.mahoraga.adaptation["red"]) * 100)
    #     pu_p = int((1.0 - self.mahoraga.adaptation["purple"]) * 100)
    #     i_p = int(self.mahoraga.adaptation["infinity"] * 100)
    #     v_p = int((1.0 - self.mahoraga.adaptation["void"]) * 100)
    #     sm_txt = f"PN:{p_p}% BL:{b_p}% RD:{r_p}% PR:{pu_p}% IN:{i_p}% VD:{v_p}%"
        
    #     render_surf.blit(self.get_text(sm_txt, WHITE, font=self.micro_font), (WIDTH - 335, 270))

    if getattr(self, "clash_active_flag", False):
        g_bar_x, g_bar_y, bar_w, bar_h = 356, 10, 15, 210
        pygame.draw.rect(render_surf, (0, 0, 0), (g_bar_x - 4, g_bar_y - 4, bar_w + 8, bar_h + 8), border_radius=4)
        pygame.draw.rect(render_surf, (40, 40, 40), (g_bar_x, g_bar_y, bar_w, bar_h), border_radius=2)
        g_stance = max(0, getattr(self.gojo, "stance", 300))
        g_fill_h = int((g_stance / 600.0) * bar_h)
        if g_fill_h > 0:
            pygame.draw.rect(render_surf, (200, 200, 255), (g_bar_x, g_bar_y + bar_h - g_fill_h, bar_w, g_fill_h), border_radius=2)

        # s_bar_x = WIDTH - 370
        # pygame.draw.rect(render_surf, (0, 0, 0), (s_bar_x - 4, g_bar_y - 4, bar_w + 8, bar_h + 8), border_radius=4)
        # pygame.draw.rect(render_surf, (40, 40, 40), (s_bar_x, g_bar_y, bar_w, bar_h), border_radius=2)
        # s_stance = max(0, getattr(self.sukuna, "stance", 300))
        # s_fill_h = int((s_stance / 600.0) * bar_h)
        # if s_fill_h > 0:
        #     pygame.draw.rect(render_surf, (255, 100, 100), (s_bar_x, g_bar_y + bar_h - s_fill_h, bar_w, s_fill_h), border_radius=2)

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
    
    if self.paused:
        self.shared_ui_overlay.fill((0, 0, 0, 200))
        render_surf.blit(self.shared_ui_overlay, (0, 0))
        
        instr_bg = pygame.Rect(WIDTH//2 - 400, HEIGHT//2 - 300, 800, 600)
        pygame.draw.rect(render_surf, (15, 15, 25, 240), instr_bg, border_radius=20)
        pygame.draw.rect(render_surf, (100, 100, 255), instr_bg, 2, border_radius=20)
        
        title = self.get_text("CONTROLS & INSTRUCTIONS", WHITE)
        render_surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 280))
        
        # Categories and their controls
        sections = [
            ("BASIC ACTIONS", [
                ("[A / D]", "Move Left/Right"),
                ("[SPACE]", "Jump / Double Jump"),
                ("[SHIFT]", "Dodge (I-frames)"),
                ("[F]", "BLOCK")
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
        
        # Set clipping area for scrolling content
        clip_rect = pygame.Rect(WIDTH//2 - 380, HEIGHT//2 - 230, 760, 460)
        old_clip = render_surf.get_clip()
        render_surf.set_clip(clip_rect)
        
        for section_title, controls in sections:
            # Draw section header
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
            
            start_y += 15 # Gap between sections

        render_surf.set_clip(old_clip)
        
        # Scroll bar visualization
        content_h = 650 # Total height of content
        view_h = 460    # Viewable area
        if content_h > view_h:
            bar_track_h = 460
            bar_w = 6
            bar_x = WIDTH//2 + 385
            bar_y = HEIGHT//2 - 230
            
            # Draw track
            pygame.draw.rect(render_surf, (30, 30, 50), (bar_x, bar_y, bar_w, bar_track_h), border_radius=3)
            
            # Draw handle
            handle_h = int((view_h / content_h) * bar_track_h)
            # Clamp scroll ratio between 0 and 1
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
        msg = "THE KING REIGNS" if self.gojo.is_split else "THE STRONGEST SURVIVED"
        msg_surf = self.get_text(msg, WHITE)
        render_surf.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT//2 - 50))
        
        btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        pygame.draw.rect(render_surf, (60, 60, 80), btn_rect, border_radius=10)
        pygame.draw.rect(render_surf, WHITE, btn_rect, 2, border_radius=10)
        btn_txt = self.get_text("EXIT GAME", WHITE)
        render_surf.blit(btn_txt, (WIDTH//2 - btn_txt.get_width()//2, HEIGHT//2 + 80 - btn_txt.get_height()//2))