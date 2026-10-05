#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security alerts simulator for the course exam.

Run:   python simulator.py      (Windows: or double-click run.bat)
Stop:  Ctrl+C

No arguments and no installs are needed. Alerts are written to the "alerts"
folder next to this file. See README.md.

Do not change this file.
"""
# Keep this file parseable by old Pythons (no f-strings) so the version check
# below can print a clear message instead of a syntax error.
from __future__ import print_function

import sys

if sys.version_info < (3, 6):
    print("This simulator needs Python 3.6 or newer (you are running Python %d.%d)."
          % tuple(sys.version_info[:2]))
    sys.exit(1)

import datetime
import errno
import heapq
import json
import math
import os
import platform
import random
import re
import shutil
import signal
import time
import uuid
from collections import OrderedDict
from pathlib import Path

# ---------------------------------------------------------------------------
# Locations and timing
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
ALERTS_DIR = BASE_DIR / "alerts"
LOCK_FILE = BASE_DIR / ".simulator.lock"

AGENCIES = ("aman", "mossad", "pikud-haoref", "shabak")
ALERT_FOLDER_RE = re.compile(r"^\d{8}T\d{9}_\d{6}$")
JSON_NAME = "alert.json"
READY_NAME = "alert.ready"

BACKGROUND_GAP = (1.0, 3.0)        # seconds between regular alerts (~2 on average)
FIRST_INCIDENT = (15.0, 30.0)      # the first multi-alert incident comes early
INCIDENT_PAUSE = (15.0, 30.0)      # quiet time after an incident ends (one incident at a time)
STATUS_EVERY = 60.0                # console status line
SALVO_SIZE = (8, 20)
SALVO_SPREAD = (2.0, 4.0)          # a salvo is written over this many seconds
SLOW_WRITE_SECONDS = (0.2, 1.0)    # alert.json is written in chunks over this time
SLOW_WRITE_CHUNKS = (2, 5)
INVALID_RATE = 0.05
DUPLICATE_RATE = 0.03
DUPLICATE_DELAY = (5.0, 60.0)
JITTER_KM = 0.5                    # random offset around each place (regions keep a 2 km margin)

LOW_DISK_BYTES = 200 * 1024 * 1024
RESUME_DISK_BYTES = 300 * 1024 * 1024
DISK_CHECK_EVERY = 30.0

DIR_MODE = 0o777                   # open permissions: a watcher running as another
FILE_MODE = 0o666                  # user (e.g. Docker root vs. host user) can delete

UTC = datetime.timezone.utc

# ---------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------
# key, Hebrew name, lat, lon, region, zone, country, seconds to reach shelter (Israel only)
# zone: IL = Israel, ENTRY = Israeli entry point, GAZA / LB / SY = arenas, FAR = overseas.
# Every place is at least 2 km from any edge in regions.geojson (tests/check_regions.py).

_PLACE_ROWS = [
    # --- Israel, north
    ("Haifa", "חיפה", 32.794, 34.989, "NORTH", "IL", "IL", 60),
    ("Nahariya", "נהריה", 33.006, 35.095, "NORTH", "IL", "IL", 15),
    ("Akko", "עכו", 32.927, 35.083, "NORTH", "IL", "IL", 30),
    ("Karmiel", "כרמיאל", 32.919, 35.296, "NORTH", "IL", "IL", 30),
    ("Safed", "צפת", 32.965, 35.496, "NORTH", "IL", "IL", 30),
    ("Kiryat Shmona", "קריית שמונה", 33.207, 35.570, "NORTH", "IL", "IL", 15),
    ("Tiberias", "טבריה", 32.795, 35.531, "NORTH", "IL", "IL", 60),
    ("Katzrin", "קצרין", 32.990, 35.690, "NORTH", "IL", "IL", 30),
    ("Afula", "עפולה", 32.607, 35.289, "NORTH", "IL", "IL", 60),
    ("Nazareth", "נצרת", 32.700, 35.303, "NORTH", "IL", "IL", 60),
    ("Hadera", "חדרה", 32.434, 34.919, "NORTH", "IL", "IL", 90),
    ("Yokneam", "יקנעם", 32.659, 35.110, "NORTH", "IL", "IL", 60),
    ("Beit Shean", "בית שאן", 32.497, 35.497, "NORTH", "IL", "IL", 60),
    ("Kiryat Bialik", "קריית ביאליק", 32.838, 35.087, "NORTH", "IL", "IL", 60),
    ("Kiryat Ata", "קריית אתא", 32.806, 35.106, "NORTH", "IL", "IL", 60),
    ("Maalot-Tarshiha", "מעלות-תרשיחא", 33.016, 35.272, "NORTH", "IL", "IL", 30),
    ("Rosh Pina", "ראש פינה", 32.969, 35.543, "NORTH", "IL", "IL", 30),
    ("Migdal HaEmek", "מגדל העמק", 32.676, 35.241, "NORTH", "IL", "IL", 60),
    ("Shfaram", "שפרעם", 32.806, 35.170, "NORTH", "IL", "IL", 60),
    ("Zichron Yaakov", "זכרון יעקב", 32.572, 34.953, "NORTH", "IL", "IL", 90),
    ("Nof HaGalil", "נוף הגליל", 32.707, 35.327, "NORTH", "IL", "IL", 60),
    ("Sakhnin", "סחנין", 32.864, 35.297, "NORTH", "IL", "IL", 30),
    ("Kiryat Tivon", "קריית טבעון", 32.716, 35.125, "NORTH", "IL", "IL", 60),
    # --- Israel, center
    ("Tel Aviv", "תל אביב-יפו", 32.085, 34.781, "CENTER", "IL", "IL", 90),
    ("Jerusalem", "ירושלים", 31.768, 35.214, "CENTER", "IL", "IL", 90),
    ("Petah Tikva", "פתח תקווה", 32.087, 34.887, "CENTER", "IL", "IL", 90),
    ("Rishon LeZion", "ראשון לציון", 31.973, 34.789, "CENTER", "IL", "IL", 90),
    ("Holon", "חולון", 32.011, 34.772, "CENTER", "IL", "IL", 90),
    ("Netanya", "נתניה", 32.321, 34.853, "CENTER", "IL", "IL", 90),
    ("Herzliya", "הרצליה", 32.166, 34.844, "CENTER", "IL", "IL", 90),
    ("Kfar Saba", "כפר סבא", 32.175, 34.907, "CENTER", "IL", "IL", 90),
    ("Rehovot", "רחובות", 31.894, 34.811, "CENTER", "IL", "IL", 90),
    ("Modiin", "מודיעין", 31.898, 35.010, "CENTER", "IL", "IL", 90),
    ("Ramla", "רמלה", 31.929, 34.873, "CENTER", "IL", "IL", 90),
    ("Bnei Brak", "בני ברק", 32.084, 34.834, "CENTER", "IL", "IL", 90),
    ("Yavne", "יבנה", 31.878, 34.739, "CENTER", "IL", "IL", 90),
    ("Lod", "לוד", 31.951, 34.888, "CENTER", "IL", "IL", 90),
    ("Rosh HaAyin", "ראש העין", 32.095, 34.957, "CENTER", "IL", "IL", 90),
    ("Raanana", "רעננה", 32.184, 34.871, "CENTER", "IL", "IL", 90),
    ("Bat Yam", "בת ים", 32.017, 34.745, "CENTER", "IL", "IL", 90),
    ("Ramat Gan", "רמת גן", 32.068, 34.824, "CENTER", "IL", "IL", 90),
    ("Hod HaSharon", "הוד השרון", 32.150, 34.889, "CENTER", "IL", "IL", 90),
    ("Elad", "אלעד", 32.052, 34.951, "CENTER", "IL", "IL", 90),
    ("Mevaseret Zion", "מבשרת ציון", 31.802, 35.150, "CENTER", "IL", "IL", 90),
    ("Ness Ziona", "נס ציונה", 31.930, 34.799, "CENTER", "IL", "IL", 90),
    # --- Israel, south
    ("Sderot", "שדרות", 31.525, 34.596, "SOUTH", "IL", "IL", 15),
    ("Ashkelon", "אשקלון", 31.668, 34.574, "SOUTH", "IL", "IL", 30),
    ("Ashdod", "אשדוד", 31.804, 34.655, "SOUTH", "IL", "IL", 45),
    ("Netivot", "נתיבות", 31.420, 34.588, "SOUTH", "IL", "IL", 30),
    ("Ofakim", "אופקים", 31.314, 34.620, "SOUTH", "IL", "IL", 45),
    ("Beer Sheva", "באר שבע", 31.252, 34.791, "SOUTH", "IL", "IL", 60),
    ("Dimona", "דימונה", 31.070, 35.033, "SOUTH", "IL", "IL", 90),
    ("Arad", "ערד", 31.261, 35.215, "SOUTH", "IL", "IL", 90),
    ("Kiryat Gat", "קריית גת", 31.610, 34.764, "SOUTH", "IL", "IL", 45),
    ("Mitzpe Ramon", "מצפה רמון", 30.610, 34.801, "SOUTH", "IL", "IL", 90),
    ("Eilat", "אילת", 29.558, 34.948, "SOUTH", "IL", "IL", 90),
    ("Yeruham", "ירוחם", 30.988, 34.929, "SOUTH", "IL", "IL", 90),
    ("Kiryat Malakhi", "קריית מלאכי", 31.731, 34.746, "SOUTH", "IL", "IL", 45),
    ("Gan Yavne", "גן יבנה", 31.787, 34.706, "SOUTH", "IL", "IL", 45),
    ("Rahat", "רהט", 31.393, 34.754, "SOUTH", "IL", "IL", 60),
    ("Omer", "עומר", 31.265, 34.849, "SOUTH", "IL", "IL", 60),
    ("Lehavim", "להבים", 31.373, 34.816, "SOUTH", "IL", "IL", 60),
    ("Ein Gedi", "עין גדי", 31.460, 35.390, "SOUTH", "IL", "IL", 90),
    ("Neve Zohar", "נווה זוהר", 31.153, 35.366, "SOUTH", "IL", "IL", 90),
    ("Sde Boker", "שדה בוקר", 30.874, 34.793, "SOUTH", "IL", "IL", 90),
    # --- Israeli entry points (used only by the "hostile operative entry" alert; Eilat is also one)
    ("Ben Gurion Airport", "נמל התעופה בן גוריון", 32.009, 34.885, "CENTER", "ENTRY", "IL", 90),
    ("Haifa Port", "נמל חיפה", 32.820, 35.000, "NORTH", "ENTRY", "IL", 60),
    # --- Gaza Strip (south)
    ("Gaza City", "העיר עזה", 31.502, 34.466, "SOUTH", "GAZA", "GAZA", 0),
    ("Jabalia", "ג׳באליה", 31.528, 34.483, "SOUTH", "GAZA", "GAZA", 0),
    ("Deir al-Balah", "דיר אל-בלח", 31.418, 34.351, "SOUTH", "GAZA", "GAZA", 0),
    ("Khan Yunis", "ח׳אן יונס", 31.346, 34.306, "SOUTH", "GAZA", "GAZA", 0),
    # --- Lebanon (north)
    ("Beirut", "ביירות", 33.894, 35.502, "NORTH", "LB", "LB", 0),
    ("Tyre", "צור", 33.271, 35.204, "NORTH", "LB", "LB", 0),
    ("Nabatieh", "נבטייה", 33.378, 35.484, "NORTH", "LB", "LB", 0),
    ("Sidon", "צידון", 33.563, 35.371, "NORTH", "LB", "LB", 0),
    ("Tripoli (LB)", "טריפולי", 34.437, 35.850, "NORTH", "LB", "LB", 0),
    ("Baalbek", "בעלבכ", 34.006, 36.211, "NORTH", "LB", "LB", 0),
    # --- Syria (north)
    ("Damascus", "דמשק", 33.513, 36.292, "NORTH", "SY", "SY", 0),
    ("Daraa", "דרעא", 32.625, 36.106, "NORTH", "SY", "SY", 0),
    ("Quneitra", "קוניטרה", 33.126, 35.824, "NORTH", "SY", "SY", 0),
    ("Homs", "חומס", 34.733, 36.717, "NORTH", "SY", "SY", 0),
    ("Aleppo", "חלב", 36.202, 37.134, "NORTH", "SY", "SY", 0),
    ("Latakia", "לטקיה", 35.523, 35.792, "NORTH", "SY", "SY", 0),
    ("Palmyra", "תדמור", 34.560, 38.270, "NORTH", "SY", "SY", 0),
    ("Deir ez-Zor", "דיר א-זור", 35.336, 40.141, "NORTH", "SY", "SY", 0),
    # --- overseas
    ("Tehran", "טהרן", 35.689, 51.389, "OVERSEAS", "FAR", "IR", 0),
    ("Isfahan", "איספהאן", 32.652, 51.668, "OVERSEAS", "FAR", "IR", 0),
    ("Tabriz", "תבריז", 38.080, 46.292, "OVERSEAS", "FAR", "IR", 0),
    ("Bandar Abbas", "בנדר עבאס", 27.183, 56.267, "OVERSEAS", "FAR", "IR", 0),
    ("Baghdad", "בגדאד", 33.315, 44.366, "OVERSEAS", "FAR", "IQ", 0),
    ("Mosul", "מוסול", 36.340, 43.130, "OVERSEAS", "FAR", "IQ", 0),
    ("Basra", "בצרה", 30.508, 47.783, "OVERSEAS", "FAR", "IQ", 0),
    ("Sanaa", "צנעא", 15.369, 44.191, "OVERSEAS", "FAR", "YE", 0),
    ("Hodeidah", "חודיידה", 14.798, 42.954, "OVERSEAS", "FAR", "YE", 0),
    ("Istanbul", "איסטנבול", 41.008, 28.978, "OVERSEAS", "FAR", "TR", 0),
    ("Larnaca", "לרנקה", 34.917, 33.630, "OVERSEAS", "FAR", "CY", 0),
    ("Athens", "אתונה", 37.984, 23.728, "OVERSEAS", "FAR", "GR", 0),
    ("Cairo", "קהיר", 30.044, 31.236, "OVERSEAS", "FAR", "EG", 0),
    ("El Arish", "אל-עריש", 31.132, 33.803, "OVERSEAS", "FAR", "EG", 0),
    ("Amman", "עמאן", 31.954, 35.911, "OVERSEAS", "FAR", "JO", 0),
    ("Port Sudan", "פורט סודאן", 19.616, 37.216, "OVERSEAS", "FAR", "SD", 0),
]

COUNTRY_HE = {
    "IL": "ישראל", "GAZA": "רצועת עזה", "LB": "לבנון", "SY": "סוריה", "IR": "איראן",
    "IQ": "עיראק", "YE": "תימן", "TR": "טורקיה", "CY": "קפריסין", "GR": "יוון",
    "EG": "מצרים", "JO": "ירדן", "SD": "סודן",
}

COUNTRY_EN = {
    "IL": "Israel", "GAZA": "Gaza Strip", "LB": "Lebanon", "SY": "Syria", "IR": "Iran",
    "IQ": "Iraq", "YE": "Yemen", "TR": "Turkey", "CY": "Cyprus", "GR": "Greece",
    "EG": "Egypt", "JO": "Jordan", "SD": "Sudan",
}

PLACES = OrderedDict()
for _row in _PLACE_ROWS:
    _key, _he, _lat, _lon, _region, _zone, _country, _shelter = _row
    _name_en = _key.replace(" (LB)", "")
    PLACES[_key] = {
        "key": _key, "he": _he, "lat": _lat, "lon": _lon, "region": _region,
        "zone": _zone, "country": _country, "shelter": _shelter,
        # Name inside alert text (Hebrew) and in the console log (English, ASCII).
        # Foreign places also get their country.
        "where": _he if _country == "IL" else "%s, %s" % (_he, COUNTRY_HE[_country]),
        "en": _name_en if _country == "IL" else "%s, %s" % (_name_en, COUNTRY_EN[_country]),
    }


def _pick(pred):
    return [p for p in PLACES.values() if pred(p)]


def _keys(*keys):
    return [PLACES[k] for k in keys]


POOLS = {
    "IL_N": _pick(lambda p: p["zone"] == "IL" and p["region"] == "NORTH"),
    "IL_C": _pick(lambda p: p["zone"] == "IL" and p["region"] == "CENTER"),
    "IL_S": _pick(lambda p: p["zone"] == "IL" and p["region"] == "SOUTH"),
    "GAZA": _pick(lambda p: p["zone"] == "GAZA"),
    "LB": _pick(lambda p: p["zone"] == "LB"),
    "SY": _pick(lambda p: p["zone"] == "SY"),
    "ENTRY": _keys("Ben Gurion Airport", "Haifa Port", "Eilat"),
    "FAR_BALLISTIC": _keys("Tehran", "Isfahan", "Tabriz", "Sanaa", "Hodeidah"),
    "FAR_LAUNCH": _keys("Tehran", "Isfahan", "Tabriz", "Bandar Abbas", "Sanaa", "Hodeidah",
                        "Baghdad", "Mosul", "Basra"),
    "FAR_STRATEGIC": _keys("Tehran", "Isfahan", "Tabriz", "Bandar Abbas"),
    "FAR_SMUGGLE": _keys("Bandar Abbas", "Basra", "Baghdad", "Hodeidah", "Port Sudan", "El Arish"),
    "FAR_TRAVEL": _keys("Istanbul", "Larnaca", "Athens", "Cairo", "Amman"),
    "FAR_FINANCE": _keys("Istanbul", "Tehran", "Baghdad"),
    "FAR_ALL": _pick(lambda p: p["zone"] == "FAR"),
}
IL_ALL = (("IL_N", 1), ("IL_C", 1), ("IL_S", 1))
IL_CENTER_HEAVY = (("IL_N", 1), ("IL_C", 2), ("IL_S", 1))

# ---------------------------------------------------------------------------
# Alert catalog: 24 titles. The title fixes source, priority and classification.
# ---------------------------------------------------------------------------

VEHICLES = ("רכב פרטי", "טנדר", "אופנוע", "רכב מסחרי")
COLORS = ("לבן", "שחור", "כסוף", "אפור", "אדום", "כחול")


def _t_rocket_launch(rng, p):
    origin = "לבנון" if p["region"] == "NORTH" else "רצועת עזה"
    n = rng.randint(1, 30)
    if n == 1:
        return "זוהה שיגור אחד מ%s לעבר אזור %s. צפויות התרעות באזור." % (origin, p["where"])
    return "זוהו %d שיגורים מ%s לעבר אזור %s. צפויות התרעות באזור." % (n, origin, p["where"])


def _t_ballistic(rng, p):
    return ("זוהה שיגור טיל בליסטי מאזור %s לעבר ישראל. זמן מעוף משוער: %d דקות."
            % (p["where"], rng.randint(7, 12)))


def _t_launch_prep(rng, p):
    return "זוהו הכנות לשיגור באזור %s. זוהו %d משגרים בשטח." % (p["where"], rng.randint(2, 8))


def _t_uav(rng, p):
    return ("זוהה כלי טיס בלתי מאויש עוין בשמי %s, בגובה של כ-%d מטרים."
            % (p["where"], rng.randint(3, 30) * 100))


def _t_force_move(rng, p):
    return ("זוהתה תנועת כוחות חריגה באזור %s: כ-%d כלי רכב וכ-%d לוחמים."
            % (p["where"], rng.randint(3, 40), rng.randint(2, 30) * 10))


def _t_gps(rng, p):
    return ("דווחו שיבושי GPS באזור %s, ברדיוס של כ-%d קילומטרים. מערכות ניווט עלולות להציג מיקום שגוי."
            % (p["where"], rng.randint(5, 40)))


def _t_threat_abroad(rng, p):
    target = rng.choice(("תיירים ישראלים", "נציגות ישראלית", "אנשי עסקים ישראלים", "טיסה של חברה ישראלית"))
    return "התקבל מידע על כוונה לפגוע ב%s באזור %s." % (target, p["where"])


def _t_smuggling(rng, p):
    cargo = rng.choice(("רקטות", "טילים נגד טנקים", "רחפנים", "חומרי נפץ", "רכיבי טילים"))
    return "זוהה נתיב הברחה של %s דרך אזור %s." % (cargo, p["where"])


def _t_strategic(rng, p):
    site = rng.choice(("אתר גרעיני", "מפעל לייצור טילים", "בסיס צבאי", "מחסן נשק"))
    return "זוהתה פעילות חריגה ב%s באזור %s." % (site, p["where"])


def _t_entry(rng, p):
    return "התקבל מידע כי פעיל עוין ינסה להיכנס לישראל דרך %s, בזהות בדויה." % p["where"]


def _t_financing(rng, p):
    amount = rng.randint(5, 500) * 10000
    return "זוהתה העברה של כ-{:,} דולר לארגון טרור דרך {}.".format(amount, p["where"])


def _t_travel(rng, p):
    options = [c for c in ("LB", "SY", "IR", "IQ", "YE", "TR", "CY", "GR", "EG", "JO") if c != p["country"]]
    return "פעיל עוין זוהה באזור %s, בדרכו ל%s." % (p["where"], COUNTRY_HE[rng.choice(options)])


def _t_rocket_alert(rng, p):
    return "ירי רקטות וטילים לעבר %s. יש להיכנס למרחב המוגן תוך %d שניות." % (p["where"], p["shelter"])


def _t_hostile_aircraft(rng, p):
    return "חדירת כלי טיס עוין באזור %s. יש להיכנס למרחב המוגן ולשהות בו 10 דקות." % p["where"]


def _t_infiltration(rng, p):
    return "חשש לחדירת מחבלים באזור %s. יש להיכנס לבית, לנעול את הדלת ולהתרחק מהחלונות." % p["where"]


def _t_early_warning(rng, p):
    return "בדקות הקרובות צפויות להתקבל התרעות באזור %s. יש להתקרב למרחב מוגן." % p["where"]


def _t_earthquake(rng, p):
    return ("הורגשה רעידת אדמה בעוצמה %.1f באזור %s. יש לצאת לשטח פתוח."
            % (rng.randint(35, 60) / 10.0, p["where"]))


def _t_all_clear(rng, p):
    return "האירוע באזור %s הסתיים. ניתן לצאת מהמרחב המוגן." % p["where"]


def _t_terror_warning(rng, p):
    return "התקבל מידע על כוונה לבצע פיגוע באזור %s ב-%d השעות הקרובות." % (p["where"], rng.randint(2, 48))


def _t_wanted(rng, p):
    return ("מחבל מבוקש זוהה באזור %s. נע ב%s בצבע %s."
            % (p["where"], rng.choice(VEHICLES), rng.choice(COLORS)))


def _t_settlement_infil(rng, p):
    return "דווח על חשד לחדירה ליישוב באזור %s. כוחות ביטחון בדרך למקום." % p["where"]


def _t_suspicious_vehicle(rng, p):
    return "זוהה %s חשוד בצבע %s באזור %s." % (rng.choice(VEHICLES), rng.choice(COLORS), p["where"])


def _t_espionage(rng, p):
    return ("התקבל מידע על תושב מאזור %s שגורם עוין יצר איתו קשר ברשת חברתית כדי לאסוף מידע."
            % p["where"])


def _t_weapons_theft(rng, p):
    item = rng.choice(("רובים", "תחמושת", "רימונים", "אמצעי ראיית לילה"))
    return "דווח על גניבת %s מבסיס צבאי באזור %s." % (item, p["where"])


# weight = how often the title appears as a regular (background) alert. 0 = only inside incidents.
CATALOG = [
    # aman
    dict(key="ROCKET_LAUNCH", source="aman", title="זוהה שיגור רקטות", priority="CRITICAL",
         classification="SECRET", pools=(("IL_N", 1), ("IL_S", 1)), weight=2, text=_t_rocket_launch),
    dict(key="BALLISTIC_LAUNCH", source="aman", title="זוהה שיגור טיל בליסטי", priority="CRITICAL",
         classification="SECRET", pools=(("FAR_BALLISTIC", 1),), weight=1, text=_t_ballistic),
    dict(key="LAUNCH_PREP", source="aman", title="זוהו הכנות לשיגור", priority="HIGH",
         classification="SECRET", pools=(("FAR_LAUNCH", 2), ("LB", 1), ("GAZA", 1)), weight=3,
         text=_t_launch_prep),
    dict(key="HOSTILE_UAV", source="aman", title="זוהה כלי טיס בלתי מאויש עוין", priority="HIGH",
         classification="SECRET", pools=(("IL_N", 2), ("IL_C", 2), ("IL_S", 2)), weight=2, text=_t_uav),
    dict(key="FORCE_MOVEMENT", source="aman", title="תנועת כוחות חריגה סמוך לגבול", priority="MEDIUM",
         classification="SECRET", pools=(("LB", 2), ("SY", 2), ("GAZA", 1)), weight=2, text=_t_force_move),
    dict(key="GPS_JAMMING", source="aman", title="שיבושי ניווט באזור", priority="LOW",
         classification="RESTRICTED", pools=(("IL_N", 1), ("IL_C", 2)), weight=2, text=_t_gps),
    # mossad
    dict(key="THREAT_ABROAD", source="mossad", title="התרעה על כוונה לפגוע ביעד ישראלי בחוץ לארץ",
         priority="HIGH", classification="TOP_SECRET", pools=(("FAR_TRAVEL", 1),), weight=2,
         text=_t_threat_abroad),
    dict(key="SMUGGLING", source="mossad", title="זוהה נתיב הברחת אמצעי לחימה", priority="MEDIUM",
         classification="SECRET", pools=(("FAR_SMUGGLE", 2), ("SY", 2), ("LB", 1)), weight=2,
         text=_t_smuggling),
    dict(key="STRATEGIC_SITE", source="mossad", title="פעילות חריגה באתר אסטרטגי", priority="HIGH",
         classification="TOP_SECRET", pools=(("FAR_STRATEGIC", 3), ("SY", 1)), weight=2, text=_t_strategic),
    dict(key="OPERATIVE_ENTRY", source="mossad", title="ניסיון כניסה של פעיל עוין לישראל", priority="HIGH",
         classification="TOP_SECRET", pools=(("ENTRY", 1),), weight=1, text=_t_entry),
    dict(key="TERROR_FINANCING", source="mossad", title="העברת כספים לארגון טרור", priority="LOW",
         classification="SECRET", pools=(("FAR_FINANCE", 2), ("LB", 1)), weight=2, text=_t_financing),
    dict(key="OPERATIVE_TRAVEL", source="mossad", title="תנועת פעיל עוין בין מדינות", priority="MEDIUM",
         classification="SECRET", pools=(("FAR_ALL", 2), ("LB", 1), ("SY", 1)), weight=2, text=_t_travel),
    # pikud-haoref
    dict(key="ROCKET_ALERT", source="pikud-haoref", title="ירי רקטות וטילים", priority="CRITICAL",
         classification="UNCLASSIFIED", pools=IL_ALL, weight=2, text=_t_rocket_alert),
    dict(key="HOSTILE_AIRCRAFT", source="pikud-haoref", title="חדירת כלי טיס עוין", priority="CRITICAL",
         classification="UNCLASSIFIED", pools=(("IL_N", 3), ("IL_C", 1), ("IL_S", 1)), weight=1,
         text=_t_hostile_aircraft),
    dict(key="INFILTRATION", source="pikud-haoref", title="חדירת מחבלים", priority="CRITICAL",
         classification="UNCLASSIFIED", pools=(("IL_N", 1), ("IL_S", 1)), weight=0, text=_t_infiltration),
    dict(key="EARLY_WARNING", source="pikud-haoref", title="התרעה מקדימה", priority="HIGH",
         classification="UNCLASSIFIED", pools=IL_ALL, weight=0, text=_t_early_warning),
    dict(key="EARTHQUAKE", source="pikud-haoref", title="רעידת אדמה", priority="HIGH",
         classification="UNCLASSIFIED", pools=IL_ALL, weight=1, text=_t_earthquake),
    dict(key="ALL_CLEAR", source="pikud-haoref", title="האירוע הסתיים", priority="LOW",
         classification="UNCLASSIFIED", pools=IL_ALL, weight=0, text=_t_all_clear),
    # shabak
    dict(key="TERROR_WARNING", source="shabak", title="התרעה חמה לפיגוע", priority="CRITICAL",
         classification="SECRET", pools=IL_CENTER_HEAVY, weight=2, text=_t_terror_warning),
    dict(key="WANTED_TERRORIST", source="shabak", title="תנועת מחבל מבוקש", priority="HIGH",
         classification="SECRET", pools=IL_CENTER_HEAVY, weight=2, text=_t_wanted),
    dict(key="SETTLEMENT_INFILTRATION", source="shabak", title="חשד לחדירה ליישוב", priority="HIGH",
         classification="RESTRICTED", pools=(("IL_N", 1), ("IL_S", 1)), weight=1, text=_t_settlement_infil),
    dict(key="SUSPICIOUS_VEHICLE", source="shabak", title="רכב חשוד", priority="MEDIUM",
         classification="RESTRICTED", pools=IL_CENTER_HEAVY, weight=2, text=_t_suspicious_vehicle),
    dict(key="ESPIONAGE", source="shabak", title="חשד לפעילות ריגול עבור גורם עוין", priority="MEDIUM",
         classification="SECRET", pools=IL_CENTER_HEAVY, weight=1, text=_t_espionage),
    dict(key="WEAPONS_THEFT", source="shabak", title="גניבת אמצעי לחימה", priority="MEDIUM",
         classification="RESTRICTED", pools=IL_CENTER_HEAVY, weight=1, text=_t_weapons_theft),
]
# English labels for the console log only (the console stays ASCII).
_LOG_LABELS = {
    "ROCKET_LAUNCH": "Rocket launch detected",
    "BALLISTIC_LAUNCH": "Ballistic missile launch",
    "LAUNCH_PREP": "Launch preparations detected",
    "HOSTILE_UAV": "Hostile UAV detected",
    "FORCE_MOVEMENT": "Unusual force movement",
    "GPS_JAMMING": "GPS jamming",
    "THREAT_ABROAD": "Threat to Israelis abroad",
    "SMUGGLING": "Weapons smuggling route",
    "STRATEGIC_SITE": "Activity at strategic site",
    "OPERATIVE_ENTRY": "Hostile operative entry attempt",
    "TERROR_FINANCING": "Terror financing transfer",
    "OPERATIVE_TRAVEL": "Hostile operative on the move",
    "ROCKET_ALERT": "Rockets and missiles",
    "HOSTILE_AIRCRAFT": "Hostile aircraft intrusion",
    "INFILTRATION": "Terrorist infiltration",
    "EARLY_WARNING": "Early warning",
    "EARTHQUAKE": "Earthquake",
    "ALL_CLEAR": "All clear",
    "TERROR_WARNING": "Hot terror warning",
    "WANTED_TERRORIST": "Wanted terrorist on the move",
    "SETTLEMENT_INFILTRATION": "Suspected infiltration",
    "SUSPICIOUS_VEHICLE": "Suspicious vehicle",
    "ESPIONAGE": "Suspected espionage",
    "WEAPONS_THEFT": "Weapons theft",
}
for _entry in CATALOG:
    _entry["label"] = _LOG_LABELS[str(_entry["key"])]
BY_KEY = dict((e["key"], e) for e in CATALOG)
ALERT_FIELDS = ("alert_id", "source", "title", "content", "priority", "classification",
                "lat", "lon", "timestamp", "status")

# ---------------------------------------------------------------------------
# Building alert files
# ---------------------------------------------------------------------------


def _weighted(rng, pairs):
    total = sum(w for _, w in pairs)
    r = rng.uniform(0, total)
    for item, w in pairs:
        r -= w
        if r <= 0:
            return item
    return pairs[-1][0]


def _jitter(place, rng):
    """Random point up to JITTER_KM from the place, rounded to 4 decimals (~11 m)."""
    dist = JITTER_KM * math.sqrt(rng.random())
    angle = rng.uniform(0, 2 * math.pi)
    dlat = dist * math.cos(angle) / 110.57
    dlon = dist * math.sin(angle) / (111.32 * math.cos(math.radians(place["lat"])))
    return round(place["lat"] + dlat, 4), round(place["lon"] + dlon, 4)


def iso_utc(now_dt):
    return now_dt.strftime("%Y-%m-%dT%H:%M:%S") + ".%03dZ" % (now_dt.microsecond // 1000)


def build_alert(entry, place, rng, now_dt):
    lat, lon = _jitter(place, rng)
    return OrderedDict([
        ("alert_id", str(uuid.uuid4())),
        ("source", entry["source"]),
        ("title", entry["title"]),
        ("content", entry["text"](rng, place)),
        ("priority", entry["priority"]),
        ("classification", entry["classification"]),
        ("lat", lat),
        ("lon", lon),
        ("timestamp", iso_utc(now_dt)),
        ("status", "WAITING"),
    ])


def encode(alert):
    # ensure_ascii: Hebrew becomes \uXXXX, so the file is plain ASCII and reads
    # correctly with any default encoding, in any language, on any OS.
    return (json.dumps(alert, ensure_ascii=True, indent=2) + "\n").encode("ascii")


def corrupt(alert, rng):
    """One of the 3 documented kinds of invalid alert. All other fields stay valid."""
    kind = rng.choice(("broken_json", "missing_field", "bad_coordinate"))
    if kind == "broken_json":
        data = encode(alert)
        return data[:rng.randint(len(data) // 5, len(data) * 9 // 10)]
    alert = OrderedDict(alert)
    if kind == "missing_field":
        del alert[rng.choice(ALERT_FIELDS)]
        return encode(alert)
    key = rng.choice(("lat", "lon"))
    mode = rng.choice(("string", "null", "out_of_range"))
    if mode == "string":
        alert[key] = "%.4f" % alert[key]
    elif mode == "null":
        alert[key] = None
    else:
        limit = 90 if key == "lat" else 180
        alert[key] = round(rng.choice((1, -1)) * rng.uniform(limit + 1, limit * 2), 4)
    return encode(alert)


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------


class Job(object):
    """One alert folder to write. build(now_dt, now_mono) returns the alert.json bytes.

    info (label, place, priority), incident and the banners are only used for the console log.
    """
    __slots__ = ("source", "build", "slow", "info", "incident", "banner_before", "banner_after")

    def __init__(self, source, build, slow, info):
        self.source = source
        self.build = build
        self.slow = slow
        self.info = info
        self.incident = None
        self.banner_before = None
        self.banner_after = None


class Scheduler(object):
    """Timeline of alerts. Uses the time values it is given, so tests can drive it fast."""

    def __init__(self, rng, now):
        self.rng = rng
        self._heap = []
        self._counter = 0
        self.incidents = 0
        self.at(now + rng.uniform(0.5, 1.5), self._background)
        self.at(now + rng.uniform(*FIRST_INCIDENT), self._incident)

    def at(self, when, action):
        self._counter += 1
        heapq.heappush(self._heap, (when, self._counter, action))

    def next_time(self):
        return self._heap[0][0]

    def pop_job(self, now):
        """Run due timers; return the next due Job or None."""
        while self._heap and self._heap[0][0] <= now:
            _, _, action = heapq.heappop(self._heap)
            if isinstance(action, Job):
                return action
            action(now)       # chains continue from "now", so a sleeping laptop causes no flood
        return None

    # -- jobs ----------------------------------------------------------------

    def job(self, key, place, slow=True):
        entry = BY_KEY[key]
        rng = self.rng
        sched = self
        info = (entry["label"], place["en"], entry["priority"])

        def build(now_dt, now_mono):
            alert = build_alert(entry, place, rng, now_dt)
            if rng.random() < INVALID_RATE:
                return corrupt(alert, rng)
            data = encode(alert)
            if rng.random() < DUPLICATE_RATE:
                sched.at(now_mono + rng.uniform(*DUPLICATE_DELAY),
                         Job(entry["source"], lambda *_: data, slow, info))
            return data

        return Job(entry["source"], build, slow, info)

    def _random_place(self, entry):
        return self.rng.choice(POOLS[_weighted(self.rng, entry["pools"])])

    # -- regular alerts --------------------------------------------------------

    def _background(self, now):
        rng = self.rng
        entry = _weighted(rng, [(e, e["weight"]) for e in CATALOG if e["weight"] > 0])
        self.at(now, self.job(entry["key"], self._random_place(entry)))
        self.at(now + rng.uniform(*BACKGROUND_GAP), self._background)

    # -- incidents: a few agencies reacting to the same event ------------------
    # Each incident builds a timeline [(time, job)]. The first job carries the start banner,
    # the last one the end banner. The next incident starts only after this one ends.

    def _incident(self, now):
        rng = self.rng
        kind = _weighted(rng, (("barrage_north", 2), ("barrage_south", 2), ("ballistic", 2),
                               ("uav", 1), ("infiltration", 1)))
        timeline = []
        title = getattr(self, "_incident_" + kind)(now, timeline)
        timeline.sort(key=lambda item: item[0])
        self.incidents += 1
        timeline[0][1].banner_before = "INCIDENT #%d: %s" % (self.incidents, title)
        timeline[-1][1].banner_after = "INCIDENT #%d ENDED" % self.incidents
        for when, job in timeline:
            job.incident = self.incidents
            self.at(when, job)
        self.at(timeline[-1][0] + rng.uniform(*INCIDENT_PAUSE), self._incident)

    def _salvo(self, timeline, start, pool):
        """8-20 rocket alerts for different places over a few seconds. Returns (places, end)."""
        rng = self.rng
        places = rng.sample(POOLS[pool], min(len(POOLS[pool]), rng.randint(*SALVO_SIZE)))
        spread = rng.uniform(*SALVO_SPREAD)
        for i, p in enumerate(places):
            timeline.append((start + spread * i / max(1, len(places) - 1),
                             self.job("ROCKET_ALERT", p, slow=False)))
        return places, start + spread

    def _series(self, timeline, start, key, places, slow=False):
        for i, p in enumerate(places):
            timeline.append((start + 0.3 * i, self.job(key, p, slow=slow)))

    def _all_clear(self, timeline, start, places, count):
        self._series(timeline, start, "ALL_CLEAR", self.rng.sample(places, min(count, len(places))))

    def _barrage(self, now, timeline, pool):
        rng = self.rng
        timeline.append((now, self.job("ROCKET_LAUNCH", rng.choice(POOLS[pool]))))
        places, end = self._salvo(timeline, now + rng.uniform(1, 3), pool)
        self._all_clear(timeline, end + rng.uniform(10, 20), places, rng.randint(1, 3))

    def _incident_barrage_north(self, now, timeline):
        self._barrage(now, timeline, "IL_N")
        return "ROCKET BARRAGE FROM LEBANON"

    def _incident_barrage_south(self, now, timeline):
        self._barrage(now, timeline, "IL_S")
        return "ROCKET BARRAGE FROM GAZA"

    def _incident_ballistic(self, now, timeline):
        rng = self.rng
        launch = rng.choice(POOLS["FAR_BALLISTIC"])
        timeline.append((now, self.job("BALLISTIC_LAUNCH", launch)))
        pool = _weighted(rng, (("IL_C", 3), ("IL_S", 2), ("IL_N", 1)))
        t = now + rng.uniform(2, 4)
        self._series(timeline, t, "EARLY_WARNING", rng.sample(POOLS[pool], rng.randint(3, 6)))
        places, end = self._salvo(timeline, t + rng.uniform(8, 15), pool)
        self._all_clear(timeline, end + rng.uniform(10, 20), places, rng.randint(1, 3))
        return "BALLISTIC MISSILE FROM %s" % COUNTRY_EN[launch["country"]].upper()

    def _incident_uav(self, now, timeline):
        rng = self.rng
        pool = _weighted(rng, (("IL_N", 3), ("IL_S", 1)))
        timeline.append((now, self.job("HOSTILE_UAV", rng.choice(POOLS[pool]))))
        t = now + rng.uniform(1, 3)
        places = rng.sample(POOLS[pool], rng.randint(1, 5))
        self._series(timeline, t, "HOSTILE_AIRCRAFT", places)
        self._all_clear(timeline, t + rng.uniform(10, 20), places, rng.randint(1, 2))
        return "HOSTILE UAV INTRUSION"

    def _incident_infiltration(self, now, timeline):
        rng = self.rng
        pool = rng.choice(("IL_N", "IL_S"))
        timeline.append((now, self.job("SETTLEMENT_INFILTRATION", rng.choice(POOLS[pool]))))
        t = now + rng.uniform(2, 5)
        places = rng.sample(POOLS[pool], rng.randint(1, 3))
        self._series(timeline, t, "INFILTRATION", places)
        self._all_clear(timeline, t + rng.uniform(20, 40), places, 1)
        return "TERRORIST INFILTRATION"


# ---------------------------------------------------------------------------
# Console output (ASCII-safe on any console, pipe or container)
# ---------------------------------------------------------------------------


def say(message=""):
    out = sys.stdout
    if out is None:
        return
    try:
        out.write(message + "\n")
    except UnicodeEncodeError:
        try:
            out.write(message.encode("ascii", "backslashreplace").decode("ascii") + "\n")
        except Exception:
            return
    except Exception:
        return
    try:
        out.flush()
    except Exception:
        pass


def _clock():
    return time.strftime("%H:%M:%S")


def _hms(seconds):
    seconds = int(seconds)
    return "%02d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


def _want_color():
    """ANSI colors only on a real terminal that supports them; plain text everywhere else."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    try:
        if sys.stdout is None or not sys.stdout.isatty():
            return False
    except Exception:
        return False
    if os.name != "nt":
        return True
    try:                                   # Windows 10+: turn on VT processing for this console
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.GetStdHandle.restype = ctypes.c_void_p
        handle = ctypes.c_void_p(kernel32.GetStdHandle(-11))
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        return False


class _Paint(object):
    enabled = False
    CODES = {"CRITICAL": "1;31", "HIGH": "33", "MEDIUM": "36", "LOW": "32",
             "banner": "1;35", "system": "90"}

    @classmethod
    def text(cls, text, kind):
        if not cls.enabled or kind not in cls.CODES:
            return text
        return "\x1b[%sm%s\x1b[0m" % (cls.CODES[kind], text)


RULE = "=" * 88


def log(text, kind=None):
    say("[%s] %s" % (_clock(), _Paint.text(text, kind)))


def log_system(text):
    log("SYSTEM   " + text, "system")


def log_alert(number, job):
    label, place, priority = job.info
    tag = "INC-%d" % job.incident if job.incident else ""
    log("#%s  %-6s  %-12s  %s  %-31s  %s" % (number, _Paint.text("%-6s" % tag, "banner") if tag else tag,
                                             job.source.upper(), _Paint.text("%-8s" % priority, priority),
                                             label, place))


def _pause_if_interactive():
    """Keep a double-clicked window open so the message can be read."""
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            input("Press Enter to close...")
    except Exception:
        pass


def _short_error(exc):
    return "%s: %s" % (type(exc).__name__, getattr(exc, "strerror", None) or exc)


# ---------------------------------------------------------------------------
# Stopping
# ---------------------------------------------------------------------------


class _Stop(object):
    requested = False


STOP = _Stop()


def _on_stop_signal(signum, frame):
    if STOP.requested:
        raise KeyboardInterrupt
    STOP.requested = True
    log_system("Stopping: finishing the current alert (press Ctrl+C again to stop at once)")


def _install_signal_handlers():
    for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, _on_stop_signal)
            except (ValueError, OSError, RuntimeError):
                pass


def _sleep(seconds):
    """Sleep in small steps; returns early when a stop was requested."""
    end = time.monotonic() + seconds
    while not STOP.requested:
        left = end - time.monotonic()
        if left <= 0:
            return
        time.sleep(min(left, 0.05))


# ---------------------------------------------------------------------------
# File system
# ---------------------------------------------------------------------------


def _share(path, mode):
    if os.name != "nt":
        try:
            os.chmod(str(path), mode)
        except OSError:
            pass


def _retry(action, attempts=10, delay=0.05):
    """Retry on PermissionError: antivirus / OneDrive / indexers lock files for a moment."""
    for _ in range(attempts - 1):
        try:
            return action()
        except PermissionError:
            time.sleep(delay)
    return action()                    # last attempt: a PermissionError here goes to the caller


def _ensure_dirs():
    for agency in AGENCIES:
        path = ALERTS_DIR / agency
        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)
            _share(path, DIR_MODE)
    _share(ALERTS_DIR, DIR_MODE)


class _Seq(object):
    value = 0

    @classmethod
    def next(cls):
        cls.value = cls.value % 999999 + 1
        return cls.value


def _new_alert_folder(agency_dir):
    for _ in range(200):
        now = datetime.datetime.now(UTC)
        name = now.strftime("%Y%m%dT%H%M%S") + "%03d_%06d" % (now.microsecond // 1000, _Seq.next())
        path = agency_dir / name
        try:
            path.mkdir()
        except FileExistsError:
            continue
        except FileNotFoundError:          # the student deleted the agency folder (or all of alerts/)
            _ensure_dirs()
            continue
        except PermissionError:            # Windows: a deleted folder name can be busy for a moment
            time.sleep(0.02)
            continue
        _share(path, DIR_MODE)
        return path
    raise OSError(errno.EIO, "could not create a new alert folder")


def _create_ready(path):
    """Create the empty alert.ready file. Its creation is the signal, so once it exists the
    alert is delivered: errors while closing it (a fast watcher may already have deleted the
    folder, e.g. over a Docker bind mount) are ignored."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, FILE_MODE)
    try:
        os.close(fd)
    except OSError:
        pass
    _share(path, FILE_MODE)


def _split(data, rng):
    count = rng.randint(*SLOW_WRITE_CHUNKS)
    cuts = sorted(rng.sample(range(1, len(data)), count - 1))
    bounds = [0] + cuts + [len(data)]
    return [data[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]


def write_alert(job, data, rng):
    """Create the alert folder, write alert.json (slowly if job.slow), then alert.ready."""
    folder = _new_alert_folder(ALERTS_DIR / job.source)
    json_path = str(folder / JSON_NAME)
    chunks = _split(data, rng) if job.slow and len(data) > SLOW_WRITE_CHUNKS[1] else [data]
    pause = rng.uniform(*SLOW_WRITE_SECONDS) / max(1, len(chunks) - 1)
    f = _retry(lambda: open(json_path, "xb"))
    try:
        for i, chunk in enumerate(chunks):
            f.write(chunk)
            f.flush()
            if i < len(chunks) - 1:
                _sleep(pause)          # returns at once when stopping: the alert is finished fast
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    finally:
        f.close()
    _share(json_path, FILE_MODE)
    ready_path = str(folder / READY_NAME)
    try:
        _retry(lambda: _create_ready(ready_path))
    except FileNotFoundError:
        # Over a Docker bind mount, a fast watcher can see alert.ready and delete the whole
        # folder while the create call is still returning. alert.json was already complete,
        # so the alert was delivered. Only a folder that still exists without alert.ready
        # is a real failure.
        if folder.exists() and not os.path.exists(ready_path):
            raise
    return folder.name


def repair_leftovers():
    """Finish alert folders left incomplete when the simulator was killed mid-write.

    alert.json present -> add alert.ready (a cut file is simply "broken JSON");
    empty folder -> remove it. Only folders with the simulator's name pattern are touched.
    """
    fixed = removed = 0
    for agency in AGENCIES:
        try:
            entries = list(os.scandir(str(ALERTS_DIR / agency)))
        except OSError:
            continue
        for entry in entries:
            try:
                if not entry.is_dir() or not ALERT_FOLDER_RE.match(entry.name):
                    continue
                folder = Path(entry.path)
                if (folder / READY_NAME).exists():
                    continue
                if (folder / JSON_NAME).exists():
                    _create_ready(str(folder / READY_NAME))
                    fixed += 1
                elif not any(folder.iterdir()):
                    folder.rmdir()
                    removed += 1
            except OSError:
                continue
    return fixed, removed


def _acquire_lock():
    """Returns (handle, ok). ok is False only when another simulator holds the lock."""
    try:
        handle = open(str(LOCK_FILE), "a+b")
    except OSError:
        return None, True                  # read-only folder: run without the lock
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle, True
    except (IOError, OSError) as exc:
        busy = (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK, errno.EDEADLK,
                getattr(errno, "EDEADLOCK", errno.EDEADLK))
        if exc.errno in busy:
            handle.close()
            return None, False
        return handle, True                # locking not supported here: run without it


def _disk_is_low(threshold):
    try:
        return shutil.disk_usage(str(ALERTS_DIR)).free < threshold
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _alerts_on_disk():
    """Number of alert folders currently in alerts/ (for the STATUS line)."""
    count = 0
    for agency in AGENCIES:
        try:
            for entry in os.scandir(str(ALERTS_DIR / agency)):
                if ALERT_FOLDER_RE.match(entry.name):
                    count += 1
        except OSError:
            pass
    return count


def _header():
    say(RULE)
    say("  ALERT SIMULATOR  |  agencies online: %s" % ", ".join(a.upper() for a in AGENCIES))
    say("  Python %s on %s" % (platform.python_version(), platform.system() or "unknown"))
    say("  Alerts folder: %s" % ALERTS_DIR)
    say("  Stop: Ctrl+C")
    say(RULE)


def run():
    _Paint.enabled = _want_color()
    _install_signal_handlers()
    _header()

    lock, ok = _acquire_lock()
    if not ok:
        log_system("The simulator is already running (maybe in another window).")
        log_system("Use the one that is running, or close it and start again.")
        _pause_if_interactive()
        return 1

    try:
        _ensure_dirs()
    except OSError as exc:
        log_system("ERROR: cannot create the alerts folder (%s)." % _short_error(exc))
        if os.name == "nt":
            log_system("Windows may be blocking programs from writing in this folder (for example Documents")
            log_system("or Desktop, when 'Controlled folder access' is on).")
            log_system("Copy the alert-simulator folder to another place, for example C:\\exam\\alert-simulator,")
            log_system("and run it again.")
        else:
            log_system("Copy the alert-simulator folder to a folder you can write to and run it again.")
        _pause_if_interactive()
        return 1

    fixed, removed = repair_leftovers()
    if fixed or removed:
        log_system("Finished %d alert(s) left incomplete by the previous run." % (fixed + removed))
    if os.name == "nt" and len(str(ALERTS_DIR)) > 200:
        log_system("Warning: the folder path is very long. If you see errors, move alert-simulator to a shorter path.")

    rng = random.Random()
    started = time.monotonic()
    sched = Scheduler(rng, started)
    sent = 0
    paused = False
    next_disk_check = 0.0
    next_status = started + STATUS_EVERY
    log_system("Online. Every alert that is sent is listed below.")

    try:
        while not STOP.requested:
            try:
                now = time.monotonic()
                if now >= next_disk_check:
                    next_disk_check = now + DISK_CHECK_EVERY
                    if not paused and _disk_is_low(LOW_DISK_BYTES):
                        paused = True
                        log_system("Low disk space: alerts are paused. Free some space (or delete the alerts folder).")
                    elif paused and not _disk_is_low(RESUME_DISK_BYTES):
                        paused = False
                        log_system("Disk space is OK again: alerts resumed.")
                if now >= next_status:
                    next_status = now + STATUS_EVERY
                    log("STATUS   uptime %s | alerts sent: %d | alerts in folder: %d"
                        % (_hms(now - started), sent, _alerts_on_disk()), "system")

                job = sched.pop_job(now)
                if job is None:
                    _sleep(min(0.1, max(0.0, sched.next_time() - now)))
                    continue
                if paused:
                    continue
                if job.banner_before:
                    say()
                    log(">>> %s <<<" % job.banner_before, "banner")
                data = job.build(datetime.datetime.now(UTC), now)
                try:
                    name = write_alert(job, data, rng)
                    sent += 1
                    log_alert(name[-6:], job)
                except OSError as exc:
                    log_system("Skipped one alert (%s). Still running." % _short_error(exc))
                if job.banner_after:
                    log("<<< %s >>>" % job.banner_after, "banner")
                    say()
            except KeyboardInterrupt:
                raise
            except Exception as exc:       # never crash in the middle of an exam
                log_system("Unexpected error (%s). Still running." % _short_error(exc))
                _sleep(1.0)
    except KeyboardInterrupt:
        log_system("Stopped immediately.")

    log_system("Stopped. %d alerts sent in %s." % (sent, _hms(time.monotonic() - started)))
    if lock is not None:
        try:
            lock.close()
        except Exception:
            pass
    return 0


def main():
    try:
        code = run()
    except KeyboardInterrupt:
        code = 0
    except Exception as exc:               # last resort: show the reason and keep the window open
        say("ERROR: %s" % _short_error(exc))
        _pause_if_interactive()
        code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
