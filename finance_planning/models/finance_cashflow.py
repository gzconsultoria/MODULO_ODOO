# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FinanceCashflowPlan(models.Model):
    _name = "finance.cashflow.plan"
    _description = "Planejamento de fluxo de caixa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    name = fields.Char(default=lambda self: _("Planejamento %s") % fields.Date.today(), required=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    item_ids = fields.One2many("finance.cashflow.item", "plan_id", string="Itens de fluxo")
    monthly_income = fields.Monetary(compute="_compute_summary", store=True, currency_field="currency_id")
    monthly_expense = fields.Monetary(compute="_compute_summary", store=True, currency_field="currency_id")
    monthly_surplus = fields.Monetary(compute="_compute_summary", store=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    @api.depends("item_ids", "item_ids.amount", "item_ids.entry_type")
    def _compute_summary(self):
        for plan in self:
            incomes = sum(item.amount for item in plan.item_ids.filtered(lambda i: i.entry_type == "income"))
            expenses = sum(item.amount for item in plan.item_ids.filtered(lambda i: i.entry_type == "expense"))
            plan.monthly_income = incomes
            plan.monthly_expense = expenses
            plan.monthly_surplus = incomes - expenses


class FinanceCashflowItem(models.Model):
    _name = "finance.cashflow.item"
    _description = "Item do planejamento financeiro"
    _order = "entry_type, amount desc"

    plan_id = fields.Many2one("finance.cashflow.plan", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    entry_type = fields.Selection([("income", "Receita"), ("expense", "Despesa")], required=True)
    category = fields.Selection(
        [
            ("housing", "Moradia"),
            ("food", "Alimentação"),
            ("leisure", "Lazer"),
            ("debts", "Dívidas"),
            ("education", "Educação"),
            ("health", "Saúde"),
            ("other", "Outros"),
        ],
        required=True,
    )
    periodicity = fields.Selection(
        [("monthly", "Mensal"), ("yearly", "Anual"), ("one_time", "Pontual")],
        default="monthly",
        required=True,
    )
    amount = fields.Monetary(required=True, currency_field="currency_id")
    actual_amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="plan_id.currency_id", store=True, readonly=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="plan_id.company_id",
        store=True,
        readonly=True,
    )

    @api.constrains("amount")
    def _check_positive_amount(self):
        for item in self:
            if item.amount <= 0:
                raise ValidationError(_("O valor planejado deve ser positivo."))


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    cashflow_plan_ids = fields.One2many("finance.cashflow.plan", "profile_id", string="Planejamentos")
