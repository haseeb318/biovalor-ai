# """Transparent prototype scoring for scientific knowledge-base records."""


MAX_SCORES = {
	"evidence_strength": 25,
	"component_value": 25,
	"application_potential": 20,
	"processing_feasibility": 15,
	"pathway_maturity": 15,
}

EVIDENCE_SCORES = {
	"peer-reviewed systematic/review evidence": 25,
	"peer-reviewed comprehensive review evidence": 23,
	"peer-reviewed review and experimental evidence": 23,
	"peer-reviewed review evidence": 20,
}

# Normalize one knowledge-base field for scoring.
def _text(waste_data, field_name):
	value = waste_data.get(field_name, "")
	return "" if value is None else str(value).strip()

# Count documented semicolon-separated entries.
def _count_entries(value):
	return len([entry for entry in value.split(";") if entry.strip()])

# Convert a documented evidence level into its fixed score.
def _evidence_strength(evidence_level):
	return EVIDENCE_SCORES.get(evidence_level.lower(), 0)

# Score documented components and valorization pathways.
def _component_value(major_components, pathways):
	component_count = _count_entries(major_components)
	pathway_count = _count_entries(pathways)
	return min(25, component_count * 4 + pathway_count * 3)

# Score documented products and application categories.
def _application_potential(products, applications):
	category_count = _count_entries(products) + _count_entries(applications)
	return min(20, category_count * 2)

# Deduct feasibility points for documented processing burdens.
def _processing_feasibility(processing_steps, limitations):
	text = f"{processing_steps} {limitations}".lower()
	penalty = 0

	for phrase in ("strong chemical", "chemical treatment", "chemical activation"):
		if phrase in text:
			penalty += 2
	for phrase in ("high-temperature", "high temperature", "thermal treatment", "energy demand"):
		if phrase in text:
			penalty += 2
	for phrase in ("complex", "fractionation", "deacetylation", "purification"):
		if phrase in text:
			penalty += 1

	return max(0, min(15, 15 - penalty))

# Score pathway specificity, breadth, and supporting evidence.
def _pathway_maturity(pathway, known_pathways, evidence_level):
	pathway_count = _count_entries(known_pathways)
	score = 4 if pathway else 0
	score += min(6, pathway_count * 2)
	score += 5 if _evidence_strength(evidence_level) >= 20 else 0
	return min(15, score)

# Calculate the bounded score and return every component.
def calculate_valorization_score(waste_data):
	if waste_data is None:
		return None

	evidence_strength = _evidence_strength(_text(waste_data, "evidence_level"))
	component_value = _component_value(
		_text(waste_data, "major_components"),
		_text(waste_data, "known_valorization_pathways"),
	)
	application_potential = _application_potential(
		_text(waste_data, "potential_products"),
		_text(waste_data, "potential_applications"),
	)
	processing_feasibility = _processing_feasibility(
		_text(waste_data, "basic_processing_steps"),
		_text(waste_data, "limitations"),
	)
	pathway_maturity = _pathway_maturity(
		_text(waste_data, "recommended_pathway"),
		_text(waste_data, "known_valorization_pathways"),
		_text(waste_data, "evidence_level"),
	)

	scores = {
		"evidence_strength": evidence_strength,
		"component_value": component_value,
		"application_potential": application_potential,
		"processing_feasibility": processing_feasibility,
		"pathway_maturity": pathway_maturity,
	}

	for criterion, maximum in MAX_SCORES.items():
		scores[criterion] = max(0, min(maximum, int(scores[criterion])))

	scores["total_score"] = sum(scores.values())
	scores["total_score"] = max(0, min(100, scores["total_score"]))
	return {
		"total_score": scores["total_score"],
		"evidence_strength": scores["evidence_strength"],
		"component_value": scores["component_value"],
		"application_potential": scores["application_potential"],
		"processing_feasibility": scores["processing_feasibility"],
		"pathway_maturity": scores["pathway_maturity"],
	}