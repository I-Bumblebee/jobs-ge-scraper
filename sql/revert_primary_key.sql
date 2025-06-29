-- Revert Primary Key: Change back from composite '(id, platform)' to single 'id'
-- This reverts the previous migration

-- Start transaction
BEGIN;

-- Step 1: Drop existing foreign key constraints 
ALTER TABLE IF EXISTS job_requirements DROP CONSTRAINT IF EXISTS job_requirements_job_id_fkey;
ALTER TABLE IF EXISTS job_responsibilities DROP CONSTRAINT IF EXISTS job_responsibilities_job_id_fkey;
ALTER TABLE IF EXISTS job_benefits DROP CONSTRAINT IF EXISTS job_benefits_job_id_fkey;
ALTER TABLE IF EXISTS job_skills DROP CONSTRAINT IF EXISTS job_skills_job_id_fkey;
ALTER TABLE IF EXISTS job_contacts DROP CONSTRAINT IF EXISTS job_contacts_job_id_fkey;

-- Step 2: Drop composite primary key constraints
ALTER TABLE job_listings DROP CONSTRAINT IF EXISTS job_listings_pkey;
ALTER TABLE job_details DROP CONSTRAINT IF EXISTS job_details_pkey;

-- Step 3: Add back single column primary keys
ALTER TABLE job_listings ADD CONSTRAINT job_listings_pkey PRIMARY KEY (id);
ALTER TABLE job_details ADD CONSTRAINT job_details_pkey PRIMARY KEY (id);

-- Step 4: Recreate foreign key constraints
ALTER TABLE job_requirements ADD CONSTRAINT job_requirements_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES job_details(id);
    
ALTER TABLE job_responsibilities ADD CONSTRAINT job_responsibilities_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES job_details(id);
    
ALTER TABLE job_benefits ADD CONSTRAINT job_benefits_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES job_details(id);
    
ALTER TABLE job_skills ADD CONSTRAINT job_skills_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES job_details(id);
    
ALTER TABLE job_contacts ADD CONSTRAINT job_contacts_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES job_details(id);

-- Step 5: Update indexes
DROP INDEX IF EXISTS idx_job_listings_id;
DROP INDEX IF EXISTS idx_job_details_id;

-- Recreate platform indexes
CREATE INDEX IF NOT EXISTS idx_job_listings_platform ON job_listings(platform);
CREATE INDEX IF NOT EXISTS idx_job_details_platform ON job_details(platform);

-- Commit transaction
COMMIT;

-- Verification
SELECT 'Reverted to single id primary key' as status; 