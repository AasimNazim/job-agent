import pytest
import os
import json
from job_agent.adapters.base import JobSourceAdapter
from job_agent.adapters.registry import AdapterRegistry
from job_agent.core.config_loader import ConfigurationLoader
from job_agent.models.company import Company

# Dummy adapter for testing
class DummyGreenhouseAdapter(JobSourceAdapter):
    async def discover_jobs(self, company):
        return []

def test_adapter_registry():
    # Register the dummy adapter
    AdapterRegistry.register("greenhouse", DummyGreenhouseAdapter)
    
    # Retrieve it
    adapter = AdapterRegistry.get_adapter("greenhouse")
    assert isinstance(adapter, DummyGreenhouseAdapter)
    
    # Check unsupported
    with pytest.raises(ValueError):
        AdapterRegistry.get_adapter("unknown_platform")
        
    assert "greenhouse" in AdapterRegistry.supported_platforms()

def test_config_loader(db_session, tmp_path):
    # Create a dummy companies.json
    config_file = tmp_path / "companies.json"
    dummy_data = [
        {"name": "Test1", "career_url": "url1", "platform": "lever", "enabled": True},
        {"name": "Test2", "career_url": "url2", "platform": "greenhouse", "enabled": False}
    ]
    with open(config_file, "w") as f:
        json.dump(dummy_data, f)
        
    # Load into db
    companies = ConfigurationLoader.load_companies_from_file(str(config_file), db_session)
    
    assert len(companies) == 2
    
    # Verify DB state
    db_company = db_session.query(Company).filter_by(name="Test2").first()
    assert db_company is not None
    assert db_company.platform == "greenhouse"
    assert db_company.enabled is False
