# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    finance_profile_id = fields.Many2one("finance.profile", string="Perfil financeiro")
    finance_expected_aum = fields.Monetary(string="AUM estimado", currency_field="company_currency")
    finance_origin = fields.Selection(
        [
            ("referral", "Indicação"),
            ("event", "Evento"),
            ("online", "Canal digital"),
            ("other", "Outro"),
        ],
        string="Origem financeira",
    )
    finance_services = fields.Selection(
        [
            ("wealth", "Gestão de patrimônio"),
            ("planning", "Planejamento"),
            ("pension", "Previdência"),
            ("other", "Outros"),
        ],
        string="Serviço desejado",
    )
    finance_suitability_status = fields.Selection(
        [("draft", "Não iniciado"), ("in_progress", "Em andamento"), ("done", "Concluído")],
        default="draft",
    )

    def action_create_finance_profile(self):
        for lead in self:
            partner = lead.partner_id or lead._create_lead_partner()
            profile = self.env["finance.profile"].search([("partner_id", "=", partner.id)], limit=1)
            if not profile:
                profile = self.env["finance.profile"].create(
                    {
                        "partner_id": partner.id,
                        "advisor_id": self.env.user.id,
                        "investor_type": "pf" if partner.company_type != "company" else "pj",
                        "annual_income": lead.planned_revenue,
                        "saving_capacity": lead.expected_revenue,
                    }
                )
            lead.finance_profile_id = profile
            lead.message_post(body=_("Perfil financeiro criado e vinculado."))
            if lead.stage_id and lead.stage_id.is_won:
                profile.onboarding_stage = "diagnosis"
        return True

    @api.onchange("finance_profile_id")
    def _onchange_finance_profile_id(self):
        if self.finance_profile_id:
            self.partner_id = self.finance_profile_id.partner_id

