from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "waste_knowledge.csv"


def get_waste_data(waste_name):
	"""Return the single knowledge-base record for a waste type, if found."""
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