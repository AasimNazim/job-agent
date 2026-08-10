# Adapters package
from .registry import AdapterRegistry
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .workable import WorkableAdapter
from .ashby import AshbyAdapter

# Register all implemented adapters
AdapterRegistry.register("greenhouse", GreenhouseAdapter)
AdapterRegistry.register("lever", LeverAdapter)
AdapterRegistry.register("workable", WorkableAdapter)
AdapterRegistry.register("ashby", AshbyAdapter)
