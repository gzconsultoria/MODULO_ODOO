# -*- coding: utf-8 -*-
from datetime import date

from odoo import _, api, fields, models
from odoo.addons.queue_job.job import job
from odoo.exceptions import ValidationError


class FinancePortfolio(models.Model):
    _name = "finance.portfolio"
    _description = "Carteira de investimentos do cliente"
    _inherit = ["mail.thread"]

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True, default=lambda self: _("Carteira principal"))
    target_allocation = fields.Json(string="Alocação alvo", help="Distribuição alvo por classe de ativo")
    benchmark = fields.Selection(
        [
            ("cdi", "CDI"),
            ("ipca_plus", "IPCA+"),
            ("ibov", "Ibovespa"),
            ("mixed", "Composta"),
        ],
        default="cdi",
    )
    snapshot_ids = fields.One2many("finance.portfolio.snapshot", "portfolio_id", string="Snapshots")
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    def action_create_snapshot(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.portfolio.snapshot.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_portfolio_id": self.id},
        }

    def action_open_review_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.review.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_profile_id": self.profile_id.id,
                "default_portfolio_id": self.id,
            },
        }


class FinancePortfolioSnapshot(models.Model):
    _name = "finance.portfolio.snapshot"
    _description = "Snapshot versionado da carteira"
    _order = "snapshot_date desc"

    portfolio_id = fields.Many2one("finance.portfolio", required=True, ondelete="cascade", index=True)
    profile_id = fields.Many2one(related="portfolio_id.profile_id", store=True)
    snapshot_date = fields.Date(default=fields.Date.context_today, required=True)
    position_ids = fields.One2many("finance.portfolio.position", "snapshot_id", string="Posições")
    market_value = fields.Monetary(currency_field="currency_id", compute="_compute_market_value", store=True)
    allocation_warning = fields.Char()
    notes = fields.Text()
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="portfolio_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("portfolio_snapshot_unique", "unique(portfolio_id, snapshot_date)", "Já existe um snapshot para esta data."),
    ]

    @api.depends("position_ids", "position_ids.market_value")
    def _compute_market_value(self):
        for snapshot in self:
            snapshot.market_value = sum(snapshot.position_ids.mapped("market_value"))

    @api.constrains("snapshot_date")
    def _check_snapshot_date(self):
        for snapshot in self:
            if snapshot.snapshot_date > date.today():
                raise ValidationError(_("O snapshot não pode estar no futuro."))

    def evaluate_allocation(self):
        for snapshot in self:
            target = snapshot.portfolio_id.target_allocation or {}
            if not target:
                snapshot.allocation_warning = False
                continue
            deviation_messages = []
            actual_totals = {}
            total_value = snapshot.market_value or 0
            for position in snapshot.position_ids:
                asset_class = position.reference_id.asset_type
                actual_totals.setdefault(asset_class, 0.0)
                actual_totals[asset_class] += position.market_value
            for asset_class, target_pct in target.items():
                actual_value = actual_totals.get(asset_class, 0.0)
                actual_pct = (actual_value / total_value * 100.0) if total_value else 0
                if abs(actual_pct - target_pct) > 10:
                    deviation_messages.append(
                        _(
                            "Classe %(asset_class)s com %(actual).1f%% vs meta %(target).1f%%.",
                            asset_class=asset_class,
                            actual=actual_pct,
                            target=target_pct,
                        )
                    )
            snapshot.allocation_warning = "\n".join(deviation_messages) if deviation_messages else False

    @job(default_channel="root.finance")
    def job_post_process_snapshot(self):
        self.ensure_one()
        self.evaluate_allocation()
        self.profile_id.message_post(
            body=_("Snapshot de %(date)s processado com sucesso.", date=self.snapshot_date),
        )
        if self.allocation_warning:
            self.profile_id.advisory_alert_ids.create(
                {
                    "profile_id": self.profile_id.id,
                    "name": _("Rebalanceamento sugerido"),
                    "category": "portfolio",
                    "description": self.allocation_warning,
                }
            )


class FinancePortfolioPosition(models.Model):
    _name = "finance.portfolio.position"
    _description = "Posição de investimento"

    snapshot_id = fields.Many2one("finance.portfolio.snapshot", required=True, ondelete="cascade", index=True)
    reference_id = fields.Many2one("finance.asset.ref", required=True, ondelete="restrict")
    quantity = fields.Float(required=True)
    avg_price = fields.Monetary(currency_field="currency_id")
    market_price = fields.Float()
    market_value = fields.Monetary(currency_field="currency_id", compute="_compute_market_value", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="snapshot_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("finance_position_quantity_positive", "CHECK(quantity >= 0)", "A quantidade não pode ser negativa."),
    ]

    @api.depends("quantity", "market_price")
    def _compute_market_value(self):
        for position in self:
            position.market_value = (position.market_price or 0.0) * position.quantity

    @api.constrains("reference_id", "snapshot_id")
    def _check_unique_reference_per_snapshot(self):
        for position in self:
            duplicates = self.search_count(
                [
                    ("snapshot_id", "=", position.snapshot_id.id),
                    ("reference_id", "=", position.reference_id.id),
                    ("id", "!=", position.id),
                ]
            )
            if duplicates:
                raise ValidationError(_("Não é permitido duplicar o mesmo ativo dentro do snapshot."))


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    portfolio_ids = fields.One2many("finance.portfolio", "profile_id", string="Portfólios")
    portfolio_snapshot_ids = fields.One2many("finance.portfolio.snapshot", "profile_id", string="Snapshots")

    @api.depends("portfolio_snapshot_ids", "portfolio_snapshot_ids.market_value")
    def _compute_financial_snapshots(self):
        super()._compute_financial_snapshots()
        for profile in self:
            snapshots = profile.portfolio_snapshot_ids.sorted(lambda s: s.snapshot_date, reverse=True)
            if snapshots:
                profile.portfolio_value = snapshots[0].market_value

