# """Knowledge-base loading helpers for selected biological waste records."""

from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "waste_knowledge.csv"

# Load the selected waste record from the CSV knowledge base.
def get_waste_data(waste_name):
	if not DATA_PATH.exists():
		raise FileNotFoundError(
			f"Knowledge base file was not found at {DATA_PATH}."
		)

	try:
		knowledge_base = pd.read_csv(DATA_PATH)
	except Exception as error:
		raise RuntimeError(
			f"The knowledge base could not be read from {DATA_PATH}: {error}"
		) from error

	knowledge_base.columns = knowledge_base.columns.str.strip()
	knowledge_base["waste_name"] = knowledge_base["waste_name"].astype(str).str.strip()

	matches = knowledge_base[knowledge_base["waste_name"] == waste_name.strip()]
	if matches.empty:
		return None

	return matches.iloc[0]