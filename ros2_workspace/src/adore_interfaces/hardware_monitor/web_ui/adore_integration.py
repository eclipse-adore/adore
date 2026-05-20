"""
adore_integration.py

Drop-in integration for adore_api.py.

Add two lines to adore_api.py after the app is created and CORS is applied:

    from hardware_monitor.hardware_monitor_api import get_hardware_monitor_blueprint
    app.register_blueprint(get_hardware_monitor_blueprint())

Then add the tab and panel to index.html (see adore_integration_snippet.html).

Alternatively, call register_with_adore_app(app) from within adore_api.py:

    try:
        from hardware_monitor.web_ui.adore_integration import register_with_adore_app
        register_with_adore_app(app)
        print("✓ hardware_monitor blueprint registered")
    except ImportError as e:
        print(f"⚠ hardware_monitor not available: {e}")
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))


def register_with_adore_app(app, url_prefix: str = '/api/hardware'):
    """
    Register the hardware_monitor blueprint and hardware monitor UI route
    into an existing Flask app instance (e.g. adore_api.app).

    Args:
        app:        The Flask application instance.
        url_prefix: API prefix for hardware endpoints. Default: /api/hardware
    """
    from hardware_monitor.hardware_monitor_api import get_hardware_monitor_blueprint
    from flask import render_template_string, send_from_directory

    bp = get_hardware_monitor_blueprint(url_prefix=url_prefix)
    app.register_blueprint(bp)

    template_path = os.path.join(_HERE, 'templates', 'hardware_monitor.html')

    @app.route('/hardware-monitor')
    def hardware_monitor_ui():
        with open(template_path, 'r') as f:
            return f.read()

    return bp
