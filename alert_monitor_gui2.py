import requests
import winsound
import time
import tkinter as tk
from threading import Thread
from datetime import datetime
import os
import pytz

# Configuration constants
CONFIG = {
    "NWS_API_URL": "https://api.weather.gov/alerts/active",
    "ALERT_LOG_PATH": r"C:\Users\x0rap\Desktop\AlertLog",
    "ALERT_SOUND_PATHS": {
        "tornado": r"C:\Users\x0rap\Music\WAMT\X3.wav",
        "thunderstorm": r"C:\Users\x0rap\Music\WAMT\X2.wav",
        "tornadowatch": r"C:\Users\x0rap\Music\WAMT\X1.wav",
        "thunderstormwatch": r"C:\Users\x0rap\Music\WAMT\X4.wav"
    },
    "TORNADO_KEYWORDS": ["Tornado Warning"],
    "THUNDERSTORM_KEYWORDS": ["Severe Thunderstorm Warning"],
    "TORNADO_WATCH_KEYWORDS": ["Tornado Watch"],
    "THUNDERSTORM_WATCH_KEYWORDS": ["Severe Thunderstorm Watch"],
    "EXCLUDE_KEYWORDS": ["AST", "ADT"],
    "MAX_ALERT_HISTORY_SIZE": 5,
    "MAX_CONTAINER_HEIGHT": 300,  # Max height of the alert container in pixels
    "MAX_CONTAINER_WIDTH": 350,  # Max width of the alert container in pixels
}

# States
sound_enabled = True
alert_history = {
    "tornado": [],
    "thunderstorm": [],
    "tornadowatch": [],
    "thunderstormwatch": []
}
current_alert_index = {
    "tornado": -1,
    "thunderstorm": -1,
    "tornadowatch": -1,
    "thunderstormwatch": -1
}

# Misc. Global Variables
notified_alerts = set()


def log_alert(alert_type, header, description):
    os.makedirs(CONFIG['ALERT_LOG_PATH'], exist_ok=True)
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(CONFIG['ALERT_LOG_PATH'], f"{alert_type}_{current_time}.txt")
    with open(filename, 'w') as file:
        file.write(f"Alert Header: {header}\nAlert Description: {description}\n")


def fetch_alerts():
    try:
        response = requests.get(CONFIG['NWS_API_URL'])
        response.raise_for_status()
        alerts = response.json().get('features', [])
        return alerts
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching alerts: {e}")
        return []


def filter_alerts(alerts):
    new_tornado_alerts, new_thunderstorm_alerts = [], []
    new_tornado_watch_alerts, new_thunderstorm_watch_alerts = [], []

    for alert in alerts:
        properties = alert.get('properties', {})
        event = properties.get('event', '')
        headline = properties.get('headline') or ''
        description = properties.get('description') or ''
        area_desc = properties.get('areaDesc', '')

        if any(exclude in headline + description for exclude in CONFIG['EXCLUDE_KEYWORDS']) or "AK" in area_desc:
            continue

        if any(keyword in event for keyword in CONFIG['TORNADO_KEYWORDS']):
            new_tornado_alerts.append((event, headline, description))
        elif any(keyword in event for keyword in CONFIG['THUNDERSTORM_KEYWORDS']):
            new_thunderstorm_alerts.append((event, headline, description))
        elif any(keyword in event for keyword in CONFIG['TORNADO_WATCH_KEYWORDS']):
            new_tornado_watch_alerts.append((event, headline, description))
        elif any(keyword in event for keyword in CONFIG['THUNDERSTORM_WATCH_KEYWORDS']):
            new_thunderstorm_watch_alerts.append((event, headline, description))

    return new_tornado_alerts, new_thunderstorm_alerts, new_tornado_watch_alerts, new_thunderstorm_watch_alerts


def update_alert_display(alert_type, alert_text_widget):
    history = alert_history[alert_type]
    index = current_alert_index[alert_type]
    alert_text_widget.config(state=tk.NORMAL)
    alert_text_widget.delete(1.0, tk.END)
    if index < 0 or index >= len(history):
        alert_text_widget.insert(tk.END, "No active alerts.")
    else:
        event, headline, description = history[index]
        alert_text_widget.insert(tk.END, f"{event}\n{headline}\n{description}")
    alert_text_widget.config(state=tk.DISABLED)


def play_alert_sound(alert_type):
    if sound_enabled:
        winsound.PlaySound(CONFIG['ALERT_SOUND_PATHS'][alert_type], winsound.SND_FILENAME)


def handle_new_alerts(alert_type, new_alerts, alert_text_widget):
    global current_alert_index, notified_alerts
    history = alert_history[alert_type]

    for event, headline, description in new_alerts:
        alert_id = (headline, description)
        if alert_id not in notified_alerts:
            play_alert_sound(alert_type)
            log_alert(event, headline, description)
            history.append((event, headline, description))
            if len(history) > CONFIG['MAX_ALERT_HISTORY_SIZE']:
                history.pop(0)
            current_alert_index[alert_type] = len(history) - 1
            update_alert_display(alert_type, alert_text_widget)
            notified_alerts.add(alert_id)


def alert_thread():
    while True:
        alerts = fetch_alerts()
        filtered_alerts = filter_alerts(alerts)
        if len(filtered_alerts) == 4:  # Ensure filter_alerts always returns four lists
            new_tornado_alerts, new_thunderstorm_alerts, new_tornado_watch_alerts, new_thunderstorm_watch_alerts = filtered_alerts
            handle_new_alerts("tornado", new_tornado_alerts, tornado_alert_text)
            handle_new_alerts("thunderstorm", new_thunderstorm_alerts, thunderstorm_alert_text)
            handle_new_alerts("tornadowatch", new_tornado_watch_alerts, tornado_watch_alert_text)
            handle_new_alerts("thunderstormwatch", new_thunderstorm_watch_alerts, thunderstorm_watch_alert_text)

            update_background_colors()
        else:
            print(f"Unexpected filter_alerts return value: {filtered_alerts}")
        time.sleep(60)


def start_alert_thread():
    thread = Thread(target=alert_thread)
    thread.daemon = True  # Ensure the thread terminates when the main script ends
    thread.start()


def show_previous_alert(alert_type, text_widget):
    if current_alert_index[alert_type] > 0:
        current_alert_index[alert_type] -= 1
    update_alert_display(alert_type, text_widget)


def show_next_alert(alert_type, text_widget):
    if current_alert_index[alert_type] < len(alert_history[alert_type]) - 1:
        current_alert_index[alert_type] += 1
    update_alert_display(alert_type, text_widget)


def update_background_colors():
    new_bg_color = "#5b2c6f" if any(alert_history.values()) else "#196f3d"
    root.config(bg=new_bg_color)
    container_bg_label.config(bg=new_bg_color)
    container_frame.config(bg=new_bg_color)
    bottom_container_frame.config(bg=new_bg_color)


time_zones = [
    ("Pacific", "America/Los_Angeles", "#1f618d"),
    ("Mountain", "America/Denver", "#566573"),
    ("GMT", "Etc/GMT", "#943126"),
    ("Central", "America/Chicago", "#27ae60"),
    ("Atlantic", "America/New_York", "#5499c7"),
]


def update_clocks():
    for label, tz in zip(clock_labels, time_zones):
        zone = pytz.timezone(tz[1])
        current_time = datetime.now(zone).strftime('%Y-%m-%d %H:%M:%S')
        label.config(text=f"{tz[0]}: {current_time}")
    root.after(1000, update_clocks)


def create_alert_frame(label_text, bg_color):
    frame = tk.Frame(container_frame, bg=bg_color, relief=tk.RAISED, borderwidth=1)
    tk.Label(frame, text=label_text, bg=bg_color, fg="white").pack()

    text_widget = tk.Text(frame, wrap=tk.WORD, bg=bg_color, fg="white", height=10, width=40)
    text_widget.insert(tk.END, "No active alerts.")
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(padx=10, pady=10, expand=True, fill=tk.BOTH, side=tk.LEFT)

    scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)

    frame.pack_propagate(False)  # Prevent frame from resizing to fit its contents
    frame.config(height=CONFIG["MAX_CONTAINER_HEIGHT"], width=CONFIG["MAX_CONTAINER_WIDTH"])

    return frame, text_widget


def add_navigation_buttons(frame, alert_type, text_widget):
    nav_frame = tk.Frame(frame, bg="#000000")
    prev_button = tk.Button(nav_frame, text=f"Previous {alert_type.capitalize()} Alert",
                            command=lambda: show_previous_alert(alert_type, text_widget))
    prev_button.pack(side=tk.LEFT, padx=5, pady=(0, 10))

    next_button = tk.Button(nav_frame, text=f"Next {alert_type.capitalize()} Alert",
                            command=lambda: show_next_alert(alert_type, text_widget))
    next_button.pack(side=tk.RIGHT, padx=5, pady=(0, 10))

    nav_frame.pack(side=tk.BOTTOM, fill=tk.X)


root = tk.Tk()
root.title("NWS Alert Monitor")
root.geometry("1400x1000")
root.config(bg="#196f3d")

container_bg_label = tk.Label(root, text="NWS ALERTS", bg="#196f3d", fg="white")
container_bg_label.pack()

container_frame = tk.Frame(root, bg="#196f3d")
container_frame.pack(fill=tk.BOTH, expand=True)

container_frame.grid_columnconfigure((0, 2), weight=1)
container_frame.grid_rowconfigure((0, 1), weight=1)

# Tornado alerts
tornado_frame, tornado_alert_text = create_alert_frame("Tornado Alerts", "#943126")
tornado_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
add_navigation_buttons(tornado_frame, "tornado", tornado_alert_text)

# Severe Thunderstorm alerts
thunderstorm_frame, thunderstorm_alert_text = create_alert_frame("Severe Thunderstorm Alerts", "#b7950b")
thunderstorm_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
add_navigation_buttons(thunderstorm_frame, "thunderstorm", thunderstorm_alert_text)

# Tornado Watch alerts
tornado_watch_frame, tornado_watch_alert_text = create_alert_frame("Tornado Watch Alerts", "#2874A6")
tornado_watch_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
add_navigation_buttons(tornado_watch_frame, "tornadowatch", tornado_watch_alert_text)

# Thunderstorm Watch alerts
thunderstorm_watch_frame, thunderstorm_watch_alert_text = create_alert_frame("Severe Thunderstorm Watch Alerts",
                                                                             "#D68910")
thunderstorm_watch_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=10)
add_navigation_buttons(thunderstorm_watch_frame, "thunderstormwatch", thunderstorm_watch_alert_text)

# Bottom container frame
bottom_container_frame = tk.Frame(root, bg="#196f3d")
bottom_container_frame.pack(fill=tk.BOTH, expand=False)

clock_labels = [tk.Label(bottom_container_frame, text="", bg=tz[2], fg="white", font=("Helvetica", 12)) for tz in
                time_zones]
for label in clock_labels:
    label.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)

update_clocks()
start_alert_thread()
root.mainloop()