
CREATE TABLE IF NOT EXISTS applicants (
    id SERIAL PRIMARY KEY,                     -- Unique identifier for each applicant
    program VARCHAR(255) NOT NULL,            -- Program name
    comments TEXT,                             -- Additional comments
    date_added TIMESTAMP DEFAULT NOW(),       -- Timestamp of addition
    url VARCHAR(255),                          -- URL related to the applicant
    status VARCHAR(255),                       -- Current application status
    term VARCHAR(255),                         -- Term of application (e.g., Fall 2025)
    us_or_international VARCHAR(20),           -- Indicate if US or international
    gpa FLOAT CHECK (gpa >= 0 AND gpa <= 4),  -- GPA value validation
    gre FLOAT CHECK (gre >= 0),                -- GRE score validation
    gre_v FLOAT CHECK (gre_v >= 0),            -- GRE verbal score validation
    gre_aw FLOAT CHECK (gre_aw >= 0),          -- GRE analytical writing score
    degree VARCHAR(100),                       -- Degree type (e.g., Masters, PhD)
    llm_generated_program VARCHAR(255),        -- LLM generated program name
    llm_generated_university VARCHAR(255)     -- LLM generated university name
);

