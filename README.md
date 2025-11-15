# Finance Advisory Suite

Conjunto modular de aplicativos Odoo que centraliza dados do cliente, metas, planejamento, investimentos, recomendações e compliance sem duplicar cadastros nativos.

## Visão geral

Cada domínio financeiro é tratado como um módulo independente para facilitar evolução, performance e implantação gradual. Todos se apoiam em um perfil financeiro 1:1 com o contato (`res.partner`).

| Módulo | Objetivo |
| --- | --- |
| `finance_core` | Perfil financeiro, alertas inteligentes, dashboard 360° e grupos de segurança. |
| `finance_planning` | Metas, fluxo de caixa e wizard de onboarding de metas. |
| `finance_investments` | Biblioteca única de ativos, carteiras versionadas, snapshots e rebalanceamento. |
| `finance_compliance` | Recomendações auditáveis, documentos e trilha de compliance. |
| `finance_portal` | Portal do cliente com visão 360°, upload seguro e mensagens. |
| `finance_crm_integration` | Campos e botão de conversão no `crm.lead`. |
| `finance_calendar_integration` | Extensões de agenda com tipos de reunião, gravação e conflitos. |
| `finance_reports` | Relatório PDF 360° pronto para compartilhar com o cliente. |

## Principais recursos

- Perfil financeiro dedicado (`finance.profile`) vinculado ao contato com score, suitability, compliance e botões rápidos.
- Alertas automáticos sobre suitability vencida, metas atrasadas, desvios de carteira e documentos expirados, com atividades geradas para follow-up.
- Planejamento financeiro normalizado com metas rastreáveis e fluxo de caixa com surplus calculado.
- Carteira versionada por snapshot, biblioteca única de ativos (`finance.asset.ref`) e wizards para snapshots e rebalanceamento.
- Recomendações validadas por suitability, assistentes guiados, logs imutáveis e documentos de compliance com expiração monitorada.
- Integração direta com CRM, calendário, portal e relatório PDF para enviar ao cliente em um clique.
- Portal responsivo para o cliente acompanhar metas, carteira, recomendações, documentos e reuniões, com upload seguro e mensagens.

## Instalação

1. Copie os diretórios de módulos para o diretório de addons do Odoo.
2. Instale primeiro `finance_core` e, em seguida, os demais módulos conforme a necessidade.
3. Conceda os grupos "Consultor Financeiro", "Backoffice", "Compliance" e "Supervisor" aos usuários apropriados.

Após a instalação, utilize o menu **Consultoria Financeira** para acessar o painel 360°, planejamento, investimentos, recomendações e compliance com UX orientada a fluxo.
