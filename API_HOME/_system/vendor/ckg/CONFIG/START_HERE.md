# CKG station

Start here: RUN_CKG.bat. Check counts without API calls: CHECK_INBOX.bat.

TEMPLATES/01_BLANK_TEMPLATE.md is the empty headings-and-fields form.
TEMPLATES/02_FULLY_EXPLAINED_TEMPLATE.md explains every section and rule.
TEMPLATES/CKG_ATOM_MASTER_TEMPLATE.md is the runner's current prompt contract; keep it aligned with the explained version.
PYTHON/run_ckg.py is the station entry point. Shared implementation is in workbench/.

Put an unprocessed UTF-8 paper in INBOX/03_GENERAL. WAITING is excluded. Set DEEPSEEK_API_KEY or supply CONFIG/keys.local.json privately. Keys were not copied.

Choose 1 for the first live test. No paid test has been run. Existing results from this runner resume from saved stages. Importing an old partially filled CKG and filling only its missing sections is NOT implemented. Do not feed an old companion to this runner expecting an incremental repair.

This station is self-contained. Older launchers at the parent folder use a different inbox; use this CKG folder going forward. The parent files are preserved. See CURRENT_CAPABILITIES.md for outstanding integrations.
