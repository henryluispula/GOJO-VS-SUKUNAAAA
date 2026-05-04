import pygame, random, math 
from settings import *
from projectile import Projectile


def update_domain_boundary(game):
    """Constrains fighters within the shrunk UV bubble."""
    g = game.gojo
    if g.domain_active and getattr(g, "domain_shrunk", False):
        if not hasattr(g, "domain_center_x"):
            g.domain_center_x = max(750, min(WORLD_WIDTH - 750, g.rect.centerx))
            g.domain_center_y = max(450, min(WORLD_HEIGHT - 450, g.rect.centery))
    else:
        g.domain_shrunk = False
        for attr in ("domain_center_x", "domain_center_y"):
            if hasattr(g, attr): delattr(g, attr)

    if g.domain_active and getattr(g, "domain_shrunk", False) and hasattr(g, "domain_center_x"):
        cx, cy, radius = g.domain_center_x, g.domain_center_y, 400
        for f in [g, game.sukuna]:
            if f and f.hp > 0:
                dx, dy = f.rect.centerx - cx, f.rect.centery - cy
                d = math.hypot(dx, dy)
                if d > radius - 35 and d > 0:
                    push = (radius - 35 - d) * 0.8
                    f.rect.x += (dx / d) * push; f.rect.y += (dy / d) * push


def update_physics_and_grabs(game, dt):
    """CE regen (cinematic), beatdown/grab damage, physics tick. Returns gojo_can_clash."""
    g = game.gojo; s = game.sukuna
    is_cinematic = g.domain_charge > 0 or s.domain_charge > 0 or getattr(game, "clash_decision_timer", 0) > 0
    active_fighters = [f for f in [g, s, game.mahoraga] if f]
    time_mult = dt * 60.0

    if is_cinematic:
        g.vel_y = 0; s.vel_y = 0
        if game.mahoraga: game.mahoraga.vel_y = 0
        for f in active_fighters:
            base_regen = 25.0 if f.name == "Gojo" else 0.8 if f.name == "Mahoraga" else 1.0
            regen_mult = 1.2 if f.potential_timer > 0 else 1.0
            if f.energy <= 0.5:
                f.ce_exhausted = True
                if f.name == "Gojo": f.infinity = 0
            if f.ce_exhausted:
                regen_mult *= 0.8 if f.name == "Sukuna" else 0.4
                thresh = 80 if f.name == "Sukuna" else (420 if f.name == "Gojo" else 30)
                if f.energy >= thresh: f.ce_exhausted = False
            f.energy = min(f.max_energy, f.energy + base_regen * regen_mult * time_mult)
            if f.name == "Gojo" and f.infinity < f.max_infinity and f.technique_burnout == 0:
                inf_cost = 0.1 * f.cost_mult * time_mult
                if f.energy >= inf_cost:
                    f.prev_energy = f.energy
                    f.infinity = min(f.max_infinity, f.infinity + 3.5 * time_mult)
                    f.energy -= inf_cost
    else:
        # ── Sukuna beatdown escape ───────────────────────────────────────────
        if s.grab_timer > 0 and getattr(s, "grab_type", "") == "gojo_beatdown":
            escaped = False
            if s.attack_cooldown <= 0 and random.random() < 0.08:
                is_burned_out = (g.domain_uses >= 5 and g.technique_burnout > 0)
                has_infinity = g.infinity > 0 and g.energy > 0 and not is_burned_out
                is_da_locked_out = getattr(s, "tactical_eval_timer", 0) > 0
                can_da_counter = has_infinity and s.grab_cd <= 0 and s.energy >= 15 * s.cost_mult and not is_da_locked_out
                can_cleave_counter = (not has_infinity or s.amp_duration <= 0) and s.grab_cd <= 0 and s.energy >= 30 * s.cost_mult and s.cleave_cd <= 0
                can_da_escape = (s.amp_cd <= 0 or s.amp_duration > 0) and s.energy >= 10 * s.cost_mult and not is_da_locked_out
                if can_da_counter or can_cleave_counter:
                    s.grab_timer = 0; g.grab_timer = 300; g.purple_charge = 0; g.domain_charge = 0; s.attack_cooldown = 30; escaped = True
                    if can_da_counter:
                        g.grab_type = "amp_punch"; s.amp_duration = max(s.amp_duration, 300); s.energy -= 15 * s.cost_mult; s.grab_cd = 480
                        game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 80, "timer": 45, "text": "COUNTER: DA BEATDOWN!", "color": (255, 255, 0)})
                    else:
                        g.grab_type = "cleave"; s.amp_duration = 0; s.energy -= 30 * s.cost_mult; s.cleave_cd = 600; s.grab_cd = 600
                        game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 80, "timer": 45, "text": "COUNTER: CLEAVE!", "color": RED})
                        p = Projectile(g.rect.centerx, g.rect.centery, g.rect.centerx, g.rect.centery, 1, RED, size_mult=4.0, type="cleave")
                        p.vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 0.1
                        p.lifetime = 300; p.is_grab_cleave = True; game.projectiles.append(p)
                elif can_da_escape and s.hp < s.max_hp * 0.65:
                    s.grab_timer = 0; s.amp_duration = max(s.amp_duration, 60); s.energy -= 10 * s.cost_mult; s.attack_cooldown = 20; escaped = True
                    kb_dir = 1 if s.rect.centerx > g.rect.centerx else -1
                    s.rect.x += kb_dir * 180; g.rect.x -= kb_dir * 180; game.shake_timer = 15
                    game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 80, "timer": 45, "text": "DA BURST ESCAPE!", "color": WHITE})

            if not escaped:
                s.rect.centerx = g.rect.centerx + (40 * g.direction); s.rect.centery = g.rect.centery
                beatdown_dmg = 1.2 * time_mult
                imbue_cost = 2.0 * g.cost_mult * time_mult
                if g.energy >= imbue_cost: g.energy -= imbue_cost; beatdown_dmg *= 1.6
                if s.energy > 0:
                    rm = random.uniform(0.15, 0.35); md = beatdown_dmg * (1.0 - rm); beatdown_dmg *= rm
                    s.energy = max(0, s.energy - (md * 2.0) * s.cost_mult)
                s.hp -= beatdown_dmg; g.tech_hits = min(g.max_tech_hits, g.tech_hits + beatdown_dmg)
                
                if not hasattr(s, "vfx_ticker"): s.vfx_ticker = 0
                s.vfx_ticker += time_mult
                if s.vfx_ticker >= 6:
                    s.vfx_ticker -= 6
                    game.shake_timer = 3; sc = WHITE if random.random() < 0.5 else BLUE
                    for _ in range(6): game.hit_sparks.append([s.rect.centerx + random.randint(-20, 20), s.rect.centery + random.randint(-30, 30), random.uniform(-10, 10), random.uniform(-10, 10), random.randint(15, 30), sc])

        # ── Gojo grab (Sukuna holds Gojo) ────────────────────────────────────
        if g.grab_timer > 0:
            grab_type = getattr(g, "grab_type", "cleave")
            
            if s.technique_burnout > 0 and grab_type == "cleave":
                g.grab_timer = 0
                return g.technique_burnout == 0 and g.infinity > 0 and g.energy >= 50

            g.rect.centerx = s.rect.centerx + (40 * s.direction); g.rect.centery = s.rect.centery
            
            if not hasattr(g, "vfx_ticker"): g.vfx_ticker = 0
            g.vfx_ticker += time_mult

            def _cleave_tick():
                if g.infinity > 0 and g.energy > 0 and g.technique_burnout == 0:
                    g.energy = max(0, g.energy - 3.0 * g.cost_mult * time_mult)
                    g.inf_hit_timer = 15 
                    s.tech_hits = min(s.max_tech_hits, s.tech_hits + 0.5 * time_mult)
                    if random.random() < 0.3:
                        game.hit_sparks.append([g.rect.centerx + random.randint(-20, 20), g.rect.centery + random.randint(-30, 30), random.uniform(-5, 5), random.uniform(-5, 5), random.randint(15, 25), INF_COLOR])
                    return

                cleave_dmg = 0.4 * time_mult
                if g.energy > 0:
                    rm = random.uniform(0.15, 0.35); md = cleave_dmg * (1.0 - rm); cleave_dmg *= rm
                    g.energy = max(0, g.energy - (md * 3.5) * g.cost_mult)
                g.hp -= cleave_dmg; s.tech_hits = min(s.max_tech_hits, s.tech_hits + 0.5 * time_mult)
                if g.vfx_ticker >= 10:
                    g.vfx_ticker -= 10
                    game.shake_timer = 5
                    game.blood_particles.append([g.rect.centerx, g.rect.centery, random.uniform(-5, 5), random.uniform(-5, 0), 30, random.randint(3, 6)])

            if grab_type == "amp_punch":
                maho_active = game.mahoraga and game.mahoraga.hp > 0
                if not maho_active:
                    s.amp_duration = max(s.amp_duration, 10)
                
                bd = 0.2 * time_mult
                if s.energy >= 2.0 * s.cost_mult * time_mult: s.energy -= 2.0 * s.cost_mult * time_mult; bd *= 1.6
                if g.energy > 0:
                    rm = random.uniform(0.15, 0.35); md = bd * (1.0 - rm); bd *= rm
                    g.energy = max(0, g.energy - (md * 3.5) * g.cost_mult)
                g.hp -= bd; s.tech_hits = min(s.max_tech_hits, s.tech_hits + bd)
                if g.vfx_ticker >= 8:
                    g.vfx_ticker -= 8
                    game.shake_timer = 4; sc = WHITE if random.random() < 0.5 else RED
                    for _ in range(5): game.hit_sparks.append([g.rect.centerx + random.randint(-15, 15), g.rect.centery + random.randint(-20, 20), random.uniform(-8, 8), random.uniform(-8, 8), random.randint(15, 30), sc])
            elif grab_type == "cleave":
                _cleave_tick()

        # ── Physics tick ─────────────────────────────────────────────────────
        g.update_physics(dt)
        if getattr(game.sukuna, "mahoraga_was_summoned", False):
            if game.mahoraga is None or game.mahoraga.hp <= 0: game.sukuna.mahoraga_is_dead = True
        game.sukuna.update_physics(dt)
        if game.mahoraga and game.mahoraga.hp > 0: game.mahoraga.update_physics(dt)
        
        if getattr(game.mahoraga, "is_cinematic_landing", False) and game.mahoraga and game.mahoraga.on_ground:
            game.mahoraga.is_cinematic_landing = False; game.shake_timer = 50
            dist_to_gojo = abs(g.rect.centerx - game.mahoraga.rect.centerx)
            if dist_to_gojo < 600:
                kb_dir = 1 if g.rect.centerx > game.mahoraga.rect.centerx else -1; g.rect.x += kb_dir * 150
            for _ in range(80):
                dx = game.mahoraga.rect.centerx + random.randint(-150, 150); dy = game.mahoraga.rect.bottom - random.randint(0, 40)
                c = random.randint(180, 240)
                game.hit_sparks.append([dx, dy, random.uniform(-25, 25), random.uniform(-15, -2), random.randint(20, 50), (c, c, c)])

        if game.sukuna.is_paralyzed and game.sukuna.rct_timer > 0 and getattr(game.sukuna, "mahoraga_lockout", 0) > 898:
            if pygame.time.get_ticks() - getattr(game, "last_uv_vow", 0) > 5000:
                game.maho_announcements.append({"text": "SUKUNA VOW: FORCED RCT IN UV! (MAHO 15s)", "timer": 150})
                game.last_uv_vow = pygame.time.get_ticks()

    return g.technique_burnout == 0 and g.infinity > 0 and g.energy >= 50


def update_domain_clash(game, keys, gojo_can_clash, dt):
    """Domain clash initiation (shrink timing) and 20-second clash phase."""
    g = game.gojo; s = game.sukuna
    time_mult = dt * 60.0

    if g.domain_active and s.domain_active and gojo_can_clash:
        clash_window = 30 
        if getattr(game, "clash_decision_timer", 0) <= 0 and not getattr(game, "clash_resolved", False):
            game.clash_decision_timer = clash_window; game.clash_failed = False
        if getattr(game, "clash_decision_timer", 0) > 0:
            game.clash_decision_timer -= time_mult
            is_sweet_spot = 1 <= game.clash_decision_timer <= 8 
            
            # --- AUTO-CAST CLASH POSE ON SWEET SPOT ---
            if is_sweet_spot and not getattr(g, "domain_shrunk", False) and not getattr(game, "clash_failed", False):
                # We can reuse the `domain_charge` flag to force fighter.py to grab the domain pose!
                g.domain_charge = 1  
                
            if keys[pygame.K_z] and keys[pygame.K_v] and not getattr(game, "clash_failed", False):
                if is_sweet_spot and not getattr(g, "domain_shrunk", False):
                    g.domain_shrunk = True; game.shake_timer = 20
                    g.domain_charge = 0 # Release pose lock
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100, "timer": 60, "text": "CRITICAL SHRINK!", "color": (0, 255, 255)})
                elif game.clash_decision_timer > 8:
                    game.clash_failed = True
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 50, "timer": 30, "text": "TOO EARLY!", "color": RED})
            if game.clash_decision_timer <= 0:
                game.clash_resolved = True
                g.domain_charge = 0 # Release pose lock safely if time ran out
                if getattr(g, "domain_shrunk", False) and not getattr(game, "clash_failed", False):
                    game.clash_active_flag = True; g.stance = 600; s.stance = 600
                    g.last_hp_clash = g.hp; g.last_ce_clash = g.energy
                    s.last_hp_clash = s.hp; s.last_ce_clash = s.energy
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100, "timer": 60, "text": "DOMAIN CLASH: BREAK STANCE!", "color": WHITE})
                    game.shake_timer = 20
                else:
                    game.clash_winner = "FAILED TO SHRINK DOMAIN!"; g.end_domain(); g.domain_shrunk = False
                    game.clash_msg_timer = 90; game.shake_timer = 30
                    game.popups.append({
                        "x": g.rect.centerx, 
                        "y": g.rect.centery - 100, 
                        "timer": 60, 
                        "text": "TIMING FAILED: DOMAIN COLLAPSED!", 
                        "color": RED
                    })
    else:
        game.clash_resolved = False; game.clash_decision_timer = 0; game.clash_failed = False

    if getattr(game, "clash_active_flag", False):
        g.domain_was_clashed = True
        s.domain_was_clashed = True
        maho_exists = game.mahoraga and game.mahoraga.hp > 0
        maho_adapted = maho_exists and game.mahoraga.adaptation["void"] <= 0

        if maho_adapted:
            game.clash_active_flag = False
            game.clash_winner = "MAHORAGA WINS!"
            game.clash_msg_timer = 120 
            game.shake_timer = 60 
            
            g.end_domain()
            s.end_domain()
            g.domain_shrunk = False
            
            game.popups.append({
                "x": game.mahoraga.rect.centerx, 
                "y": game.mahoraga.rect.centery - 120, 
                "timer": 90, 
                "text": "VOID ADAPTATION COMPLETE", 
                "color": (0, 255, 0)
            })
            return 

        g.domain_timer = max(g.domain_timer, 200); s.domain_timer = max(s.domain_timer, 200)
        
        purple_in_air = any(p.type == "purple_orb" for p in game.projectiles)
        purple_charging = g.purple_charge > 0
        purple_unlocked_or_close = g.purple_cd <= 0 and g.tech_hits >= (g.max_tech_hits * 0.80)
        is_purple_threat = purple_in_air or purple_charging or purple_unlocked_or_close

        incoming_threats = [p for p in game.projectiles if p.active and p.type in ["blue_orb", "red_orb"] and abs(p.pos.x - s.rect.centerx) < 300]
        
        dist_clash = abs(g.rect.centerx - s.rect.centerx)
        gojo_is_facing = (g.direction == 1 and g.rect.centerx < s.rect.centerx) or (g.direction == -1 and g.rect.centerx > s.rect.centerx)
        actual_punch_threat = g.punch_timer > 0 and dist_clash < 140 and gojo_is_facing
        is_greedy = s.hp > (s.max_hp * 0.65)
        
        maho_active = game.mahoraga and game.mahoraga.hp > 0
        
        if maho_active:
            s.amp_duration = 0
        elif (is_purple_threat or incoming_threats or getattr(g, "grab_timer", 0) > 0 or (actual_punch_threat and not is_greedy)) and s.energy > 5 and getattr(s, "tactical_eval_timer", 0) <= 0:
            s.amp_duration = max(s.amp_duration, 20)
        else:
            s.amp_duration = 0
        # Adaptation transfer logic
        if s.amp_duration <= 0:
            if maho_active:
                s.adapting_to = None
                game.mahoraga.adapting_to = "void"
                game.mahoraga.adaptation_points["void"] += 1.25 * time_mult
                # Note: Mahoraga's internal Fighter class now handles its own pulses
                m_turns = game.mahoraga.adaptation_points["void"] / 250.0
                game.mahoraga.adaptation["void"] = max(0, 1.0 - min(1.0, m_turns / 14.0))
            else:
                s.adapting_to = "void"
                # Updated to 1000 to match the 4-turn visual click for Megumi's wheel
                old_s_v_turns = int(s.adaptation_points["void"] // 1000)
                s.adaptation_points["void"] += 1.25 * time_mult
                if int(s.adaptation_points["void"] // 1000) > old_s_v_turns:
                    s.adapt_pulse_timer = 30
                s_turns = s.adaptation_points["void"] / 250.0
                s.adaptation["void"] = max(0, 1.0 - min(1.0, s_turns / 14.0))
        else:
            s.adapting_to = None
            if maho_active: game.mahoraga.adapting_to = None

        for fighter in [g, s]:
            hp_diff = getattr(fighter, "last_hp_clash", fighter.hp) - fighter.hp
            vow_ignore = getattr(fighter, "vow_hp_to_ignore", 0)
            
            hp_lost = max(0, hp_diff - vow_ignore)
            fighter.vow_hp_to_ignore = 0 
            
            ce_lost = getattr(fighter, "last_ce_clash", fighter.energy) - fighter.energy
            if hp_lost > 0:
                raw = hp_lost
                if ce_lost > 0:
                    raw += ce_lost / max(0.1, fighter.cost_mult * 2.0)
                fighter.stance = max(0, getattr(fighter, "stance", 700) - raw)
            fighter.last_hp_clash = fighter.hp
            fighter.last_ce_clash = fighter.energy

        if s.stance <= 0:
            game.clash_active_flag = False; game.clash_winner = "GOJO WINS CLASH!"; s.end_domain()
            g.domain_shrunk = False; g.domain_timer = 400; game.clash_msg_timer = 90; game.shake_timer = 40
            game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 100, "timer": 60, "text": "SHRINE COLLAPSED!", "color": BLUE})
        elif g.stance <= 0:
            game.clash_active_flag = False; game.clash_winner = "SUKUNA WINS CLASH!"; g.end_domain(); g.domain_shrunk = False
            g.technique_burnout = 1200; s.domain_timer = 400; game.clash_msg_timer = 90; game.shake_timer = 40
            game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100, "timer": 60, "text": "UV COLLAPSED!", "color": RED})