# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FinanceAssetReference(models.Model):
    _name = "finance.asset.ref"
    _description = "Referência única de ativo financeiro"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _sql_constraints = [
        ("finance_asset_ref_unique", "unique(identifier)", "Já existe uma referência com esse identificador."),
    ]

    display_name = fields.Char(compute="_compute_display_name", store=True)
    identifier = fields.Char(required=True, help="Ticker, ISIN ou identificador único do ativo.")
    asset_type = fields.Selection(
        [
            ("fixed_income", "Renda fixa"),
            ("equity_br", "Ação Brasil"),
            ("equity_foreign", "Ação exterior"),
            ("fii", "Fundo imobiliário"),
            ("pension", "Previdência"),
            ("crypto", "Cripto"),
            ("fund", "Fundo"),
            ("other", "Outro"),
        ],
        required=True,
    )
    asset_class = fields.Selection(
        [
            ("conservative", "Conservador"),
            ("moderate", "Moderado"),
            ("aggressive", "Arrojado"),
        ],
        default="moderate",
    )
    name = fields.Char(required=True)
    provider_name = fields.Char(string="Instituição")
    last_price = fields.Float(string="Último preço")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    suitability_min_profile = fields.Selection(
        [
            ("conservative", "Conservador"),
            ("moderate", "Moderado"),
            ("bold", "Arrojado"),
        ],
        default="conservative",
    )

    @api.depends("identifier", "name")
    def _compute_display_name(self):
        for asset in self:
            asset.display_name = f"{asset.identifier or ''} - {asset.name}".strip(" -")


class FinanceAsset(models.Model):
    _name = "finance.asset"
    _description = "Ativo patrimonial do cliente"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    reference_id = fields.Many2one("finance.asset.ref", required=True, ondelete="restrict")
    amount = fields.Monetary(string="Valor", currency_field="currency_id")
    notes = fields.Text()
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("finance_asset_amount_positive", "CHECK(amount >= 0)", "O valor do ativo deve ser positivo."),
    ]


class FinanceLiability(models.Model):
    _name = "finance.liability"
    _description = "Passivo do cliente"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    liability_type = fields.Selection(
        [
            ("loan", "Empréstimo"),
            ("financing", "Financiamento"),
            ("credit_card", "Cartão de crédito"),
            ("consortium", "Consórcio"),
            ("other", "Outro"),
        ],
        required=True,
    )
    outstanding_balance = fields.Monetary(currency_field="currency_id")
    interest_rate = fields.Float(string="Taxa de juros a.a.")
    maturity_date = fields.Date()
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("finance_liability_balance_positive", "CHECK(outstanding_balance >= 0)", "O saldo deve ser positivo."),
    ]


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    asset_ids = fields.One2many("finance.asset", "profile_id", string="Ativos")
    liability_ids = fields.One2many("finance.liability", "profile_id", string="Passivos")

    def _generate_smart_alerts(self):
        super()._generate_smart_alerts()
        for profile in self:
            overweight_assets = profile.portfolio_snapshot_ids.filtered(lambda s: s.allocation_warning)
            if overweight_assets:
                profile.advisory_alert_ids.filtered(lambda a: a.category == "portfolio").write({"state": "open"})
