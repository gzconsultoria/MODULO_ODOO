# -*- coding: utf-8 -*-
from odoo import _, fields, models


class FinanceRecommendationWizard(models.TransientModel):
    _name = "finance.recommendation.wizard"
    _description = "Assistente guiado de recomendação"

    profile_id = fields.Many2one("finance.profile", required=True)
    goal_id = fields.Many2one("finance.goal", domain="[('profile_id', '=', profile_id)]")
    narrative = fields.Html(string="Justificativa técnica", required=True)
    impact_overview = fields.Text(string="Impacto esperado")
    send_now = fields.Boolean(string="Enviar imediatamente", default=True)
    line_ids = fields.One2many("finance.recommendation.wizard.line", "wizard_id", string="Linhas")

    def action_confirm(self):
        self.ensure_one()
        recommendation_vals = {
            "profile_id": self.profile_id.id,
            "goal_id": self.goal_id.id,
            "narrative": self.narrative,
            "impact_overview": self.impact_overview,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "reference_id": line.reference_id.id,
                        "action_type": line.action_type,
                        "amount": line.amount,
                        "rationale_plain": line.rationale_plain,
                        "rationale_expert": line.rationale_expert,
                        "risk_notes": line.risk_notes,
                        "impact_summary": line.impact_summary,
                    },
                )
                for line in self.line_ids
            ],
        }
        recommendation = self.env["finance.recommendation"].create(recommendation_vals)
        if self.send_now:
            recommendation.action_send()
        action = {
            "type": "ir.actions.act_window",
            "res_model": "finance.recommendation",
            "res_id": recommendation.id,
            "view_mode": "form",
        }
        return action


class FinanceRecommendationWizardLine(models.TransientModel):
    _name = "finance.recommendation.wizard.line"
    _description = "Linha temporária da recomendação"

    wizard_id = fields.Many2one("finance.recommendation.wizard", required=True, ondelete="cascade")
    reference_id = fields.Many2one("finance.asset.ref", required=True)
    action_type = fields.Selection(
        selection=lambda self: self.env["finance.recommendation.line"]._fields["action_type"].selection,
        required=True,
    )
    amount = fields.Monetary(currency_field="currency_id")
    rationale_plain = fields.Text(string="Resumo simples")
    rationale_expert = fields.Text(string="Resumo técnico")
    risk_notes = fields.Text(string="Riscos")
    impact_summary = fields.Text(string="Impacto na carteira")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
