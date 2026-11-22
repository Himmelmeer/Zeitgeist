#!/usr/bin/env python3
"""
Shared single-source-of-truth shot choreography computed dynamically from timeline.json.
Ensures 100% frame-accurate synchronization between video cuts, UI animations,
Foley accents, J-Cut transition, and Bach Solo Cello cadence.
"""
WORK_DIR = "/tmp/zeitgeist_work"
RAW_VID = f"{WORK_DIR}/raw/videos"
UI_DIR = f"{WORK_DIR}/ui_renders"


def compute_shot_layout(tl):
    acts = tl["acts"]
    total_dur = tl["total_duration"]
    cues = {c["id"]: c for c in tl["cues"]}

    def c_mid(cid, frac):
        c = cues[cid]
        return round(c["start"] + c["duration"] * frac, 3)

    a1_end = acts["1"]["end"]
    a2_end = acts["2"]["end"]
    cliff_s = acts["cliff"]["start"]
    cliff_e = acts["cliff"]["end"]
    a3_end = acts["3"]["end"]
    a4_end = acts["4"]["end"]

    # Key dynamic UI sync anchors
    regen_start = cues["a2_04"]["start"]
    regen_end = min(round(regen_start + 7.4, 3), cues["a2_05"]["start"])
    grid_start = regen_end
    grid_end = min(round(grid_start + 8.4, 3), c_mid("a2_06", 0.35))

    editor_start = cues["a4_03"]["start"]
    editor_end = min(round(editor_start + 15.4, 3), cues["a4_05"]["start"])
    if editor_end - editor_start < 13.5:
        # Ensure the full Delete + slow human typing choreography finishes before cutting
        editor_end = min(round(editor_start + 15.2, 3), round(a4_end - 4.2, 3))

    finale_card_start = round(max(cues["a5_02"]["end"] + 0.4, cues["a5_03"]["start"] - 0.55), 3)
    # Cap finale card to <= 9.4s (the rendered length of ui_finale_we_touch.mp4)
    if total_dur - finale_card_start > 9.45:
        finale_card_start = round(total_dur - 9.45, 3)

    # Split Act 5 human hands montage cleanly into 4 equal breathing portraits
    h_span = finale_card_start - a4_end
    h1 = round(a4_end + h_span * 0.26, 3)
    h2 = round(a4_end + h_span * 0.52, 3)
    h3 = round(a4_end + h_span * 0.77, 3)

    # Split remaining Act 4 tail cleanly between mixer knobs & vintage camera viewfinder
    a4_tail_mid = round(editor_end + (a4_end - editor_end) * 0.48, 3)

    # Tuple: (start_s, end_s, src, in_ss, mode, zoom_dir, fade_in, fade_out, slow_factor, tag)
    shots = [
        # --- ACT 1: 平滑的狂欢 ---
        (0.000, 0.550, "BLACK", 0.0, "black", "none", 0.0, 0.0, 1.0, "a1_black"),
        (0.550, 1.350, f"{RAW_VID}/a1_podcast2_2948.mp4", 1.5, "cold", "none", 0.0, 0.0, 1.0, "a1_flash1"),
        (1.350, 2.150, f"{RAW_VID}/a1_stage_13222.mp4", 2.0, "cold", "none", 0.0, 0.0, 1.0, "a1_flash2"),
        (2.150, round(cues["a1_01"]["start"] + 0.65, 3), f"{UI_DIR}/ui_act1_taste_wall.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0, "a1_taste_title"),
        (round(cues["a1_01"]["start"] + 0.65, 3), cues["a1_01"]["end"], f"{UI_DIR}/ui_act1_taste_wall.mp4", 2.8, "ui_cold", "none", 0.0, 0.0, 1.0, "a1_quote_feed"),
        (cues["a1_01"]["end"], c_mid("a1_02", 0.45), f"{RAW_VID}/a1_podcast3_2955.mp4", 2.0, "cold", "in", 0.0, 0.0, 1.0, "a1_pod3"),
        (c_mid("a1_02", 0.45), cues["a1_02"]["end"], f"{RAW_VID}/a1_min_room_3110.mp4", 1.5, "cold", "in", 0.0, 0.0, 1.0, "a1_room"),
        (cues["a1_02"]["end"], round(cues["a1_03"]["start"] + 1.55, 3), f"{RAW_VID}/a1_coffee_3574.mp4", 1.0, "cold", "in", 0.0, 0.0, 1.0, "a1_coffee"),
        (round(cues["a1_03"]["start"] + 1.55, 3), a1_end, f"{RAW_VID}/a1_cgi_sunset_33919.mp4", 1.0, "cold", "in", 0.25, 0.45, 1.25, "a1_cgi_sunset"),

        # --- ACT 2: 舌头的逻辑 ---
        (a1_end, cues["a2_01"]["end"], f"{RAW_VID}/a2_wine_black1_52407.mp4", 2.0, "cold", "in", 0.45, 0.0, 1.25, "a2_wine1"),
        (cues["a2_01"]["end"], c_mid("a2_02", 0.52), f"{RAW_VID}/a2_wine_black2_52406.mp4", 4.0, "cold", "in", 0.0, 0.0, 1.25, "a2_wine2"),
        (c_mid("a2_02", 0.52), cues["a2_03"]["start"], f"{RAW_VID}/a2_wine_white_52418.mp4", 3.0, "cold", "in", 0.0, 0.0, 1.25, "a2_wine3"),
        (cues["a2_03"]["start"], regen_start, f"{RAW_VID}/a2_scroll1_21364.mp4", 2.0, "cold", "in", 0.0, 0.0, 1.0, "a2_scroll"),
        (regen_start, regen_end, f"{UI_DIR}/ui_act2_regenerate.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0, "a2_regen"),
        (grid_start, grid_end, f"{UI_DIR}/ui_act2_pixel_grid.mp4", 0.0, "ui_cold", "none", 0.0, 0.0, 1.0, "a2_grid"),
        (grid_end, cues["a2_07"]["start"], f"{RAW_VID}/a2_glasses_screen_14771.mp4", 0.0, "cold", "in", 0.0, 0.0, 1.15, "a2_glasses"),
        (cues["a2_07"]["start"], a2_end, f"{RAW_VID}/a2_museum2_46425.mp4", 2.0, "cold", "out", 0.0, 0.0, 1.0, "a2_museum"),

        # --- THE CLIFF: 1.50s DEAD BLACK ---
        (cliff_s, cliff_e, "BLACK", 0.0, "black", "none", 0.0, 0.0, 1.0, "cliff_black"),

        # --- ACT 3: 进入阻力 / HANDWERKLICHKEIT ---
        (cliff_e, cues["a3_02"]["start"], f"{RAW_VID}/a3_wood_chisel_39500.mp4", 2.0, "warm", "in", 0.12, 0.0, 1.0, "a3_wood_chisel"),
        (cues["a3_02"]["start"], cues["a3_03"]["start"], f"{RAW_VID}/a3_clock_mech_3651.mp4", 0.5, "warm", "in", 0.0, 0.0, 1.15, "a3_clock_mech"),
        (cues["a3_03"]["start"], c_mid("a3_03", 0.52), f"{RAW_VID}/a3_pottery_wheel_32085.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0, "a3_pottery_wheel"),
        (c_mid("a3_03", 0.52), cues["a3_04"]["start"], f"{RAW_VID}/a3_wood_carve_20438.mp4", 1.0, "warm", "in", 0.0, 0.0, 1.0, "a3_wood_carve"),
        (cues["a3_04"]["start"], c_mid("a3_04", 0.24), f"{RAW_VID}/a3_wood_detail_3815.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0, "a3_wood_detail"),
        (c_mid("a3_04", 0.24), c_mid("a3_04", 0.48), f"{RAW_VID}/a3_brush_hand_5197.mp4", 1.5, "warm", "in", 0.0, 0.0, 1.0, "a3_brush_hand"),
        (c_mid("a3_04", 0.48), cues["a3_05"]["start"], f"{RAW_VID}/a3_pottery_model_1973.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0, "a3_pottery_model"),
        (cues["a3_05"]["start"], c_mid("a3_05", 0.48), f"{RAW_VID}/a3_wood_sand2_20388.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0, "a3_wood_sand"),
        (c_mid("a3_05", 0.48), cues["a3_06"]["start"], f"{RAW_VID}/a3_pottery_tool_1979.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.0, "a3_pottery_tool"),
        (cues["a3_06"]["start"], c_mid("a3_06", 0.44), f"{RAW_VID}/a3_glass_craft_4175.mp4", 2.0, "warm", "in", 0.0, 0.0, 1.10, "a3_glass_craft"),
        (c_mid("a3_06", 0.44), cues["a3_07"]["start"], f"{RAW_VID}/a3_clock_gears_2561.mp4", 1.5, "warm", "in", 0.0, 0.0, 1.15, "a3_clock_gears"),
        (cues["a3_07"]["start"], a3_end, f"{RAW_VID}/a3_dough_form_42466.mp4", 0.5, "warm", "in", 0.0, 0.45, 1.15, "a3_dough_form"),

        # --- ACT 4: 数字时代的毛边 ---
        (a3_end, c_mid("a4_01", 0.62), f"{RAW_VID}/a4_typing_laptop_1808.mp4", 1.0, "warm", "in", 0.45, 0.0, 1.0, "a4_laptop"),
        (c_mid("a4_01", 0.62), cues["a4_02"]["start"], f"{RAW_VID}/a3_dough_mix_42464.mp4", 1.0, "warm", "in", 0.0, 0.0, 1.0, "a4_dough_cb"),
        (cues["a4_02"]["start"], editor_start, f"{RAW_VID}/a4_typing_close_47321.mp4", 1.5, "warm", "in", 0.0, 0.25, 1.0, "a4_typing_dark"),
        (editor_start, editor_end, f"{UI_DIR}/ui_act4_rough_edge_editor.mp4", 0.0, "ui_warm", "none", 0.30, 0.30, 1.0, "a4_editor"),
        (editor_end, a4_tail_mid, f"{RAW_VID}/a4_mixer_knobs_25242.mp4", 3.0, "warm", "in", 0.25, 0.0, 1.0, "a4_mixer"),
        (a4_tail_mid, a4_end, f"{RAW_VID}/a4_viewfinder_49652.mp4", 2.0, "warm", "in", 0.0, 0.35, 1.0, "a4_viewfinder"),

        # --- ACT 5: 尾声 · 人类双手肖像蒙太奇 + WE TOUCH. ---
        (a4_end, h1, f"{RAW_VID}/a5_elderly_hands_48789.mp4", 2.0, "warm", "in", 0.35, 0.25, 1.15, "a5_elderly"),
        (h1, h2, f"{RAW_VID}/a5_child_paint_15163.mp4", 3.0, "warm", "in", 0.25, 0.25, 1.15, "a5_child"),
        (h2, h3, f"{RAW_VID}/a5_hand_wheat_8864.mp4", 2.0, "warm", "in", 0.25, 0.25, 1.15, "a5_wheat"),
        (h3, finale_card_start, f"{RAW_VID}/a5_hand_leaves_2563.mp4", 4.0, "warm", "in", 0.25, 0.55, 1.15, "a5_leaves"),
        (finale_card_start, total_dur, f"{UI_DIR}/ui_finale_we_touch.mp4", 0.0, "ui_warm", "none", 0.30, 0.0, 1.0, "a5_finale_card"),
    ]

    # Build lookup map by tag for exact Foley placement
    by_tag = {sh[9]: (sh[0], sh[1]) for sh in shots}
    return shots, by_tag
