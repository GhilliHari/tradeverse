from kill_switch import KillSwitch
from risk_engine import RiskEngine
import os

ks = KillSwitch()
risk = RiskEngine()

print("Initial Status:", ks.get_status())
print("Risk Check:", risk.validate_order({"price": 100, "quantity": 1}))

print("\nACTIVATING KILL SWITCH...")
ks.activate("Test Activation")

print("Status After Activation:", ks.get_status())
print("Risk Check:", risk.validate_order({"price": 100, "quantity": 1}))

print("\nDEACTIVATING KILL SWITCH...")
ks.deactivate()

print("Final Status:", ks.get_status())
print("Risk Check:", risk.validate_order({"price": 100, "quantity": 1}))
