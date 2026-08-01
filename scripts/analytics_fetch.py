#!/usr/bin/env python3
"""Pull site analytics from Cloudflare GraphQL API"""
import json, subprocess, sys, os
from datetime import date, timedelta

CF_TOKEN = os.path.expanduser("~/.cf_api_token")
try:
    token = open(CF_TOKEN).read().strip()
except:
    print("NO_CF_TOKEN")
    sys.exit(1)

API = "https://api.cloudflare.com/client/v4/graphql"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Step 1: Get zones
print("=== Enumerating zones...", file=sys.stderr)
r = subprocess.run(["curl", "-s", "https://api.cloudflare.com/client/v4/zones?per_page=50",
    "-H", f"Authorization: Bearer {token}"], capture_output=True, text=True, timeout=15)
zones = json.loads(r.stdout)
zone_map = {}
for z in zones.get("result", []):
    zone_map[z["id"]] = z["name"]
    print(f"  {z['name']}: {z['id']}", file=sys.stderr)

# Step 2: For each zone, get 7-day overview
print("\n=== Zone Analytics (7 days)...", file=sys.stderr)
results = {}
for zid, zname in zone_map.items():
    # Need to loop last 7 days individually (1 day cap)
    total_visits = 0
    total_bytes = 0
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i+1)
        query = {
            "query": f"""
            {{
              viewer {{
                zones(filter:{{zoneTag:"{zid}"}}) {{
                  httpRequestsAdaptiveGroups(
                    filter:{{date_geq:"{day.isoformat()}", date_lt:"{(day+timedelta(days=1)).isoformat()}"}}
                    limit:1
                  ) {{
                    sum {{
                      visits
                      edgeResponseBytes
                    }}
                  }}
                }}
              }}
            }}
            """
        }
        r = subprocess.run(["curl", "-s", API, "-X", "POST",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(query)], capture_output=True, text=True, timeout=15)
        try:
            data = json.loads(r.stdout)
            groups = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("httpRequestsAdaptiveGroups", [])
            if groups:
                total_visits += int(groups[0]["sum"]["visits"])
                total_bytes += int(groups[0]["sum"]["edgeResponseBytes"])
        except:
            pass
    
    results[zname] = {"edge_requests_7d": total_visits, "bytes_7d": total_bytes}

# Step 3: Top pages (single day)
for zid, zname in zone_map.items():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    query = {
        "query": f"""
        {{
          viewer {{
            zones(filter:{{zoneTag:"{zid}"}}) {{
              httpRequestsAdaptiveGroups(
                filter:{{date_geq:"{yesterday}", date_lt:"{today}"}}
                limit:10
              ) {{
                dimensions {{
                  clientRequestPath
                }}
                sum {{
                  visits
                }}
              }}
            }}
          }}
        }}
        """
    }
    r = subprocess.run(["curl", "-s", API, "-X", "POST",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(query)], capture_output=True, text=True, timeout=15)
    try:
        data = json.loads(r.stdout)
        groups = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("httpRequestsAdaptiveGroups", [])
        pages = []
        for g in groups:
            pages.append({"path": g["dimensions"]["clientRequestPath"], "visits": g["sum"]["visits"]})
        results[zname]["top_pages_1d"] = pages
    except Exception as e:
        results[zname]["top_pages_1d"] = []

# Step 4: Countries (single day)
for zid, zname in zone_map.items():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    query = {
        "query": f"""
        {{
          viewer {{
            zones(filter:{{zoneTag:"{zid}"}}) {{
              httpRequestsAdaptiveGroups(
                filter:{{date_geq:"{yesterday}", date_lt:"{today}"}}
                limit:10
              ) {{
                dimensions {{
                  clientCountryName
                }}
                sum {{
                  visits
                }}
              }}
            }}
          }}
        }}
        """
    }
    r = subprocess.run(["curl", "-s", API, "-X", "POST",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(query)], capture_output=True, text=True, timeout=15)
    try:
        data = json.loads(r.stdout)
        groups = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("httpRequestsAdaptiveGroups", [])
        countries = []
        for g in groups:
            countries.append({"country": g["dimensions"]["clientCountryName"], "visits": g["sum"]["visits"]})
        results[zname]["countries_1d"] = countries
    except:
        results[zname]["countries_1d"] = []

# Step 5: Device type (single day)
for zid, zname in zone_map.items():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    query = {
        "query": f"""
        {{
          viewer {{
            zones(filter:{{zoneTag:"{zid}"}}) {{
              httpRequestsAdaptiveGroups(
                filter:{{date_geq:"{yesterday}", date_lt:"{today}"}}
                limit:5
              ) {{
                dimensions {{
                  clientDeviceType
                }}
                sum {{
                  visits
                }}
              }}
            }}
          }}
        }}
        """
    }
    r = subprocess.run(["curl", "-s", API, "-X", "POST",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(query)], capture_output=True, text=True, timeout=15)
    try:
        data = json.loads(r.stdout)
        groups = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("httpRequestsAdaptiveGroups", [])
        devices = []
        for g in groups:
            devices.append({"device": g["dimensions"]["clientDeviceType"], "visits": g["sum"]["visits"]})
        results[zname]["devices_1d"] = devices
    except:
        results[zname]["devices_1d"] = []

print(json.dumps(results, indent=2))
