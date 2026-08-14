# Database schema

| Table | Purpose | Important fields |
|---|---|---|
| `users` | Student identity | `id`, unique `email`, `name`, `created_at` |
| `student_profiles` | Editable career evidence | unique `user_id`, `name`, and JSON arrays for `education`, `skills`, `experience`, `certifications`, and `projects` |
| `resumes` | Uploaded resume metadata and parsed result | `user_id`, `filename`, `mime_type`, `raw_text`, `parsed_data`, `created_at` |
| `job_postings` | Normalized internship knowledge base | `title`, `company`, `location`, `description`, JSON `required_skills`, `employment_type`, optional `source_url` |
| `applications` | Job-search state and notes | `user_id`, `job_id`, `status`, `notes`, optional string `deadline`, `updated_at` |
| `saved_jobs` | Saved listing relationship | `user_id`, `job_id`, `created_at` |
| `ai_match_results` | Explainable match output storage | `user_id`, `job_id`, `compatibility_score`, JSON `matched_skills`, JSON `missing_skills`, `reasoning`, `used_fallback` |

`student_profiles.user_id` is one-to-one with `users.id`. Resume, application, saved-job, and match records reference a user. Applications and saved jobs reference a job posting. JSON arrays keep the MVP easy to demonstrate; normalized child tables can be introduced when advanced querying is required.

For local use, `sqlite:///./career_companion.db` is created automatically at FastAPI startup and is ignored by Git. For PostgreSQL, set `DATABASE_URL` before starting the API and run the same initialization path against the target database after reviewing migrations. The demo code normalizes `mysql://` URLs to SQLAlchemy's `mysql+pymysql://` form for managed-template compatibility. Destructive schema changes are intentionally not automated in this MVP.
