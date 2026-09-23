"""Consulting-grade scoping and reporting.

``scope_assessment`` produces the scoping document that structures a
black-box engagement (what is in scope, what access exists, what the rules
of engagement are). ``generate_report`` turns campaign results into a
markdown report with an executive summary, findings table, risk-domain
breakdown, an attempted-vs-completed distinction (completed = verified
consequences, not judge opinions), concrete recommendations, and an explicit
attack-budget disclosure.
"""

from .report import scope_assessment, generate_report, save_report

__all__ = ["scope_assessment", "generate_report", "save_report"]
