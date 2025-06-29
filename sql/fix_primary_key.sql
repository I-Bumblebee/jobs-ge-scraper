-- Fix Primary Key Issue: Change from single 'id' to composite '(id, platform)'
-- This allows different platforms to have the same job IDs without conflicts

-- Start transaction
BEGIN;

-- Step 1: Drop existing foreign key constraints that reference job_listings.id
ALTER TABLE IF EXISTS job_requirements DROP CONSTRAINT IF EXISTS job_requirements_job_id_fkey;
ALTER TABLE IF EXISTS job_responsibilities DROP CONSTRAINT IF EXISTS job_responsibilities_job_id_fkey;
ALTER TABLE IF EXISTS job_benefits DROP CONSTRAINT IF EXISTS job_benefits_job_id_fkey;
ALTER TABLE IF EXISTS job_skills DROP CONSTRAINT IF EXISTS job_skills_job_id_fkey;
ALTER TABLE IF EXISTS job_contacts DROP CONSTRAINT IF EXISTS job_contacts_job_id_fkey;

-- Step 2: Drop existing primary key constraint on job_listings
ALTER TABLE job_listings DROP CONSTRAINT IF EXISTS job_listings_pkey;

-- Step 3: Add new composite primary key
ALTER TABLE job_listings ADD CONSTRAINT job_listings_pkey PRIMARY KEY (id, platform);

-- Step 4: Do the same for job_details table
ALTER TABLE job_details DROP CONSTRAINT IF EXISTS job_details_pkey;
ALTER TABLE job_details ADD CONSTRAINT job_details_pkey PRIMARY KEY (id, platform);

-- Step 5: Skip foreign key recreation for now since they would need platform columns
-- TODO: In the future, add platform columns to child tables and create proper composite foreign keys

-- Step 6: Update indexes to reflect new primary key
DROP INDEX IF EXISTS idx_job_listings_platform;
CREATE INDEX idx_job_listings_platform ON job_listings(platform);
CREATE INDEX idx_job_listings_id ON job_listings(id);

DROP INDEX IF EXISTS idx_job_details_platform;
CREATE INDEX idx_job_details_platform ON job_details(platform);
CREATE INDEX idx_job_details_id ON job_details(id);

-- Commit transaction
COMMIT;

-- Verification queries
SELECT 'job_listings primary key check' as info, 
       COUNT(*) as total_jobs,
       COUNT(DISTINCT (id, platform)) as unique_id_platform_pairs
FROM job_listings;

SELECT 'Platform ID ranges after fix' as info, 
       platform, 
       MIN(id) as min_id, 
       MAX(id) as max_id, 
       COUNT(*) as count 
FROM job_listings 
GROUP BY platform; 