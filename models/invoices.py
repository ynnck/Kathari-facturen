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
    price: Decimal = Decimal(0)
    price_vat_included: Decimal = Decimal(0)

    class Config:
        validate_assignment = True

    @validator("price", pre=True, always=True)
    def price_validator(cls, v, values) -> Decimal:
        service = values["service"]
        amount = values["amount"]
        return service.unit_price * amount

    @validator("price_vat_included", pre=True, always=True)
    def price_vat_included_validator(cls, v, values) -> Decimal:
        service = values["service"]
        price = values["price"]
        return price * (1 + (service.vat / 100))


class Invoice(BaseModel):
    customer: Customer
    counter: int
    invoice_date: date = Field(default_factory=lambda: date.today())
    due_date: Optional[date] = None
    period: Optional[str] = None
    invoice_number: Optional[str] = None
    records: list[InvoiceRecord] = []
    total_vat_excluded: Decimal = Decimal(0)
    total_vat_included: Decimal = Decimal(0)

    class Config:
        validate_assignment = True

    @validator("invoice_date", pre=True, always=True)
    def invoice_date_validator(cls, v, values) -> date:
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        if isinstance(v, date):
            return v

        return date.today()

    @validator("due_date", pre=True, always=True)
    def due_date_validator(cls, v, values) -> date:
        due_date = v

        if not due_date:
            due_date = values["invoice_date"] + timedelta(
                days=values["customer"].payment_term
            )
        if isinstance(v, str):
            due_date = datetime.strptime(v, "%Y-%m-%d").date()

        if due_date < values["invoice_date"]:
            raise ValidationError("due date cannot be before invoice date")

        return due_date

    @validator("period", pre=True, always=True)
    def period_validator(cls, v, values) -> str:
        return values["invoice_date"].strftime("%B %Y")

    @validator("invoice_number", pre=True, always=True)
    def invoice_number_validator(cls, v, values) -> str:
        if not v:
            return f"{values['invoice_date'].year}/{values['customer'].abbreviation}/{values['counter']:04d}"

        return v

    @validator("total_vat_excluded", pre=True, always=True)
    def total_vat_excluded_validator(cls, v, values) -> Decimal:
        return Decimal(sum([rec.price for rec in values["records"]]))

    @validator("total_vat_included", pre=True, always=True)
    def total_vat_included_validator(cls, v, values) -> Decimal:
        total_vat_included = Decimal(
            sum([rec.price_vat_included for rec in values["records"]])
        )

        if total_vat_included < values["total_vat_excluded"]:
            raise ValidationError(
                "Total including VAT cannot be smaller than total Excluding VAT"
            )

        return total_vat_included

    def parse_html_file(
        self,
        path: str = "templates/invoice.html",
        path_css: str = "templates/style.css",
    ) -> tuple[str, str]:
        loader = FileSystemLoader(".")
        env = Environment(loader=loader)
        template = env.get_template(path)
        css = env.get_template(path_css)

        html = template.render(**self.dict())
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
