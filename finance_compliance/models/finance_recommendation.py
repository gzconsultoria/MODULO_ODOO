# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FinanceRecommendation(models.Model):
    _name = "finance.recommendation"
    _description = "Recomendação de investimento auditável"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "recommendation_date desc"

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True, tracking=True)
    goal_id = fields.Many2one("finance.goal", string="Meta relacionada")
    recommendation_date = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    narrative = fields.Html(string="Justificativa técnica", required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("sent", "Enviada"),
            ("ack", "Cliente ciente"),
            ("rejected", "Recusada"),
        ],
        default="draft",
        tracking=True,
    )
    line_ids = fields.One2many("finance.recommendation.line", "recommendation_id", string="Linhas")
    pdf_report_attachment_id = fields.Many2one("ir.attachment", string="Relatório gerado")
    compliance_log_ids = fields.One2many("finance.compliance.log", "recommendation_id")
    impact_overview = fields.Text(string="Impacto esperado")
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    def action_send(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Inclua pelo menos uma linha de recomendação."))
            if rec.profile_id.suitability_state != "valid":
                raise ValidationError(
                    _("A suitability do cliente precisa estar válida para enviar recomendações."))
            rec.state = "sent"
            rec._create_compliance_log("sent")

    def action_acknowledge(self):
        for rec in self:
            rec.state = "ack"
            rec._create_compliance_log("ack")

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"
            rec._create_compliance_log("rejected")

    def _create_compliance_log(self, action):
        message = {
            "sent": _("Recomendação enviada ao cliente."),
            "ack": _("Cliente registrou ciência."),
            "rejected": _("Cliente recusou a recomendação."),
        }[action]
        for rec in self:
            self.env["finance.compliance.log"].create(
                {
                    "profile_id": rec.profile_id.id,
                    "recommendation_id": rec.id,
                    "event": action,
                    "description": message,
                }
            )


class FinanceRecommendationLine(models.Model):
    _name = "finance.recommendation.line"
    _description = "Linha da recomendação"

    recommendation_id = fields.Many2one("finance.recommendation", required=True, ondelete="cascade")
    reference_id = fields.Many2one("finance.asset.ref", required=True)
    action_type = fields.Selection(
        [("buy", "Compra"), ("sell", "Venda"), ("hold", "Manter"), ("rebalance", "Rebalancear")],
        required=True,
    )
    amount = fields.Monetary(currency_field="currency_id")
    rationale_plain = fields.Text(string="Resumo em linguagem simples")
    rationale_expert = fields.Text(string="Resumo técnico")
    risk_notes = fields.Text(string="Riscos do ativo")
    impact_summary = fields.Text(string="Impacto na carteira")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="recommendation_id.company_id",
        store=True,
        readonly=True,
    )

    @api.constrains("reference_id", "recommendation_id")
    def _check_asset_suitability(self):
        for line in self:
            profile = line.recommendation_id.profile_id
            if profile.suitability_profile and line.reference_id.suitability_min_profile:
                allowed_sequence = ["conservative", "moderate", "bold"]
                if allowed_sequence.index(profile.suitability_profile) < allowed_sequence.index(line.reference_id.suitability_min_profile):
                    raise ValidationError(
                        _(
                            "O ativo %(asset)s exige perfil %(required)s. O cliente possui perfil %(actual)s.",
                            asset=line.reference_id.display_name,
                            required=line.reference_id.suitability_min_profile,
                            actual=profile.suitability_profile,
                        )
                    )

