# -*- coding: utf-8 -*-
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FinanceGoal(models.Model):
    _name = "finance.goal"
    _description = "Meta financeira do cliente"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True, tracking=True)
    goal_type = fields.Selection(
        [
            ("retirement", "Aposentadoria"),
            ("education", "Educação"),
            ("house", "Casa"),
            ("emergency", "Reserva de emergência"),
            ("freedom", "Independência financeira"),
            ("other", "Outra"),
        ],
        required=True,
        tracking=True,
    )
    target_amount = fields.Monetary(required=True, currency_field="currency_id", tracking=True)
    accumulated_amount = fields.Monetary(currency_field="currency_id", tracking=True)
    horizon_date = fields.Date(string="Prazo alvo", required=True, tracking=True)
    periodic_contribution = fields.Monetary(currency_field="currency_id", tracking=True)
    probability = fields.Float(string="Probabilidade de atingir", tracking=True)
    state = fields.Selection(
        [("draft", "Planejamento"), ("active", "Em andamento"), ("achieved", "Atingida"), ("archived", "Arquivada")],
        default="draft",
        tracking=True,
    )
    description = fields.Html()
    progress_ratio = fields.Float(compute="_compute_progress_ratio", store=True)
    is_late = fields.Boolean(compute="_compute_is_late", store=True)
    alert_message = fields.Char(compute="_compute_alert_message")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("goal_positive_target", "CHECK(target_amount > 0)", "O valor alvo deve ser maior que zero."),
    ]

    @api.depends("accumulated_amount", "target_amount")
    def _compute_progress_ratio(self):
        for goal in self:
            if goal.target_amount:
                goal.progress_ratio = min(goal.accumulated_amount / goal.target_amount, 1.0)
            else:
                goal.progress_ratio = 0.0

    @api.depends("horizon_date", "state", "progress_ratio")
    def _compute_is_late(self):
        today = date.today()
        for goal in self:
            goal.is_late = bool(
                goal.state == "active"
                and goal.horizon_date
                and goal.horizon_date < today
                and goal.progress_ratio < 1.0
            )

    @api.depends("is_late", "progress_ratio", "horizon_date")
    def _compute_alert_message(self):
        for goal in self:
            if goal.is_late:
                goal.alert_message = _(
                    "A meta %(name)s deveria ter sido atingida em %(date)s e está com progresso de %(progress)s%%.",
                    name=goal.name,
                    date=goal.horizon_date,
                    progress=int(goal.progress_ratio * 100),
                )
            else:
                goal.alert_message = False

    @api.constrains("state", "horizon_date")
    def _check_active_goal_has_horizon(self):
        for goal in self:
            if goal.state == "active" and not goal.horizon_date:
                raise ValidationError(_("Metas ativas precisam de um prazo definido."))

    @api.constrains("probability")
    def _check_probability_range(self):
        for goal in self:
            if goal.probability and not 0 <= goal.probability <= 100:
                raise ValidationError(_("A probabilidade deve estar entre 0 e 100."))


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    goal_ids = fields.One2many("finance.goal", "profile_id", string="Metas financeiras")

    def action_open_goal_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.goal.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_profile_id": self.id},
        }
