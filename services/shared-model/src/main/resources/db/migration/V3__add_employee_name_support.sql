ALTER TABLE enrollment.enrollment_record
    ADD COLUMN IF NOT EXISTS employee_name VARCHAR(255);

UPDATE enrollment.enrollment_record
SET employee_name = employee_id
WHERE employee_name IS NULL;

ALTER TABLE enrollment.enrollment_record
    ALTER COLUMN employee_name SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_enrollment_record_employee_name
    ON enrollment.enrollment_record (lower(employee_name));

ALTER TABLE processing.enrollment_processing_record
    ADD COLUMN IF NOT EXISTS employee_name VARCHAR(255);

UPDATE processing.enrollment_processing_record
SET employee_name = employee_id
WHERE employee_name IS NULL;

ALTER TABLE processing.enrollment_processing_record
    ALTER COLUMN employee_name SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_processing_record_employee_name
    ON processing.enrollment_processing_record (lower(employee_name));
