# jobs.teeortee.com

Daily project-role jobs board for TeeOrTee. GitHub Actions fetches public job listings every morning,
rebuilds the static site and deploys it to GitHub Pages. A weekly workflow emails Brevo subscribers
the jobs matching their role, with matching tees from teeortee.com.

Secrets: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `BREVO_API_KEY`. Variables: `SIGNUP_URL`, `BREVO_LISTS`.
