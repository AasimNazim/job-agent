# Adapters package
from .registry import AdapterRegistry
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .workable import WorkableAdapter
from .ashby import AshbyAdapter
from .jazzhr import JazzhrAdapter
from .hirestream import HirestreamAdapter

# Register all implemented adapters
AdapterRegistry.register("greenhouse", GreenhouseAdapter)
AdapterRegistry.register("lever", LeverAdapter)
AdapterRegistry.register("workable", WorkableAdapter)
AdapterRegistry.register("ashby", AshbyAdapter)
AdapterRegistry.register("jazzhr", JazzhrAdapter)
AdapterRegistry.register("hirestream", HirestreamAdapter)
