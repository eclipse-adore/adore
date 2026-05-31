"""
hardware_monitor_web.py

Standalone Flask app for the hardware monitor web UI.
Can also be imported to attach routes to an existing app.

Usage:
    python hardware_monitor_web.py [--port 8889] [--host 0.0.0.0]
"""

import argparse
import os
import sys

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

_HERE = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_HERE, 'templates'),
    static_folder=os.path.join(_HERE, 'static'),
)
CORS(app)

# Register the hardware monitor blueprint
sys.path.insert(0, os.path.dirname(_HERE))
from hardware_monitor.hardware_monitor_api import get_hardware_monitor_blueprint

app.register_blueprint(get_hardware_monitor_blueprint())


@app.route('/')
def index():
    return render_template('hardware_monitor.html')


@app.route('/health')
def health():
    return {'status': 'ok'}


def main():
    parser = argparse.ArgumentParser(description='Hardware Monitor Web UI')
    parser.add_argument('--port', type=int, default=8889)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    args = parser.parse_args()
    print(f'\n🖥  Hardware Monitor UI → http://{args.host}:{args.port}')
    app.run(debug=False, use_reloader=False, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
