import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.database import SessionLocal, sync_engine, test_connection
from sqlalchemy import text, exc
from sqlalchemy.dialects.postgresql import insert


class DatabaseOutputManager:
    """
    Database output manager for saving job scraping data directly to PostgreSQL.
    Handles job listings, job details, and related data.
    """
    
    def __init__(self):
        """Initialize the database output manager."""
        self.logger = logging.getLogger(f"{__name__}.DatabaseOutputManager")
        
        # Test database connection
        if not test_connection():
            raise ConnectionError("Cannot connect to database. Please check your database configuration.")
        
        self.logger.info("Database output manager initialized successfully")
    
    def _get_session(self):
        """Get a database session."""
        return SessionLocal()
    
    async def save_job_listing(self, job_data: Dict[str, Any]) -> bool:
        """
        Save a job listing to the database.
        
        Args:
            job_data: Job listing data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._get_session()
            
            # Prepare job listing data for database
            listing_data = self._prepare_job_listing_data(job_data)
            
            # Use INSERT ON CONFLICT DO UPDATE to handle duplicates
            stmt = text("""
                INSERT INTO job_listings (
                    id, platform, title, job_type, category, url, short_description,
                    city, region, country, is_remote,
                    company_name, company_website, company_logo_url,
                    salary_min, salary_max, salary_currency, salary_period, salary_negotiable,
                    published_date, deadline_date, updated_date, scraped_date,
                    is_expiring, was_recently_updated, has_salary_info, is_new, 
                    is_in_region, is_featured, is_urgent, is_vip
                ) VALUES (
                    :id, :platform, :title, :job_type, :category, :url, :short_description,
                    :city, :region, :country, :is_remote,
                    :company_name, :company_website, :company_logo_url,
                    :salary_min, :salary_max, :salary_currency, :salary_period, :salary_negotiable,
                    :published_date, :deadline_date, :updated_date, :scraped_date,
                    :is_expiring, :was_recently_updated, :has_salary_info, :is_new,
                    :is_in_region, :is_featured, :is_urgent, :is_vip
                )
                ON CONFLICT (id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    scraped_date = :scraped_date
            """)
            
            session.execute(stmt, listing_data)
            session.commit()
            session.close()
            
            self.logger.debug(f"Saved job listing: {listing_data['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving job listing: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    async def save_job_details(self, job_data: Dict[str, Any]) -> bool:
        """
        Save detailed job information to the database.
        
        Args:
            job_data: Job details data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._get_session()
            
            # Prepare job details data for database
            details_data = self._prepare_job_details_data(job_data)
            
            # Save main job details
            stmt = text("""
                INSERT INTO job_details (
                    id, platform, title, description, experience_level, education_level,
                    url, application_url, description_file_path,
                    city, region, country, is_remote,
                    company_name, company_website, company_logo_url, company_description,
                    company_industry, company_size, company_location,
                    salary_min, salary_max, salary_currency, salary_period, salary_negotiable,
                    published_date, deadline_date, updated_date, scraped_date,
                    is_expiring, was_recently_updated, has_salary_info, is_new,
                    is_in_region, is_featured, is_urgent, is_vip
                ) VALUES (
                    :id, :platform, :title, :description, :experience_level, :education_level,
                    :url, :application_url, :description_file_path,
                    :city, :region, :country, :is_remote,
                    :company_name, :company_website, :company_logo_url, :company_description,
                    :company_industry, :company_size, :company_location,
                    :salary_min, :salary_max, :salary_currency, :salary_period, :salary_negotiable,
                    :published_date, :deadline_date, :updated_date, :scraped_date,
                    :is_expiring, :was_recently_updated, :has_salary_info, :is_new,
                    :is_in_region, :is_featured, :is_urgent, :is_vip
                )
                ON CONFLICT (id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    scraped_date = :scraped_date,
                    description = :description,
                    experience_level = :experience_level,
                    education_level = :education_level
            """)
            
            session.execute(stmt, details_data)
            
            # Save related data (requirements, responsibilities, benefits, skills, contacts)
            job_id = details_data['id']
            
            # Save requirements
            if job_data.get('requirements'):
                await self._save_job_requirements(session, job_id, job_data['requirements'])
            
            # Save responsibilities  
            if job_data.get('responsibilities'):
                await self._save_job_responsibilities(session, job_id, job_data['responsibilities'])
            
            # Save benefits
            if job_data.get('benefits'):
                await self._save_job_benefits(session, job_id, job_data['benefits'])
            
            # Save skills
            if job_data.get('skills'):
                await self._save_job_skills(session, job_id, job_data['skills'])
            
            # Save contact information
            if job_data.get('contact_info'):
                await self._save_job_contacts(session, job_id, job_data['contact_info'])
            
            session.commit()
            session.close()
            
            self.logger.debug(f"Saved job details: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving job details {job_data.get('id', 'unknown')}: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    async def save_scraping_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        """
        Save scraping result summary to database.
        
        Args:
            result_data: Scraping result data
            
        Returns:
            Result ID if successful, None otherwise
        """
        try:
            session = self._get_session()
            result_id = str(uuid4())
            
            stmt = text("""
                INSERT INTO scraping_results (
                    id, platform, total_jobs_found, successful_scrapes, failed_scrapes,
                    start_time, end_time
                ) VALUES (
                    :id, :platform, :total_jobs_found, :successful_scrapes, :failed_scrapes,
                    :start_time, :end_time
                )
            """)
            
            session.execute(stmt, {
                'id': result_id,
                'platform': result_data.get('platform', ''),
                'total_jobs_found': result_data.get('total_jobs_found', 0),
                'successful_scrapes': result_data.get('successful_scrapes', 0),
                'failed_scrapes': result_data.get('failed_scrapes', 0),
                'start_time': result_data.get('start_time'),
                'end_time': result_data.get('end_time')
            })
            
            # Save errors if any
            if result_data.get('errors'):
                await self._save_scraping_errors(session, result_id, result_data['errors'])
            
            session.commit()
            session.close()
            
            self.logger.info(f"Saved scraping result: {result_id}")
            return result_id
            
        except Exception as e:
            self.logger.error(f"Error saving scraping result: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return None
    
    def _prepare_job_listing_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job listing data for database insertion."""
        company = job_data.get('company') or {}
        location = job_data.get('location') or {}
        salary = job_data.get('salary') or {}
        dates = job_data.get('dates') or {}
        metadata = job_data.get('metadata') or {}
        
        return {
            'id': job_data.get('id', ''),
            'platform': job_data.get('platform', ''),
            'title': job_data.get('title', ''),
            'job_type': job_data.get('job_type'),
            'category': job_data.get('category'),
            'url': job_data.get('url'),
            'short_description': job_data.get('short_description'),
            
            # Location
            'city': location.get('city'),
            'region': location.get('region'),
            'country': location.get('country'),
            'is_remote': location.get('is_remote', False),
            
            # Company
            'company_name': company.get('name'),
            'company_website': company.get('website'),
            'company_logo_url': company.get('logo_url'),
            
            # Salary - handle the case where salary is None
            'salary_min': salary.get('min_amount') if salary else None,
            'salary_max': salary.get('max_amount') if salary else None,
            'salary_currency': salary.get('currency') if salary else None,
            'salary_period': salary.get('period') if salary else None,
            'salary_negotiable': salary.get('is_negotiable', False) if salary else False,
            
            # Dates
            'published_date': self._parse_date(dates.get('published')),
            'deadline_date': self._parse_date(dates.get('deadline')),
            'updated_date': self._parse_date(dates.get('updated')),
            'scraped_date': datetime.now(),
            
            # Metadata
            'is_expiring': metadata.get('is_expiring', False),
            'was_recently_updated': metadata.get('was_recently_updated', False),
            'has_salary_info': metadata.get('has_salary_info', False),
            'is_new': metadata.get('is_new', False),
            'is_in_region': metadata.get('is_in_region', False),
            'is_featured': metadata.get('is_featured', False),
            'is_urgent': metadata.get('is_urgent', False),
            'is_vip': metadata.get('is_vip', False),
        }
    
    def _prepare_job_details_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job details data for database insertion."""
        company = job_data.get('company') or {}
        location = job_data.get('location') or {}
        salary = job_data.get('salary') or {}
        dates = job_data.get('dates') or {}
        metadata = job_data.get('metadata') or {}
        
        return {
            'id': job_data.get('id', ''),
            'platform': job_data.get('platform', ''),
            'title': job_data.get('title', ''),
            'description': job_data.get('description', ''),
            'experience_level': job_data.get('experience_level'),
            'education_level': job_data.get('education_level'),
            'url': job_data.get('url'),
            'application_url': job_data.get('application_url'),
            'description_file_path': job_data.get('description_file_path'),
            
            # Location
            'city': location.get('city'),
            'region': location.get('region'),
            'country': location.get('country'),
            'is_remote': location.get('is_remote', False),
            
            # Company
            'company_name': company.get('name'),
            'company_website': company.get('website'),
            'company_logo_url': company.get('logo_url'),
            'company_description': company.get('description'),
            'company_industry': company.get('industry'),
            'company_size': company.get('size'),
            'company_location': company.get('location'),
            
            # Salary - handle the case where salary is None
            'salary_min': salary.get('min_amount') if salary else None,
            'salary_max': salary.get('max_amount') if salary else None,
            'salary_currency': salary.get('currency') if salary else None,
            'salary_period': salary.get('period') if salary else None,
            'salary_negotiable': salary.get('is_negotiable', False) if salary else False,
            
            # Dates
            'published_date': self._parse_date(dates.get('published')),
            'deadline_date': self._parse_date(dates.get('deadline')),
            'updated_date': self._parse_date(dates.get('updated')),
            'scraped_date': datetime.now(),
            
            # Metadata
            'is_expiring': metadata.get('is_expiring', False),
            'was_recently_updated': metadata.get('was_recently_updated', False),
            'has_salary_info': metadata.get('has_salary_info', False),
            'is_new': metadata.get('is_new', False),
            'is_in_region': metadata.get('is_in_region', False),
            'is_featured': metadata.get('is_featured', False),
            'is_urgent': metadata.get('is_urgent', False),
            'is_vip': metadata.get('is_vip', False),
        }
    
    async def _save_job_requirements(self, session, job_id: str, requirements: List[str]):
        """Save job requirements."""
        for requirement in requirements:
            if requirement.strip():
                stmt = text("""
                    INSERT INTO job_requirements (job_id, requirement) 
                    VALUES (:job_id, :requirement)
                """)
                session.execute(stmt, {'job_id': job_id, 'requirement': requirement.strip()})
    
    async def _save_job_responsibilities(self, session, job_id: str, responsibilities: List[str]):
        """Save job responsibilities."""
        for responsibility in responsibilities:
            if responsibility.strip():
                stmt = text("""
                    INSERT INTO job_responsibilities (job_id, responsibility) 
                    VALUES (:job_id, :responsibility)
                """)
                session.execute(stmt, {'job_id': job_id, 'responsibility': responsibility.strip()})
    
    async def _save_job_benefits(self, session, job_id: str, benefits: List[str]):
        """Save job benefits."""
        for benefit in benefits:
            if benefit.strip():
                stmt = text("""
                    INSERT INTO job_benefits (job_id, benefit) 
                    VALUES (:job_id, :benefit)
                """)
                session.execute(stmt, {'job_id': job_id, 'benefit': benefit.strip()})
    
    async def _save_job_skills(self, session, job_id: str, skills: List[str]):
        """Save job skills."""
        for skill in skills:
            if skill.strip():
                stmt = text("""
                    INSERT INTO job_skills (job_id, skill) 
                    VALUES (:job_id, :skill)
                """)
                session.execute(stmt, {'job_id': job_id, 'skill': skill.strip()})
    
    async def _save_job_contacts(self, session, job_id: str, contacts: Dict[str, str]):
        """Save job contact information."""
        for contact_type, contact_value in contacts.items():
            if contact_value and contact_value.strip():
                stmt = text("""
                    INSERT INTO job_contacts (job_id, contact_type, contact_value) 
                    VALUES (:job_id, :contact_type, :contact_value)
                """)
                session.execute(stmt, {
                    'job_id': job_id, 
                    'contact_type': contact_type, 
                    'contact_value': contact_value.strip()
                })
    
    async def _save_scraping_errors(self, session, result_id: str, errors: List[str]):
        """Save scraping errors."""
        for error in errors:
            if error.strip():
                stmt = text("""
                    INSERT INTO scraping_errors (scraping_result_id, error_message) 
                    VALUES (:result_id, :error_message)
                """)
                session.execute(stmt, {'result_id': result_id, 'error_message': error.strip()})
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        if isinstance(date_str, str):
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        
        return None
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics from database."""
        try:
            session = self._get_session()
            
            # Get total jobs by platform
            stmt = text("""
                SELECT platform, COUNT(*) as count 
                FROM job_listings 
                GROUP BY platform
            """)
            platform_stats = session.execute(stmt).fetchall()
            
            # Get recent scraping activity
            stmt = text("""
                SELECT platform, COUNT(*) as count, MAX(scraped_date) as last_scraped
                FROM job_listings 
                WHERE scraped_date >= NOW() - INTERVAL '24 hours'
                GROUP BY platform
            """)
            recent_stats = session.execute(stmt).fetchall()
            
            session.close()
            
            return {
                'platform_totals': {row[0]: row[1] for row in platform_stats},
                'recent_activity': {
                    row[0]: {'count': row[1], 'last_scraped': row[2]} 
                    for row in recent_stats
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting scraping stats: {str(e)}")
            return {} 