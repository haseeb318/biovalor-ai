# """Pathway comparison helpers for validated waste analyses."""

import re


COMPARISON_CRITERIA = (
	"Scientific evidence",
	"Resource value",
	"Processing complexity",
	"Application potential",
)

# Normalize one comparison record field.
def _text(record, field_name):
	value = record.get(field_name, "")
	return "" if value is None else str(value).strip()

# Tokenize text for documented pathway matching.
def _tokens(value):
	return set(re.findall(r"[a-z0-9]+", value.lower()))

# Collect unique recommended and alternative pathways.
def _pathways(analysis):
	values = [analysis.get("recommended_pathway", "")]
	alternatives = analysis.get("alternative_pathways", [])
	if isinstance(alternatives, str):
		alternatives = [alternatives]
	values.extend(alternatives)

	result = []
	seen = set()
	for value in values:
		pathway = str(value).strip()
		key = pathway.casefold()
		if pathway and key not in seen:
			result.append(pathway)
			seen.add(key)
	return result

# Convert evidence wording into a comparison rating.
def _evidence_rating(evidence_level):
	level = evidence_level.casefold()
	if "systematic" in level or "comprehensive" in level:
		return "High"
	if "peer-reviewed" in level:
		return "Medium"
	return "Not available"

# Rate pathway alignment with documented resource information.
def _resource_rating(pathway, record):
	pathway_tokens = _tokens(pathway)
	documented = " ".join(
		_text(record, field_name)
		for field_name in (
			"major_components",
			"known_valorization_pathways",
			"potential_products",
		)
	)
	if not pathway_tokens or not pathway_tokens.intersection(_tokens(documented)):
		return "Not available"
	return "High"

# Rate the documented processing complexity of a pathway.
def _complexity_rating(pathway, record):
	documented = " ".join(
		[pathway, _text(record, "basic_processing_steps"), _text(record, "limitations")]
	).casefold()
	if not documented.strip():
		return "Not available"
	if any(
		phrase in documented
		for phrase in (
			"strong acid",
			"strong base",
			"strong chemical",
			"chemical treatment",
			"chemical activation",
			"deacetylation",
		)
	):
		return "High"
	if any(
		phrase in documented
		for phrase in ("purification", "fractionation", "extraction", "complex")
	):
		return "Medium"
	return "Not available"

# Rate pathway alignment with documented applications.
def _application_rating(pathway, record):
	pathway_tokens = _tokens(pathway)
	documented = " ".join(
		_text(record, field_name)
		for field_name in ("potential_products", "potential_applications")
	)
	if not pathway_tokens or not pathway_tokens.intersection(_tokens(documented)):
		return "Not available"
	return "High"

# Build comparison rows for the recommended and alternative pathways.
def build_pathway_comparison(waste_record, analysis):
	pathways = _pathways(analysis)
	if len(pathways) < 2:
		return []

	evidence_rating = _evidence_rating(_text(waste_record, "evidence_level"))
	column_names = [f"Recommended: {pathways[0]}", *pathways[1:]]
	rows = []
	for criterion in COMPARISON_CRITERIA:
		row = {"Criteria": criterion}
		for pathway, column_name in zip(pathways, column_names):
			if criterion == "Scientific evidence":
				rating = evidence_rating
			elif criterion == "Resource value":
				rating = _resource_rating(pathway, waste_record)
			elif criterion == "Processing complexity":
				rating = _complexity_rating(pathway, waste_record)
			else:
				rating = _application_rating(pathway, waste_record)
			row[column_name] = rating
		rows.append(row)
	return rows