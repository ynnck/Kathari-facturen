from typing import Any, Optional

from pydantic import BaseModel

from .customers import Customer


class Company(BaseModel):
    name: str
    template: str
    template_css: str
    customers: list[Customer] = []
    standard_vat_tariff: int
    counter: int
    verlegging_text: str


    def get_active_customers(self) -> list[Customer]:
        return [customer for customer in self.customers if customer.active]

    def check_if_key_in_registry(self, abbreviation=None) -> bool:
        return abbreviation in [customer.abbreviation for customer in self.customers]

    def get_customer_by_key(self, key: str) -> Optional[Customer]:
        selected_customer = [obj for obj in self.customers if obj.abbreviation == key]
        if selected_customer:
            return selected_customer[0]
        else:
            return None
