import pygame, random, math # type: ignore
from settings import *
from projectile import Projectile

def update_sukuna_ai(game, dt):
    """Full Sukuna AI. Returns: (dist, fuga_priority, gojo_has_inf)."""
    g = game.gojo
    s = game.sukuna
    time_mult = dt * 60.0

    dist = abs(s.rect.centerx - g.rect.centerx)
    fuga_priority = (s.tech_hits >= s.max_tech_hits and s.fuga_cd == 0
                     and s.energy >= 195 * s.cost_mult and not g.domain_active
                     and g.domain_cd > 600) or s.fuga_charge > 0
    gojo_has_inf = g.infinity > 0 and g.technique_burnout == 0

    # ── Domain Cast Decision ─────────────────────────────────────────────────
    if (s.energy >= 200 * s.cost_mult and s.domain_cd == 0 and s.technique_burnout == 0
            and s.domain_charge == 0 and not s.domain_active and not s.is_paralyzed
            and g.grab_timer <= 0 and s.attack_cooldown <= 0 and game.mahoraga_summon_timer <= 0):
        should_cast_domain = False
        sukuna_est_power = s.hp + s.energy
        gojo_est_power = g.hp + g.energy
        power_advantage = sukuna_est_power >= gojo_est_power
        sukuna_domains_left = 5 - s.domain_uses
        gojo_domains_left = 5 - g.domain_uses
        domain_advantage = sukuna_domains_left >= gojo_domains_left

        if g.domain_active:
            should_cast_domain = True
        elif g.domain_charge > 0:
            can_interrupt = False
            if s.world_slash_unlocked and s.world_slash_cd <= 0 and getattr(s, "world_slash_charge", 0) <= 0 and s.energy >= 80 * s.cost_mult:
                can_interrupt = True
            elif not gojo_has_inf and s.dismantle_cd <= 0 and s.energy >= 10 * s.cost_mult:
                can_interrupt = True
            elif dist <= 150 and s.energy >= 15 * s.cost_mult:
                can_interrupt = True
            frames_unprotected = max(0, 400 - s.max_sd_hits) if s.sd_broken_timer <= 0 else 400
            can_survive_uv = not (s.hp <= frames_unprotected * 1.5 or s.energy < 400 * 1.0)
            if not can_interrupt:
                should_cast_domain = False if (not power_advantage and can_survive_uv and s.sd_broken_timer <= 0) else True
            elif can_interrupt and not can_survive_uv:
                should_cast_domain = True
        else:
            gojo_is_vulnerable = g.technique_burnout > 0 or g.domain_cd > 0 or g.energy < 150 * g.cost_mult
            gojo_is_hoarding = gojo_domains_left > sukuna_domains_left
            if gojo_is_vulnerable: should_cast_domain = True
            elif gojo_is_hoarding: should_cast_domain = False
            elif domain_advantage and power_advantage and s.hp > s.max_hp * 0.5:
                if random.random() < 0.01: should_cast_domain = True
            elif s.hp < s.max_hp * 0.3 and random.random() < 0.005:
                should_cast_domain = True

        if should_cast_domain:
            s.domain_charge = 60
            s.energy -= 200 * s.cost_mult

    # ── Simple Domain While Trapped in UV ───────────────────────────────────
    elif g.domain_active and not s.domain_active:
        if s.energy > 5 * s.cost_mult and s.sd_broken_timer <= 0:
            if not getattr(s, "sd_was_active", False):
                s.energy -= 25.0 * s.cost_mult; s.sd_hits = 0
            s.simple_domain_active = True; s.sd_was_active = True
            s.energy -= 1.0 * s.cost_mult * time_mult
        else:
            s.simple_domain_active = False; s.sd_was_active = False
    else:
        s.simple_domain_active = False; s.sd_was_active = False

    # ── Main AI: Movement & Combat ───────────────────────────────────────────
    if not s.is_paralyzed and s.grab_timer <= 0 and s.domain_charge == 0:
        is_amp = s.amp_duration > 0
        purple_flying = any(p.type == "purple_orb" for p in game.projectiles)
        purple_imminent = g.purple_cd == 0 and g.tech_hits >= g.max_tech_hits
        is_purple_threat = g.purple_charge > 0 or purple_flying or purple_imminent

        # Purple / Domain charge threat response
        if g.domain_charge > 0 or is_purple_threat:
            can_tank_purple = not (is_purple_threat and (s.hp <= 150 or s.energy <= 300 * s.cost_mult))
            if is_purple_threat and not can_tank_purple:
                run_dir = -1 if s.rect.x < g.rect.x else 1
                if (s.rect.left < 150 and run_dir == -1) or (s.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                    run_dir *= -1
                    if s.on_ground: s.jump()
                s.direction = run_dir; s.rect.x += 28 * run_dir * time_mult
                if s.dodge_cd <= 0 and s.stamina >= 20: s.dodge(); s.dodge_cd = 15
                vow_cost = 2.4 * s.cost_mult
                if s.energy > vow_cost:
                    s.energy -= vow_cost; s.hp = min(s.max_hp, s.hp + 2.0)
                    s.amp_duration = max(s.amp_duration, 60); is_amp = True
                    if pygame.time.get_ticks() - getattr(game, "last_purple_vow", 0) > 5000:
                        game.maho_announcements.append({"text": "SUKUNA VOW: CE BURNED TO TANK PURPLE!", "timer": 120})
                        game.last_purple_vow = pygame.time.get_ticks()
            else:
                s.direction = 1 if s.rect.x < g.rect.x else -1
                if s.world_slash_unlocked and s.world_slash_cd <= 0 and getattr(s, "world_slash_charge", 0) <= 0 and s.energy >= 80 * s.cost_mult:
                    s.world_slash_charge = 120
                elif dist > 100:
                    s.rect.x += 28 * s.direction * time_mult
                    if s.dodge_cd <= 0 and s.stamina >= 20: s.dodge(); s.dodge_cd = 20

        # Dodge incoming orbs
        incoming_orbs = [p for p in game.projectiles if p.type in ["blue_orb", "red_orb", "purple_orb"] and abs(p.pos.x - s.rect.centerx) < 400]
        if incoming_orbs:
            closest_orb = min(incoming_orbs, key=lambda p: abs(p.pos.x - s.rect.centerx))
            if s.on_ground and abs(closest_orb.pos.x - s.rect.centerx) < 180: s.jump()
            if s.dodge_cd <= 0 and s.stamina >= 20:
                if s.rect.centerx < 100: s.direction = 1
                elif s.rect.centerx > WORLD_WIDTH - 100: s.direction = -1
                else: s.direction = 1 if s.rect.centerx > closest_orb.pos.x else -1
                s.dodge(); s.dodge_cd = 40

        if is_amp and dist > 150 and (s.dismantle_cd == 0 or s.cleave_cd == 0) and not is_purple_threat:
            s.amp_duration = 0; is_amp = False

        in_clash = getattr(game, "clash_phase_timer", 0) > 0
        is_greedy = s.hp > (s.max_hp * 0.65)
        prioritize_adaptation = in_clash and is_greedy

        if dist <= 150 and s.energy > 30 * s.cost_mult and not fuga_priority and not s.ce_exhausted and g.grab_timer <= 0 and not prioritize_adaptation:
            if g.infinity > 0:
                s.amp_duration = max(s.amp_duration, 60); is_amp = True
            elif s.amp_cd == 0 and s.amp_duration == 0:
                if s.grab_cd > 0 or g.domain_active:
                    s.amp_duration = 600; is_amp = True

        if is_amp: s.energy -= 0.25 * s.cost_mult * time_mult

        rush_distance = 40 if g.domain_active else 110
        is_draining_ce = s.energy < (s.max_energy * 0.65)
        if getattr(s, "tactical_eval_timer", 0) > 0: s.tactical_eval_timer -= time_mult
        is_tactical_eval = getattr(s, "tactical_eval_timer", 0) > 0

        # CE Vow / Flesh vow
        if is_draining_ce and not s.ce_exhausted and g.grab_timer <= 0:
            vow_hp_cost = s.max_hp * 0.80
            vow_ce_gain = s.max_energy * 0.40
            can_afford = s.hp > (vow_hp_cost + 20)
            desperate = s.energy < (s.max_energy * 0.40)
            in_clash = getattr(game, "clash_phase_timer", 0) > 0
            if can_afford and desperate and not in_clash:
                s.hp -= vow_hp_cost
                s.energy = min(s.max_energy, s.energy + vow_ce_gain)
                game.shake_timer = 20; s.amp_duration = 0; s.amp_cd = 600
                s.tactical_eval_timer = 600; is_amp = False; is_tactical_eval = True
                game.maho_announcements.append({"text": "SUKUNA VOW: 80% HP FOR CE! (DA LOST 10s)", "timer": 120})
                for _ in range(30):
                    bx, by = s.rect.center
                    game.blood_particles.append([bx, by, random.uniform(-8, 8), random.uniform(-10, -2), 50, random.randint(4, 7)])
            elif dist < 180 and s.dodge_cd <= 0 and s.stamina >= 20 and not g.domain_active:
                s.direction = 1 if s.rect.x > g.rect.x else -1
                s.dodge(); s.dodge_cd = 25

        needs_healing = s.hp < (s.max_hp * 0.4) and s.energy > 50 and not s.ce_exhausted
        needs_energy = s.energy < (s.max_energy * 0.3)
        retreating = (needs_healing or needs_energy or is_tactical_eval) and not g.domain_active

        if retreating and g.grab_timer <= 0:
            if is_tactical_eval:
                can_survive_counter = s.hp > (s.max_hp * 0.25)
                if s.energy >= 200 * s.cost_mult and s.domain_cd == 0 and s.technique_burnout == 0 and not s.domain_active:
                    s.domain_charge = 60; s.energy -= 200 * s.cost_mult
                elif s.tech_hits >= s.max_tech_hits and s.fuga_cd == 0 and s.energy >= 195 * s.cost_mult and s.technique_burnout == 0 and not g.domain_active and not s.is_paralyzed:
                    if s.hp > (s.max_hp * 0.50 + 40): s.fuga_charge = 120
                elif dist > 250 and s.dismantle_cd <= 0 and s.energy >= 30 * s.cost_mult and s.technique_burnout == 0 and can_survive_counter:
                    s.slash_count = 3; s.slash_type = "dismantle"
                    s.energy -= 10 * s.cost_mult; s.dismantle_cd = 40
                    s.direction = -1 if s.rect.x > g.rect.x else 1

            if needs_healing and s.energy > 1000 * s.cost_mult:
                s.energy -= 4.0 * s.cost_mult * time_mult; s.hp = min(s.max_hp, s.hp + 5.0 * time_mult); s.rct_timer = 5

            if not needs_energy and not is_tactical_eval and s.energy >= 200 * s.cost_mult and s.domain_cd == 0 and s.technique_burnout == 0 and s.domain_charge == 0 and not s.domain_active and s.attack_cooldown <= 0:
                if (5 - g.domain_uses) <= (5 - s.domain_uses):
                    s.domain_charge = 60; s.energy -= 200 * s.cost_mult

            speed = 18 if not is_tactical_eval else 24
            if dist < 250: run_dir = 1 if s.rect.x > g.rect.x else -1
            elif dist > 550: run_dir = -1 if s.rect.x > g.rect.x else 1
            else:
                if getattr(s, "dash_dance_timer", 0) <= 0:
                    s.dash_dance_dir = random.choice([-1, 1]); s.dash_dance_timer = random.randint(15, 35)
                else: s.dash_dance_timer -= time_mult
                run_dir = getattr(s, "dash_dance_dir", 1)

            if (s.rect.left < 150 and run_dir == -1) or (s.rect.right > WORLD_WIDTH - 150 and run_dir == 1):
                run_dir *= -1
                if s.on_ground: s.jump()
            else:
                jump_chance = 0.08 if needs_energy else 0.04
                if s.on_ground and random.random() < jump_chance: s.jump()

            s.rect.x += speed * run_dir * time_mult
            if s.dodge_cd <= 0 and s.stamina >= 20 and not s.stamina_exhausted:
                s.direction = (-1 if s.rect.x > g.rect.x else 1) if (dist < 350 and random.random() < 0.3) else run_dir
                s.dodge(); s.dodge_cd = 20 if needs_energy or is_tactical_eval else 25
            if not is_tactical_eval and s.dismantle_cd <= 0 and s.energy >= 10 * s.cost_mult and random.random() < 0.04 and s.technique_burnout == 0 and not gojo_has_inf:
                s.slash_count = 1; s.slash_type = "dismantle"
                s.energy -= 10 * s.cost_mult; s.dismantle_cd = 80; s.direction = -run_dir
            if not is_tactical_eval and s.energy > 15 * s.cost_mult and s.amp_cd <= 0:
                s.amp_duration = max(s.amp_duration, 60); is_amp = True

        elif g.domain_active and not s.domain_active and g.rect.bottom < s.rect.top - 20 and s.on_ground:
            s.jump()
        elif dist > rush_distance or g.grab_timer > 0:
            speed = 35 if (s.ce_exhausted or g.domain_active) else (28 if (s.cleave_cd <= 0 and dist < 600 and g.grab_timer <= 0) else 9)
            if g.grab_timer > 0:
                s.rect.x += speed * s.direction * time_mult
                if random.random() < 0.02: s.direction *= -1
            else:
                s.rect.x += (-speed if s.rect.x > g.rect.x else speed) * time_mult
            if g.domain_active and not s.domain_active:
                if s.dodge_cd <= 0 and s.stamina >= 20 and not s.stamina_exhausted and not incoming_orbs:
                    s.direction = -1 if s.rect.x > g.rect.x else 1; s.dodge(); s.dodge_cd = 25
            else:
                if s.dodge_cd == 0 and random.random() < 0.04 and g.grab_timer <= 0:
                    s.direction = -1 if s.rect.x > g.rect.x else 1; s.dodge()
                    if s.on_ground: s.jump()
                    s.dodge_cd = 70
                elif s.on_ground and random.random() < 0.02: s.jump()

        # Fuga firing decision
        if s.energy >= 195 * s.cost_mult and s.fuga_cd == 0 and s.fuga_charge == 0 and s.technique_burnout == 0 and not g.domain_active and g.domain_cd > 600:
            if s.tech_hits >= s.max_tech_hits:
                vow_hp_cost = s.max_hp * 0.50
                can_survive_vow = s.hp > (vow_hp_cost + 20)
                gojo_is_vulnerable = g.infinity <= 0 or g.technique_burnout > 0 or g.ce_exhausted
                is_guaranteed_kill = g.hp < 150 and gojo_is_vulnerable
                gojo_is_tanky = g.hp > g.max_hp * 0.7 and g.energy > g.max_energy * 0.5 and g.infinity > 0
                if can_survive_vow:
                    if is_guaranteed_kill or (gojo_is_vulnerable and not gojo_is_tanky) or s.hp > s.max_hp * 0.85:
                        s.fuga_charge = 120

        # World Slash charge countdown
        if getattr(s, "world_slash_charge", 0) > 0:
            s.world_slash_charge -= time_mult
            if s.world_slash_charge <= 0:
                s.world_slash_charge = 0
                game.projectiles.append(Projectile(s.rect.centerx, s.rect.centery, g.rect.centerx, g.rect.centery, 55, BLACK, size_mult=12.0, type="world_slash"))
                s.energy = max(0, s.energy - 80 * s.cost_mult); s.world_slash_cd = 1800; game.shake_timer = 40

        # Fuga charge countdown + fire
        if s.fuga_charge > 0:
            if s.is_paralyzed or g.domain_active: s.fuga_charge = 0
            else:
                s.fuga_charge -= time_mult
                if s.fuga_charge <= 0:
                    s.fuga_charge = 0
                    game.projectiles.append(Projectile(s.rect.centerx, s.rect.centery, g.rect.centerx, g.rect.centery, 28, (255, 100, 0), size_mult=5.8, type="fuga_arrow"))
                    s.energy = max(0, s.energy - 195 * s.cost_mult)
                    s.hp -= s.max_hp * 0.50; game.shake_timer = 35
                    for _ in range(30):
                        bx, by = s.rect.center
                        game.blood_particles.append([bx, by, random.uniform(-8, 8), random.uniform(-10, 0), 50, random.randint(4, 7)])
                    game.maho_announcements.append({"text": "SUKUNA VOW: 50% HP OFFERED FOR FUGA!", "timer": 120})
                    s.fuga_cd = 720; s.tech_hits = 0

        # Grab / Cleave initiation
        if s.technique_burnout == 0 and not fuga_priority and g.grab_timer <= 0:
            if s.rect.colliderect(g.rect) and s.grab_cd <= 0:
                is_burned_out = (g.domain_uses >= 5 and g.technique_burnout > 0)
                has_infinity = g.infinity > 0 and g.energy > 0 and not is_burned_out
                if has_infinity:
                    is_da_locked_out = getattr(s, "tactical_eval_timer", 0) > 0
                    if s.energy >= 15 * s.cost_mult and not is_da_locked_out:
                        s.amp_duration = max(s.amp_duration, 300); is_amp = True
                        g.grab_timer = 300; g.grab_type = "amp_punch"; g.purple_charge = 0; g.domain_charge = 0
                        game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 80, "timer": 45, "text": "DOM AMP BEATDOWN!", "color": (255, 255, 0)})
                        g.rect.centerx = s.rect.centerx + (40 * s.direction); g.rect.centery = s.rect.centery
                        s.energy -= 15 * s.cost_mult; s.grab_cd = 480
                else:
                    if s.energy >= 30 * s.cost_mult and s.cleave_cd <= 0:
                        s.amp_duration = 0; is_amp = False
                        g.grab_timer = 300; g.grab_type = "cleave"; g.purple_charge = 0; g.domain_charge = 0
                        game.popups.append({"x": s.rect.centerx, "y": s.rect.centery - 80, "timer": 45, "text": "CLEAVE!", "color": RED})
                        g.rect.centerx = s.rect.centerx + (40 * s.direction); g.rect.centery = s.rect.centery
                        p = Projectile(g.rect.centerx, g.rect.centery, g.rect.centerx, g.rect.centery, 1, RED, size_mult=4.0, type="cleave")
                        p.vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 0.1
                        p.lifetime = 300; p.is_grab_cleave = True; game.projectiles.append(p)
                        s.energy -= 15 * s.cost_mult; s.cleave_cd = 600
                        if g.infinity > 0 and g.energy > 0 and g.technique_burnout == 0:
                            g.energy = max(0, g.energy - 0.5 * g.cost_mult)
                            s.tech_hits = min(s.max_tech_hits, s.tech_hits + 20)
                        else:
                            g.hp -= 120.0; s.tech_hits = min(s.max_tech_hits, s.tech_hits + 20); game.shake_timer = 40
                            for _ in range(50):
                                bx, by = g.rect.center
                                game.blood_particles.append([bx, by, random.uniform(-10, 10), random.uniform(-10, 10), 60, random.randint(4, 8)])
                        s.energy -= 15 * s.cost_mult; s.cleave_cd = 600; s.grab_cd = 600

        # Dismantle / WS offense when DA is off
        if not is_amp and s.energy > 40 * s.cost_mult and not fuga_priority and s.technique_burnout == 0 and g.grab_timer <= 0:
            if s.world_slash_unlocked and s.energy > 80 * s.cost_mult and s.world_slash_cd <= 0 and getattr(s, "world_slash_charge", 0) <= 0:
                s.world_slash_charge = 120
            elif dist > 180 and s.dismantle_cd == 0 and not gojo_has_inf:
                s.slash_count = 6; s.slash_type = "dismantle"
                s.energy -= 10 * s.cost_mult; s.dismantle_cd = 40
            elif dist > 180 and gojo_has_inf and s.dodge_cd <= 0 and s.stamina >= 20:
                s.direction = 1 if s.rect.x < g.rect.x else -1; s.dodge(); s.dodge_cd = 40

        # Fire slashes
        if s.slash_count > 0 and s.slash_type != "cleave":
            if s.slash_delay <= 0:
                if s.slash_type == "world_slash":
                    s.slash_count -= 1
                else:
                    offset_y = (s.slash_count - 2.5) * 45
                    size = 2.5 if s.slash_type == "dismantle" else 4.2
                    game.projectiles.append(Projectile(s.rect.centerx, s.rect.centery + offset_y, g.rect.centerx, g.rect.centery, 110, RED, size_mult=size, type=s.slash_type))
                    s.slash_count -= 1; s.slash_delay = 2
            else: s.slash_delay -= time_mult

        # Melee punch
        if dist < 120 and s.attack_cooldown <= 90 and not fuga_priority:
            if s.attack_cooldown == 0:
                s.punch_timer = 20; s.punch_count += 1; melee_dmg = 7.5
                imbue_cost = 2.0 * s.cost_mult
                if s.energy >= imbue_cost: s.energy -= imbue_cost; melee_dmg *= 1.6
                bf_chance = random.uniform(0.05, 0.10) if s.potential_timer > 0 else random.uniform(0.0005, 0.001)
                if random.random() < bf_chance:
                    if s.potential_timer <= 0: game.bf_zoom_timer = 45; game.bf_zoom_pos = (g.rect.centerx, g.rect.centery)
                    melee_dmg *= math.pow(2.5, 2.5); s.black_flash_timer = 20; s.potential_timer = 600
                    game.shake_timer = 15; s.energy = s.max_energy
                    game.bf_words.append({"x": g.rect.centerx, "y": g.rect.centery - 60, "timer": 45})
                if is_amp:
                    if not g.is_dodging:
                        actual_dmg = melee_dmg
                        if g.energy > 0:
                            rm = random.uniform(0.15, 0.35); md = actual_dmg * (1.0 - rm); actual_dmg *= rm
                            g.energy = max(0, g.energy - (md * 3.5) * g.cost_mult)
                        g.hp -= actual_dmg
                        sc = (255, 0, 0) if s.black_flash_timer > 0 else RED
                        for _ in range(12): game.hit_sparks.append([g.rect.centerx + random.randint(-15, 15), g.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), sc])
                        g.rect.x += (1 if g.rect.centerx > s.rect.centerx else -1) * 15
                else:
                    if g.infinity > 0 and g.energy > 0 and g.technique_burnout == 0:
                        g.energy = max(0, g.energy - 0.5 * g.cost_mult)
                        g.rect.x += (1 if g.rect.centerx > s.rect.centerx else -1) * 5
                    else:
                        if not g.is_dodging:
                            actual_dmg = melee_dmg
                            if g.energy > 0:
                                rm = random.uniform(0.15, 0.35); md = actual_dmg * (1.0 - rm); actual_dmg *= rm
                                g.energy = max(0, g.energy - (md * 3.5) * g.cost_mult)
                            g.hp -= actual_dmg
                            sc = (255, 0, 0) if s.black_flash_timer > 0 else RED
                            for _ in range(12): game.hit_sparks.append([g.rect.centerx + random.randint(-15, 15), g.rect.centery - random.randint(10, 30), random.uniform(-12, 12), random.uniform(-12, 12), random.randint(15, 30), sc])
                            g.rect.x += (1 if g.rect.centerx > s.rect.centerx else -1) * 15
                s.attack_cooldown = 12

        purple_active = any(p.type == "purple_orb" for p in game.projectiles)
        if (purple_active or g.purple_charge > 0) and s.on_ground:
            if random.random() < 0.15: s.jump()

        # Mahoraga summon triggers
        uv_adapt_percent = 1.0 - s.adaptation["void"]
        can_summon_lore = uv_adapt_percent >= 0.65
        is_fully_adapted = s.adaptation["void"] <= 0.0
        if g.domain_active and game.mahoraga is None and is_fully_adapted and getattr(s, "mahoraga_lockout", 0) <= 0 and game.mahoraga_summon_timer <= 0:
            game.mahoraga_summon_timer = 300
        elif can_summon_lore and s.hp < s.max_hp * 0.5 and game.mahoraga is None and not s.world_slash_unlocked and g.domain_cd > 0 and getattr(game, "clash_decision_timer", 0) == 0 and g.domain_charge == 0 and s.domain_charge == 0 and not g.domain_active:
            if getattr(s, "mahoraga_lockout", 0) <= 0: game.mahoraga_summon_timer = 300
        elif game.mahoraga is None and is_fully_adapted and game.mahoraga_summon_timer <= 0 and not g.domain_active:
            if getattr(s, "mahoraga_lockout", 0) <= 0: game.mahoraga_summon_timer = 300

    # ── Domain Charge Countdown ──────────────────────────────────────────────
    if s.domain_charge > 0:
        s.domain_charge -= time_mult
        if s.domain_charge <= 0:
            s.domain_charge = 0
            s.domain_active = True; s.domain_timer = 400
            s.domain_cd = 3000; game.shake_timer = 30

    return dist, fuga_priority, gojo_has_inf