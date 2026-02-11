import os
import pygame

from .controller import GameController, MasMode
from .models import Side


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("AFWI (Python Prototype)")

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    board_path = os.path.join(root, "assets", "board.jpg")
    manifest_path = os.path.join(root, "assets", "token_manifest.json")
    stats_path = os.path.join(root, "data", "token_stats.json")

    board_img = None
    if os.path.exists(board_path):
        board_img = pygame.image.load(board_path).convert()

    font = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 18)

    ctrl = GameController(seed=1)
    ctrl.new_game()

    # Load token types (images + stats). If token_stats.json doesn't exist yet, we load defaults.
    if os.path.exists(manifest_path):
        ctrl.load_tokens(manifest_path, stats_path)
        if not os.path.exists(stats_path):
            ctrl.log("token_stats.json not found yet; token stats are using safe defaults (move=1, sensor=1, etc.).")

    log_scroll = 0
    clock = pygame.time.Clock()

    def draw_text(x: int, y: int, text: str, small: bool = False) -> int:
        f = font_small if small else font
        surf = f.render(text, True, (220, 220, 220))
        screen.blit(surf, (x, y))
        return y + (18 if small else 22)

    def band_to_screen(board_rect: pygame.Rect, band: int) -> tuple[int, int]:
        """Very simple mapping of bands 1..5 to columns across the board image."""
        band = max(1, min(5, band))
        col_w = board_rect.width / 5.0
        x = int(board_rect.left + (band - 0.5) * col_w)
        y = int(board_rect.top + board_rect.height * 0.55)
        return x, y

    def draw_tokens(board_rect: pygame.Rect) -> None:
        """Draw tokens as simple circles + labels.

        Fog-of-war:
        - if token.face_up, show name
        - else show 'UNKNOWN'
        """
        # stack tokens within same band by a small offset
        stacks: dict[int, int] = {}
        for tid, inst in ctrl.gs.tokens.items():
            if inst.band is None:
                continue
            stacks.setdefault(inst.band, 0)
            stacks[inst.band] += 1
            offset = stacks[inst.band] - 1

            x, y = band_to_screen(board_rect, inst.band)
            x += offset * 18
            y += (offset % 3) * 18

            # color by side
            color = (80, 160, 255) if inst.side == Side.US else (255, 80, 80)
            pygame.draw.circle(screen, color, (x, y), 14)
            pygame.draw.circle(screen, (0, 0, 0), (x, y), 14, 2)

            # label with fog-of-war
            tt = ctrl.gs.token_types.get(inst.type_id)
            if inst.face_up and tt:
                label = tt.name
            else:
                label = "UNKNOWN"

            text = font_small.render(label, True, (240, 240, 240))
            screen.blit(text, (x - 20, y - 26))

            # winchester marker
            if inst.winchester:
                w = font_small.render("W", True, (255, 255, 0))
                screen.blit(w, (x - 5, y - 8))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # log scrolling
                if event.key == pygame.K_UP:
                    log_scroll = max(0, log_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    log_scroll = min(max(0, len(ctrl.gs.log) - 1), log_scroll + 1)

                # universal
                elif event.key == pygame.K_ESCAPE:
                    ctrl.mas_exit()

                # posture / initiative / intel
                elif event.key == pygame.K_1:
                    if ctrl.mas_mode == MasMode.MENU:
                        ctrl.mas_choose(1)
                    else:
                        ctrl.choose_posture(1)
                elif event.key == pygame.K_2:
                    if ctrl.mas_mode == MasMode.MENU:
                        ctrl.mas_choose(2)
                    else:
                        ctrl.choose_posture(2)
                elif event.key == pygame.K_3:
                    if ctrl.mas_mode == MasMode.MENU:
                        ctrl.mas_choose(3)
                    else:
                        ctrl.choose_posture(3)
                elif event.key == pygame.K_i:
                    ctrl.resolve_initiative()
                elif event.key == pygame.K_r:
                    ctrl.intel_roll()

                # turn actions
                elif event.key == pygame.K_p:
                    ctrl.pass_turn()
                elif event.key == pygame.K_e:
                    ctrl.play_enabler()
                elif event.key == pygame.K_s:
                    ctrl.activate_squadron()
                elif event.key == pygame.K_m:
                    ctrl.mas_enter_menu()

                # MAS selection controls
                elif event.key == pygame.K_LEFTBRACKET:
                    ctrl.select_prev_own()
                elif event.key == pygame.K_RIGHTBRACKET:
                    ctrl.select_next_own()
                elif event.key == pygame.K_COMMA:
                    ctrl.select_prev_enemy()
                elif event.key == pygame.K_PERIOD:
                    ctrl.select_next_enemy()

                # MOVE controls
                elif event.key == pygame.K_a:
                    ctrl.move_adjust_destination(-1)
                elif event.key == pygame.K_d:
                    ctrl.move_adjust_destination(+1)

                # confirm actions
                elif event.key == pygame.K_RETURN:
                    if ctrl.mas_mode == MasMode.MOVE:
                        ctrl.move_confirm()
                    elif ctrl.mas_mode == MasMode.ACQUIRE:
                        ctrl.acquire_attempt()
                    elif ctrl.mas_mode == MasMode.SHOOT:
                        ctrl.shoot_attempt()

        screen.fill((30, 30, 30))

        # draw board
        board_rect = pygame.Rect(10, 10, 780, 780)
        if board_img:
            board_scaled = pygame.transform.smoothscale(board_img, (board_rect.width, board_rect.height))
            screen.blit(board_scaled, (board_rect.left, board_rect.top))
        else:
            draw_text(20, 20, "Board image not found. Put it at assets/board.jpg")

        # draw tokens on top of board
        draw_tokens(board_rect)

        # right panel
        panel_x, panel_y = 810, 10
        panel_w, panel_h = 380, 780
        pygame.draw.rect(screen, (15, 15, 15), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (80, 80, 80), (panel_x, panel_y, panel_w, panel_h), 1)

        y = panel_y + 10
        y = draw_text(panel_x + 10, y, f"Phase: {ctrl.phase.name}")
        y = draw_text(panel_x + 10, y, f"ATO: {ctrl.gs.ato_number} | Turn: {ctrl.gs.current_side.value}")
        y = draw_text(panel_x + 10, y, f"MAS Mode: {ctrl.mas_mode.name}", small=True)

        own, enemy = ctrl.get_selected_ids()
        y = draw_text(panel_x + 10, y, f"Selected own: {own or '-'}", small=True)
        y = draw_text(panel_x + 10, y, f"Selected enemy: {enemy or '-'}", small=True)
        y += 6

        y = draw_text(panel_x + 10, y, "Controls:")
        y = draw_text(panel_x + 10, y, "ATO_START: 1/2/3 choose posture", small=True)
        y = draw_text(panel_x + 10, y, "I = Initiative | R = Intel roll", small=True)
        y = draw_text(panel_x + 10, y, "Turns: E=Enabler, S=Squadron, M=MAS, P=Pass", small=True)
        y = draw_text(panel_x + 10, y, "MAS: [ ] own token, , . enemy token", small=True)
        y = draw_text(panel_x + 10, y, "MOVE: A/D adjust band, ENTER confirm", small=True)
        y = draw_text(panel_x + 10, y, "ACQUIRE/SHOOT: ENTER roll", small=True)
        y = draw_text(panel_x + 10, y, "ESC exits MAS | UP/DOWN scroll log", small=True)

        y += 10
        y = draw_text(panel_x + 10, y, "Event Log:")

        visible_lines = 24
        start = log_scroll
        end = min(len(ctrl.gs.log), start + visible_lines)
        ly = y + 10
        for line in ctrl.gs.log[start:end]:
            surf = font_small.render(line, True, (200, 200, 200))
            screen.blit(surf, (panel_x + 10, ly))
            ly += 18

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
