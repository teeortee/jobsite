"""Settings for the TeeOrTee project jobs board."""
SHOP = "https://teeortee.com"
SITE = "https://jobs.teeortee.com"
# Search engine site-verification tokens for jobs.teeortee.com (meta tag content values)
VERIFY = {"google-site-verification": "", "msvalidate.01": ""}
INDEXNOW_KEY = "7f3c2a9e5b1d4e8fa6c0b2d4e6f8a1c3"

# Role families: (id, label, keywords matched against lower-case title)
ROLES = [
    ("project-manager", "Project Manager", ["project manager", "project lead", "project management"]),
    ("programme-manager", "Programme / Program Manager", ["programme manager", "program manager", "portfolio manager"]),
    ("pmo", "PMO", ["pmo", "project management office", "portfolio office"]),
    ("project-controls", "Planner / Scheduler / Project Controls", ["planner", "scheduler", "project controls", "cost controller", "project control"]),
    ("scrum-delivery", "Scrum Master / Delivery Manager", ["scrum master", "delivery manager", "agile coach", "delivery lead", "release train"]),
    ("project-coordinator", "Project Coordinator", ["project coordinator", "project co-ordinator", "project administrator", "project analyst"]),
    ("product-manager", "Product Manager / Owner", ["product manager", "product owner"]),
]
EXCLUDE = ["intern ", "internship", "unpaid", "commission only", "recruiting", "recruiter", "talent acquisition", "media planner", "event planner", "financial planner", "meal planner"]

# Regions: id, label, Adzuna country codes, location keywords for keyless sources
REGIONS = [
    ("usa", "USA", ["us"], ["united states", "usa", ", us", "remote - us", "new york", "san francisco", "seattle", "austin", "chicago", "boston", "los angeles", "denver", "atlanta", "washington"]),
    ("uk", "UK", ["gb"], ["united kingdom", " uk", "london", "manchester", "birmingham", "edinburgh", "glasgow", "leeds", "bristol", "england", "scotland"]),
    ("europe", "Europe", ["de", "nl", "fr", "es", "it", "be", "at", "ch", "pl"], ["germany", "berlin", "munich", "netherlands", "amsterdam", "france", "paris", "spain", "madrid", "barcelona", "ireland", "dublin", "italy", "belgium", "austria", "switzerland", "poland", "sweden", "denmark", "portugal", "lisbon", "europe", "emea"]),
    ("canada", "Canada", ["ca"], ["canada", "toronto", "vancouver", "montreal", "calgary", "ottawa", "ontario", "british columbia"]),
    ("australia", "Australia & NZ", ["au", "nz"], ["australia", "sydney", "melbourne", "brisbane", "perth", "new zealand", "auckland"]),
]

# Company career boards (public ATS feeds). Unknown/invalid tokens are skipped.
GREENHOUSE = ["airbnb", "stripe", "databricks", "cloudflare", "gitlab", "figma", "dropbox", "reddit",
              "instacart", "datadog", "mongodb", "elastic", "twilio", "pinterest", "asana", "airtable",
              "squarespace", "duolingo", "discord", "affirm", "brex", "gusto", "samsara", "toast"]
LEVER = ["plaid", "palantir", "spotify", "netflix", "lever", "matterport", "kraken"]
ASHBY = ["notion", "ramp", "openai", "linear", "deel", "vercel", "replit", "posthog"]

# Which tees to show for which role family (product slugs on teeortee.com)
TEES = {
    "roadmap": ("It's on the Roadmap", "its-on-the-roadmap-t-shirt-funny-project-manager-gift"),
    "cr": ("Raise a Change Request", "you-want-one-more-thing-raise-a-change-request-t-shirt-project-manager-pmo-gift"),
    "scope": ("Who Changed the Scope?", "on-time-on-budget-who-changed-the-scope-t-shirt-project-manager-pmo-gift"),
    "risk": ("It's an Identified Risk", "its-not-a-problem-its-an-identified-risk-t-shirt-project-manager-pmo-gift"),
    "cp": ("I Know the Critical Path", "i-know-the-critical-path-t-shirt-funny-project-manager-gift"),
    "baseline": ("Blame the Baseline", "think-strategically-blame-the-baseline-t-shirt-funny-project-manager-gift"),
    "deps": ("I Manage Dependencies", "i-dont-make-excuses-i-manage-dependencies-t-shirt-project-manager-pmo-gift"),
    "meeting": ("Add It to the Risk Register", "another-meeting-ill-add-it-to-the-risk-register-t-shirt-project-manager-pmo-gift"),
    "pm": ("That's Why I'm the PM", "thats-why-im-the-pm-t-shirt-project-manager-pmo-gift"),
}
ROLE_TEES = {
    "project-manager": ["pm", "scope", "cr"],
    "programme-manager": ["deps", "baseline", "risk"],
    "pmo": ["meeting", "risk", "cr"],
    "project-controls": ["cp", "baseline", "deps"],
    "scrum-delivery": ["roadmap", "deps", "meeting"],
    "project-coordinator": ["meeting", "scope", "pm"],
    "product-manager": ["roadmap", "scope", "cr"],
}
