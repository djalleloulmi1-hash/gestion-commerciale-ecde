import inspect
from logic import BusinessLogic

logic = BusinessLogic()

print("Source of calculate_client_balance:")
try:
    print(inspect.getsource(logic.calculate_client_balance))
except Exception as e:
    print(e)

print("\nSource of get_client_situation:")
try:
    print(inspect.getsource(logic.get_client_situation))
except Exception as e:
    print(e)
