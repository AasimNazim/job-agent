import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from ..models.company import Company
from ..models.candidate import CandidateProfile, Resume

logger = logging.getLogger(__name__)

class ConfigurationLoader:
    
    @staticmethod
    def load_companies_from_file(file_path: str, db: Session) -> List[Company]:
        """
        Loads companies from a JSON configuration file and synchronizes them with the database.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Configuration file not found: {file_path}")
            return []
            
        with open(path, 'r', encoding='utf-8') as f:
            try:
                companies_data: List[Dict[str, Any]] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {file_path}: {e}")
                return []
                
        synced_companies = []
        
        for data in companies_data:
            name = data.get("name")
            if not name:
                continue
                
            # Check if company exists
            company = db.query(Company).filter_by(name=name).first()
            
            if not company:
                company = Company(
                    name=name,
                    career_url=data.get("career_url", ""),
                    platform=data.get("platform", "custom").lower(),
                    enabled=data.get("enabled", True)
                )
                db.add(company)
                logger.info(f"Added new company from config: {name} ({company.platform})")
            else:
                # Update existing
                company.career_url = data.get("career_url", company.career_url)
                company.platform = data.get("platform", company.platform).lower()
                company.enabled = data.get("enabled", company.enabled)
                logger.debug(f"Updated company from config: {name}")
                
            synced_companies.append(company)
            
        db.commit()
        return synced_companies
        
    @staticmethod
    def load_candidate_profile(file_path: str, db: Session) -> Optional[CandidateProfile]:
        """
        Loads the candidate profile and their specific resumes from a JSON configuration file.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Candidate configuration file not found: {file_path}")
            return None
            
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data: Dict[str, Any] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {file_path}: {e}")
                return None
                
        # We assume one active candidate for now
        profile = db.query(CandidateProfile).first()
        
        if not profile:
            profile = CandidateProfile(profile_data=data)
            db.add(profile)
        else:
            profile.profile_data = data
            
        profile.career_level = data.get("education_level", "entry_level")
        db.commit()
        
        # Load resumes
        resumes_data = data.get("resumes", [])
        for r_data in resumes_data:
            filename = r_data.get("file_path", "")
            domain = r_data.get("domain_name", "")
            if not filename or not domain:
                continue
                
            resume = db.query(Resume).filter_by(filename=filename).first()
            if not resume:
                resume = Resume(filename=filename, domains=[domain])
                db.add(resume)
            else:
                domains = resume.domains or []
                if domain not in domains:
                    domains.append(domain)
                resume.domains = domains
            
        db.commit()
        
        logger.info(f"Loaded candidate profile with {len(resumes_data)} resumes.")
        return profile
