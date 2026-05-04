import pygame, random, math 
from settings import *
from projectile import Projectile


def update_gojo_controls(game, keys, mouse_click, target, dt):
    """All Gojo player controls. Returns: punching (bool)."""
    g = game.gojo
    s = game.sukuna
    dist = abs(g.rect.centerx - s.rect.centerx)
    time_mult = dt * 60.0

    # ── Simple Domain (Right-Click Hold) ──────────────────
    in_clash = getattr(game, "clash_phase_timer", 0) > 0
    can_activate_sd = mouse_click[2]
    
    if can_activate_sd and g.energy > 5 * g.cost_mult and (not g.domain_active or in_clash) and g.sd_broken_timer <= 0:
        if not getattr(g, "sd_was_active", False):
            g.energy -= 25.0 * g.cost_mult
        g.simple_domain_active = True
        g.sd_was_active = True
        if g.domain_charge <= 0:
            g.energy -= 1.5 * g.cost_mult * time_mult
    else:
        g.simple_domain_active = False
        g.sd_was_active = False

    # ── Domain Expansion (V) ─────────────────────────────────────────────────
    if keys[pygame.K_v] and g.domain_cd == 0 and g.technique_burnout == 0 \
            and g.domain_charge <= 0 and not g.domain_active and g.grab_timer <= 0 \
            and getattr(g, "stun_timer", 0) <= 0 and getattr(g, "punch_timer", 0) <= 0 and not getattr(g, "is_blocking", False):
        if g.energy >= 190 * g.cost_mult:
            g.domain_charge = 60
            g.energy -= 190 * g.cost_mult
        else:
            if g.attack_cooldown == 0:
                game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100,
                                    "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                g.attack_cooldown = 20

    is_actually_burned_out = (g.domain_uses >= 5 and g.technique_burnout > 0)

    # ── Point-Blank Blue (E + W) ─────────────────────────────────────────────
    if (keys[pygame.K_e] and keys[pygame.K_w] and game.pb_blue_ready
            and g.energy >= 60 * g.cost_mult and g.blue_cd <= 0
            and g.grab_timer <= 0 and not is_actually_burned_out 
            and g.domain_charge <= 0 and g.purple_charge <= 0):
        game.pb_blue_ready = False
        g.energy -= 60 * g.cost_mult
        g.blue_cd = 300
        s.rect.centerx = g.rect.centerx + (50 * g.direction)
        pb_blue_dmg = 30.0
        if s.amp_duration > 0: pb_blue_dmg *= 0.2
        if s.energy > 0:
            reduction_mult = random.uniform(0.15, 0.35)
            mitigated_dmg = pb_blue_dmg * (1.0 - reduction_mult)
            pb_blue_dmg *= reduction_mult
            s.energy = max(0, s.energy - (mitigated_dmg * 2.0) * s.cost_mult)
        s.hp -= pb_blue_dmg
        s.memory.record("pb_blue", dist, hit=True)
        s.grab_timer = 180
        setattr(s, "grab_type", "gojo_beatdown")
        s.fuga_charge = 0; s.domain_charge = 0; s.amp_duration = 0; s.attack_cooldown = 30
        g.tech_hits = min(g.max_tech_hits, g.tech_hits + 25)
        game.shake_timer = 10
        game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 80,
                            "timer": 45, "text": "WARPED!", "color": BLUE})
        for _ in range(20):
            game.hit_sparks.append([s.rect.centerx, s.rect.centery,
                                     random.uniform(-15, 15), random.uniform(-15, 15),
                                     random.randint(20, 40), BLUE])
        game.gojo_combo_buffer.clear()

    # ── Point-Blank Red (E + S) ──────────────────────────────────────────────
    elif (keys[pygame.K_e] and keys[pygame.K_s] and game.pb_red_ready
          and g.energy >= 100 * g.cost_mult and g.red_cd <= 0
          and (g.grab_timer > 0 or s.grab_timer > 0) 
          and g.domain_charge <= 0 and g.purple_charge <= 0):
        game.pb_red_ready = False
        g.grab_timer = 0; s.grab_timer = 0
        if is_actually_burned_out:
            g.technique_burnout = 0
            g.energy -= 150 * g.cost_mult
            game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 120,
                                "timer": 60, "text": "BRAIN RCT REFRESH!", "color": HEAL_GREEN})
        g.energy -= 100 * g.cost_mult
        g.red_cd = 240
        g.tech_hits = min(g.max_tech_hits, g.tech_hits + 25)
        s.domain_charge = 0
        pb_red_dmg = 150.0
        if s.amp_duration > 0: pb_red_dmg *= 0.3
        if s.energy > 0:
            reduction_mult = random.uniform(0.15, 0.35)
            mitigated_dmg = pb_red_dmg * (1.0 - reduction_mult)
            pb_red_dmg *= reduction_mult
            s.energy = max(0, s.energy - (mitigated_dmg * 2.0) * s.cost_mult)
        s.hp -= pb_red_dmg
        s.memory.record("red", dist, hit=True)
        s.attack_cooldown = 45

        if s.rect.centerx > g.rect.centerx:
            s.rect.right = WORLD_WIDTH              
        else:
            s.rect.left = 0   

        game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 80,
                            "timer": 45, "text": "REPELLED!", "color": RED})
        mid_x = (g.rect.centerx + s.rect.centerx) // 2
        mid_y = (g.rect.centery + s.rect.centery) // 2
        red_burst = Projectile(mid_x, mid_y, mid_x, mid_y, 0, RED, size_mult=3.0, type="red_orb")
        red_burst.lifetime = 15
        game.projectiles.append(red_burst)
        game.shake_timer = 30
        game.hit_stop = 8
        for p in game.projectiles:
            if getattr(p, "is_grab_cleave", False): p.active = False
        game.gojo_combo_buffer.clear()

    # ── Movement + Standard Combat ───────────────────────────────────────────
    punching = False
    
    if keys[pygame.K_f] and g.stamina > 0 and g.grab_timer <= 0 and not g.is_paralyzed and g.domain_charge <= 0:
        g.is_blocking = True
        g.stamina = max(0, g.stamina - 1.5 * time_mult)
    else:
        g.is_blocking = False

    if not g.is_paralyzed and g.grab_timer <= 0 and g.domain_charge <= 0 and not g.is_blocking:
        if keys[pygame.K_a]: g.rect.x -= 20 * time_mult; g.direction = -1
        if keys[pygame.K_d]: g.rect.x += 20 * time_mult; g.direction = 1

        if mouse_click[0] and not getattr(g, "mouse_held", False) and g.attack_cooldown <= 0:
            punching = True
            g.punch_timer = 20
            g.punch_count += 1
            if abs(g.rect.centerx - target.rect.centerx) < 130:
                dmg = 6.5 * (target.adaptation["punch"] if target.name == "Mahoraga" else 1.0)
                imbue_cost = 2.0 * g.cost_mult
                if g.energy >= imbue_cost:
                    g.energy -= imbue_cost; dmg *= 1.6
                
                bf_chance = random.uniform(0.05, 0.10) if g.potential_timer > 0 else random.uniform(0.005, 0.01)
                is_black_flash = random.random() < bf_chance
                
                if is_black_flash:
                    game.bf_zoom_timer = 45
                    game.bf_zoom_pos = (target.rect.centerx, target.rect.centery)
                    
                    dmg *= math.pow(2.5, 2.5)
                    g.black_flash_timer = 20; g.potential_timer = 600
                    game.shake_timer = 15; g.energy = g.max_energy
                    game.hit_stop = 30
                    game.bf_words.append({"x": target.rect.centerx, "y": target.rect.centery - 60, "timer": 45})
                
                if not target.is_dodging:
                    is_blocked = getattr(target, "is_blocking", False)
                    is_tanking = False
                    
                    if not is_black_flash:
                        if target.name == "Sukuna" and target.energy > 0:
                            reduction_mult = random.uniform(0.15, 0.35)
                            mitigated_dmg = dmg * (1.0 - reduction_mult)
                            dmg *= reduction_mult
                            target.energy = max(0, target.energy - (mitigated_dmg * 2.0) * target.cost_mult)
                        elif target.name == "Mahoraga":
                            dmg *= random.uniform(0.6, 0.85)
                            
                        if not is_blocked:
                            if target.name == "Sukuna" and target.hp > target.max_hp * 0.7:
                                is_tanking = True
                            elif target.name == "Mahoraga" and target.adaptation["punch"] < 0.6:
                                is_tanking = True
                    
                    if is_blocked:
                        if target.stamina < 10:
                            target.stamina = 0
                            target.is_blocking = False
                            is_blocked = False
                            target.hp -= dmg
                            target.stun_timer = 40
                            game.popups.append({"x": target.rect.centerx, "y": target.rect.centery - 60, "timer": 45, "text": "GUARD BREAK!", "color": (255, 50, 50)})
                        else:
                            dmg *= 0.2
                            target.stamina -= 10
                            target.hp -= dmg
                            game.popups.append({"x": target.rect.centerx, "y": target.rect.centery - 60, "timer": 20, "text": "BLOCKED", "color": (150, 150, 255)})
                    else:
                        target.hp -= dmg
                        if not is_tanking and not is_black_flash:
                            target.stun_timer = 15

                    if target.name == "Sukuna": target.memory.record("punch", dist, hit=True)
                    spark_color = (150, 150, 255) if is_blocked else ((255, 0, 0) if g.black_flash_timer > 0 else WHITE)
                    for _ in range(12):
                        game.hit_sparks.append([target.rect.centerx + random.randint(-15, 15),
                                                 target.rect.centery - random.randint(10, 30),
                                                 random.uniform(-12, 12), random.uniform(-12, 12),
                                                 random.randint(15, 30), spark_color])
                    
                    kb_dir = 1 if target.rect.centerx > g.rect.centerx else -1
                    kb_dist = 1200 if is_black_flash else 35
                    target.rect.x += kb_dir * kb_dist
                    
                    if target.name == "Mahoraga" and game.sukuna.amp_duration <= 0:
                        old_p_turns = int(target.adaptation_points["punch"] // 1000)
                        target.trigger_adaptation("punch", 15.0)
                        if int(target.adaptation_points["punch"] // 1000) > old_p_turns:
                            target.adapt_pulse_timer = 30
                        turns = target.adaptation_points["punch"] / 250.0
                        target.adaptation["punch"] = max(0, 1.0 - min(1.0, turns / 9.0))
            g.attack_cooldown = 12

        # RCT Heal (Q)
        if keys[pygame.K_q] and g.energy > 5 * g.cost_mult:
            g.hp = min(g.max_hp, g.hp + 1.5 * time_mult)
            g.energy -= 2 * g.cost_mult * time_mult
            g.rct_timer = 5

        is_actually_burned_out = (g.domain_uses >= 5 and g.technique_burnout > 0)

        # Lapse Blue (W)
        if keys[pygame.K_w] and g.blue_cd <= 0 and g.purple_charge <= 0:
            if g.energy >= 20 * g.cost_mult:
                if not is_actually_burned_out:
                    game.projectiles.append(Projectile(g.rect.centerx, g.rect.centery,
                                                        target.rect.centerx, target.rect.centery,
                                                        18, BLUE, size_mult=2.5, type="blue_orb"))
                    g.energy -= 20 * g.cost_mult; g.blue_cd = 60
            else:
                if g.attack_cooldown == 0:
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100,
                                        "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                    g.attack_cooldown = 20

        # Reversal Red (S)
        if keys[pygame.K_s] and g.red_cd <= 0 and g.purple_charge <= 0:
            if g.energy >= 40 * g.cost_mult:
                if not is_actually_burned_out:
                    game.projectiles.append(Projectile(g.rect.centerx, g.rect.centery,
                                                        target.rect.centerx, target.rect.centery,
                                                        30, RED, size_mult=1.8, type="red_orb"))
                    g.energy -= 40 * g.cost_mult; g.red_cd = 120
            else:
                if g.attack_cooldown == 0:
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100,
                                        "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                    g.attack_cooldown = 20

        is_beatdown_active = s.grab_timer > 0 and getattr(s, "grab_type", "") == "gojo_beatdown"

        # Hollow Purple (R)
        if keys[pygame.K_r] and g.purple_cd <= 0 and g.purple_charge <= 0 and not is_beatdown_active:
            if g.energy >= 195 * g.cost_mult:
                if not is_actually_burned_out and g.tech_hits >= g.max_tech_hits:
                    g.purple_charge = 120
            else:
                if g.attack_cooldown == 0:
                    game.popups.append({"x": g.rect.centerx, "y": g.rect.centery - 100,
                                        "timer": 30, "text": "NOT ENOUGH CE!", "color": RED})
                    g.attack_cooldown = 20

    if g.purple_charge > 0:
        g.purple_charge -= time_mult
        if g.purple_charge <= 0:
            g.purple_charge = 0
            game.projectiles.append(Projectile(g.rect.centerx, g.rect.centery,
                                                target.rect.centerx, target.rect.centery,
                                                20, PURPLE, size_mult=3.5, type="purple_orb"))
            g.energy = max(0, g.energy - (195 * g.cost_mult))
            g.purple_cd = 720; g.tech_hits = 0

    # ── Domain Charge Countdown ──────────────────────────────────────────────
    if g.domain_charge > 0:
        g.domain_charge -= time_mult
        if g.domain_charge <= 0:
            g.domain_charge = 0
            g.domain_active = True; g.domain_timer = 900 
            g.domain_start_ticks = pygame.time.get_ticks()
            g.domain_was_clashed = False
            g.domain_cd = 3000; g.infinity = g.max_infinity
            game.shake_timer = 30

    g.mouse_held = mouse_click[0]
    return punching