import json
import locale
from decimal import Decimal

import click

from models.companies import Company
from models.database import Database
from models.invoices import (
    CompanyInvoiceRegistry,
    Invoice,
    InvoiceRecord,
    InvoiceRegistry,
)
from scripts.json_utils import DecimalEncoder

locale.setlocale(locale.LC_ALL, "nl_BE.UTF-8")


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
        "Set invoice number",
        default=invoice.get_default_invoice_number(company.counter),
        type=str,
    )

    ### Select invoice date
    invoice_date = click.prompt(
        "Set invoice date",
        default=invoice.invoice_date,
        type=click.DateTime(["%Y/%m/%d", "%Y-%m-%d"]),
    )
    ### Select Period date
    period = click.prompt(
        "Set period", default=invoice_date.strftime("%B %Y"), type=str
    )

    ### Iterate Service Lines
    for i, service_line in enumerate(selected_customer.service_list, 1):
        click.echo(
            f"{i}. {service_line.description} (price: {service_line.unit_price} / {service_line.unit})"
        )

    input_records = []
    while True:
        number = click.prompt(
            'Please enter the name of the service line you want to add to the invoice. Type "0" to stop adding service lines.',
            type=int,
            default=0,
        )
        chosen_service_line = selected_customer.service_list[number - 1]
        if number == 0:
            break

        amount = click.prompt(
            f"{chosen_service_line.description} (price: {chosen_service_line.unit_price} / {chosen_service_line.unit})",
            type=float,
            default=0,
        )
        amount_decimal = round(Decimal(amount), 2)

        if amount:
            comment = click.prompt(
                "Specify extra info on the invoice line.", type=str, default=""
            )
            invoice_record = InvoiceRecord(
                service=chosen_service_line,
                amount=amount_decimal,
                comment=comment,
                vat=selected_customer.service_list[number - 1].vat
                if selected_customer.vat_required
                else 0,
            )
            input_records.append(invoice_record)

    invoice = Invoice(
        customer=selected_customer,
        period=period,
        counter=company.counter,
        invoice_date=invoice_date,
        invoice_number=invoice_number,
        records=input_records,
    )

    ### Save Invoice To File
    invoice.save_to_file(
        template=company.template,
        template_css=company.template_css,
        path=f'output/{company.name.lower()}/factuur_{invoice.invoice_date.strftime("%Y")}_{invoice.invoice_index}_{invoice.customer.abbreviation}.pdf',
    )

    ### Increase counter only if invoice number is default
    if str(company.counter) in invoice_number:
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
    if not invoice_registry.check_if_company_exists(company=company.name):
        company_invoice = CompanyInvoiceRegistry(company_name=company.name)
        invoice_registry.companies.append(company_invoice)

    company_invoice = invoice_registry.get_registry_by_company_name(company.name)
    if company_invoice:
        company_invoice.invoices.append(invoice)

    invoice_registry_dict = invoice_registry.dict()
    with open(filename, "w") as file:
        json.dump(invoice_registry_dict, file, cls=DecimalEncoder)


if __name__ == "__main__":
    cli()
