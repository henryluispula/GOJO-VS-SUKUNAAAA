import math
import pygame 
import importlib
import sys
import time
import random

# Initial imports
import settings
import aura
import fighter

def run_studio():
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Fighter Design Studio - [R]eload | [1-3] Switch | [P]unch | [B]lack Flash")
    clock = pygame.time.Clock()

    def create_preview_fighter(name):
        # Match the logic from game.py
        if name == "Sukuna":
            f = fighter.Fighter(400, 400, name, color=settings.WHITE)
        elif name == "Mahoraga":
            f = fighter.Fighter(400, 400, name, color=settings.MAHO_COLOR)
        else:
            f = fighter.Fighter(400, 400, name) # Defaults to CLOTHES (Gojo)

        # Persistent effects for design review
        f.rct_timer = 999
        f.aura_hit_timer = 999
        return f

    current_fighter = create_preview_fighter("Sukuna")
    running = True

    # --- BUTTON UI CONFIG ---
    ui_font = pygame.font.SysFont("Consolas", 14)
    buttons = [
        {"label": "GOJO [1]", "key": pygame.K_1, "rect": pygame.Rect(10, 40, 110, 30)},
        {"label": "SUKUNA [2]", "key": pygame.K_2, "rect": pygame.Rect(10, 80, 110, 30)},
        {"label": "MAHORAGA [3]", "key": pygame.K_3, "rect": pygame.Rect(10, 120, 110, 30)},
        
        {"label": "PUNCH [P]", "key": pygame.K_p, "rect": pygame.Rect(130, 40, 110, 30)},
        {"label": "BLACK FLASH [B]", "key": pygame.K_b, "rect": pygame.Rect(130, 80, 110, 30)},
        {"label": "GRAB [G]", "key": pygame.K_g, "rect": pygame.Rect(130, 120, 110, 30)},
        
        {"label": "120% POT [V]", "key": pygame.K_v, "rect": pygame.Rect(250, 40, 110, 30)},
        {"label": "DOM AMP [A]", "key": pygame.K_a, "rect": pygame.Rect(250, 80, 110, 30)},
        {"label": "SIM DOM [D]", "key": pygame.K_d, "rect": pygame.Rect(250, 120, 110, 30)},
        
        {"label": "DAMAGE [H]", "key": pygame.K_h, "rect": pygame.Rect(370, 40, 110, 30)},
        {"label": "HEAL [J]", "key": pygame.K_j, "rect": pygame.Rect(370, 80, 110, 30)},
        {"label": "KILL [K]", "key": pygame.K_k, "rect": pygame.Rect(370, 120, 110, 30)},
        
        {"label": "EXHAUST [U]", "key": pygame.K_u, "rect": pygame.Rect(490, 40, 110, 30)},
        {"label": "RESTORE [I]", "key": pygame.K_i, "rect": pygame.Rect(490, 80, 110, 30)},
        
        {"label": "RELOAD [R]", "key": pygame.K_r, "rect": pygame.Rect(10, 170, 590, 30)},
    ]

    while running:
        screen.fill((20, 20, 25)) # Slightly darker for better contrast
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Helper to handle actions
            def handle_action(action_key):
                nonlocal current_fighter
                if action_key == pygame.K_r:
                    print("Reloading fighter.py and aura.py...")
                    importlib.reload(settings)
                    importlib.reload(aura)
                    importlib.reload(fighter)
                    hp = current_fighter.hp
                    energy = current_fighter.energy
                    current_fighter = create_preview_fighter(current_fighter.name)
                    current_fighter.hp = hp # keep hp across reloads
                    current_fighter.energy = energy # keep energy across reloads
                elif action_key == pygame.K_1: current_fighter = create_preview_fighter("Gojo")
                elif action_key == pygame.K_2: current_fighter = create_preview_fighter("Sukuna")
                elif action_key == pygame.K_3: current_fighter = create_preview_fighter("Mahoraga")
                elif action_key == pygame.K_p: current_fighter.punch_timer = 20
                elif action_key == pygame.K_b: current_fighter.black_flash_timer = 30
                elif action_key == pygame.K_g: current_fighter.grab_timer = 30
                elif action_key == pygame.K_v: 
                    if getattr(current_fighter, "potential_timer", 0) > 0: current_fighter.potential_timer = 0
                    else: current_fighter.potential_timer = 600
                elif action_key == pygame.K_a:
                    if getattr(current_fighter, "amp_duration", 0) > 0: current_fighter.amp_duration = 0
                    else: current_fighter.amp_duration = 600
                elif action_key == pygame.K_d:
                    current_fighter.simple_domain_active = not getattr(current_fighter, "simple_domain_active", False)
                elif action_key == pygame.K_h:
                    current_fighter.hp = max(1, current_fighter.hp - current_fighter.max_hp * 0.1)
                elif action_key == pygame.K_j:
                    current_fighter.hp = min(current_fighter.max_hp, current_fighter.hp + current_fighter.max_hp * 0.1)
                elif action_key == pygame.K_k:
                    current_fighter.hp = 0
                elif action_key == pygame.K_u:
                    current_fighter.energy = max(0, current_fighter.energy - current_fighter.max_energy * 0.1)
                elif action_key == pygame.K_i:
                    current_fighter.energy = min(current_fighter.max_energy, current_fighter.energy + current_fighter.max_energy * 0.1)

            if event.type == pygame.KEYDOWN:
                handle_action(event.key)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for btn in buttons:
                        if btn["rect"].collidepoint(event.pos):
                            handle_action(btn["key"])

        # Manually progress animation frames
        current_fighter.anim_tick += 1
        if current_fighter.punch_timer > 0: current_fighter.punch_timer -= 1
        if current_fighter.black_flash_timer > 0: current_fighter.black_flash_timer -= 1
        if getattr(current_fighter, "grab_timer", 0) > 0: current_fighter.grab_timer -= 1
        
        # Lock position to center
        current_fighter.rect.center = (400, 450) # Shifted down to make room for UI
        
        # Draw everything from fighter.py
        eff = "summoning" if getattr(current_fighter, "is_paralyzed", False) else None
        current_fighter.draw_detailed(screen, effect=eff, is_amp=getattr(current_fighter, "amp_duration", 0) > 0)

        # --- DRAW UI BUTTONS ---
        for btn in buttons:
            is_hover = btn["rect"].collidepoint(mouse_pos)
            color = (60, 60, 90) if is_hover else (40, 40, 60)
            pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
            pygame.draw.rect(screen, settings.WHITE, btn["rect"], 1, border_radius=5)
            
            txt = ui_font.render(btn["label"], True, settings.WHITE)
            screen.blit(txt, (btn["rect"].centerx - txt.get_width()//2, btn["rect"].centery - txt.get_height()//2))

        # --- DRAW TEXT OVERLAYS ---
        f = current_fighter
        g_color = settings.RED
        if f.name == "Gojo": g_color = settings.PURPLE
        elif f.name == "Sukuna": g_color = settings.BLUE
        elif f.name == "Mahoraga": g_color = settings.MAHO_COLOR

        font = pygame.font.SysFont("Impact", 26)
        def get_text(text, color): return font.render(text, True, color)

        base_y = f.rect.y - 120
        
        # GRABBED
        if getattr(f, "grab_timer", 0) > 0:
            scale_f = 1.1 + math.sin(pygame.time.get_ticks() * 0.012) * 0.1
            txt = get_text("GRABBED!", settings.BLACK)
            out = get_text("GRABBED!", g_color)
            s_out = pygame.transform.scale(out, (int(out.get_width() * scale_f), int(out.get_height() * scale_f)))
            s_txt = pygame.transform.scale(txt, (int(txt.get_width() * scale_f), int(txt.get_height() * scale_f)))
            gx, gy = f.rect.centerx, base_y
            base_y -= 40
            for dx, dy in [(-3,-3), (3,3), (-3,3), (3,-3)]: screen.blit(s_out, (gx - s_out.get_width()//2 + dx, gy - s_out.get_height()//2 + dy))
            screen.blit(s_txt, (gx - s_txt.get_width()//2, gy - s_txt.get_height()//2))

        # 120% POTENTIAL
        if getattr(f, "potential_timer", 0) > 0:
            scale_f = 1.0 + math.sin(pygame.time.get_ticks() * 0.008) * 0.05
            pot_txt = get_text("120% POTENTIAL", settings.BLACK)
            pot_out = get_text("120% POTENTIAL", g_color)
            s_out = pygame.transform.scale(pot_out, (int(pot_out.get_width() * scale_f), int(pot_out.get_height() * scale_f)))
            s_txt = pygame.transform.scale(pot_txt, (int(pot_txt.get_width() * scale_f), int(pot_txt.get_height() * scale_f)))
            gx, gy = f.rect.centerx, base_y
            for dx, dy in [(-3,-3), (3,3), (-3,3), (3,-3)]: screen.blit(s_out, (gx - s_out.get_width()//2 + dx, gy - s_out.get_height()//2 + dy))
            screen.blit(s_txt, (gx - s_txt.get_width()//2, gy - s_txt.get_height()//2))

            # Black & Red Lightning
            for _ in range(2):
                start_x = f.rect.centerx + random.randint(-70, 70)
                start_y = f.rect.centery + random.randint(-110, 110)
                end_x = start_x + random.randint(-50, 50)
                end_y = start_y + random.randint(-50, 50)
                lightning_color = settings.BLACK if random.random() > 0.5 else settings.RED
                thickness = random.randint(2, 5)
                pygame.draw.line(screen, lightning_color, (start_x, start_y), (end_x, end_y), thickness)
                if random.random() > 0.5:
                    branch_x = end_x + random.randint(-30, 30)
                    branch_y = end_y + random.randint(-30, 30)
                    pygame.draw.line(screen, lightning_color, (end_x, end_y), (branch_x, branch_y), max(1, thickness - 1))

        # Status Label
        screen.blit(pygame.font.SysFont("Impact", 20).render("FIGHTER STUDIO - CONTROLS UI", True, settings.WHITE), (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_studio()