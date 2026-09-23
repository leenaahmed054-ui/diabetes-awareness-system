"""Protected endpoints intended for an external daily scheduler."""

import hmac
import os

from flask import Blueprint, jsonify, request

from app.extensions import csrf
from app.services.notification_scheduler import prepare_daily_ramadan_notifications
from app.services.notification_dispatcher import dispatch_pending_notifications


tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.post("/daily-notifications")
@csrf.exempt
def daily_notifications():
    """Prepare seasonal notices and dispatch all pending WhatsApp messages."""

    expected_secret = os.getenv("CRON_SECRET", "")
    supplied_secret = request.headers.get("X-Cron-Secret", "")

    if not expected_secret or not hmac.compare_digest(expected_secret, supplied_secret):
        return jsonify({"status": "unauthorized"}), 401

    preparation = prepare_daily_ramadan_notifications(batch_size=500)
    dispatch = dispatch_pending_notifications(limit=500)

    return jsonify({
        "status": "completed",
        "preparation": preparation,
        "dispatch": dispatch
    })
