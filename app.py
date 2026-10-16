import os
from pathlib import Path

from dotenv import load_dotenv

# IMPORTANT:
# Load .env BEFORE importing Config because Config reads environment
# variables when the class is created.
load_dotenv()

from flask import Flask, jsonify, render_template, request, send_file, url_for

from config import Config
from models import Analysis, db
from services.analyzer import (
    InvalidInstagramUrl,
    NoCommentsError,
    analyze_url,
    run_analysis,
)
from services.classifier import ModelUnavailableError
from services.scraper import ScraperError, scrape_comments
from utils.csv_export import analysis_csv


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------
    database_url = app.config["DATABASE_URL"]

    if database_url.lower().startswith("sqlite:///"):
        database_path = Path(database_url.removeprefix("sqlite:///"))

        if str(database_path) != ":memory:":
            if not database_path.is_absolute():
                database_path = Path(app.root_path) / database_path

            database_path.parent.mkdir(parents=True, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------------------------------------------------------
    # APPLICATION STATUS
    # ---------------------------------------------------------
    @app.context_processor
    def inject_app_status():
        classifier = app.extensions.get("toxicity_classifier")

        return {
            "model_status": (
                classifier.status
                if classifier
                else "Local model ready"
            ),
            "mock_mode": app.config["MOCK_SCRAPER"],
        }

    # ---------------------------------------------------------
    # PAGES
    # ---------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/analyze")
    def analyze_page():
        return render_template("index.html")

    @app.get("/history")
    def history_page():
        analyses = Analysis.query.order_by(
            Analysis.created_at.desc()
        ).all()

        return render_template(
            "history.html",
            analyses=analyses,
        )

    @app.get("/analysis/<int:analysis_id>")
    def analysis_page(analysis_id: int):
        analysis = Analysis.query.get_or_404(analysis_id)

        return render_template(
            "analysis.html",
            analysis=analysis,
            analysis_json=analysis.to_dict(
                include_comments=True
            ),
        )

    # ---------------------------------------------------------
    # COMMON RESPONSE
    # ---------------------------------------------------------
    def _analysis_response(analysis: Analysis):
        payload = analysis.to_dict(include_comments=True)

        payload["success"] = True
        payload["analysis_id"] = analysis.id
        payload["detail_url"] = url_for(
            "analysis_page",
            analysis_id=analysis.id,
        )

        return jsonify(payload)

    # ---------------------------------------------------------
    # REAL INSTAGRAM ANALYSIS
    # ---------------------------------------------------------
    @app.post("/api/analyze")
    def analyze_api():
        payload = request.get_json(silent=True) or request.form

        try:
            url = str(payload.get("url", "")).strip()

            analysis = analyze_url(url)

            return _analysis_response(analysis)

        except InvalidInstagramUrl as exc:
            return jsonify({
                "success": False,
                "error": str(exc),
            }), 400

        except (NoCommentsError, ScraperError) as exc:
            return jsonify({
                "success": False,
                "error": str(exc),
            }), 422

        except ModelUnavailableError as exc:
            return jsonify({
                "success": False,
                "error": str(exc),
            }), 503

        except Exception:
            app.logger.exception(
                "Analysis request failed"
            )

            return jsonify({
                "success": False,
                "error": (
                    "The analysis could not be "
                    "completed. Please try again."
                ),
            }), 500

    # ---------------------------------------------------------
    # DEMO
    #
    # IMPORTANT:
    # Demo NEVER calls Apify.
    # It directly uses DEMO_COMMENTS from scraper.py.
    # ---------------------------------------------------------
    @app.post("/api/demo")
    def demo_api():
        try:
            print("=" * 60)
            print("DEMO MODE: using local sample comments")
            print("DEMO MODE: Apify will NOT be called")
            print("=" * 60)

            comments = scrape_comments(
                "https://www.instagram.com/demo-post/",
                mock_mode=True,
                apify_token="",
                actor_id="",
            )

            print(
                f"DEMO: loaded {len(comments)} local comments"
            )

            analysis = run_analysis(
                "Demo data (local sample comments)",
                comments,
                is_demo=True,
            )

            print(
                f"DEMO: analyzed "
                f"{analysis.comments_analyzed} comments"
            )

            return _analysis_response(analysis)

        except (
            NoCommentsError,
            ScraperError,
            ModelUnavailableError,
        ) as exc:
            app.logger.exception(
                "Demo request failed"
            )

            return jsonify({
                "success": False,
                "error": str(exc),
            }), 422

        except Exception:
            app.logger.exception(
                "Demo request failed"
            )

            return jsonify({
                "success": False,
                "error": (
                    "The demo could not be completed. "
                    "Please try again."
                ),
            }), 500

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------
    @app.get("/api/history")
    def history_api():
        analyses = Analysis.query.order_by(
            Analysis.created_at.desc()
        ).all()

        return jsonify({
            "success": True,
            "analyses": [
                item.to_dict()
                for item in analyses
            ],
        })

    # ---------------------------------------------------------
    # SINGLE ANALYSIS API
    # ---------------------------------------------------------
    @app.get("/api/analysis/<int:analysis_id>")
    def analysis_api(analysis_id: int):
        analysis = Analysis.query.get_or_404(
            analysis_id
        )

        return jsonify({
            "success": True,
            **analysis.to_dict(
                include_comments=True
            ),
        })

    # ---------------------------------------------------------
    # DELETE ANALYSIS
    # ---------------------------------------------------------
    @app.delete("/api/analysis/<int:analysis_id>")
    def delete_analysis_api(analysis_id: int):
        analysis = Analysis.query.get_or_404(
            analysis_id
        )

        db.session.delete(analysis)
        db.session.commit()

        return jsonify({
            "success": True
        })

    # ---------------------------------------------------------
    # CSV EXPORT
    # ---------------------------------------------------------
    @app.get("/api/analysis/<int:analysis_id>/export")
    def export_analysis_api(analysis_id: int):
        analysis = Analysis.query.get_or_404(
            analysis_id
        )

        return send_file(
            analysis_csv(analysis),
            mimetype="text/csv",
            as_attachment=True,
            download_name=(
                f"analysis_{analysis.id}.csv"
            ),
        )

    # ---------------------------------------------------------
    # ERROR HANDLERS
    # ---------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return (
            render_template(
                "error.html",
                code=400,
                message="That request was not valid.",
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": (
                    "The requested resource "
                    "was not found."
                ),
            }), 404

        return (
            render_template(
                "error.html",
                code=404,
                message=(
                    "The page you requested "
                    "was not found."
                ),
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()

        return (
            render_template(
                "error.html",
                code=500,
                message=(
                    "Something went wrong "
                    "on the server. Please try again."
                ),
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", "5000")
        ),
        debug=(
            os.environ.get(
                "FLASK_DEBUG",
                "false",
            ).lower()
            == "true"
        ),
    )