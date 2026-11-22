"""
Script de diagnóstico y prueba visual para Bosconian (Integrante 4).
Ubícalo en la raíz del repositorio (al mismo nivel que la carpeta assets/) y ejecútalo con:
    python test_assets_and_window.py

Controles dentro de la ventana:
    T           : Alternar vista entre HUD de Juego y Pantalla de Título
    1 - 9, 0    : Cambiar entre Nivel 1 y Nivel 10 (actualiza minimapa, ronda y música)
    A           : Cambiar estado de alerta (GREEN -> YELLOW -> RED) + sonido
    S           : Probar uno por uno todos los efectos de sonido (SFX)
    M           : Silenciar / reactivar música
    ESC         : Salir
"""

import json
import os
import random
import sys
import pygame

CFG_DIR = os.path.join("assets", "cfg")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_path(p):
    """Intenta resolver rutas con o sin prefijo assets/."""
    if os.path.exists(p):
        return p
    alt = os.path.join("assets", p)
    if os.path.exists(alt):
        return alt
    return p


def audit_configs():
    print("=" * 60)
    print("1. AUDITORÍA DE ARCHIVOS JSON Y RUTAS DE ASSETS")
    print("=" * 60)

    required_jsons = [
        "window.json",
        "world.json",
        "audio.json",
        "score.json",
        "interface.json",
    ]
    optional_jsons = [
        "bullet.json",
        "enemies.json",
        "explosion.json",
        "player.json",
    ]

    configs = {}
    missing_assets = []
    errors = []

    for name in required_jsons + optional_jsons:
        path = os.path.join(CFG_DIR, name)
        if not os.path.exists(path):
            tag = "[ERROR]" if name in required_jsons else "[AVISO]"
            print(f"{tag} No existe: {path}")
            if name in required_jsons:
                errors.append(path)
            continue
        try:
            data = load_json(path)
            configs[name] = data
            print(f"[OK] JSON válido: {path}")
        except Exception as e:
            print(f"[ERROR] JSON inválido en {path}: {e}")
            errors.append(path)

    # Verificar niveles 01 al 10
    levels = {}
    for i in range(1, 11):
        lvl_path = os.path.join(CFG_DIR, "levels", f"level_{i:02d}.json")
        if not os.path.exists(lvl_path):
            print(f"[ERROR] Falta nivel: {lvl_path}")
            errors.append(lvl_path)
            continue
        try:
            levels[i] = load_json(lvl_path)
            print(
                f"[OK] Nivel {i:02d}: {len(levels[i].get('bases', []))} bases, "
                f"{len(levels[i].get('obstacles', []))} obstáculos"
            )
        except Exception as e:
            print(f"[ERROR] Nivel {i:02d} inválido: {e}")
            errors.append(lvl_path)

    # Revisar rutas referenciadas dentro de los JSON
    def check_asset(source, key, rel_path):
        if not isinstance(rel_path, str):
            return
        if os.path.exists(rel_path):
            return
        if os.path.exists(os.path.join("assets", rel_path)):
            print(f"[AVISO] En {source} ({key}): '{rel_path}' funciona solo si antepones 'assets/'")
            return
        missing_assets.append((source, key, rel_path))
        print(f"[FALTA] En {source} ({key}): no se encontró '{rel_path}'")

    if "audio.json" in configs:
        for k, v in configs["audio.json"].get("music", {}).items():
            check_asset("audio.json", f"music.{k}", v)
        for k, v in configs["audio.json"].get("sfx", {}).items():
            check_asset("audio.json", f"sfx.{k}", v)

    if "interface.json" in configs:
        check_asset("interface.json", "font", configs["interface.json"].get("font"))
        logo = configs["interface.json"].get("menus", {}).get("title_screen", {}).get("logo_image")
        if logo:
            check_asset("interface.json", "logo_image", logo)

    for lvl_num, lvl_data in levels.items():
        if "music" in lvl_data:
            check_asset(f"level_{lvl_num:02d}.json", "music", lvl_data["music"])

    for other in optional_jsons:
        if other not in configs:
            continue
        data = configs[other]
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ("image", "sound", "sound_move", "sound_chase") and isinstance(v, str):
                    check_asset(other, k, v)
                elif isinstance(v, dict):
                    for sk, sv in v.items():
                        if sk in ("image", "sound", "sound_move", "sound_chase") and isinstance(sv, str):
                            check_asset(other, f"{k}.{sk}", sv)

    print("-" * 60)
    print(f"Resumen: {len(errors)} errores críticos de JSON | {len(missing_assets)} rutas faltantes.")
    print("=" * 60)
    return configs, levels, errors


def run_visual_test(configs, levels):
    pygame.init()
    audio_ok = True
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"[AVISO] No se pudo inicializar el audio: {e}")
        audio_ok = False

    win_cfg = configs["window.json"]
    world_cfg = configs["world.json"]
    ui_cfg = configs["interface.json"]
    audio_cfg = configs.get("audio.json", {})
    score_cfg = configs.get("score.json", {})

    w = win_cfg["size"]["w"]
    h = win_cfg["size"]["h"]
    fps = win_cfg.get("framerate", 60)
    bg = (
        win_cfg["bg_color"]["r"],
        win_cfg["bg_color"]["g"],
        win_cfg["bg_color"]["b"],
    )

    # pygame.SCALED mantiene la resolución exacta 256x208 y la escala nítidamente en pantallas grandes
    flags = pygame.SCALED
    screen = pygame.display.set_mode((w, h), flags)
    pygame.display.set_caption(f"{win_cfg.get('title', 'Bosconian')} - TEST VENTANA ({w}x{h})")
    clock = pygame.time.Clock()

    # Cargar fuente
    font_path = resolve_path(ui_cfg.get("font", "assets/fnt/PressStart2P.ttf"))
    font_size = ui_cfg.get("hud", {}).get("font_size", ui_cfg.get("size", 5))
    try:
        font = pygame.font.Font(font_path, font_size)
        font_small = pygame.font.Font(font_path, 8)
    except Exception as e:
        print(f"[AVISO] Error cargando fuente '{font_path}': {e}. Usando fuente por defecto.")
        font = pygame.font.SysFont("monospace", 8)
        font_small = pygame.font.SysFont("monospace", 6)

    # Cargar logo de título y miniatura de nave para vidas
    logo_img = None
    logo_path = resolve_path(
        ui_cfg.get("menus", {}).get("title_screen", {}).get("logo_image", "assets/img/titulo.png")
    )
    if os.path.exists(logo_path):
        logo_img = pygame.image.load(logo_path).convert_alpha()

    life_icon = None
    hero_path = resolve_path("assets/img/Hero.png")
    if os.path.exists(hero_path):
        raw_hero = pygame.image.load(hero_path).convert_alpha()
        life_icon = pygame.transform.scale(raw_hero, (8, 8))

    # Cargar SFX
    sfx_map = {}
    sfx_names = []
    if audio_ok:
        sfx_vol = audio_cfg.get("volumes", {}).get("sfx", 0.7)
        for name, path in audio_cfg.get("sfx", {}).items():
            rp = resolve_path(path)
            if os.path.exists(rp):
                try:
                    snd = pygame.mixer.Sound(rp)
                    snd.set_volume(sfx_vol)
                    sfx_map[name] = snd
                    sfx_names.append(name)
                except Exception as e:
                    print(f"[AVISO] No se pudo cargar SFX '{name}' ({rp}): {e}")

    # Generar estrellas desde world.json
    star_colors = [(c["r"], c["g"], c["b"]) for c in world_cfg.get("star_colors", [])] or [(255, 255, 255)]
    blink_min = world_cfg.get("stars_blink_speed", {}).get("min", 0.25)
    blink_max = world_cfg.get("stars_blink_speed", {}).get("max", 0.5)
    stars = []
    for _ in range(world_cfg.get("stars_number", 100)):
        stars.append({
            "x": random.uniform(0, w),
            "y": random.uniform(0, h),
            "color": random.choice(star_colors),
            "layer": random.choice([0.3, 0.6, 1.0]),
            "blink_speed": random.uniform(blink_min, blink_max),
            "timer": random.uniform(0, 1.0),
            "visible": True,
        })

    # Estado interactivo de prueba
    mode = "hud"  # "hud" o "title"
    current_level = 1 if 1 in levels else (min(levels.keys()) if levels else 1)
    alert_states = ["GREEN", "YELLOW", "RED"]
    alert_idx = 0
    sfx_idx = 0
    last_sfx_label = "Presiona S para probar SFX"
    muted = False
    music_vol = audio_cfg.get("volumes", {}).get("music", 0.5)

    def play_music(path):
        if not audio_ok or muted or not path:
            return
        rp = resolve_path(path)
        if os.path.exists(rp):
            try:
                pygame.mixer.music.load(rp)
                pygame.mixer.music.set_volume(music_vol)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"[AVISO] Error reproduciendo música '{rp}': {e}")

    if current_level in levels:
        play_music(levels[current_level].get("music"))

    hud_cfg = ui_cfg.get("hud", {})
    mm_cfg = ui_cfg.get("minimap", {})
    alerts_cfg = ui_cfg.get("alerts", {})
    colors = hud_cfg.get("colors", {})

    running = True
    while running:
        dt = clock.tick(fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_t:
                    mode = "title" if mode == "hud" else "hud"
                    if mode == "title":
                        play_music(audio_cfg.get("music", {}).get("menu"))
                    elif current_level in levels:
                        play_music(levels[current_level].get("music"))
                elif event.key == pygame.K_a:
                    alert_idx = (alert_idx + 1) % len(alert_states)
                    st = alert_states[alert_idx]
                    if st == "YELLOW" and "alert_yellow" in sfx_map:
                        sfx_map["alert_yellow"].play()
                    elif st == "RED" and "alert_red" in sfx_map:
                        sfx_map["alert_red"].play()
                        play_music(audio_cfg.get("music", {}).get("alert_red"))
                    elif st == "GREEN" and current_level in levels:
                        play_music(levels[current_level].get("music"))
                elif event.key == pygame.K_s and sfx_names:
                    name = sfx_names[sfx_idx]
                    sfx_map[name].play()
                    last_sfx_label = f"SFX: {name}"
                    sfx_idx = (sfx_idx + 1) % len(sfx_names)
                elif event.key == pygame.K_m and audio_ok:
                    muted = not muted
                    if muted:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    num = 10 if event.key == pygame.K_0 else (event.key - pygame.K_0)
                    if num in levels:
                        current_level = num
                        if mode == "hud":
                            play_music(levels[current_level].get("music"))

        # Actualizar estrellas
        for st in stars:
            st["x"] = (st["x"] - 25 * st["layer"] * dt) % w
            st["timer"] += dt
            if st["timer"] >= st["blink_speed"]:
                st["timer"] = 0.0
                st["visible"] = not st["visible"]

        # Dibujar fondo y estrellas
        screen.fill(bg)
        for st in stars:
            if st["visible"]:
                screen.set_at((int(st["x"]), int(st["y"])), st["color"])

        if mode == "title":
            ts = ui_cfg.get("menus", {}).get("title_screen", {})
            if logo_img:
                # Ajustar si el logo es más ancho que la ventana
                lw, lh = logo_img.get_size()
                if lw > w - 16:
                    scale = (w - 16) / lw
                    draw_logo = pygame.transform.scale(logo_img, (int(lw * scale), int(lh * scale)))
                else:
                    draw_logo = logo_img
                lx = (w - draw_logo.get_width()) // 2
                ly = ts.get("logo_position", [28, 24])[1]
                screen.blit(draw_logo, (lx, ly))
            else:
                txt = font.render("BOSCONIAN", False, (255, 255, 255))
                screen.blit(txt, ((w - txt.get_width()) // 2, 36))

            ox, oy = ts.get("options_start_pos", [76, 118])
            spacing = ts.get("options_spacing", 14)
            for idx, opt in enumerate(ts.get("options", [])):
                col = ts.get("selected_color", [255, 235, 0]) if idx == 0 else ts.get("normal_color", [255, 255, 255])
                prefix = "> " if idx == 0 else "  "
                surf = font.render(prefix + opt["label"], False, col)
                screen.blit(surf, (ox, oy + idx * spacing))

            hint = font_small.render("T:VER HUD | M:MUTE | ESC:SALIR", False, (160, 160, 160))
            screen.blit(hint, (8, h - 10))
        else:
            # Área jugable (izquierda) con información de prueba
            lvl = levels.get(current_level, {})
            info_lines = [
                f"TEST VENTANA {w}x{h} @ {int(clock.get_fps())}FPS",
                f"NIVEL {current_level:02d} (TECLAS 1-9,0)",
                f"BASES: {len(lvl.get('bases', []))} | OBS: {len(lvl.get('obstacles', []))}",
                last_sfx_label,
                "A:ALERTA | S:SFX | T:TITULO",
            ]
            for i, line in enumerate(info_lines):
                surf = font_small.render(line, False, (200, 220, 255))
                screen.blit(surf, (6, 8 + i * 12))

            # Panel HUD lateral derecho
            pr = pygame.Rect(*hud_cfg.get("panel_rect", [192, 0, 64, 208]))
            pygame.draw.rect(screen, hud_cfg.get("panel_bg_color", [12, 12, 24]), pr)
            pygame.draw.line(
                screen,
                hud_cfg.get("panel_border_color", [65, 105, 225]),
                (pr.left, 0),
                (pr.left, h),
                1,
            )

            # HI-SCORE y 1UP
            c_red = colors.get("label_red", [220, 40, 40])
            c_white = colors.get("label_white", [255, 255, 255])
            c_yellow = colors.get("value_yellow", [255, 235, 0])

            screen.blit(font.render(hud_cfg.get("high_score_label", "HI-SCORE"), False, c_red), hud_cfg.get("high_score_label_pos", [196, 8]))
            screen.blit(font.render(str(score_cfg.get("default_high_score", 20000)), False, c_white), hud_cfg.get("high_score_value_pos", [196, 18]))
            screen.blit(font.render(hud_cfg.get("score_label", "1UP"), False, c_red), hud_cfg.get("score_label_pos", [196, 32]))
            screen.blit(font.render("00000", False, c_white), hud_cfg.get("score_value_pos", [196, 42]))

            # Alerta
            st_key = alert_states[alert_idx]
            st_cfg = alerts_cfg.get(st_key, {"short_text": st_key, "color": [0, 220, 80]})
            screen.blit(font.render(st_cfg.get("short_text", st_key), False, st_cfg.get("color", [0, 220, 80])), hud_cfg.get("alert_label_pos", [196, 58]))

            # Minimapa con jugador y bases reales del nivel actual
            mm_rect = pygame.Rect(*mm_cfg.get("rect", [198, 76, 52, 68]))
            pygame.draw.rect(screen, mm_cfg.get("bg_color", [0, 16, 32]), mm_rect)
            pygame.draw.rect(screen, mm_cfg.get("border_color", [65, 105, 225]), mm_rect, 1)

            world_w = lvl.get("world_size", {}).get("w", 1024)
            world_h = lvl.get("world_size", {}).get("h", 1024)
            msize = mm_cfg.get("marker_size", 2)

            for b in lvl.get("bases", []):
                bx = mm_rect.left + int((b["position"]["x"] / world_w) * (mm_rect.width - msize))
                by = mm_rect.top + int((b["position"]["y"] / world_h) * (mm_rect.height - msize))
                pygame.draw.rect(screen, mm_cfg.get("base_color", [0, 255, 80]), (bx, by, msize, msize))

            ppos = lvl.get("player_spawn", {}).get("position", {"x": world_w / 2, "y": world_h / 2})
            px = mm_rect.left + int((ppos["x"] / world_w) * (mm_rect.width - msize))
            py = mm_rect.top + int((ppos["y"] / world_h) * (mm_rect.height - msize))
            pygame.draw.rect(screen, mm_cfg.get("player_color", [255, 255, 255]), (px, py, msize, msize))

            # Ronda y vidas
            screen.blit(font.render(hud_cfg.get("round_label", "ROUND"), False, c_white), hud_cfg.get("round_label_pos", [196, 152]))
            screen.blit(font.render(f"{current_level:02d}", False, c_yellow), hud_cfg.get("round_value_pos", [232, 152]))
            screen.blit(font.render(hud_cfg.get("lives_label", "SHIPS"), False, c_white), hud_cfg.get("lives_label_pos", [196, 166]))

            lx, ly = hud_cfg.get("lives_icons_pos", [196, 176])
            lives = score_cfg.get("initial_lives", 4)
            for i in range(lives):
                if life_icon:
                    screen.blit(life_icon, (lx + i * 10, ly))
                else:
                    pygame.draw.rect(screen, c_white, (lx + i * 8, ly, 5, 5))

            # Indicador habilidad especial del nivel
            sp_on = lvl.get("player_spawn", {}).get("special_ability", False)
            sp_txt = "SPC:ON" if sp_on else "SPC:OFF"
            sp_col = colors.get("special_on", [0, 255, 120]) if sp_on else colors.get("special_off", [120, 120, 120])
            screen.blit(font.render(sp_txt, False, sp_col), hud_cfg.get("special_indicator_pos", [196, 194]))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    configs, levels, errors = audit_configs()
    if "window.json" not in configs or "world.json" not in configs or "interface.json" not in configs:
        print("No se puede abrir la ventana de prueba porque faltan JSON obligatorios.")
        sys.exit(1)
    run_visual_test(configs, levels)
