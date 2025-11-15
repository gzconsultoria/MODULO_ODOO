# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models


class FinanceOnboardingWizard(models.TransientModel):
    _name = "finance.onboarding.wizard"
    _description = "Assistente guiado de onboarding financeiro"

    partner_id = fields.Many2one("res.partner", required=True, string="Cliente")
    advisor_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    investor_type = fields.Selection(
        [("pf", "Pessoa física"), ("pj", "Pessoa jurídica")],
        required=True,
        default="pf",
    )
    annual_income = fields.Monetary(currency_field="currency_id", string="Renda anual")
    net_worth = fields.Monetary(currency_field="currency_id", string="Patrimônio líquido")
    emergency_fund_months = fields.Float(string="Meses de reserva")
    saving_capacity = fields.Monetary(currency_field="currency_id", string="Capacidade de poupança mensal")
    suitability_profile = fields.Selection(
        [("conservative", "Conservador"), ("moderate", "Moderado"), ("bold", "Arrojado")],
        string="Perfil de risco",
    )
    suitability_score = fields.Integer(string="Pontuação suitability")
    suitability_last_review = fields.Date(string="Última revisão")
    compliance_status = fields.Selection(
        [("clean", "Em conformidade"), ("pending", "Pendências"), ("restricted", "Restrito")],
        default="clean",
    )
    objective_summary = fields.Text(string="Objetivos do cliente")
    risk_warnings = fields.Text(string="Alertas de risco")
    monthly_income_estimate = fields.Monetary(currency_field="currency_id", string="Receitas mensais")
    monthly_expense_estimate = fields.Monetary(currency_field="currency_id", string="Despesas mensais")
    next_review_suggestion = fields.Datetime(
        string="Sugestão de próxima revisão",
        default=lambda self: fields.Datetime.now() + timedelta(days=90),
    )
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.investor_type = "pj" if self.partner_id.company_type == "company" else "pf"

    def action_confirm(self):
        self.ensure_one()
        profile = self.env["finance.profile"].search([("partner_id", "=", self.partner_id.id)], limit=1)
        if not profile:
            profile = self.env["finance.profile"].create(
                {
                    "partner_id": self.partner_id.id,
                    "advisor_id": self.advisor_id.id,
                    "investor_type": self.investor_type,
                    "company_id": self.env.company.id,
                }
            )
        profile_vals = {
            "annual_income": self.annual_income,
            "net_worth": self.net_worth,
            "emergency_fund_months": self.emergency_fund_months,
            "saving_capacity": self.saving_capacity,
            "suitability_profile": self.suitability_profile,
            "suitability_score": self.suitability_score,
            "suitability_last_review": self.suitability_last_review,
            "compliance_status": self.compliance_status,
            "objective_summary": self.objective_summary,
            "risk_warnings": self.risk_warnings,
            "advisor_id": self.advisor_id.id,
        }
        profile.write(profile_vals)
        if self.monthly_income_estimate or self.monthly_expense_estimate:
            self._create_cashflow_snapshot(profile)
        if self.next_review_suggestion and "calendar.event" in self.env:
            self.env["calendar.event"].create(
                {
                    "name": _("Revisão financeira"),
                    "start": self.next_review_suggestion,
                    "stop": self.next_review_suggestion + timedelta(hours=1),
                    "finance_profile_id": profile.id,
                    "finance_meeting_type": "onboarding",
                    "partner_ids": [(6, 0, profile.partner_id.ids)],
                }
            )
        profile.message_post(body=_("Onboarding financeiro atualizado via assistente."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.profile",
            "res_id": profile.id,
            "view_mode": "form",
        }

    def _create_cashflow_snapshot(self, profile):
        if "finance.cashflow.plan" not in self.env:
            return
        plan = self.env["finance.cashflow.plan"].create(
            {
                "profile_id": profile.id,
                "name": _("Fluxo inicial"),
            }
        )
        if self.monthly_income_estimate:
            self.env["finance.cashflow.item"].create(
                {
                    "plan_id": plan.id,
                    "name": _("Receita informada"),
                    "entry_type": "income",
                    "category": "other",
                    "amount": self.monthly_income_estimate,
                }
            )
        if self.monthly_expense_estimate:
            self.env["finance.cashflow.item"].create(
                {
                    "plan_id": plan.id,
                    "name": _("Despesas informadas"),
                    "entry_type": "expense",
                    "category": "other",
                    "amount": self.monthly_expense_estimate,
                }
            )
