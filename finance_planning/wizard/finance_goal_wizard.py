# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class FinanceGoalWizard(models.TransientModel):
    _name = "finance.goal.wizard"
    _description = "Assistente de criação de metas financeiras"

    profile_id = fields.Many2one("finance.profile", required=True)
    goal_type = fields.Selection(
        selection=lambda self: self.env["finance.goal"]._fields["goal_type"].selection,
        string="Tipo de meta",
    )
    template_id = fields.Many2one("finance.goal.template", string="Modelo sugerido")
    name = fields.Char(string="Nome da meta", required=True)
    target_amount = fields.Monetary(currency_field="currency_id", required=True)
    horizon_date = fields.Date()
    periodic_contribution = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if self.template_id:
            self.name = self.template_id.name
            self.goal_type = self.template_id.goal_type
            self.target_amount = self.template_id.target_amount
            self.periodic_contribution = self.template_id.periodic_contribution

    def action_create_goal(self):
        self.ensure_one()
        vals = {
            "profile_id": self.profile_id.id,
            "name": self.name or self.template_id.name,
            "goal_type": self.goal_type or self.template_id.goal_type,
            "target_amount": self.target_amount or self.template_id.target_amount,
            "horizon_date": self.horizon_date,
            "periodic_contribution": self.periodic_contribution,
            "state": "active",
        }
        goal = self.env["finance.goal"].create(vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.goal",
            "res_id": goal.id,
            "view_mode": "form",
        }


class FinanceGoalTemplate(models.Model):
    _name = "finance.goal.template"
    _description = "Modelo de meta financeira"

    name = fields.Char(required=True)
    goal_type = fields.Selection(
        selection=lambda self: self.env["finance.goal"]._fields["goal_type"].selection,
        required=True,
    )
    target_amount = fields.Monetary(currency_field="currency_id")
    periodic_contribution = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
