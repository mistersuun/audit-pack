"""
Utility to fetch tomorrow's detailed weather for Laval, QC and render a
weather card image replicating the MétéoMédia detailed forecast style.

Uses Open-Meteo API (free, no API key required).
Returns 4 time periods: Matin, Après-midi, Soir, Nuit — each with
temperature, feels-like, conditions, wind, gusts, humidity, precipitation %.
"""

import json
import io
import math
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont


# ─── WMO Weather codes → French descriptions + icon type ───
WMO_CODES = {
    0:  ("Ciel dégagé",                     "sun"),
    1:  ("Principalement dégagé",            "sun"),
    2:  ("Partiellement nuageux",            "sun_cloud"),
    3:  ("Couvert",                          "cloud"),
    45: ("Brouillard",                       "fog"),
    48: ("Brouillard givrant",               "fog"),
    51: ("Bruine légère",                    "drizzle"),
    53: ("Bruine modérée",                   "drizzle"),
    55: ("Bruine forte",                     "drizzle"),
    56: ("Bruine verglaçante",               "freezing_rain"),
    57: ("Bruine verglaçante forte",         "freezing_rain"),
    61: ("Pluie légère",                     "rain"),
    63: ("Pluie modérée",                    "rain"),
    65: ("Pluie forte",                      "rain"),
    66: ("Pluie verglaçante",                "freezing_rain"),
    67: ("Pluie verglaçante forte",          "freezing_rain"),
    71: ("Neige légère",                     "snow_light"),
    73: ("Neige modérée",                    "snow"),
    75: ("Neige forte",                      "snow"),
    77: ("Grains de neige",                  "snow_light"),
    80: ("Averses légères",                  "shower"),
    81: ("Averses modérées",                 "shower"),
    82: ("Averses violentes",                "shower"),
    85: ("Averses de neige",                 "snow"),
    86: ("Averses de neige fortes",          "snow"),
    95: ("Orage",                            "storm"),
    96: ("Orage avec grêle",                 "storm"),
    99: ("Orage avec grêle forte",           "storm"),
}

SNOW_CODES = {71, 73, 75, 77, 85, 86}

DAYS_FR = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']
DAYS_FR_FULL = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
MONTHS_FR = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
             'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
MONTHS_FR_FULL = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

PERIODS = [
    ("Matin",       6, 12),
    ("Après-midi", 12, 18),
    ("Soir",       18, 24),
    ("Nuit",        0,  6),
]


def _wind_direction_fr(degrees):
    if degrees is None:
        return ""
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
    idx = round(degrees / 45) % 8
    return dirs[idx]


def fetch_tomorrow_weather(target_date=None):
    """
    Fetch hourly weather for Laval, QC using Open-Meteo.
    target_date: a datetime object or 'YYYY-MM-DD' string for the date to fetch.
                 Defaults to tomorrow if not provided.
    """
    try:
        if target_date is None:
            target_dt = datetime.now() + timedelta(days=1)
        elif isinstance(target_date, str):
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        else:
            target_dt = target_date

        date_str = target_dt.strftime('%Y-%m-%d')

        url = (
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=45.5833&longitude=-73.75'
            '&hourly=temperature_2m,apparent_temperature,weathercode,'
            'windspeed_10m,winddirection_10m,windgusts_10m,'
            'relativehumidity_2m,precipitation_probability,snowfall'
            '&daily=temperature_2m_max,temperature_2m_min,weathercode,'
            'precipitation_sum,windspeed_10m_max'
            '&timezone=America/Toronto'
            f'&start_date={date_str}&end_date={date_str}'
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'SheratonAudit/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())

        hourly = data['hourly']
        daily = data.get('daily', {})

        periods = []
        for label, h_start, h_end in PERIODS:
            temps, feels, codes, winds, dirs, gusts, humids, probs, snows = \
                [], [], [], [], [], [], [], [], []

            for i, time_str in enumerate(hourly['time']):
                hour = int(time_str.split('T')[1].split(':')[0])
                if h_start < h_end:
                    in_period = h_start <= hour < h_end
                else:
                    in_period = hour >= h_start or hour < h_end

                if in_period:
                    temps.append(hourly['temperature_2m'][i])
                    feels.append(hourly['apparent_temperature'][i])
                    codes.append(hourly['weathercode'][i])
                    winds.append(hourly['windspeed_10m'][i])
                    dirs.append(hourly['winddirection_10m'][i])
                    gusts.append(hourly['windgusts_10m'][i])
                    humids.append(hourly['relativehumidity_2m'][i])
                    probs.append(hourly['precipitation_probability'][i])
                    snows.append(hourly['snowfall'][i])

            if not temps:
                continue

            avg_temp = round(sum(temps) / len(temps))
            avg_feels = round(sum(feels) / len(feels))
            avg_wind = round(sum(winds) / len(winds))
            max_gust = round(max(gusts))
            avg_humid = round(sum(humids) / len(humids))
            max_prob = round(max(probs))
            total_snow = round(sum(snows), 1)

            code_counts = Counter(codes)
            dominant_code = code_counts.most_common(1)[0][0]
            desc, icon_type = WMO_CODES.get(dominant_code, ("Inconnu", "cloud"))

            avg_dir_deg = sum(dirs) / len(dirs) if dirs else 0
            wind_dir = _wind_direction_fr(avg_dir_deg)

            has_snow = any(c in SNOW_CODES for c in codes)
            snow_cm = total_snow if has_snow else 0

            # Night icons
            if label in ('Nuit', 'Soir') and icon_type == 'sun':
                icon_type = 'night_clear'
            elif label in ('Nuit', 'Soir') and icon_type == 'sun_cloud':
                icon_type = 'night_cloud'

            periods.append({
                'label': label,
                'temp': avg_temp,
                'feels_like': avg_feels,
                'description': desc,
                'weather_code': dominant_code,
                'icon_type': icon_type,
                'wind_kmh': avg_wind,
                'wind_dir': wind_dir,
                'gusts_kmh': max_gust,
                'humidity': avg_humid,
                'precip_prob': max_prob,
                'snow_cm': snow_cm,
            })

        daily_max = round(daily['temperature_2m_max'][0]) if daily.get('temperature_2m_max') else None
        daily_min = round(daily['temperature_2m_min'][0]) if daily.get('temperature_2m_min') else None
        daily_code = daily['weathercode'][0] if daily.get('weathercode') else 0
        daily_precip = round(daily['precipitation_sum'][0], 1) if daily.get('precipitation_sum') else 0
        daily_wind = round(daily['windspeed_10m_max'][0]) if daily.get('windspeed_10m_max') else 0

        return {
            'date': date_str,
            'date_obj': target_dt,
            'day_name': DAYS_FR_FULL[target_dt.weekday()],
            'day_short': DAYS_FR[target_dt.weekday()],
            'day_num': target_dt.day,
            'month_name': MONTHS_FR_FULL[target_dt.month - 1],
            'month_short': MONTHS_FR[target_dt.month - 1],
            'year': target_dt.year,
            'temp_max': daily_max,
            'temp_min': daily_min,
            'description': WMO_CODES.get(daily_code, ("Inconnu", "cloud"))[0],
            'precipitation_mm': daily_precip,
            'wind_max_kmh': daily_wind,
            'periods': periods,
        }

    except Exception as e:
        print(f"Error fetching weather from Open-Meteo: {e}")
        import traceback
        traceback.print_exc()
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Rendering — Exact MétéoMédia replica
# ═══════════════════════════════════════════════════════════════════════════════

# Colors sampled from the actual MétéoMédia screenshots
BG           = (25, 35, 52)
HEADER_BG    = (18, 26, 40)
ROW_BG_A     = (32, 44, 65)
ROW_BG_B     = (25, 35, 52)
BORDER       = (45, 58, 80)
WHITE        = (255, 255, 255)
GREY_TEXT    = (160, 172, 190)
LABEL_GREY   = (120, 135, 158)
DATE_YELLOW  = (200, 195, 175)
SUN_BODY     = (255, 200, 40)
SUN_GLOW     = (255, 230, 100)
CLOUD_FILL   = (190, 200, 218)
CLOUD_SHADOW = (140, 155, 178)
RAIN_DROP    = (90, 170, 255)
SNOW_DOT     = (210, 225, 245)
MOON_FILL    = (230, 230, 200)
MOON_SHADOW  = (200, 200, 170)
BOLT_COLOR   = (255, 240, 80)
FOG_LINE     = (160, 175, 195)
STAR_GREEN   = (100, 190, 100)
BLUE_LINK    = (100, 180, 255)


# ─── Icon drawing functions ───

def _draw_sun(draw, cx, cy, r=18):
    """Full sun with rays."""
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + int((r + 3) * math.cos(rad))
        y1 = cy + int((r + 3) * math.sin(rad))
        x2 = cx + int((r + 9) * math.cos(rad))
        y2 = cy + int((r + 9) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=SUN_GLOW, width=3)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_BODY)


def _draw_small_sun(draw, cx, cy, r=12):
    """Smaller sun for behind-cloud combos."""
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + int((r + 2) * math.cos(rad))
        y1 = cy + int((r + 2) * math.sin(rad))
        x2 = cx + int((r + 6) * math.cos(rad))
        y2 = cy + int((r + 6) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=SUN_GLOW, width=2)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_BODY)


def _draw_cloud(draw, cx, cy, scale=1.0, dark=False):
    """Cloud shape made of overlapping ellipses."""
    s = scale
    color = CLOUD_SHADOW if dark else CLOUD_FILL
    # Bottom base
    draw.ellipse([int(cx - 22 * s), int(cy - 4 * s), int(cx + 22 * s), int(cy + 12 * s)], fill=color)
    # Left bump
    draw.ellipse([int(cx - 20 * s), int(cy - 14 * s), int(cx - 2 * s), int(cy + 4 * s)], fill=color)
    # Right bump (taller)
    draw.ellipse([int(cx - 6 * s), int(cy - 20 * s), int(cx + 16 * s), int(cy + 2 * s)], fill=color)
    # Fill gap
    draw.rectangle([int(cx - 18 * s), int(cy - 4 * s), int(cx + 18 * s), int(cy + 8 * s)], fill=color)


def _draw_rain(draw, cx, cy, drops=3):
    """Rain drops."""
    offsets = [(-12, 0), (0, 5), (12, 0)]
    for i in range(min(drops, len(offsets))):
        dx, dy = offsets[i]
        x = cx + dx
        y = cy + dy
        draw.line([(x, y), (x - 4, y + 10)], fill=RAIN_DROP, width=2)


def _draw_snow(draw, cx, cy, dots=4):
    """Snow dots/flakes."""
    offsets = [(-14, 0), (-4, 6), (6, 0), (14, 6)]
    for i in range(min(dots, len(offsets))):
        dx, dy = offsets[i]
        x, y = cx + dx, cy + dy
        # Small star
        for a in range(0, 360, 60):
            rad = math.radians(a)
            draw.line([(x, y), (x + int(3 * math.cos(rad)), y + int(3 * math.sin(rad)))],
                      fill=SNOW_DOT, width=1)
        draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=WHITE)


def _draw_moon(draw, cx, cy, r=15):
    """Crescent moon."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOON_FILL)
    # Darken a portion to create crescent
    draw.ellipse([cx - r + 7, cy - r - 3, cx + r + 7, cy + r - 3], fill=BG)


def _draw_bolt(draw, cx, cy):
    """Lightning bolt."""
    pts = [(cx - 1, cy - 12), (cx + 7, cy - 1), (cx + 2, cy - 1),
           (cx + 5, cy + 12), (cx - 5, cy + 2), (cx, cy + 2)]
    draw.polygon(pts, fill=BOLT_COLOR)


def _draw_fog(draw, cx, cy):
    """Fog as horizontal dashes."""
    for i in range(4):
        y = cy - 10 + i * 8
        w = 18 - abs(i - 1.5) * 4
        draw.line([(cx - int(w), y), (cx + int(w), y)], fill=FOG_LINE, width=3)


def draw_weather_icon(draw, cx, cy, icon_type):
    """Draw the weather icon at given center. Icon area is ~60x60."""
    if icon_type == 'sun':
        _draw_sun(draw, cx, cy)

    elif icon_type == 'sun_cloud':
        _draw_small_sun(draw, cx - 8, cy - 8)
        _draw_cloud(draw, cx + 6, cy + 6, scale=0.9)

    elif icon_type == 'cloud':
        _draw_cloud(draw, cx, cy, scale=1.1)

    elif icon_type == 'fog':
        _draw_fog(draw, cx, cy)

    elif icon_type == 'drizzle':
        _draw_cloud(draw, cx, cy - 8, scale=0.9, dark=True)
        _draw_rain(draw, cx, cy + 14, drops=2)

    elif icon_type == 'rain':
        _draw_cloud(draw, cx, cy - 8, scale=1.0, dark=True)
        _draw_rain(draw, cx, cy + 14, drops=3)

    elif icon_type == 'freezing_rain':
        _draw_cloud(draw, cx, cy - 8, scale=1.0, dark=True)
        _draw_rain(draw, cx - 6, cy + 14, drops=2)
        _draw_snow(draw, cx + 10, cy + 12, dots=2)

    elif icon_type == 'snow_light':
        _draw_cloud(draw, cx, cy - 8, scale=0.9)
        _draw_snow(draw, cx, cy + 14, dots=3)

    elif icon_type == 'snow':
        _draw_cloud(draw, cx, cy - 8, scale=1.0)
        _draw_snow(draw, cx, cy + 14, dots=4)

    elif icon_type == 'shower':
        _draw_small_sun(draw, cx - 10, cy - 12, r=9)
        _draw_cloud(draw, cx + 4, cy - 2, scale=0.85, dark=True)
        _draw_rain(draw, cx + 4, cy + 16, drops=2)

    elif icon_type == 'storm':
        _draw_cloud(draw, cx, cy - 10, scale=1.1, dark=True)
        _draw_bolt(draw, cx, cy + 10)

    elif icon_type == 'night_clear':
        _draw_moon(draw, cx, cy)

    elif icon_type == 'night_cloud':
        _draw_moon(draw, cx - 8, cy - 6, r=11)
        _draw_cloud(draw, cx + 6, cy + 6, scale=0.8)

    else:
        _draw_cloud(draw, cx, cy)


# ─── Small inline icons for wind/humidity/P.D.P. labels ───

def _draw_wind_icon(draw, x, y):
    """Small wind swirl icon."""
    # Three curved lines
    draw.arc([x, y, x + 14, y + 8], 180, 0, fill=GREY_TEXT, width=2)
    draw.arc([x + 2, y + 5, x + 16, y + 13], 180, 0, fill=GREY_TEXT, width=2)
    draw.arc([x, y + 10, x + 12, y + 18], 180, 0, fill=GREY_TEXT, width=2)


def _draw_gust_icon(draw, x, y):
    """Small gust/wind icon."""
    draw.arc([x, y + 2, x + 12, y + 10], 180, 0, fill=GREY_TEXT, width=2)
    draw.line([(x + 2, y + 8), (x + 16, y + 8)], fill=GREY_TEXT, width=2)
    draw.arc([x + 4, y + 8, x + 18, y + 16], 180, 0, fill=GREY_TEXT, width=2)


def _draw_humidity_icon(draw, x, y):
    """Small water droplet icon."""
    # Teardrop shape
    pts = [(x + 7, y), (x + 13, y + 10), (x + 7, y + 16), (x + 1, y + 10)]
    draw.polygon(pts, fill=RAIN_DROP)


def _draw_star_icon(draw, x, y, color=STAR_GREEN):
    """Small star/raindrop for P.D.P."""
    # Raindrop
    pts = [(x + 6, y), (x + 11, y + 9), (x + 6, y + 14), (x + 1, y + 9)]
    draw.polygon(pts, fill=color)


def _draw_snowflake_icon(draw, x, y):
    """Tiny snowflake icon."""
    cx, cy = x + 7, y + 7
    for a in range(0, 360, 60):
        rad = math.radians(a)
        draw.line([(cx, cy), (cx + int(6 * math.cos(rad)), cy + int(6 * math.sin(rad)))],
                  fill=BLUE_LINK, width=1)
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=WHITE)


# ─── Font loading ───

def _load_fonts():
    bold_path = reg_path = None
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        try:
            ImageFont.truetype(p, 10)
            bold_path = p
            break
        except Exception:
            pass
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        try:
            ImageFont.truetype(p, 10)
            reg_path = p
            break
        except Exception:
            pass

    def b(size):
        return ImageFont.truetype(bold_path, size) if bold_path else ImageFont.load_default()
    def r(size):
        return ImageFont.truetype(reg_path, size) if reg_path else ImageFont.load_default()
    return b, r


# ─── Main render ───

def render_weather_card(weather_data):
    """
    Renders a detailed weather card replicating the exact MétéoMédia layout.
    Structure per row (matching the reference screenshots):

      Matin
      [icon]  −6°  Ensoleillé avec passages nuageux    ⊙ Vents     23 km/h O    ★ P.D.P.  20%
                    T. ress −13                          ⊛ Rafales   39 km/h
                                                         ♨ Humidité  73%
    """
    if weather_data is None or not weather_data.get('periods'):
        return None

    B, R = _load_fonts()

    # ─── Dimensions (scaled up for landscape full-width) ───
    W = 1600
    ROW_H = 130
    HEADER_H = 45
    periods = weather_data['periods']
    H = HEADER_H + len(periods) * ROW_H + 30

    img = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ─── Column X positions ───
    X_PAD      = 25
    X_ICON     = 90       # center of weather icon
    X_TEMP     = 140      # temperature text left edge
    X_DESC     = 280      # description + T.ress
    X_WIND_SEC = 780      # wind section start (icon + Vents/Rafales/Humidité)
    X_WIND_VAL = 900      # wind values
    X_PDP_SEC  = 1250     # P.D.P. section
    X_PDP_VAL  = 1370     # P.D.P. percentage
    X_SNOW     = 1250     # snow info (below P.D.P.)

    # ─── Header ───
    draw.rectangle([0, 0, W, HEADER_H], fill=HEADER_BG)
    date_label = f"{weather_data['day_num']} {weather_data['month_short']} {weather_data['day_short']}"
    draw.text((X_PAD, 12), date_label, fill=DATE_YELLOW, font=B(19))

    y = HEADER_H

    for i, p in enumerate(periods):
        bg = ROW_BG_A if i % 2 == 0 else ROW_BG_B
        draw.rectangle([0, y, W, y + ROW_H], fill=bg)
        draw.line([(0, y), (W, y)], fill=BORDER, width=1)

        # ─── Period label (top-left) ───
        draw.text((X_PAD, y + 8), p['label'], fill=WHITE, font=B(20))

        # ─── Weather icon (centered vertically in row) ───
        icon_cy = y + ROW_H // 2 + 5
        draw_weather_icon(draw, X_ICON, icon_cy, p['icon_type'])

        # ─── Temperature (large) ───
        temp_str = f"−{abs(p['temp'])}°" if p['temp'] < 0 else f"{p['temp']}°"
        draw.text((X_TEMP, y + 30), temp_str, fill=WHITE, font=B(48))

        # ─── Description ───
        draw.text((X_DESC, y + 35), p['description'], fill=WHITE, font=R(21))

        # ─── T. ress (feels like) ───
        feels_str = f"T. ress {p['feels_like']}"
        draw.text((X_DESC, y + 68), feels_str, fill=GREY_TEXT, font=R(17))

        # ─── Wind section (3 stacked lines) ───
        line_y = y + 22

        # Line 1: Vents
        _draw_wind_icon(draw, X_WIND_SEC, line_y + 2)
        draw.text((X_WIND_SEC + 22, line_y), "Vents", fill=GREY_TEXT, font=R(17))
        draw.text((X_WIND_VAL, line_y), f"{p['wind_kmh']} km/h {p['wind_dir']}",
                  fill=WHITE, font=R(17))

        # Line 2: Rafales
        line_y += 30
        _draw_gust_icon(draw, X_WIND_SEC, line_y + 1)
        draw.text((X_WIND_SEC + 22, line_y), "Rafales", fill=GREY_TEXT, font=R(17))
        draw.text((X_WIND_VAL, line_y), f"{p['gusts_kmh']} km/h",
                  fill=WHITE, font=R(17))

        # Line 3: Humidité
        line_y += 30
        _draw_humidity_icon(draw, X_WIND_SEC, line_y)
        draw.text((X_WIND_SEC + 22, line_y), "Humidité", fill=GREY_TEXT, font=R(17))
        draw.text((X_WIND_VAL, line_y), f"{p['humidity']}%",
                  fill=WHITE, font=R(17))

        # ─── P.D.P. section (right side) ───
        pdp_y = y + 28
        _draw_star_icon(draw, X_PDP_SEC, pdp_y + 2)
        draw.text((X_PDP_SEC + 18, pdp_y), "P.D.P.", fill=GREY_TEXT, font=R(17))
        draw.text((X_PDP_VAL, pdp_y), f"{p['precip_prob']}%",
                  fill=WHITE, font=B(24))

        # Snow accumulation (below P.D.P.)
        if p['snow_cm'] > 0:
            snow_y = pdp_y + 38
            _draw_snowflake_icon(draw, X_SNOW, snow_y + 1)
            snow_txt = f"Neige  {'<1' if p['snow_cm'] < 1 else '~' + str(int(p['snow_cm']))}cm"
            draw.text((X_SNOW + 18, snow_y), snow_txt, fill=BLUE_LINK, font=R(16))

        y += ROW_H

    # ─── Bottom border ───
    draw.line([(0, y), (W, y)], fill=BORDER, width=1)

    # ─── Footer ───
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    draw.text((X_PAD, y + 8),
              f"Source: Open-Meteo.com (Environnement Canada) · Généré: {now_str}",
              fill=LABEL_GREY, font=R(13))

    return img


def get_weather_screenshot(target_date=None):
    """
    Main entry point — fetches weather for the given date and returns a PIL Image card.
    target_date: 'YYYY-MM-DD' string or datetime. Defaults to tomorrow.
    """
    weather_data = fetch_tomorrow_weather(target_date)
    if weather_data is None:
        return None
    return render_weather_card(weather_data)
