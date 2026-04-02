import pygame # type: ignore
import math
import random
import time

from settings import * 
from fighter import Fighter
from projectile import Projectile 
from gojo_controls import update_gojo_controls
from sukuna_ai import update_sukuna_ai 
from domain_logic import update_domain_boundary, update_domain_clash, update_physics_and_grabs
from mahoraga_ai import update_mahoraga_ai
from projectile_logic import update_projectiles
from renderer import draw_world
from hud import draw_hud
from dev_controls import handle_dev_controls

class Game:
    # --- MAJOR FUNCTION: INITIALIZATION ---
    def __init__(self):
        pygame.init()
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.world_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT)).convert()
        self.cam_width = float(WIDTH)
        self.cam_height = float(HEIGHT)
        self.clock = pygame.time.Clock()
        self.prev_gojo_burnout = 0
        self.prev_sukuna_burnout = 0
        self.prev_world_slash_cd = 0
        self.gojo = Fighter(200, WORLD_HEIGHT - 300, "Gojo")        
        self.font = pygame.font.SysFont("Impact", 26)
        self.mini_font = pygame.font.SysFont("Impact", 16)
        self.text_cache = {}        
        self.prev_adaptations = {"blue": 1.0, "red": 1.0, "purple": 1.0, "punch": 1.0, "infinity": 0.0, "void": 1.0}
        self.maho_announcements = []        
        self.uv_stars = [(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT), random.randint(1, 4)) for _ in range(400)]
        self.star_layers = []
        for _ in range(3):
            star_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
            for sx, sy, r in self.uv_stars:
                pygame.draw.circle(star_surf, (255, 255, 255, random.randint(100, 255)), (sx, sy), r)
            self.star_layers.append(star_surf)
            
        self.cached_ms_bg = None
        self.cached_ms_shrunk = False
        self.cached_uv_bg = None
        self.cached_uv_bg_shrunk = None
        self.cached_uv_shrunk = False        
        self.shared_flash_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
        self.shared_world_overlay = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
        self.shared_ui_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.shared_ui_overlay.fill((0, 0, 0, 200))        
        self.micro_font = pygame.font.SysFont("Impact", 13)
        self.render_surf = pygame.Surface((WIDTH, HEIGHT)).convert()        
        self.gojo_hud_bg = pygame.Surface((340, 210), pygame.SRCALPHA)
        self.gojo_hud_bg.fill((0, 0, 15, 180))
        pygame.draw.rect(self.gojo_hud_bg, (100, 150, 255), (0, 0, 340, 210), 2)        
        self.sukuna_hud_bg_normal = pygame.Surface((340, 210), pygame.SRCALPHA)
        self.sukuna_hud_bg_normal.fill((20, 0, 0, 180))
        pygame.draw.rect(self.sukuna_hud_bg_normal, (255, 100, 100), (0, 0, 340, 210), 2)        
        self.sukuna_hud_bg_maho = pygame.Surface((340, 290), pygame.SRCALPHA)
        self.sukuna_hud_bg_maho.fill((20, 0, 0, 180))
        pygame.draw.rect(self.sukuna_hud_bg_maho, (255, 100, 100), (0, 0, 340, 290), 2)        
        self.clash_msg_bg = pygame.Surface((800, 100), pygame.SRCALPHA)        
        self.sukuna = Fighter(1000, WORLD_HEIGHT - 300, "Sukuna", color=WHITE)
        self.mahoraga = None
        self.projectiles = []
        self.blood_particles = [] 
        self.hit_sparks = [] 
        self.bf_words = [] 
        self.popups = [] 
        self.gojo_combo_buffer = [] 
        self.game_over = False
        self.paused = False
        self.mahoraga_summon_timer = 0 
        self.shake_timer = 0
        self.clash_msg_timer = 0
        self.clash_winner = ""        
        self.prev_adaptations = {"blue": 1.0, "red": 1.0, "purple": 1.0, "punch": 1.0, "infinity": 0.0, "void": 1.0}
        self.maho_announcements = []
        self.prev_maho_lockout = 0

    # --- MAJOR FUNCTION: TEXT CACHING & RENDERING ---
    def get_text(self, text, color, font=None):
        if font is None:
            font = self.font
        key = (text, color, font)
        if key not in self.text_cache:
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    # --- MAJOR FUNCTION: UI BAR DRAWING ---
    def draw_bar_on(self, surf, x, y, val, max_val, color, width, height, label):
        pygame.draw.rect(surf, (40, 40, 50), (x, y, width, height)) 
        fill_w = int((max(0, val) / max_val) * width)
        pygame.draw.rect(surf, color, (x, y, fill_w, height))
        pygame.draw.rect(surf, (120, 120, 150), (x, y, width, height), 1)
        if label:
            lbl = self.get_text(label, WHITE, self.mini_font)
            surf.blit(lbl, (x, y - 18))

    # --- MAJOR FUNCTION: GAME ANNOUNCEMENTS ---
    def check_announcements(self):
        """Evaluates game state changes and triggers HUD announcements."""
        tracker_source = self.mahoraga if (self.mahoraga and self.mahoraga.hp > 0) else self.sukuna
        for key in tracker_source.adaptation:
            val = tracker_source.adaptation[key]
            prev = self.prev_adaptations[key]
            is_adapted = val <= 0.0 if key != "infinity" else val >= 1.0
            was_adapted = prev <= 0.0 if key != "infinity" else prev >= 1.0

            if is_adapted and not was_adapted:
                tracker_source.adapt_pulse_timer = 30
                
                if key == "void" and (self.mahoraga is None or self.mahoraga.hp <= 0):
                    self.maho_announcements.append({"text": "MEGUMI'S SOUL ADAPTED TO UNLIMITED VOID!", "timer": 180})
                else:
                    self.maho_announcements.append({"text": f"MAHORAGA HAS FULLY ADAPTED TO {key.upper()}!", "timer": 180})
                
                if key == "infinity" and not self.sukuna.world_slash_unlocked:
                    self.sukuna.world_slash_unlocked = True
                    self.maho_announcements.append({"text": "SUKUNA HAS ACQUIRED THE WORLD CUTTING SLASH!", "timer": 240})
                    
            self.prev_adaptations[key] = val

        current_maho_lockout = getattr(self.sukuna, "mahoraga_lockout", 0)
        if getattr(self, "prev_maho_lockout", 0) > 0 and current_maho_lockout == 0:
            self.maho_announcements.append({"text": "MAHORAGA PARALYSIS LOCK EXPIRED!", "timer": 180})
        self.prev_maho_lockout = current_maho_lockout

        if self.sukuna.world_slash_cd <= 0 and self.prev_world_slash_cd > 0:
            self.maho_announcements.append({"text": "WORLD CUTTING SLASH IS READY!", "timer": 120})
        self.prev_world_slash_cd = self.sukuna.world_slash_cd

        if not self.gojo.domain_active and self.gojo.technique_burnout > 0 and self.prev_gojo_burnout <= 0:
            if self.gojo.domain_uses > 0 and self.gojo.domain_uses % 5 == 0:
                self.maho_announcements.append({"text": "GOJO'S CURSED TECHNIQUE HAS BURNED OUT!", "timer": 90})
                
        if not self.sukuna.domain_active and self.sukuna.technique_burnout > 0 and self.prev_sukuna_burnout <= 0:
            if self.sukuna.domain_uses > 0 and self.sukuna.domain_uses % 5 == 0:
                self.maho_announcements.append({"text": "SUKUNA'S CURSED TECHNIQUE HAS BURNED OUT!", "timer": 90})
        
        self.prev_gojo_burnout = self.gojo.technique_burnout
        self.prev_sukuna_burnout = self.sukuna.technique_burnout

    # --- MAJOR FUNCTION: MAIN GAME LOOP ---
    def run(self):
        self.dt = 0.016 
        running = True
        while running:
            self.screen.fill(BLACK)
            keys = pygame.key.get_pressed()
            mouse_click = pygame.mouse.get_pressed()
            
            self.gojo.simple_domain_active = False
            self.sukuna.simple_domain_active = False
            
            if not hasattr(self, "pb_blue_ready"): self.pb_blue_ready = True
            if not hasattr(self, "pb_red_ready"): self.pb_red_ready = True
            
            if not (keys[pygame.K_e] and keys[pygame.K_w]): self.pb_blue_ready = True
            if not (keys[pygame.K_e] and keys[pygame.K_s]): self.pb_red_ready = True
            
            # --- EVENT HANDLING & DEV OVERRIDES ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p: self.paused = not self.paused
                    handle_dev_controls(self, event) 

                if not self.game_over:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE: self.gojo.jump()
                        if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: self.gojo.dodge()                       
                        if event.key == pygame.K_w: self.gojo_combo_buffer.append("W")
                        if event.key == pygame.K_s: self.gojo_combo_buffer.append("S")
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.gojo_combo_buffer.append("CLICK")
                    
                    self.gojo_combo_buffer = self.gojo_combo_buffer[-3:]
                    
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if WIDTH//2 - 100 < event.pos[0] < WIDTH//2 + 100 and HEIGHT//2 + 50 < event.pos[1] < HEIGHT//2 + 110:
                            running = False

            # --- COMBAT SIMULATION & AI UPDATES ---
            if not self.game_over and not self.paused and self.mahoraga_summon_timer <= 0:
                
                target = self.sukuna 
                
                time_mult = self.dt * 60.0
                
                # --- BLACK FLASH IMPACT PAUSE ---
                bf_timer = getattr(self, "bf_zoom_timer", 0)
                if bf_timer > 25:
                    sim_dt = 0 
                else:
                    sim_dt = self.dt
                
                punching = update_gojo_controls(self, keys, mouse_click, target, sim_dt)
                dist, fuga_priority, gojo_has_inf = update_sukuna_ai(self, sim_dt)
                update_domain_boundary(self)
                
                gojo_can_clash = update_physics_and_grabs(self, sim_dt)
                update_domain_clash(self, keys, gojo_can_clash, sim_dt)

                if self.mahoraga and self.mahoraga.hp > 0:
                    update_mahoraga_ai(self, sim_dt) 

                self.check_announcements()        

                # --- UNLIMITED VOID & ADAPTATION LOGIC ---
                if self.gojo.domain_active:
                    if self.mahoraga and self.mahoraga.hp > 0 and self.mahoraga.adaptation["void"] <= 0:
                        self.gojo.end_domain()
                        self.gojo.domain_cd = 3000
                        self.shake_timer = 30
                        self.maho_announcements.append({"text": "MAHORAGA SHATTERED UNLIMITED VOID!", "timer": 180})
                        self.sukuna.is_paralyzed = False
                        self.mahoraga.is_paralyzed = False
                    else:
                        for enemy in [self.sukuna, self.mahoraga]:
                            if enemy and enemy.hp > 0:
                                is_touching_gojo = enemy.rect.colliderect(self.gojo.rect)
                                
                                if getattr(enemy, "simple_domain_active", False) and not is_touching_gojo:
                                    enemy.is_paralyzed = False 
                                    enemy.sd_hits += 1 * time_mult
                                    if enemy.sd_hits >= enemy.max_sd_hits: 
                                        enemy.simple_domain_active = False
                                        enemy.sd_was_active = False
                                        enemy.sd_broken_timer = 120 
                                        self.popups.append({"x": enemy.rect.centerx, "y": enemy.rect.centery - 100, "timer": 45, "text": "SD CRUMBLED!", "color": RED})
                                        self.shake_timer = 15
                                        enemy.is_paralyzed = True
                                elif is_touching_gojo:
                                    enemy.is_paralyzed = False 
                                else:
                                    if enemy.name == "Mahoraga" and enemy.adaptation["void"] <= 0:
                                        enemy.is_paralyzed = False 
                                    elif enemy.name == "Sukuna" and enemy.domain_active:
                                        enemy.is_paralyzed = False 
                                    else:
                                        enemy.is_paralyzed = True
                                        uv_dmg = 1.5 * (enemy.adaptation["void"] if enemy.name == "Mahoraga" else 1.0) * time_mult
                                        enemy.hp -= uv_dmg
                                        
                                        brain_drain = (4.5 if not getattr(enemy, "simple_domain_active", False) else 1.5) * time_mult
                                        enemy.energy = max(0, enemy.energy - brain_drain)

                                if enemy.name == "Sukuna" and enemy.is_paralyzed:
                                    enemy.dismantle_cd = 2
                                    enemy.cleave_cd = 2
                                    enemy.amp_cd = 2
                                    enemy.amp_duration = 0
                                    enemy.sd_broken_timer = 2
                                    enemy.rct_timer = 0
                                    enemy.fuga_cd = 2
                                    enemy.attack_cooldown = 2
                                    
                                    if self.mahoraga is None or self.mahoraga.hp <= 0:
                                        if not getattr(enemy, "mahoraga_is_dead", False):
                                            enemy.adapting_to = "void"
                                            enemy.adaptation_points["void"] += 2.0 * time_mult
                                            turns = enemy.adaptation_points["void"] / 250.0
                                            enemy.adaptation["void"] = max(0, 1.0 - min(1.0, turns / 10.0)) 
                                        else:
                                            enemy.adapting_to = None 

                                if enemy.name == "Mahoraga" and self.sukuna.amp_duration <= 0:
                                    enemy.adapting_to = "void"
                                    enemy.adaptation_points["void"] += 2.0 * time_mult
                                    turns = enemy.adaptation_points["void"] / 250.0
                                    enemy.adaptation["void"] = max(0, 1.0 - min(1.0, turns / 10.0)) 
                else:
                    self.sukuna.is_paralyzed = False
                    if self.mahoraga: self.mahoraga.is_paralyzed = False
                
                # --- SUKUNA DOMAIN SURE-HIT ---
                if self.sukuna.domain_active and not self.sukuna.is_paralyzed:
                    self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2 * time_mult)
                    
                    if not hasattr(self.sukuna, "sure_hit_ticker"): self.sukuna.sure_hit_ticker = 0
                    self.sukuna.sure_hit_ticker += time_mult

                    if self.sukuna.sure_hit_ticker >= 8:
                        self.sukuna.sure_hit_ticker -= 8
                        if not self.gojo.domain_active:
                            self.sukuna.tech_hits = min(self.sukuna.max_tech_hits, self.sukuna.tech_hits + 2)
                            
                            sx = self.gojo.rect.centerx + random.randint(-40, 40)
                            sy = self.gojo.rect.centery + random.randint(-60, 60)
                            stype = "cleave" if abs(self.sukuna.rect.centerx - self.gojo.rect.centerx) < 150 else "dismantle"
                            
                            self.projectiles.append(Projectile(sx, sy, self.gojo.rect.centerx, self.gojo.rect.centery, 5, RED, size_mult=3.0, type=stype, is_sure_hit=True))

                update_projectiles(self, sim_dt)

                # --- SUKUNA SURVIVAL VOWS & ESCAPE ---
                if self.sukuna.hp <= (self.sukuna.max_hp * 0.24) and self.sukuna.hp > 0:
                    
                    if self.sukuna.energy > 40 * self.sukuna.cost_mult and not self.sukuna.ce_exhausted:
                        self.sukuna.energy -= 12.0 * self.sukuna.cost_mult 
                        self.sukuna.hp = min((self.sukuna.max_hp * 0.5), self.sukuna.hp + 3.5) 
                        self.sukuna.rct_timer = 5
                    
                    if self.sukuna.energy >= 200 * self.sukuna.cost_mult and self.sukuna.domain_cd <= 0 and self.sukuna.technique_burnout <= 0 and self.sukuna.domain_charge <= 0 and not self.sukuna.domain_active and self.gojo.grab_timer <= 0 and self.mahoraga_summon_timer <= 0:
                        self.sukuna.domain_charge = 60
                        self.sukuna.energy -= 200 * self.sukuna.cost_mult
                        self.popups.append({"x": self.sukuna.rect.centerx, "y": self.sukuna.rect.centery - 100, "timer": 60, "text": "DESPERATE DOMAIN!", "color": RED})
                        
                    if self.gojo.grab_timer <= 0 and not self.gojo.domain_active and not self.sukuna.domain_active and self.mahoraga_summon_timer <= 0:

                        if dist > 480:
                            run_dir = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                        elif dist < 420:
                            run_dir = 1 if self.sukuna.rect.x > self.gojo.rect.x else -1
                        else:
                            run_dir = self.sukuna.direction 
                        
                        if (self.sukuna.rect.left < 150 and run_dir == -1) or (self.sukuna.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                            run_dir *= -1
                            if self.sukuna.on_ground: self.sukuna.jump()
                        
                        if self.sukuna.energy > 2.0 * self.sukuna.cost_mult and not self.sukuna.ce_exhausted:
                            self.sukuna.rect.x += 22 * run_dir * time_mult
                            self.sukuna.energy -= 2.0 * self.sukuna.cost_mult * time_mult
                        else:
                            self.sukuna.rect.x += 18 * run_dir * time_mult
                        
                        if self.sukuna.dodge_cd <= 0 and self.sukuna.stamina >= 20:
                            if dist < 300 and random.random() < 0.5:
                                self.sukuna.direction = -1 if self.sukuna.rect.x > self.gojo.rect.x else 1
                            else:
                                self.sukuna.direction = run_dir
                                
                            self.sukuna.dodge()
                            self.sukuna.dodge_cd = 15 

                if self.sukuna.hp <= 0:
                    self.sukuna.hp = 0
                    if self.mahoraga and self.mahoraga.hp > 0: 
                        self.mahoraga.hp = 0 
                    self.game_over = True
                if self.gojo.hp <= 0: self.gojo.is_split, self.game_over = True, True

            # --- MAHORAGA SPAWNING EXECUTION ---
            if self.mahoraga_summon_timer > 0:
                self.mahoraga_summon_timer -= time_mult
                if self.mahoraga_summon_timer <= 0:
                    self.mahoraga_summon_timer = 0
                    self.mahoraga = Fighter(self.sukuna.rect.x - 100, WORLD_HEIGHT - 1800, "Mahoraga", MAHO_COLOR)
                    self.sukuna.mahoraga_was_summoned = True
                    self.mahoraga.hp = self.mahoraga.max_hp 
                    self.mahoraga.vel_y = 120 
                    self.mahoraga.on_ground = False
                    setattr(self.mahoraga, "is_cinematic_landing", True) 
                    
                    self.mahoraga.adaptation_points = self.sukuna.adaptation_points.copy()
                    self.mahoraga.adaptation = self.sukuna.adaptation.copy()

            display_offset = (0,0)
            if self.shake_timer > 0:
                self.shake_timer -= time_mult
                display_offset = (random.randint(-10, 10), random.randint(-10, 10))

            if not hasattr(self, "ce_hud_popups"): self.ce_hud_popups = []

            # --- DAMAGE & CURSED ENERGY TRACKING ---
            for fighter in [self.gojo, self.sukuna, self.mahoraga]:
                if fighter is not None:
                    if fighter.hp < fighter.prev_hp:
                        damage = fighter.prev_hp - fighter.hp
                        
                        if fighter.domain_charge > 0:
                            fighter.domain_charge = 0
                            fighter.domain_cd = 300 
                            self.popups.append({"x": fighter.rect.centerx, "y": fighter.rect.centery - 100, "timer": 45, "text": "DOMAIN INTERRUPTED!", "color": WHITE})
                        
                        if fighter.name == "Sukuna" and damage >= 60: 
                            if fighter.domain_active:
                                break_chance = 0.75 if damage >= 120 else 0.30 
                                if random.random() < break_chance:
                                    fighter.end_domain()
                                    self.shake_timer = 20 
                                    self.popups.append({"x": fighter.rect.centerx, "y": fighter.rect.centery - 100, "timer": 60, "text": "DOMAIN SHATTERED!", "color": WHITE})
                        
                        num_drops = min(int(damage * 1.5), 40) 
                        for _ in range(num_drops):
                            bx = fighter.rect.centerx + random.randint(-30, 30)
                            by = fighter.rect.centery + random.randint(-50, 50)
                            vx = random.uniform(-6, 6)
                            vy = random.uniform(-10, -2)
                            self.blood_particles.append([bx, by, vx, vy, random.randint(20, 45), random.randint(2, 6)])
                    
                    if fighter.energy < fighter.prev_energy:
                        change = fighter.prev_energy - fighter.energy
                        hp_lost = fighter.prev_hp - fighter.hp
                        
                        is_damage = False
                        if hp_lost > 0:
                            is_damage = True

                        elif fighter.name == "Gojo" and fighter.infinity > 0:
                            if change > (0.15 * fighter.cost_mult) or change > 1000:
                                is_damage = True
                                fighter.inf_hit_timer = 25
                                
                        if is_damage:
                            fighter.ce_loss_accum += change
                            
                            if fighter.ce_loss_accum >= 5.0 and fighter.name in ["Gojo", "Sukuna"]:
                                fighter.aura_hit_timer = 45 
                                
                                x_offset = random.randint(-15, 15)
                                val_to_show = int(fighter.ce_loss_accum)
                                fighter.ce_loss_accum -= val_to_show 
                                
                                if fighter.name == "Gojo":
                                    self.ce_hud_popups.append({"x": 165 + x_offset, "y": 75, "val": val_to_show, "timer": 45, "color": PURPLE})
                                elif fighter.name == "Sukuna":
                                    self.ce_hud_popups.append({"x": WIDTH - 205 + x_offset, "y": 75, "val": val_to_show, "timer": 45, "color": BLUE})

            # --- WORLD RENDERING & CAMERA LOGIC ---
            draw_world(self, punching, self.dt)

            active_f = [self.gojo, self.sukuna]
            if self.mahoraga and self.mahoraga.hp > 0: active_f.append(self.mahoraga)
            
            if self.gojo.domain_active and getattr(self.gojo, "domain_shrunk", False) and hasattr(self.gojo, "domain_center_x"):
                target_cam_height = 800.0
                target_cam_width = target_cam_height * (WIDTH / HEIGHT)
                
                target_center_x = self.gojo.domain_center_x
                target_center_y = self.gojo.domain_center_y
            else:
                min_x = min(f.rect.centerx for f in active_f)
                max_x = max(f.rect.centerx for f in active_f)
                min_y = min(f.rect.centery for f in active_f)
                max_y = max(f.rect.centery for f in active_f)
                
                dist_x = max_x - min_x + 600
                dist_y = max_y - min_y + 400

                if dist_x / WIDTH > dist_y / HEIGHT:
                    target_cam_width = max(WIDTH, dist_x)
                    target_cam_height = target_cam_width * (HEIGHT / WIDTH)
                else:
                    target_cam_height = max(HEIGHT, dist_y)
                    target_cam_width = target_cam_height * (WIDTH / HEIGHT)
                    
                target_center_x = (min_x + max_x) / 2
                target_center_y = (min_y + max_y) / 2
            
            # --- EPIC BLACK FLASH ---
            if getattr(self, "bf_zoom_timer", 0) > 0:
                self.bf_zoom_timer -= time_mult
                
                target_center_x, target_center_y = self.bf_zoom_pos
                
                self.cam_width += (target_cam_width - self.cam_width) * 0.4 * time_mult
                self.cam_height += (target_cam_height - self.cam_height) * 0.4 * time_mult
                self.cam_x += (target_center_x - getattr(self, "cam_x", target_center_x)) * 0.4 * time_mult
                self.cam_y += (target_center_y - getattr(self, "cam_y", target_center_y)) * 0.4 * time_mult
                
            else:
                self.cam_width += (target_cam_width - self.cam_width) * 0.1 * time_mult
                self.cam_height += (target_cam_height - self.cam_height) * 0.1 * time_mult
            
            if not hasattr(self, "cam_x"):
                self.cam_x = target_center_x
                self.cam_y = target_center_y
                
            self.cam_x += (target_center_x - self.cam_x) * 0.1 * time_mult
            self.cam_y += (target_center_y - self.cam_y) * 0.1 * time_mult
            
            self.cam_width = max(WIDTH * 0.5, min(WORLD_WIDTH, self.cam_width))
            self.cam_height = max(HEIGHT * 0.5, min(WORLD_HEIGHT, self.cam_height))
            
            cam_left = self.cam_x - self.cam_width / 2
            cam_top = self.cam_y - self.cam_height / 2

            c_left = int(max(0, min(WORLD_WIDTH - self.cam_width, cam_left)))
            c_top = int(max(0, min(WORLD_HEIGHT - self.cam_height, cam_top)))
            c_width = int(self.cam_width)
            c_height = int(self.cam_height)

            visible_world = self.world_surf.subsurface((c_left, c_top, c_width, c_height))
            scaled_visible = pygame.transform.scale(visible_world, (WIDTH, HEIGHT))
            
            render_surf = self.render_surf 
            render_surf.blit(scaled_visible, (0, 0)) 
            draw_hud(self, render_surf, self.dt)
            
            self.screen.blit(render_surf, display_offset)
            pygame.display.flip()            
            
            for fighter in [self.gojo, self.sukuna, self.mahoraga]:
                if fighter is not None:
                    fighter.prev_hp = fighter.hp
                    fighter.prev_energy = fighter.energy
            
            self.dt = self.clock.tick(FPS) / 1000.0
            
            if self.dt > 0.1:
                self.dt = 0.1
                
        pygame.quit()