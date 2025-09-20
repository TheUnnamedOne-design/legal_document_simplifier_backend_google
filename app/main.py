from flask import Flask
from app.routes.legal import legal_bp
from app.services.model_loader import embedding_model, legal_model, reranker
from flask_cors import CORS
import os



def create_app():
    app = Flask(__name__)

    frontend_origin = os.getenv("FRONTEND_URL", "*")  # fallback to "*" if not set
    CORS(app, origins=[frontend_origin])

    # Register blueprints
    app.register_blueprint(legal_bp, url_prefix="/api/legal")

    @app.route("/ping", methods=["GET"])
    def ping():
        return {"message": "pong"}, 200
    

    api_key = os.getenv("GEMINI_API_KEY")
    #print("Current API key:", api_key)

    @app.route("/")
    def home():
        return {"status": "Legal AI Backend Running"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
