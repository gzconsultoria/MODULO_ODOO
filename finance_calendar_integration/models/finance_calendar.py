# -*- coding: utf-8 -*-
from datetime import timedelta

from markupsafe import escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_datetime


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    finance_profile_id = fields.Many2one("finance.profile", string="Perfil financeiro")
    finance_meeting_type = fields.Selection(
        [
            ("onboarding", "Onboarding"),
            ("portfolio_review", "Revisão de carteira"),
            ("suitability", "Suitability"),
            ("proposal", "Proposta"),
            ("follow_up", "Follow-up"),
        ],
        string="Tipo de reunião",
    )
    finance_recording_url = fields.Char(string="Link da gravação")
    finance_next_step = fields.Text(string="Próximos passos")

    @api.constrains("finance_profile_id", "start", "stop")
    def _check_calendar_conflicts(self):
        for event in self:
            if not event.finance_profile_id or not event.start or not event.stop:
                continue
            overlapping = self.search_count(
                [
                    ("id", "!=", event.id),
                    ("finance_profile_id", "=", event.finance_profile_id.id),
                    ("start", "<", event.stop),
                    ("stop", ">", event.start),
                ]
            )
            if overlapping:
                raise ValidationError(
                    _("Já existe uma reunião financeira agendada nesse intervalo para este cliente."))

    def action_sync_google_meet(self):
        for event in self:
            if not event.finance_profile_id:
                continue
            profile = event.finance_profile_id
            profile.next_meeting_id = event
            profile.message_post(body=_("Reunião sincronizada: %s") % (event.finance_meeting_type or event.name))

    def action_generate_followup_message(self):
        self.ensure_one()
        if not self.finance_profile_id:
            raise UserError(_("Associe a reunião a um cliente para gerar o follow-up."))
        profile = self.finance_profile_id
        advisor = profile.advisor_id or self.env.user
        meeting_date = self.start or fields.Datetime.now()
        meeting_label = dict(self._fields["finance_meeting_type"].selection).get(self.finance_meeting_type, False)
        meeting_topic = meeting_label or self.name or _("consultoria financeira")
        meeting_datetime = format_datetime(self.env, meeting_date, tz=self.env.user.tz, lang_code=self.env.user.lang)
        next_steps_text = self.finance_next_step or profile.objective_summary or _("Entraremos em contato com os próximos passos combinados.")
        step_lines = [line.strip() for line in (next_steps_text or "").splitlines() if line.strip()]
        if not step_lines:
            step_lines = [_("Retornaremos com o plano detalhado.")]
        steps_html = "".join("<li>%s</li>" % escape(line) for line in step_lines)
        body_template = _(
            "<p>Olá %(client)s,</p>"
            "<p>Foi um prazer conversar com você em %(meeting_date)s sobre %(topic)s.</p>"
            "<p>Como combinado, seguem os próximos passos:</p>"
            "<ul>%(steps)s</ul>"
            "<p>Fico à disposição para qualquer dúvida.</p>"
            "<p>Abraços,<br/>%(advisor)s</p>"
        )
        body = body_template % {
            "client": escape(profile.partner_id.name or _("cliente")),
            "meeting_date": escape(meeting_datetime),
            "topic": escape(meeting_topic),
            "steps": steps_html,
            "advisor": escape(advisor.name or self.env.user.name),
        }
        subject = _( "Follow-up da reunião %s") % (self.name or meeting_topic)
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "finance.profile",
                "default_res_id": profile.id,
                "default_composition_mode": "comment",
                "default_partner_ids": [(6, 0, profile.partner_id.ids)],
                "default_subject": subject,
                "default_body": body,
            },
        }


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    event_ids = fields.One2many("calendar.event", "finance_profile_id", string="Reuniões")

    def action_schedule_review(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "calendar.event",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_finance_profile_id": self.id,
                "default_name": _("Revisão financeira"),
                "default_start": fields.Datetime.now() + timedelta(days=7),
                "default_stop": fields.Datetime.now() + timedelta(days=7, hours=1),
                "default_finance_meeting_type": "portfolio_review",
            },
        }
