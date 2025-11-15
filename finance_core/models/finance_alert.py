# -*- coding: utf-8 -*-
from odoo import fields, models


class FinanceAlert(models.Model):
    _name = "finance.alert"
    _description = "Alerta inteligente de consultoria"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "state, trigger_date desc"

    name = fields.Char(required=True)
    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    trigger_date = fields.Date(default=fields.Date.context_today)
    resolved_date = fields.Date(readonly=True)
    state = fields.Selection(
        [("open", "Aberto"), ("in_progress", "Em andamento"), ("done", "Concluído")],
        default="open",
        required=True,
    )
    category = fields.Selection(
        [
            ("goal", "Meta"),
            ("portfolio", "Carteira"),
            ("cashflow", "Fluxo de caixa"),
            ("compliance", "Compliance"),
            ("document", "Documento"),
            ("meeting", "Reunião"),
        ],
        required=True,
        default="goal",
    )
    description = fields.Text()
    action_required = fields.Text(string="Ação necessária")
    responsible_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            for alert in self:
                if alert.state == "done" and not alert.resolved_date:
                    alert.resolved_date = fields.Date.context_today(alert)
                elif alert.state != "done" and alert.resolved_date:
                    alert.resolved_date = False
        return res

