from decimal import Decimal

from pydantic import BaseModel, ValidationError, validator


class Address(BaseModel):
    street: str
    number: str
    bus: str
    postal_code: str
    city: str


class Service(BaseModel):
    description: str
    unit_price: Decimal
    unit: str
    vat: Decimal

    @validator("unit_price")
    def unit_price_cannot_be_negative(cls, v, values, **kwargs):
        if v < 0:
            raise ValidationError("Unit price cannot be negative")
        return v

    @validator("vat")
    def payment_term_cannot_be_negative(cls, v, values, **kwargs):
        if v < 0:
            raise ValidationError("VAT cannot be negative")
        return v


class Customer(BaseModel):
    name: str
    abbreviation: str
    active: bool = True
    vat_number: str
    payment_term: int = 30
    cash: bool = False
    address: Address
    service_list: list[Service] = []
    vat_required: bool = True

    # @validator("vat_required", always=True)
    # def vat_required_validator(cls, v, values, **kwargs):
    #     has_vat_services = any([s.vat > 0 for s in values["service_list"]])
    #     if not v and has_vat_services:
    #         raise ValidationError("VAT required if any service has VAT")
    #     return v

    @validator("payment_term")
    def payment_term_cannot_be_negative(cls, v, values, **kwargs):
        if v < 0:
            raise ValidationError("Payment term cannot be negative")
        return v
