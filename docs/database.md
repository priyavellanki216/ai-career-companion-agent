# Database schema

| Table | Purpose | Important fields |
|---|---|---|
| `users` | Student identity | `id`, `email`, `name` |
| `student_profiles` | Editable career evidence | `education`, `skills`, `experience`, `certifications`, `projects` as JSON arrays |
| `resumes` | Uploaded resume metadata and parsed result | `filename`, `mime_type`, `raw_text`, `parsed_data` |
| `job_postings` | Normalized internship knowledge base | `title`, `company`, `location`, `description`, `required_skills` |
| `applications` | Job-search state and notes | `job_id`, `status`, `notes`, `deadline` |
| `saved_jobs` | Saved listing relationship | `user_id`, `job_id` |
| `ai_match_results` | Explainable cached match output | `compatibility_score`, `matched_skills`, `missing_skills`, `used_fallback` |

`student_profiles.user_id` is one-to-one with `users.id`. Resume, application, saved-job, and match records reference a user. Applications and saved jobs reference a job posting. JSON arrays keep the MVP easy to demonstrate; normalized child tables can be introduced when advanced querying is required.

For local use, `sqlite:///./career_companion.db` is created automatically. For PostgreSQL, set `DATABASE_URL` before starting the API and run the same initialization path against the target database after reviewing migrations. Destructive schema changes are intentionally not automated in this MVP.
