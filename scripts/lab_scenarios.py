"""Pinned local lab mutations; these are developer operations, never agent tools."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fault:
    flag: str
    variant: str
    value: bool | int
    service: str
    symptom: str


SCENARIOS = {
    "payment-failure": Fault("paymentFailure", "100%", 1, "payment", "Payment charge requests are failing"),
    "cart-failure": Fault("cartFailure", "100%", 1, "cart", "EmptyCart requests are failing"),
    "ad-failure": Fault("adFailure", "on", True, "ad", "Ad requests are failing intermittently"),
}
