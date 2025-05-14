from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import geoip2.webservice
import dotenv

import os
import time
import csv
from pathlib import Path

dotenv.load_dotenv()

GEOIP2_ACCOUNT_ID = int(os.getenv("GEOIP2_ACCOUNT_ID") or '')
GEOIP2_LICENSE_KEY = os.getenv("GEOIP2_LICENSE_KEY") or ''

read_logfile = "/var/log/nginx/arson.log"
write_logfile = "logs/arsonloc.csv"

MAX_LINE_LENGTH = 15

FIELDNAMES = ['timestamp', 'latitude', 'longitude', 'city']

class LogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == read_logfile:
            with open(read_logfile, 'r') as f:
                f.seek(0, os.SEEK_END)
                f.seek(f.tell() - MAX_LINE_LENGTH - 1, os.SEEK_SET)

                lines = f.readlines()
                res = lines[-1].strip()

                with geoip2.webservice.Client(GEOIP2_ACCOUNT_ID, GEOIP2_LICENSE_KEY, host='geolite.info') as client:
                    response = client.city(res)

                    if not Path(write_logfile).exists():
                        os.makedirs(os.path.dirname(write_logfile), exist_ok=True)

                        with open(write_logfile, 'w') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
                            writer.writeheader()

                    with open(write_logfile, 'a') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
                        writer.writerow({
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'latitude': response.location.latitude,
                            'longitude': response.location.longitude,
                            'city': response.city.name
                        })

observer = Observer()
observer.schedule(LogHandler(), path=read_logfile, recursive=False)
observer.start()

while True: ...
