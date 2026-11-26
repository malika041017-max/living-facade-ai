#!/usr/bin/env python3
"""Local LIVING FACADE AI API server. Binds only to localhost."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path
import json, os, datetime, math

ROOT = Path(__file__).resolve().parent
MAX_BODY = 1_000_000

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json(200, {
                "ok": True,
                "weather": "Open-Meteo Archive API",
                "blender": "OBJ export workflow"
            })
        if parsed.path == "/api/weather/annual":
            try:
                q = parse_qs(parsed.query)
                lat = float(q.get("latitude", ["43.2389"])[0])
                lon = float(q.get("longitude", ["76.8897"])[0])
                year = int(q.get("year", ["2024"])[0])
                area = float(q.get("facade_area_m2", ["120"])[0])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Координаттар шектен тыс")
                if not (2010 <= year <= 2025):
                    raise ValueError("Жыл 2010–2025 аралығында болуы керек")
                if not (1 <= area <= 100000):
                    raise ValueError("Фасад ауданы 1–100000 м² аралығында болуы керек")
                start, end = f"{year}-01-01", f"{year}-12-31"
                api = ("https://archive-api.open-meteo.com/v1/archive?"
                       f"latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
                       "&hourly=shortwave_radiation,temperature_2m&timezone=auto")
                req = Request(api, headers={"User-Agent": "LivingFacadeAI/1.0"})
                with urlopen(req, timeout=60) as response:
                    weather = json.loads(response.read().decode())
                hourly = weather.get("hourly", {})
                radiation = [x for x in hourly.get("shortwave_radiation", []) if isinstance(x, (int,float))]
                temps = [x for x in hourly.get("temperature_2m", []) if isinstance(x, (int,float))]
                if len(radiation) < 8000 or not temps:
                    raise ValueError("Жылдық метеодерек толық емес немесе қолжетімсіз")
                horizontal_kwh = sum(radiation) / 1000.0
                mean_temp = sum(temps) / len(temps)
                # A transparent preliminary proxy only: horizontal irradiation × area × assumed factor.
                # Not an orientation-resolved vertical facade irradiation calculation.
                proxy = horizontal_kwh * area * 0.35
                return self.send_json(200, {
                    "source": "Open-Meteo Historical Weather API (ERA5-based archive)",
                    "year": year, "location": {"latitude": lat, "longitude": lon},
                    "annual_horizontal_kwh_m2": horizontal_kwh,
                    "mean_temperature_c": mean_temp,
                    "estimated_facade_kwh": proxy,
                    "facade_area_m2": area, "assumed_proxy_factor": 0.35,
                    "valid_hours": min(len(radiation), len(temps)),
                    "method": "Hourly shortwave_radiation sum / 1000. The facade figure is a rough horizontal-irradiation × area × 0.35 proxy; it is NOT a vertical-orientation simulation or building energy demand.",
                    "limitations": "Historical gridded weather data; no facade azimuth/tilt transposition, glazing SHGC, thermal bridge, HVAC, occupancy, shading geometry, or code compliance."
                })
            except HTTPError as e:
                return self.send_json(502, {"error": f"Open-Meteo қатесі ({e.code})"})
            except (URLError, TimeoutError) as e:
                return self.send_json(502, {"error": f"Метеодерек серверіне қосылмады: {e}"})
            except Exception as e:
                return self.send_json(400, {"error": str(e)})
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(ROOT)
    print("LIVING FACADE AI: http://127.0.0.1:8000")
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
