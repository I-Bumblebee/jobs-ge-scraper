-- Jobs Scraper Database Initialization Script

-- Create tables for job scraping data
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    website VARCHAR(500),
    logo_url VARCHAR(500),
    description TEXT,
    industry VARCHAR(100),
    size VARCHAR(50),
    location VARCHAR(255),
    jobs_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job listings table
CREATE TABLE IF NOT EXISTS job_listings (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    job_type VARCHAR(50),
    category VARCHAR(100),
    url VARCHAR(1000),
    short_description TEXT,
    
    -- Location fields
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100),
    is_remote BOOLEAN DEFAULT FALSE,
    
    -- Company info (simplified, could reference companies table)
    company_name VARCHAR(255),
    company_website VARCHAR(500),
    company_logo_url VARCHAR(500),
    
    -- Salary information
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(10),
    salary_period VARCHAR(20),
    salary_negotiable BOOLEAN DEFAULT FALSE,
    
    -- Dates
    published_date TIMESTAMP WITH TIME ZONE,
    deadline_date TIMESTAMP WITH TIME ZONE,
    updated_date TIMESTAMP WITH TIME ZONE,
    scraped_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata flags
    is_expiring BOOLEAN DEFAULT FALSE,
    was_recently_updated BOOLEAN DEFAULT FALSE,
    has_salary_info BOOLEAN DEFAULT FALSE,
    is_new BOOLEAN DEFAULT FALSE,
    is_in_region BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_urgent BOOLEAN DEFAULT FALSE,
    is_vip BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job details table (for detailed job information)
CREATE TABLE IF NOT EXISTS job_details (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    experience_level VARCHAR(50),
    education_level VARCHAR(50),
    url VARCHAR(1000),
    application_url VARCHAR(1000),
    description_file_path VARCHAR(500),
    
    -- Location fields
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100),
    is_remote BOOLEAN DEFAULT FALSE,
    
    -- Company info
    company_name VARCHAR(255),
    company_website VARCHAR(500),
    company_logo_url VARCHAR(500),
    company_description TEXT,
    company_industry VARCHAR(100),
    company_size VARCHAR(50),
    company_location VARCHAR(255),
    
    -- Salary information
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(10),
    salary_period VARCHAR(20),
    salary_negotiable BOOLEAN DEFAULT FALSE,
    
    -- Dates
    published_date TIMESTAMP WITH TIME ZONE,
    deadline_date TIMESTAMP WITH TIME ZONE,
    updated_date TIMESTAMP WITH TIME ZONE,
    scraped_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata flags
    is_expiring BOOLEAN DEFAULT FALSE,
    was_recently_updated BOOLEAN DEFAULT FALSE,
    has_salary_info BOOLEAN DEFAULT FALSE,
    is_new BOOLEAN DEFAULT FALSE,
    is_in_region BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_urgent BOOLEAN DEFAULT FALSE,
    is_vip BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job requirements table
CREATE TABLE IF NOT EXISTS job_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES job_details(id) ON DELETE CASCADE,
    requirement TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job responsibilities table
CREATE TABLE IF NOT EXISTS job_responsibilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES job_details(id) ON DELETE CASCADE,
    responsibility TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job benefits table
CREATE TABLE IF NOT EXISTS job_benefits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES job_details(id) ON DELETE CASCADE,
    benefit TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job skills table
CREATE TABLE IF NOT EXISTS job_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES job_details(id) ON DELETE CASCADE,
    skill VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Contact information table
CREATE TABLE IF NOT EXISTS job_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES job_details(id) ON DELETE CASCADE,
    contact_type VARCHAR(50) NOT NULL, -- email, phone, person, etc.
    contact_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scraping results table
CREATE TABLE IF NOT EXISTS scraping_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    total_jobs_found INTEGER DEFAULT 0,
    successful_scrapes INTEGER DEFAULT 0,
    failed_scrapes INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scraping errors table
CREATE TABLE IF NOT EXISTS scraping_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scraping_result_id UUID REFERENCES scraping_results(id) ON DELETE CASCADE,
    error_message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_job_listings_platform ON job_listings(platform);
CREATE INDEX IF NOT EXISTS idx_job_listings_scraped_date ON job_listings(scraped_date);
CREATE INDEX IF NOT EXISTS idx_job_listings_published_date ON job_listings(published_date);
CREATE INDEX IF NOT EXISTS idx_job_listings_company_name ON job_listings(company_name);
CREATE INDEX IF NOT EXISTS idx_job_listings_city ON job_listings(city);
CREATE INDEX IF NOT EXISTS idx_job_listings_is_remote ON job_listings(is_remote);

CREATE INDEX IF NOT EXISTS idx_job_details_platform ON job_details(platform);
CREATE INDEX IF NOT EXISTS idx_job_details_scraped_date ON job_details(scraped_date);
CREATE INDEX IF NOT EXISTS idx_job_details_published_date ON job_details(published_date);
CREATE INDEX IF NOT EXISTS idx_job_details_company_name ON job_details(company_name);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to relevant tables (idempotent - drop if exists first)
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_job_listings_updated_at ON job_listings;
CREATE TRIGGER update_job_listings_updated_at BEFORE UPDATE ON job_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_job_details_updated_at ON job_details;
CREATE TRIGGER update_job_details_updated_at BEFORE UPDATE ON job_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Generic jobs overview view (virtual table for easy data access)
CREATE OR REPLACE VIEW jobs_overview AS
SELECT 
    jl.id,
    jl.platform,
    jl.title,
    jl.company_name,
    jl.city,
    jl.region,
    jl.country,
    jl.is_remote,
    jl.job_type,
    jl.category,
    jl.salary_min,
    jl.salary_max,
    jl.salary_currency,
    jl.published_date,
    jl.scraped_date,
    jl.url,
    jl.short_description,
    jl.has_salary_info,
    jl.is_featured,
    jl.is_new,
    -- Computed columns for better readability
    CASE 
        WHEN jl.salary_min IS NOT NULL AND jl.salary_max IS NOT NULL 
        THEN CONCAT(jl.salary_min, '-', jl.salary_max, ' ', COALESCE(jl.salary_currency, ''))
        WHEN jl.salary_min IS NOT NULL 
        THEN CONCAT('From ', jl.salary_min, ' ', COALESCE(jl.salary_currency, ''))
        ELSE 'Not specified'
    END as salary_range,
    CASE 
        WHEN jl.is_remote THEN 'Remote'
        WHEN jl.city IS NOT NULL AND jl.region IS NOT NULL 
        THEN CONCAT(jl.city, ', ', jl.region)
        WHEN jl.city IS NOT NULL 
        THEN jl.city
        ELSE 'Location not specified'
    END as location_display,
    EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - jl.scraped_date)) as days_since_scraped,
    EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - jl.published_date)) as days_since_published
FROM job_listings jl
ORDER BY jl.scraped_date DESC;

-- Insert some initial data or configurations if needed
-- This is optional and can be removed if not needed 