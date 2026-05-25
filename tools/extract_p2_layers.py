from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "p2.jpg"
OUT = ROOT / "public" / "assets" / "home" / "p2-cut-v1"


def blur_mask(mask, sigma):
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)


def hard_polygon(mask, points, value):
    cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], value)


def make_person_mask(image_bgr):
    h, w = image_bgr.shape[:2]
    grab = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)

    probable = np.zeros((h, w), dtype=np.uint8)
    definite = np.zeros((h, w), dtype=np.uint8)

    hard_polygon(
        probable,
        [(1110, 300), (1615, 280), (1848, 600), (1870, 880), (1678, 1215), (1475, 1325), (1188, 930), (1048, 632)],
        255,
    )
    cv2.line(probable, (1385, 510), (1170, 820), 255, 150)
    cv2.line(probable, (1515, 390), (1280, 825), 255, 128)
    cv2.line(probable, (1640, 390), (1530, 930), 255, 126)
    cv2.line(probable, (1685, 420), (1678, 890), 255, 112)
    cv2.ellipse(probable, (1557, 393), (130, 118), -8, 0, 360, 255, -1)
    cv2.ellipse(probable, (1554, 760), (230, 355), -6, 0, 360, 255, -1)

    hard_polygon(definite, [(1426, 548), (1596, 470), (1744, 628), (1714, 1002), (1572, 1137), (1432, 1038), (1356, 720)], 255)
    cv2.ellipse(definite, (1554, 392), (84, 78), -8, 0, 360, 255, -1)
    cv2.line(definite, (1510, 440), (1280, 790), 255, 58)
    cv2.line(definite, (1648, 444), (1572, 884), 255, 62)
    cv2.line(definite, (1395, 650), (1274, 777), 255, 58)
    cv2.line(definite, (1720, 634), (1818, 782), 255, 64)
    cv2.line(definite, (1532, 1048), (1534, 1246), 255, 62)
    cv2.line(definite, (1610, 1048), (1576, 1268), 255, 62)

    grab[probable > 0] = cv2.GC_PR_FGD
    grab[definite > 0] = cv2.GC_FGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(image_bgr, grab, None, bgd, fgd, 7, cv2.GC_INIT_WITH_MASK)

    person = np.where((grab == cv2.GC_FGD) | (grab == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    allow = cv2.dilate(probable, np.ones((61, 61), np.uint8), iterations=1)
    person = cv2.bitwise_and(person, allow)
    person = cv2.morphologyEx(person, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=2)
    person = cv2.morphologyEx(person, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(person, 8)
    kept = np.zeros_like(person)
    for idx in range(1, count):
        x, y, ww, hh, area = stats[idx]
        cx = x + ww / 2
        cy = y + hh / 2
        if area > 360 or (1060 < cx < 1900 and 260 < cy < 1320):
            kept[labels == idx] = 255

    kept = cv2.dilate(kept, np.ones((3, 3), np.uint8), iterations=1)
    return kept


def make_shadow_region(shape):
    h, w = shape
    shadow = np.zeros((h, w), dtype=np.uint8)

    hard_polygon(
        shadow,
        [(1346, 1018), (1515, 1030), (1725, 1062), (1970, 1135), (2110, 1245), (2068, 1376), (1812, 1456), (1555, 1355), (1380, 1218)],
        255,
    )
    cv2.ellipse(shadow, (1770, 1258), (362, 160), 8, 0, 360, 255, -1)
    cv2.ellipse(shadow, (1562, 1250), (185, 258), -15, 0, 360, 255, -1)
    cv2.line(shadow, (1462, 1050), (1398, 1458), 255, 120)
    cv2.line(shadow, (1340, 1174), (1575, 1405), 255, 100)

    # The faint front of the cast shadow is intentionally broad and feathered;
    # this prevents the vertical "cut-off shadow" artifact seen in the old asset.
    cv2.ellipse(shadow, (2038, 1228), (248, 112), 8, 0, 360, 255, -1)
    cv2.ellipse(shadow, (1380, 1348), (188, 138), -22, 0, 360, 180, -1)

    return shadow


def draw_person_shape(shape):
    h, w = shape
    mask = np.zeros((h, w), dtype=np.uint8)

    # A tighter hand-built silhouette for the character. The earlier GrabCut
    # pass kept too much snow around the body, so this stays close to the real
    # figure and lets color/difference signals do the feathered edge work.
    cv2.ellipse(mask, (1560, 394), (108, 102), -8, 0, 360, 255, -1)
    hard_polygon(
        mask,
        [(1430, 520), (1606, 468), (1746, 608), (1778, 815), (1694, 1030), (1585, 1124), (1444, 1048), (1354, 754)],
        255,
    )
    cv2.line(mask, (1434, 628), (1268, 788), 255, 98)
    cv2.line(mask, (1710, 636), (1818, 790), 255, 98)
    cv2.line(mask, (1532, 1040), (1534, 1246), 255, 76)
    cv2.line(mask, (1608, 1038), (1562, 1266), 255, 78)
    cv2.ellipse(mask, (1512, 1258), (58, 70), -26, 0, 360, 255, -1)
    cv2.ellipse(mask, (1574, 1262), (56, 82), 18, 0, 360, 255, -1)

    cv2.line(mask, (1508, 420), (1348, 690), 255, 76)
    cv2.line(mask, (1350, 685), (1162, 812), 255, 82)
    cv2.line(mask, (1182, 792), (1088, 964), 255, 76)
    cv2.ellipse(mask, (1138, 936), (92, 74), 35, 0, 360, 255, -1)
    cv2.line(mask, (1642, 412), (1584, 894), 255, 82)
    cv2.line(mask, (1668, 420), (1652, 740), 255, 68)
    cv2.line(mask, (1522, 505), (1500, 812), 255, 72)

    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8), iterations=1)


def make_v2_foreground(image_rgb, clean_rgb):
    h, w = image_rgb.shape[:2]
    original = image_rgb.astype(np.float32)
    clean = clean_rgb.astype(np.float32)
    luma = original[..., 0] * 0.2126 + original[..., 1] * 0.7152 + original[..., 2] * 0.0722
    clean_luma = clean[..., 0] * 0.2126 + clean[..., 1] * 0.7152 + clean[..., 2] * 0.0722
    diff = np.mean(np.abs(original - clean), axis=2)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation = hsv[..., 1]

    person_shape = draw_person_shape((h, w))
    person_edge = cv2.GaussianBlur(person_shape.astype(np.float32), (0, 0), 2.0)

    color_signal = np.maximum.reduce(
        [
            np.clip((diff - 4.0) / 50.0, 0, 1),
            np.clip((saturation - 8.0) / 62.0, 0, 1),
            np.clip((238.0 - luma) / 88.0, 0, 1),
        ],
    )
    very_snowy = (luma > 229) & (saturation < 18) & (diff < 18)
    color_signal[very_snowy] *= 0.08

    core = cv2.erode(person_shape, np.ones((11, 11), np.uint8), iterations=1).astype(np.float32) / 255.0
    edge = person_edge / 255.0
    person_alpha = np.maximum(core * 236, edge * np.clip(color_signal * 260, 0, 248))
    person_alpha = cv2.GaussianBlur(person_alpha.astype(np.float32), (0, 0), 0.55)
    person_alpha = np.clip(person_alpha, 0, 255)

    # Pull the matte inward at near-white low-difference edges. This removes
    # the remaining snow rim without making the pale coat disappear.
    snow_rim = (person_alpha > 2) & (person_alpha < 190) & (luma > 222) & (saturation < 22) & (diff < 22)
    person_alpha[snow_rim] *= 0.18
    person_alpha[person_alpha < 6] = 0

    # Despill/dewhite only the semi-transparent fringe. The solid center keeps
    # the original illustration color.
    person_rgb = original.copy()
    fringe = (person_alpha > 0) & (person_alpha < 210) & (luma > 205)
    person_rgb[fringe] = person_rgb[fringe] * 0.82 + np.array([91, 135, 158], dtype=np.float32) * 0.18

    shadow_region = make_shadow_region((h, w)).astype(np.float32) / 255.0
    dark_delta = np.maximum(clean_luma - luma, 0)
    shadow_alpha = np.clip((dark_delta - 2.0) / 48.0, 0, 1) * 118
    shadow_alpha = np.maximum(shadow_alpha, shadow_region * 14)
    shadow_alpha = cv2.GaussianBlur(shadow_alpha.astype(np.float32), (0, 0), 5.5) * cv2.GaussianBlur(shadow_region, (0, 0), 8)
    shadow_alpha[person_alpha > 8] = 0
    shadow_alpha = np.clip(shadow_alpha, 0, 130)

    alpha = np.maximum(person_alpha, shadow_alpha).astype(np.uint8)
    foreground_rgb = np.zeros_like(original)

    shadow_rgb = np.array([45, 76, 92], dtype=np.float32)
    shadow_pixels = shadow_alpha > person_alpha
    foreground_rgb[shadow_pixels] = shadow_rgb
    foreground_rgb[person_alpha > 0] = person_rgb[person_alpha > 0]

    foreground_rgba = np.dstack([np.clip(foreground_rgb, 0, 255).astype(np.uint8), alpha])
    composite = clean * (1 - alpha[..., None] / 255.0) + foreground_rgb * (alpha[..., None] / 255.0)
    composite = np.clip(composite, 0, 255).astype(np.uint8)

    return foreground_rgba, alpha, composite


def make_v3_foreground(image_rgb, clean_rgb):
    h, w = image_rgb.shape[:2]
    original = image_rgb.astype(np.float32)
    clean = clean_rgb.astype(np.float32)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

    luma = original[..., 0] * 0.2126 + original[..., 1] * 0.7152 + original[..., 2] * 0.0722
    clean_luma = clean[..., 0] * 0.2126 + clean[..., 1] * 0.7152 + clean[..., 2] * 0.0722
    diff = np.mean(np.abs(original - clean), axis=2)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation = hsv[..., 1]

    allowed = np.zeros((h, w), dtype=np.uint8)
    hard_polygon(
        allowed,
        [(1160, 300), (1618, 270), (1845, 604), (1848, 822), (1718, 1060), (1605, 1308), (1486, 1302), (1300, 1012), (1046, 930), (1078, 768)],
        255,
    )
    cv2.line(allowed, (1515, 388), (1262, 805), 255, 132)
    cv2.line(allowed, (1372, 548), (1110, 960), 255, 124)
    cv2.line(allowed, (1650, 392), (1552, 900), 255, 126)
    allowed = cv2.dilate(allowed, np.ones((13, 13), np.uint8), iterations=1)

    grab = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)
    grab[allowed > 0] = cv2.GC_PR_FGD

    # Very white, low-difference pixels are snow, even when they sit inside the
    # broad allowed band around the character. This is the key step that removes
    # the visible white halo from the previous cut.
    snow_bg = (allowed > 0) & (luma > 230) & (saturation < 18) & (diff < 18)
    grab[snow_bg] = cv2.GC_BGD

    fg_seed = np.zeros((h, w), dtype=np.uint8)
    fg_seed[(allowed > 0) & ((luma < 212) | (saturation > 30) | (diff > 31))] = 255
    hard_polygon(fg_seed, [(1434, 540), (1600, 468), (1730, 650), (1695, 1025), (1584, 1122), (1438, 1044), (1364, 720)], 255)
    cv2.ellipse(fg_seed, (1558, 394), (94, 86), -8, 0, 360, 255, -1)
    cv2.line(fg_seed, (1514, 420), (1292, 795), 255, 72)
    cv2.line(fg_seed, (1646, 420), (1565, 900), 255, 70)
    cv2.line(fg_seed, (1422, 628), (1268, 790), 255, 72)
    cv2.line(fg_seed, (1712, 642), (1812, 790), 255, 68)
    cv2.line(fg_seed, (1532, 1036), (1538, 1248), 255, 56)
    cv2.line(fg_seed, (1608, 1036), (1564, 1268), 255, 58)
    fg_seed = cv2.bitwise_and(fg_seed, allowed)
    grab[fg_seed > 0] = cv2.GC_FGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(image_bgr, grab, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)

    raw_person = np.where((grab == cv2.GC_FGD) | (grab == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    raw_person = cv2.bitwise_and(raw_person, allowed)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(raw_person, 8)
    keep = np.zeros_like(raw_person)
    seed_overlap = cv2.dilate(fg_seed, np.ones((9, 9), np.uint8), iterations=1)
    for idx in range(1, count):
        area = stats[idx, cv2.CC_STAT_AREA]
        if area < 50:
            continue
        component = labels == idx
        if np.any(seed_overlap[component] > 0):
            keep[component] = 255

    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    solid = cv2.erode(keep, np.ones((3, 3), np.uint8), iterations=1).astype(np.float32)
    feather = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.15)
    person_alpha = np.maximum(solid, feather * 0.82)
    person_alpha = np.clip(person_alpha, 0, 255)

    rim = (person_alpha > 0) & (person_alpha < 210) & (luma > 224) & (saturation < 22) & (diff < 24)
    person_alpha[rim] *= 0.06
    person_alpha[person_alpha < 8] = 0

    person_rgb = original.copy()
    fringe = (person_alpha > 0) & (person_alpha < 190)
    person_rgb[fringe] = person_rgb[fringe] * 0.84 + np.array([82, 128, 150], dtype=np.float32) * 0.16

    shadow_region = make_shadow_region((h, w)).astype(np.float32) / 255.0
    dark_delta = np.maximum(clean_luma - luma, 0)
    shadow_alpha = np.clip((dark_delta - 1.0) / 42.0, 0, 1) * 92
    shadow_alpha = np.maximum(shadow_alpha, shadow_region * 12)
    shadow_alpha = cv2.GaussianBlur(shadow_alpha.astype(np.float32), (0, 0), 5.0) * cv2.GaussianBlur(shadow_region, (0, 0), 7)
    shadow_alpha[person_alpha > 2] = 0
    shadow_alpha = np.clip(shadow_alpha, 0, 102)

    alpha = np.maximum(person_alpha, shadow_alpha).astype(np.uint8)
    foreground_rgb = np.zeros_like(original)
    foreground_rgb[shadow_alpha > person_alpha] = np.array([34, 61, 76], dtype=np.float32)
    foreground_rgb[person_alpha > 0] = person_rgb[person_alpha > 0]

    foreground_rgba = np.dstack([np.clip(foreground_rgb, 0, 255).astype(np.uint8), alpha])
    composite = clean * (1 - alpha[..., None] / 255.0) + foreground_rgb * (alpha[..., None] / 255.0)
    composite = np.clip(composite, 0, 255).astype(np.uint8)
    return foreground_rgba, alpha, composite


def make_v4_foreground(image_rgb, clean_rgb):
    h, w = image_rgb.shape[:2]
    original = image_rgb.astype(np.float32)
    clean = clean_rgb.astype(np.float32)
    luma = original[..., 0] * 0.2126 + original[..., 1] * 0.7152 + original[..., 2] * 0.0722
    clean_luma = clean[..., 0] * 0.2126 + clean[..., 1] * 0.7152 + clean[..., 2] * 0.0722

    person = np.zeros((h, w), dtype=np.uint8)

    def poly(points, value=255):
        hard_polygon(person, points, value)

    def line(points, width, value=255):
        pts = np.array(points, dtype=np.int32)
        cv2.polylines(person, [pts], False, value, width, lineType=cv2.LINE_AA)

    # Head, scarf, coat body.
    cv2.ellipse(person, (1558, 386), (96, 86), -8, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    poly([(1458, 464), (1638, 448), (1712, 558), (1652, 632), (1478, 622), (1408, 548)])
    poly([(1394, 558), (1566, 494), (1715, 650), (1732, 907), (1648, 1074), (1534, 1118), (1432, 1055), (1358, 884), (1320, 700)])
    cv2.ellipse(person, (1555, 797), (188, 326), -7, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    poly([(1376, 916), (1716, 918), (1680, 1064), (1465, 1088), (1368, 1018)])

    # Sleeves and hands.
    line([(1408, 642), (1306, 715), (1234, 792)], 88)
    line([(1698, 642), (1764, 714), (1832, 789)], 86)
    cv2.ellipse(person, (1220, 802), (38, 28), 28, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    cv2.ellipse(person, (1842, 794), (36, 24), -34, 0, 360, 255, -1, lineType=cv2.LINE_AA)

    # Hair is drawn as strokes instead of a broad fill, so the snowy gaps stay
    # transparent.
    line([(1518, 420), (1455, 532), (1382, 674), (1284, 804), (1174, 934)], 68)
    line([(1405, 560), (1335, 728), (1268, 894), (1175, 1012)], 52)
    line([(1168, 930), (1112, 1032), (1045, 965)], 60)
    line([(1605, 430), (1605, 584), (1572, 744), (1532, 902)], 74)
    line([(1544, 522), (1542, 682), (1508, 842), (1426, 1002)], 58)
    line([(1664, 425), (1660, 568), (1648, 704)], 56)
    line([(1548, 308), (1582, 258), (1584, 325)], 18)
    line([(1632, 330), (1682, 294), (1665, 352)], 18)

    # Legs, boots, and compact foreground snow immediately under the feet.
    line([(1517, 1022), (1528, 1155), (1508, 1262)], 62)
    line([(1612, 1020), (1588, 1158), (1570, 1272)], 64)
    cv2.ellipse(person, (1505, 1265), (43, 64), -24, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    cv2.ellipse(person, (1572, 1272), (42, 68), 18, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    poly([(1465, 1248), (1642, 1232), (1646, 1392), (1510, 1438), (1418, 1340)])
    cv2.ellipse(person, (1518, 1430), (68, 52), -8, 0, 360, 255, -1, lineType=cv2.LINE_AA)

    # Carve out the largest snow gaps that were previously stuck to the cutout.
    holes = np.zeros_like(person)
    hard_polygon(holes, [(1194, 690), (1362, 604), (1415, 690), (1300, 852), (1166, 940), (1106, 905)], 255)
    hard_polygon(holes, [(1726, 680), (1830, 804), (1748, 861), (1684, 748)], 255)
    hard_polygon(holes, [(1266, 796), (1366, 752), (1398, 926), (1300, 1005), (1194, 950)], 255)
    holes = cv2.dilate(holes, np.ones((7, 7), np.uint8), iterations=1)
    person[holes > 0] = 0

    person = cv2.morphologyEx(person, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    person_alpha = cv2.GaussianBlur(person.astype(np.float32), (0, 0), 0.85)
    person_alpha[person > 0] = np.maximum(person_alpha[person > 0], 232)
    person_alpha[person_alpha < 8] = 0

    # Knock back any remaining near-white rim that is not part of the solid coat.
    diff = np.mean(np.abs(original - clean), axis=2)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation = hsv[..., 1]
    rim = (person_alpha > 0) & (person_alpha < 226) & (luma > 226) & (saturation < 20) & (diff < 20)
    person_alpha[rim] *= 0.08
    person_alpha[person_alpha < 8] = 0

    person_rgb = original.copy()
    fringe = (person_alpha > 0) & (person_alpha < 210)
    person_rgb[fringe] = person_rgb[fringe] * 0.86 + np.array([76, 124, 148], dtype=np.float32) * 0.14

    shadow_region = make_shadow_region((h, w)).astype(np.float32) / 255.0
    dark_delta = np.maximum(clean_luma - luma, 0)
    shadow_alpha = np.clip((dark_delta - 1.0) / 44.0, 0, 1) * 78
    shadow_alpha = np.maximum(shadow_alpha, shadow_region * 10)
    shadow_alpha = cv2.GaussianBlur(shadow_alpha.astype(np.float32), (0, 0), 6.0) * cv2.GaussianBlur(shadow_region, (0, 0), 8)
    shadow_alpha[person_alpha > 2] = 0
    shadow_alpha = np.clip(shadow_alpha, 0, 88)

    alpha = np.maximum(person_alpha, shadow_alpha).astype(np.uint8)
    foreground_rgb = np.zeros_like(original)
    foreground_rgb[shadow_alpha > person_alpha] = np.array([24, 45, 58], dtype=np.float32)
    foreground_rgb[person_alpha > 0] = person_rgb[person_alpha > 0]

    foreground_rgba = np.dstack([np.clip(foreground_rgb, 0, 255).astype(np.uint8), alpha])
    composite = clean * (1 - alpha[..., None] / 255.0) + foreground_rgb * (alpha[..., None] / 255.0)
    composite = np.clip(composite, 0, 255).astype(np.uint8)
    return foreground_rgba, alpha, composite


def make_v5_foreground(image_rgb, clean_rgb):
    rembg_path = OUT / "p2-rembg-anime-test.png"
    if not rembg_path.exists():
        raise FileNotFoundError(f"Missing {rembg_path}; generate it with rembg isnet-anime first.")

    h, w = image_rgb.shape[:2]
    original = image_rgb.astype(np.float32)
    clean = clean_rgb.astype(np.float32)
    rembg = np.array(Image.open(rembg_path).convert("RGBA"))

    person_alpha = rembg[..., 3].astype(np.float32)
    person_alpha = cv2.GaussianBlur(person_alpha, (0, 0), 0.45)
    person_alpha[person_alpha < 5] = 0

    luma = original[..., 0] * 0.2126 + original[..., 1] * 0.7152 + original[..., 2] * 0.0722
    clean_luma = clean[..., 0] * 0.2126 + clean[..., 1] * 0.7152 + clean[..., 2] * 0.0722
    diff = np.mean(np.abs(original - clean), axis=2)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation = hsv[..., 1]

    # Restore the small snow contact/foot trail that belongs to the walking
    # figure, but keep it compact so it does not become a white halo.
    contact_region = np.zeros((h, w), dtype=np.uint8)
    hard_polygon(contact_region, [(1452, 1202), (1632, 1214), (1664, 1458), (1512, 1524), (1388, 1382)], 255)
    cv2.ellipse(contact_region, (1510, 1395), (110, 170), -14, 0, 360, 255, -1)
    contact_signal = np.clip((diff - 4.0) / 28.0, 0, 1)
    contact_alpha = cv2.GaussianBlur((contact_region.astype(np.float32) / 255.0 * contact_signal * 170).astype(np.float32), (0, 0), 1.4)
    contact_alpha[(luma > 248) & (diff < 8)] *= 0.2

    shadow_region = make_shadow_region((h, w)).astype(np.float32) / 255.0
    dark_delta = np.maximum(clean_luma - luma, 0)
    shadow_alpha = np.clip((dark_delta - 1.0) / 42.0, 0, 1) * 88
    shadow_alpha = np.maximum(shadow_alpha, shadow_region * 9)
    shadow_alpha = cv2.GaussianBlur(shadow_alpha.astype(np.float32), (0, 0), 5.6) * cv2.GaussianBlur(shadow_region, (0, 0), 8)
    shadow_alpha[person_alpha > 4] = 0
    shadow_alpha[contact_alpha > 50] *= 0.45
    shadow_alpha = np.clip(shadow_alpha, 0, 92)

    person_rgb = rembg[..., :3].astype(np.float32)
    # Slightly neutralize bright matte fringe while preserving the model cut.
    fringe = (person_alpha > 0) & (person_alpha < 190) & (luma > 210) & (saturation < 30)
    person_rgb[fringe] = person_rgb[fringe] * 0.9 + np.array([72, 120, 145], dtype=np.float32) * 0.1

    alpha = np.maximum.reduce([person_alpha, contact_alpha, shadow_alpha]).astype(np.uint8)
    foreground_rgb = np.zeros_like(original)
    foreground_rgb[shadow_alpha > np.maximum(person_alpha, contact_alpha)] = np.array([23, 42, 54], dtype=np.float32)
    foreground_rgb[contact_alpha > np.maximum(person_alpha, shadow_alpha)] = original[contact_alpha > np.maximum(person_alpha, shadow_alpha)]
    foreground_rgb[person_alpha > 0] = person_rgb[person_alpha > 0]

    foreground_rgba = np.dstack([np.clip(foreground_rgb, 0, 255).astype(np.uint8), alpha])
    composite = clean * (1 - alpha[..., None] / 255.0) + foreground_rgb * (alpha[..., None] / 255.0)
    composite = np.clip(composite, 0, 255).astype(np.uint8)
    return foreground_rgba, alpha, composite


def save_foreground_version(name, image_rgb, clean_rgb, foreground_rgba, alpha, composite, pad=96):
    h, w = alpha.shape
    full_path = OUT / f"p2-person-shadow-full-{name}.png"
    crop_path = OUT / f"p2-person-shadow-crop-{name}.png"
    mask_path = OUT / f"p2-person-shadow-alpha-check-{name}.png"
    contact_path = OUT / f"p2-layer-contact-check-{name}.jpg"
    checker_path = OUT / f"p2-foreground-checker-{name}.jpg"

    Image.fromarray(foreground_rgba).save(full_path)
    Image.fromarray(alpha).save(mask_path)

    ys, xs = np.where(alpha > 3)
    left = max(0, xs.min() - pad)
    top = max(0, ys.min() - pad)
    right = min(w, xs.max() + pad + 1)
    bottom = min(h, ys.max() + pad + 1)
    Image.fromarray(foreground_rgba[top:bottom, left:right]).save(crop_path)

    checker = np.zeros_like(image_rgb)
    tile = 48
    for yy in range(0, h, tile):
        for xx in range(0, w, tile):
            checker[yy : yy + tile, xx : xx + tile] = (222, 238, 247) if ((xx // tile + yy // tile) % 2) else (248, 252, 255)
    a = alpha.astype(np.float32) / 255.0
    checker_comp = checker.astype(np.float32) * (1 - a[..., None]) + foreground_rgba[..., :3].astype(np.float32) * a[..., None]
    Image.fromarray(np.clip(checker_comp, 0, 255).astype(np.uint8)).save(checker_path, quality=94, subsampling=0)

    panel_w = 886
    panel_h = round(image_rgb.shape[0] * panel_w / image_rgb.shape[1])
    panels = []
    labels = ["original p2", "clean snowfield v1", f"{name} foreground over clean bg"]
    for arr in (image_rgb, clean_rgb, composite):
        panels.append(Image.fromarray(arr).resize((panel_w, panel_h), Image.Resampling.LANCZOS))
    sheet = Image.new("RGB", (panel_w * 3, panel_h + 52), (238, 248, 252))
    draw = ImageDraw.Draw(sheet)
    for idx, panel in enumerate(panels):
        x = idx * panel_w
        sheet.paste(panel, (x, 52))
        draw.text((x + 22, 16), labels[idx], fill=(43, 92, 126))
    sheet.save(contact_path, quality=94, subsampling=0)

    print(full_path)
    print(crop_path)
    print(mask_path)
    print(contact_path)
    print(checker_path)
    print(f"{name}_crop_box={left},{top},{right},{bottom}")


def create_layers():
    OUT.mkdir(parents=True, exist_ok=True)

    image_rgb = np.array(Image.open(SRC).convert("RGB"))
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    h, w = image_rgb.shape[:2]

    person = make_person_mask(image_bgr)
    shadow_region = make_shadow_region((h, w))

    inpaint_mask = cv2.dilate(person, np.ones((35, 35), np.uint8), iterations=1)
    inpaint_mask = cv2.bitwise_or(inpaint_mask, shadow_region)
    inpaint_mask = cv2.GaussianBlur(inpaint_mask, (0, 0), 3)
    inpaint_mask = np.where(inpaint_mask > 18, 255, 0).astype(np.uint8)

    clean_bgr = cv2.inpaint(image_bgr, inpaint_mask, 17, cv2.INPAINT_TELEA)
    feather = blur_mask(inpaint_mask, 10) / 255.0
    clean_rgb = cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    original = image_rgb.astype(np.float32)
    clean_rgb = original * (1 - feather[..., None]) + clean_rgb * feather[..., None]
    clean_rgb = np.clip(clean_rgb, 0, 255).astype(np.uint8)

    orig_luma = (original[..., 0] * 0.2126 + original[..., 1] * 0.7152 + original[..., 2] * 0.0722)
    clean_luma = (clean_rgb[..., 0] * 0.2126 + clean_rgb[..., 1] * 0.7152 + clean_rgb[..., 2] * 0.0722)
    dark_delta = np.maximum(clean_luma - orig_luma, 0)

    shadow_soft = blur_mask(shadow_region, 18) / 255.0
    shadow_alpha = np.clip((dark_delta - 1.0) / 58.0, 0, 1) * 132
    shadow_alpha = np.maximum(shadow_alpha, shadow_soft * 12)
    shadow_alpha = cv2.GaussianBlur(shadow_alpha.astype(np.float32), (0, 0), 5) * shadow_soft
    shadow_alpha = np.clip(shadow_alpha, 0, 148)

    person_alpha = blur_mask(person, 1.05)
    person_alpha = np.where(person > 0, np.maximum(person_alpha, 235), person_alpha)

    alpha = np.maximum(shadow_alpha, person_alpha)
    alpha = np.clip(alpha, 0, 255).astype(np.uint8)

    foreground_rgb = np.zeros_like(original)
    a = np.clip(alpha.astype(np.float32) / 255.0, 0.001, 1.0)
    solved_shadow = (original - (1.0 - a[..., None]) * clean_rgb.astype(np.float32)) / a[..., None]
    foreground_rgb = np.clip(solved_shadow, 0, 255)
    foreground_rgb[person_alpha > 18] = original[person_alpha > 18]
    foreground_rgba = np.dstack([foreground_rgb.astype(np.uint8), alpha])

    clean_path = OUT / "p2-clean-snowfield-v1.jpg"
    full_path = OUT / "p2-person-shadow-full-v1.png"
    mask_path = OUT / "p2-person-shadow-alpha-check-v1.png"
    crop_path = OUT / "p2-person-shadow-crop-v1.png"
    contact_path = OUT / "p2-layer-contact-check-v1.jpg"

    Image.fromarray(clean_rgb).save(clean_path, quality=96, subsampling=0)
    Image.fromarray(foreground_rgba).save(full_path)
    Image.fromarray(alpha).save(mask_path)

    ys, xs = np.where(alpha > 3)
    pad = 96
    left = max(0, xs.min() - pad)
    top = max(0, ys.min() - pad)
    right = min(w, xs.max() + pad + 1)
    bottom = min(h, ys.max() + pad + 1)
    Image.fromarray(foreground_rgba[top:bottom, left:right]).save(crop_path)

    composite = clean_rgb.astype(np.float32) * (1 - alpha[..., None] / 255.0) + foreground_rgb * (alpha[..., None] / 255.0)
    composite = np.clip(composite, 0, 255).astype(np.uint8)

    panel_w = 886
    panel_h = round(h * panel_w / w)
    panels = []
    labels = ["original p2", "clean snowfield", "foreground over clean bg"]
    for arr in (image_rgb, clean_rgb, composite):
        panels.append(Image.fromarray(arr).resize((panel_w, panel_h), Image.Resampling.LANCZOS))

    sheet = Image.new("RGB", (panel_w * 3, panel_h + 52), (238, 248, 252))
    draw = ImageDraw.Draw(sheet)
    for idx, panel in enumerate(panels):
        x = idx * panel_w
        sheet.paste(panel, (x, 52))
        draw.text((x + 22, 16), labels[idx], fill=(43, 92, 126))
    sheet.save(contact_path, quality=94, subsampling=0)

    print(clean_path)
    print(full_path)
    print(crop_path)
    print(mask_path)
    print(contact_path)
    print(f"crop_box={left},{top},{right},{bottom}")

    v2_rgba, v2_alpha, v2_composite = make_v2_foreground(image_rgb, clean_rgb)
    v2_full_path = OUT / "p2-person-shadow-full-v2.png"
    v2_crop_path = OUT / "p2-person-shadow-crop-v2.png"
    v2_mask_path = OUT / "p2-person-shadow-alpha-check-v2.png"
    v2_contact_path = OUT / "p2-layer-contact-check-v2.jpg"
    v2_checker_path = OUT / "p2-foreground-checker-v2.jpg"

    Image.fromarray(v2_rgba).save(v2_full_path)
    Image.fromarray(v2_alpha).save(v2_mask_path)

    ys2, xs2 = np.where(v2_alpha > 3)
    left2 = max(0, xs2.min() - pad)
    top2 = max(0, ys2.min() - pad)
    right2 = min(w, xs2.max() + pad + 1)
    bottom2 = min(h, ys2.max() + pad + 1)
    Image.fromarray(v2_rgba[top2:bottom2, left2:right2]).save(v2_crop_path)

    checker = np.zeros_like(image_rgb)
    tile = 48
    for yy in range(0, h, tile):
        for xx in range(0, w, tile):
            checker[yy : yy + tile, xx : xx + tile] = (222, 238, 247) if ((xx // tile + yy // tile) % 2) else (248, 252, 255)
    a2 = v2_alpha.astype(np.float32) / 255.0
    checker_comp = checker.astype(np.float32) * (1 - a2[..., None]) + v2_rgba[..., :3].astype(np.float32) * a2[..., None]
    Image.fromarray(np.clip(checker_comp, 0, 255).astype(np.uint8)).save(v2_checker_path, quality=94, subsampling=0)

    panels_v2 = []
    labels_v2 = ["original p2", "clean snowfield v1", "v2 foreground over clean bg"]
    for arr in (image_rgb, clean_rgb, v2_composite):
        panels_v2.append(Image.fromarray(arr).resize((panel_w, panel_h), Image.Resampling.LANCZOS))
    sheet_v2 = Image.new("RGB", (panel_w * 3, panel_h + 52), (238, 248, 252))
    draw_v2 = ImageDraw.Draw(sheet_v2)
    for idx, panel in enumerate(panels_v2):
        x = idx * panel_w
        sheet_v2.paste(panel, (x, 52))
        draw_v2.text((x + 22, 16), labels_v2[idx], fill=(43, 92, 126))
    sheet_v2.save(v2_contact_path, quality=94, subsampling=0)

    print(v2_full_path)
    print(v2_crop_path)
    print(v2_mask_path)
    print(v2_contact_path)
    print(v2_checker_path)
    print(f"v2_crop_box={left2},{top2},{right2},{bottom2}")

    v3_rgba, v3_alpha, v3_composite = make_v3_foreground(image_rgb, clean_rgb)
    save_foreground_version("v3", image_rgb, clean_rgb, v3_rgba, v3_alpha, v3_composite, pad=96)

    v4_rgba, v4_alpha, v4_composite = make_v4_foreground(image_rgb, clean_rgb)
    save_foreground_version("v4", image_rgb, clean_rgb, v4_rgba, v4_alpha, v4_composite, pad=96)

    v5_rgba, v5_alpha, v5_composite = make_v5_foreground(image_rgb, clean_rgb)
    save_foreground_version("v5", image_rgb, clean_rgb, v5_rgba, v5_alpha, v5_composite, pad=96)


if __name__ == "__main__":
    create_layers()
