# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models


class FinanceReviewWizard(models.TransientModel):
    _name = "finance.review.wizard"
    _description = "Assistente de revisão trimestral de carteira"

    profile_id = fields.Many2one("finance.profile", required=True)
    portfolio_id = fields.Many2one(
        "finance.portfolio",
        required=True,
        domain="[('profile_id', '=', profile_id)]",
    )
    review_date = fields.Date(default=fields.Date.context_today, required=True)
    include_snapshot = fields.Boolean(default=True, string="Atualizar snapshot")
    create_meeting = fields.Boolean(default=True, string="Agendar reunião")
    meeting_datetime = fields.Datetime(
        default=lambda self: fields.Datetime.now() + timedelta(days=3),
        string="Data da reunião",
    )
    create_followup_activity = fields.Boolean(default=True, string="Criar tarefa de follow-up")
    deviation_summary = fields.Text(compute="_compute_deviation_summary")
    notes = fields.Text(string="Notas da revisão")

    @api.depends("portfolio_id")
    def _compute_deviation_summary(self):
        for wizard in self:
            summary = []
            if not wizard.portfolio_id:
                wizard.deviation_summary = False
                continue
            latest_snapshot = wizard.portfolio_id.snapshot_ids[:1]
            if latest_snapshot and latest_snapshot.allocation_warning:
                summary.append(latest_snapshot.allocation_warning)
            if wizard.profile_id and wizard.profile_id.advisory_alert_ids:
                alerts = wizard.profile_id.advisory_alert_ids.filtered(lambda a: a.state != "done")
                if alerts:
                    summary.extend(alerts.mapped("description"))
            wizard.deviation_summary = "\n".join(filter(None, summary)) or False

    def action_confirm(self):
        self.ensure_one()
        snapshot = False
        if self.include_snapshot:
            snapshot = self.env["finance.portfolio.snapshot"].create(
                {
                    "portfolio_id": self.portfolio_id.id,
                    "snapshot_date": self.review_date,
                }
            )
            snapshot.with_delay(priority=5).job_post_process_snapshot()
        if self.create_meeting and "calendar.event" in self.env:
            start = self.meeting_datetime or fields.Datetime.now()
            self.env["calendar.event"].create(
                {
                    "name": _("Revisão de carteira"),
                    "start": start,
                    "stop": start + timedelta(hours=1),
                    "finance_profile_id": self.profile_id.id,
                    "finance_meeting_type": "portfolio_review",
                    "partner_ids": [(6, 0, self.profile_id.partner_id.ids)],
                    "description": self.notes,
                }
            )
        if self.create_followup_activity:
            activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
            if activity_type:
                self.env["mail.activity"].create(
                    {
                        "res_model_id": self.env["ir.model"]._get_id("finance.profile"),
                        "res_id": self.profile_id.id,
                        "activity_type_id": activity_type.id,
                        "summary": _("Enviar relatório da revisão"),
                        "note": self.notes or _("Compartilhar insights da revisão trimestral."),
                        "user_id": self.profile_id.advisor_id.id or self.env.user.id,
                        "date_deadline": fields.Date.context_today(self),
                    }
                )
        self.profile_id.message_post(body=_("Revisão trimestral concluída."), message_type="comment")
        if snapshot:
            return {
                "type": "ir.actions.act_window",
                "res_model": "finance.portfolio.snapshot",
                "view_mode": "form",
                "res_id": snapshot.id,
            }
        return {"type": "ir.actions.act_window_close"}
