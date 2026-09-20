
"""
Flask CLI Commands.

الأمر الأول:
prepare-ramadan-notifications
يفحص فترة رمضان ويجهز الإشعارات في MySQL.

الأمر الثاني:
dispatch-whatsapp
يعالج الإشعارات pending ويرسلها أو يختبرها
بحسب قيمة WHATSAPP_DRY_RUN.
"""

import json

import click
from flask import current_app

from app.services.notification_scheduler import (
    prepare_daily_ramadan_notifications
)

from app.services.notification_dispatcher import (
    dispatch_pending_notifications
)


def register_commands(app):
    """
    تسجيل أوامر الإشعارات داخل تطبيق Flask.
    """

    @app.cli.command(
        "prepare-ramadan-notifications"
    )
    @click.option(
        "--target-date",
        default=None,
        help=(
            "Optional date in YYYY-MM-DD format. "
            "If omitted, Saudi Arabia's current date is used."
        )
    )
    @click.option(
        "--batch-size",
        default=100,
        type=click.IntRange(min=1, max=1000),
        show_default=True,
        help="Number of users processed in each batch."
    )
    def prepare_ramadan_command(
        target_date,
        batch_size
    ):
        """
        تجهيز إشعارات رمضان للمستخدمين المؤهلين.
        """

        current_app.logger.info(
            "Starting Ramadan notification preparation."
        )

        result = prepare_daily_ramadan_notifications(
            target_date=target_date,
            batch_size=batch_size
        )

        # طباعة تقرير منظم دون أرقام هواتف.
        click.echo(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        # إرجاع خطأ للنظام إذا فشل أي مستخدم.
        if result.get("failed", 0) > 0:
            raise click.ClickException(
                "Some Ramadan notifications failed."
            )

    @app.cli.command("dispatch-whatsapp")
    @click.option(
        "--limit",
        default=100,
        type=click.IntRange(min=1, max=1000),
        show_default=True,
        help=(
            "Maximum number of pending notifications "
            "to process."
        )
    )
    def dispatch_whatsapp_command(limit):
        """
        إرسال أو اختبار إشعارات WhatsApp المعلقة.
        """

        current_app.logger.info(
            "Starting WhatsApp notification dispatch."
        )

        result = dispatch_pending_notifications(
            limit=limit
        )

        # تقرير الإرسال لا يحتوي أرقام الهواتف.
        click.echo(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        # توضيح وضع التشغيل للمستخدم.
        if result["mode"] == "dry_run":
            click.echo(
                "DRY_RUN is active. "
                "No real WhatsApp messages were sent."
            )

        if result["failed"] > 0:
            raise click.ClickException(
                "Some WhatsApp notifications failed."
            )
