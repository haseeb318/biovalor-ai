"""Validation rules for structured responses returned by the AI provider."""

from collections.abc import Mapping


REQUIRED_TEXT_FIELDS = (
	"primary_component",
	"recommended_pathway",
	"reason",
	"evidence_level",
)
REQUIRED_LIST_FIELDS = (
	"processing_steps",
	"alternative_pathways",
	"applications",
	"limitations",
)

# Signal that a generated response does not match the required schema.
class AIResponseValidationError(ValueError):
	"""Raised when an AI response does not match the required schema."""

# Check whether a required response value contains text.
def _has_text(value):
	return isinstance(value, str) and bool(value.strip())

# Check whether a response value is a usable string list.
def _is_usable_list(value):
	if isinstance(value, str):
		return bool(value.strip())
	if not isinstance(value, (list, tuple)):
		return False
	return all(isinstance(item, str) and item.strip() for item in value)

# Validate the complete structured response before display.
def validate_analysis_response(analysis):
	if not isinstance(analysis, Mapping):
		raise AIResponseValidationError(
			"AI response incomplete. Please try again."
		)

	missing_fields = [
		field_name
		for field_name in (*REQUIRED_TEXT_FIELDS, *REQUIRED_LIST_FIELDS)
		if field_name not in analysis
	]
	if missing_fields:
		raise AIResponseValidationError(
			"AI response incomplete. Please try again."
		)

	if any(not _has_text(analysis[field_name]) for field_name in REQUIRED_TEXT_FIELDS):
		raise AIResponseValidationError(
			"AI response incomplete. Please try again."
		)

	if any(
		not _is_usable_list(analysis[field_name])
		for field_name in REQUIRED_LIST_FIELDS
	):
		raise AIResponseValidationError(
			"AI response incomplete. Please try again."
		)

	return analysis