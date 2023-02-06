import json
import locale

import click
from devtools import debug

from models.companies import Company
from models.database import Database
from models.invoices import (
    CompanyInvoiceRegistry,
    Invoice,
    InvoiceRecord,
    InvoiceRegistry,
)
from scripts.json_utils import DecimalEncoder

locale.setlocale(locale.LC_ALL, "nl_BE")


def validate_company(value, number_of_companies) -> int:
    if int(value) < 0 or int(value) > number_of_companies - 1:
        raise click.BadParameter("Company not found")
    return int(value)


def validate_customer(value, raise_error) -> str:
    if raise_error:
        raise click.BadParameter("Customer not found in the customer list")
    return value


@click.command()
def cli() -> None:
    """A CLI program that asks for input in multiple stages."""

    ### Load Database
    filename = "./data/input.json"
    with open(filename) as file:
        data: dict = json.load(file)
    database = Database.parse_obj(data)

    ### Choose Company
    for i, company_enum in enumerate(database.companies):
        click.echo(f"{i}. {company_enum.name}")

    registry_key = click.prompt(
        "Choose company you want to create an invoice for",
        type=lambda x: validate_company(x, len(database.companies)),
    )
    company: Company = database.companies[registry_key]

    ### Choose Customer
    for customer in company.get_active_customers():
        click.echo(f"{customer.abbreviation}: {customer.name}")

    customer_key = click.prompt(
        "Choose customer",
        type=lambda x: validate_customer(x, not company.check_if_key_in_registry(x)),
    )
    selected_customer = company.get_customer_by_key(customer_key)
    if not selected_customer:
        raise click.BadArgumentUsage("Selected customer is not found")

    ### Create Invoice
    invoice = Invoice(customer=selected_customer, counter=company.counter)

    ### Select invoice number
    invoice_number = click.prompt(
        "Set invoice number", default=invoice.invoice_number, type=str
    )
    invoice.invoice_number = invoice_number

    ### Iterate Service Lines
    for service_line in selected_customer.service_list:
        amount = click.prompt(
            f"{service_line.description} (price: {service_line.unit_price} / {service_line.unit})",
            type=int,
            default=0,
        )
        if amount:
            invoice_record = InvoiceRecord(service=service_line, amount=amount)
            invoice.records.append(invoice_record)

    debug(invoice)
    ### Save Invoice To File
    invoice.save_to_file(
        template=company.template,
        path=f'output/{company.name.lower()}/factuur_{invoice.invoice_date.strftime("%Y")}_{invoice.counter}_{invoice.customer.abbreviation}.pdf',
    )

    ### Increase counter
    company.counter += 1

    ### Save Database to File
    database_dict = database.dict()
    with open("data/input.json", "w") as f:
        json.dump(database_dict, f, cls=DecimalEncoder)

    ### Save Invoice To Invoice Registry
    filename = "./data/output.json"

    with open(filename, "r") as output_file:
        output_data: dict = json.load(output_file)

    if not output_data:
        # Script can stop in this case
        return None

    invoice_registry = InvoiceRegistry.parse_obj(output_data)

    # Check if company Exists
    company_invoice: CompanyInvoiceRegistry | None = None
    if not invoice_registry.check_if_company_exists(company.name):
        company_invoice = CompanyInvoiceRegistry(company=company)
        invoice_registry.companies.append(company_invoice)

    company_invoice = invoice_registry.get_registry_by_company_name(company.name)
    if company_invoice:
        company_invoice.invoices.append(invoice)

    invoice_registry_dict = invoice_registry.dict()
    with open(filename, "w") as file:
        json.dump(invoice_registry_dict, file, cls=DecimalEncoder)


if __name__ == "__main__":
    cli()
