import json
from job_agent.core.config_loader import ConfigurationLoader
from job_agent.models.candidate import CandidateProfile, Resume

def test_load_candidate_profile(db_session, tmp_path):
    config_file = tmp_path / "candidate.json"
    dummy_data = {
        "full_name": "Test Candidate",
        "email": "test@test.com",
        "graduation_year": 2024,
        "resumes": [
            {
                "domain_name": "backend",
                "file_path": "resumes/backend.pdf",
                "tags": ["python", "api"]
            },
            {
                "domain_name": "frontend",
                "file_path": "resumes/frontend.pdf",
                "tags": ["react"]
            }
        ]
    }
    
    with open(config_file, "w") as f:
        json.dump(dummy_data, f)
        
    profile = ConfigurationLoader.load_candidate_profile(str(config_file), db_session)
    
    assert profile is not None
    assert profile.profile_data["full_name"] == "Test Candidate"
    assert profile.profile_data["email"] == "test@test.com"
    
    resumes = db_session.query(Resume).all()
    assert len(resumes) == 2
    
    backend_resume = next((r for r in resumes if r.filename == "resumes/backend.pdf"), None)
    assert backend_resume is not None
    assert "backend" in backend_resume.domains
