import folium
import requests
import polyline
from datetime import datetime

# ======================
# 1) ДАННЫЕ: REQUEST 4
# ======================
request_data = {
  "nodes": [
    {
      "lat": 43.660025,
      "lon": 51.137819,
      "sla": 0,
      "type": "depot",
      "time_window": [0,7200]
    },
    {
      "lat": 43.668658,
      "lon": 51.146461,
      "sla": 900,
      "type": "food",
      "order_id": 1621618,
      "point_id": 3251292,
      "sen_or_rec": "receiver",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T15:16:47.523929+00:00"
    },
    {
      "lat": 43.64751,
      "lon": 51.15456,
      "sla": 900,
      "type": "food",
      "order_id": 1621772,
      "point_id": 3251599,
      "sen_or_rec": "sender",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T15:26:17.165889+00:00"
    },
    {
      "lat": 43.647827,
      "lon": 51.15632,
      "sla": 900,
      "type": "food",
      "order_id": 1621839,
      "point_id": 3251733,
      "sen_or_rec": "sender",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T15:26:21.177758+00:00"
    },
    {
      "lat": 43.649116,
      "lon": 51.153045,
      "sla": 900,
      "type": "food",
      "order_id": 1621772,
      "point_id": 3251600,
      "sen_or_rec": "receiver",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T15:30:56.733244+00:00"
    },
    {
      "lat": 43.649738,
      "lon": 51.153774,
      "sla": 900,
      "type": "food",
      "order_id": 1621839,
      "point_id": 3251734,
      "sen_or_rec": "receiver",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T15:38:47.176088+00:00"
    },
    {
      "lat": 43.64751,
      "lon": 51.15456,
      "sla": 900,
      "type": "food",
      "order_id": 1621919,
      "point_id": 3251893,
      "sen_or_rec": "sender",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T16:05:30.402029+00:00"
    },
    {
      "lat": 43.647827,
      "lon": 51.15632,
      "sla": 900,
      "type": "food",
      "order_id": 1621939,
      "point_id": 3251933,
      "sen_or_rec": "sender",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T16:05:36.913698+00:00"
    },
    {
      "lat": 43.659088,
      "lon": 51.148596,
      "sla": 900,
      "type": "food",
      "order_id": 1621919,
      "point_id": 3251894,
      "sen_or_rec": "receiver",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T16:14:06.437784+00:00"
    },
    {
      "lat": 43.668884,
      "lon": 51.134763,
      "sla": 900,
      "type": "food",
      "order_id": 1621939,
      "point_id": 3251934,
      "sen_or_rec": "receiver",
      "time_window": [900,7200],
      "real_completed_at": "2024-12-16T16:33:36.790879+00:00"
    }
  ],
  "pickups_deliveries": [
    [2,3],
    [4,5],
    [8,9],
    [6,7]
  ],
  "service_time": [0,180,180,180,180,180,180,180,180,180]
}

# ======================
# 2) ДАННЫЕ: RESPONSE 4
# ======================
response_data = {
    "route": [
        7,
        3,
        6,
        2,
        4,
        5,
        8,
        9,
        1
    ],
    "eta": [
        900,
        1080,
        1345,
        1525,
        1781,
        2006,
        2597,
        3255,
        3817
    ]

}

nodes = request_data["nodes"]

# ----------------------------------
# 3) Формируем два маршрута (Real vs OR)
# ----------------------------------
# Индекс 0 - depot (курьер).
# A) Реальный: остальные сортируем по real_completed_at, prepend 0
indexed_nodes = []
for i, nd in enumerate(nodes):
    if i == 0:
        continue
    if "real_completed_at" in nd and nd["real_completed_at"]:
        dt = datetime.fromisoformat(nd["real_completed_at"].replace("Z",""))
        indexed_nodes.append((i, dt))

indexed_nodes.sort(key=lambda x: x[1])
real_route_indices = [0] + [x[0] for x in indexed_nodes]

# B) OR-tools: prepend 0 + берём из response
or_route_indices = [0] + response_data["route"]

# ----------------------------------
# 4) Функция OSRM "по дорогам"
# ----------------------------------
def get_osrm_route(lat1, lon1, lat2, lon2):
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        "?overview=full&geometries=polyline"
    )
    r = requests.get(url)
    if r.status_code != 200:
        print("OSRM error:", r.text)
        return [(lat1, lon1), (lat2, lon2)]  # fallback
    data = r.json()
    geometry = data["routes"][0]["geometry"]
    return polyline.decode(geometry)

# ----------------------------------
# 5) Собираем coords для обоих маршрутов
# ----------------------------------
def build_full_coords(route_indices):
    if len(route_indices) < 2:
        return []
    coords_all = []
    for i in range(len(route_indices) - 1):
        idx_a = route_indices[i]
        idx_b = route_indices[i+1]
        latA, lonA = nodes[idx_a]["lat"], nodes[idx_a]["lon"]
        latB, lonB = nodes[idx_b]["lat"], nodes[idx_b]["lon"]
        seg = get_osrm_route(latA, lonA, latB, lonB)
        if i == 0:
            coords_all.extend(seg)
        else:
            coords_all.extend(seg[1:])
    return coords_all

real_coords = build_full_coords(real_route_indices)
or_coords   = build_full_coords(or_route_indices)

# ----------------------------------
# 6) Создаём карту folium
# ----------------------------------
import folium

m = folium.Map(location=[nodes[0]["lat"], nodes[0]["lon"]], zoom_start=12)
fg_real = folium.FeatureGroup(name="Real route (Green)")
fg_or   = folium.FeatureGroup(name="OR-tools route (Red)")
m.add_child(fg_real)
m.add_child(fg_or)

# Линии
folium.PolyLine(
    locations=real_coords,
    color="green",
    weight=5,
    opacity=0.8
).add_to(fg_real)

folium.PolyLine(
    locations=or_coords,
    color="red",
    dash_array="5,5",
    weight=5,
    opacity=0.8
).add_to(fg_or)

# ----------------------------------
# 7) Маркеры (DivIcon)
# ----------------------------------
def add_markers(route_indices, feature_group, color_line, prefix):
    for seq, idx_node in enumerate(route_indices):
        nd = nodes[idx_node]
        lat = nd["lat"]
        lon = nd["lon"]
        num = seq + 1

        # Popup
        lines = [f"{prefix}{num} (node {idx_node})"]
        if idx_node == 0:
            lines.append("КУРЬЕР (depot)")
        else:
            lines.append(f"type: {nd['type']}")
            if "sen_or_rec" in nd:
                lines.append(nd["sen_or_rec"])
            if "order_id" in nd:
                lines.append(f"order_id: {nd['order_id']}")
            if "real_completed_at" in nd and nd["real_completed_at"]:
                lines.append(f"done={nd['real_completed_at']}")

        popup_txt = "\n".join(lines)

        # фон для маркера: depot=серый, food=оранжевый, иначе белый
        if idx_node == 0:
            bg_color = "#CCCCCC"
        elif nd["type"] == "food":
            bg_color = "#FFCCAA"
        else:
            bg_color = "#FFFFFF"

        icon_html = f"""
        <div style="font-size:14px;
                    color:#000;
                    background:{bg_color};
                    border:2px solid {color_line};
                    border-radius:15px;
                    width:36px;
                    height:36px;
                    text-align:center;
                    line-height:34px;">
            {num}
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=popup_txt,
            tooltip=f"{prefix}{num}",
            icon=folium.DivIcon(
                icon_size=(36,36),
                icon_anchor=(18,18),
                html=icon_html
            )
        ).add_to(feature_group)

# Добавляем маркеры
add_markers(real_route_indices, fg_real, "green", "R")
add_markers(or_route_indices,   fg_or,   "red",   "O")

# ----------------------------------
# 8) Автоподгонка зума
# ----------------------------------
all_points = real_coords + or_coords
if all_points:
    min_lat = min(pt[0] for pt in all_points)
    max_lat = max(pt[0] for pt in all_points)
    min_lon = min(pt[1] for pt in all_points)
    max_lon = max(pt[1] for pt in all_points)
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

# ----------------------------------
# 9) Сохраняем
# ----------------------------------
folium.LayerControl().add_to(m)
m.save("response4_chinachanges.html")

print("Готово! Файл response4_chinachanges.html создан.")
