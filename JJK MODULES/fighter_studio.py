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

    while running:
        screen.fill((20, 20, 25)) # Slightly darker for better contrast
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    print("Reloading fighter.py and aura.py...")
                    importlib.reload(settings)
                    importlib.reload(aura)
                    importlib.reload(fighter)
                    current_fighter = create_preview_fighter(current_fighter.name)

                # Switch Characters
                if event.key == pygame.K_1: current_fighter = create_preview_fighter("Gojo")
                if event.key == pygame.K_2: current_fighter = create_preview_fighter("Sukuna")
                if event.key == pygame.K_3: current_fighter = create_preview_fighter("Mahoraga")

                # Toggle Animation States for testing
                if event.key == pygame.K_p: current_fighter.punch_timer = 20 # Test punch reach/thickness
                if event.key == pygame.K_b: current_fighter.black_flash_timer = 30 # Test grit/lightning

        # Manually progress animation frames
        current_fighter.anim_tick += 1
        if current_fighter.punch_timer > 0: current_fighter.punch_timer -= 1
        if current_fighter.black_flash_timer > 0: current_fighter.black_flash_timer -= 1
        
        # Lock position to center
        current_fighter.rect.center = (400, 400)
        
        # Draw everything from fighter.py
        current_fighter.draw_detailed(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_studio()