import os

from flask import url_for


from flask import request

def register_context_processors(app):
    @app.after_request
    def add_cache_control(response):
        # Exclude static files from cache control header overriding
        if request.endpoint and request.endpoint != "static":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.context_processor
    def inject_asset_version():
        return {"ASSET_VERSION": app.config.get("ASSET_VERSION", "1")}

    @app.context_processor
    def inject_brand_logo():
        custom_logo_path = os.path.join(app.root_path, "img", "honda.jpg")
        if os.path.exists(custom_logo_path):
            return {"brand_logo_url": url_for("system_bp.brand_logo")}

        candidates = ["images/logo.jpg", "images/logo.png", "images/logo.svg"]
        for candidate in candidates:
            static_candidate_path = os.path.join(app.root_path, "static", candidate)
            if os.path.exists(static_candidate_path):
                return {"brand_logo_url": url_for("static", filename=candidate)}
        return {"brand_logo_url": url_for("static", filename="images/logo.svg")}
