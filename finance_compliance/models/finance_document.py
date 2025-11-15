# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class FinanceComplianceLog(models.Model):
    _name = "finance.compliance.log"
    _description = "Trilha de auditoria financeira"
    _order = "create_date desc"

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    recommendation_id = fields.Many2one("finance.recommendation")
    event = fields.Selection(
        [("sent", "Enviada"), ("ack", "Cliente ciente"), ("rejected", "Recusada"), ("document", "Documento")],
        required=True,
    )
    description = fields.Text(required=True, readonly=True)
    create_date = fields.Datetime(readonly=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    def unlink(self):
        raise ValidationError(_("Os logs de compliance são imutáveis."))

class FinanceDocument(models.Model):
    _name = "finance.document"
    _description = "Documentos de compliance"
    _inherit = ["mail.thread"]

    profile_id = fields.Many2one("finance.profile", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    category = fields.Selection(
        [
            ("suitability", "Suitability"),
            ("policy", "Política de investimento"),
            ("report", "Relatório"),
            ("contract", "Contrato"),
            ("other", "Outro"),
        ],
        required=True,
    )
    attachment_id = fields.Many2one("ir.attachment", string="Arquivo")
    expiration_date = fields.Date()
    is_expired = fields.Boolean(compute="_compute_is_expired", store=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="profile_id.company_id",
        store=True,
        readonly=True,
    )

    @fields.depends("expiration_date")
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for doc in self:
            doc.is_expired = bool(doc.expiration_date and doc.expiration_date < today)
