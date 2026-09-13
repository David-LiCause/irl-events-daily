.PHONY: setup-airtable preview-email

setup-airtable:
	python3 scripts/setup_airtable.py

preview-email:
	python3 scripts/preview_email.py
