from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

import weasyprint  # type: ignore
from devtools import debug
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field, ValidationError, root_validator, validator

from .customers import Customer, Service


class InvoiceRecord(BaseModel):
    service: Service
    comment: str = ""
    amount: Decimal = Decimal(0)
    vat: Decimal = Decimal("21")

    @property
    def price(self) -> Decimal:
        return round(self.service.unit_price * self.amount, 2)

    @property
    def price_vat_included(self) -> Decimal:
        return round(self.price * (1 + (self.vat / 100)), 2)

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        values = super().dict(*args, **kwargs)
        values["price"] = self.price
        values["price_vat_included"] = self.price_vat_included
        return values


class Invoice(BaseModel):
    customer: Customer
    records: list[InvoiceRecord] = []
    invoice_number: str = ""
    invoice_date: date = Field(default_factory=lambda: date.today())
    period: str = ""

    @validator("invoice_number")
    def invoice_number_separates(cls, v: str, values, **kwargs):
        if len(v.split("/")) != 3:
            raise ValidationError("Invoice number must contain 2 '/' slashes")
        return v

    @property
    def invoice_index(self) -> int:
        invoice_number_list = self.invoice_number.split("/")
        return int(invoice_number_list[2])

    @property
    def due_date(self) -> date:
        return self.invoice_date + timedelta(days=self.customer.payment_term)


    @property
    def total_vat_excluded(self) -> Decimal:
        return round(Decimal(sum([rec.price for rec in self.records])), 2)

    @property
    def total_vat_included(self) -> Decimal:
        total_vat_included = Decimal(
            sum([rec.price_vat_included for rec in self.records])
        )

        if total_vat_included < self.total_vat_excluded:
            raise ValidationError(
                "Total including VAT cannot be smaller than total Excluding VAT"
            )
        return round(Decimal(total_vat_included), 2)

    def get_default_invoice_number(self, counter: int) -> str:
        return (
            f"{self.invoice_date.year}/{self.customer.abbreviation}/{counter:04d}"
        )

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        values = super().dict(*args, **kwargs)
        values["invoice_index"] = self.invoice_index
        values["due_date"] = self.due_date
        values["period"] = self.period
        values["total_vat_excluded"] = self.total_vat_excluded
        values["total_vat_included"] = self.total_vat_included
        return values

    class Config:
        validate_assignment = True

    def parse_html_file(
        self,
        path: str = "templates/invoice.html",
        path_css: str = "templates/style.css",
    ) -> tuple[str, str]:
        loader = FileSystemLoader(".")
        env = Environment(loader=loader)
        template = env.get_template(path)
        css = env.get_template(path_css)

        html = template.render(
            {
                **self.dict(),
            }
        )
        css_html = css.render()

        return html, css_html

    def save_to_file(
        self,
        template: str = "templates/invoice.html",
        template_css: str = "templates/style.css",
        path: str = "output.pdf",
    ) -> None:
        html, css = self.parse_html_file(template, template_css)
        html_file = weasyprint.HTML(string=html)
        css_file = weasyprint.CSS(string=css)
        html_file.write_pdf(target=path, stylesheets=[css_file])


class CompanyInvoiceRegistry(BaseModel):
    company_name: str
    invoices: list[Invoice] = []


class InvoiceRegistry(BaseModel):
    companies: list[CompanyInvoiceRegistry] = []

    def check_if_company_exists(self, company: str) -> bool:
        return company in [
            company_invoice.company_name for company_invoice in self.companies
        ]

    def get_registry_by_company_name(
        self, company_name: str
    ) -> Optional[CompanyInvoiceRegistry]:
        company_invoice_registries = [
            obj for obj in self.companies if obj.company_name == company_name
        ]
        if company_invoice_registries:
            return company_invoice_registries[0]
        else:
            return None
