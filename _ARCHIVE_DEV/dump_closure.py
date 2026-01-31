import inspect
from logic import BusinessLogic
logic = BusinessLogic()
try:
    print(inspect.getsource(logic.perform_annual_closure))
except Exception as e:
    print(e)
