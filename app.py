# """Streamlit user interface for the BioValor AI decision-support prototype."""

import html

import pandas as pd
import streamlit as st

from ai.generator import (
	AIAnalysisError,
	MissingAPIKeyError,
	ask_followup_question,
	generate_analysis,
)
from utils.data_loader import get_waste_data
from utils.scoring import calculate_valorization_score
from utils.validation import AIResponseValidationError, validate_analysis_response


# Supported waste types currently available in the CSV knowledge base.
SUPPORTED_WASTES = [
	"Eggshell",
	"Fish scales",
	"Chicken feathers",
	"Rice husk",
	"Banana peel",
	"Sugarcane bagasse",
	"Citrus/fruit peels",
	"Spent coffee grounds",
	"Shrimp shells",
	"Sawdust / wood-processing residue",
]
ANALYSIS_STATE_KEY = "biovalor_analysis_context"
PAGE_STATE_KEY = "biovalor_current_page"


# Configure the shared Streamlit page before rendering any content.
st.set_page_config(
	page_title="BioValor AI",
	page_icon="BV",
	layout="wide",
)


# Apply the shared visual system and Streamlit layout overrides.
def apply_page_style():
	# Keep all presentation rules in one stylesheet so page components stay focused on content.
	st.markdown(
		"""
		<style>
		.main .block-container {
			padding-top: 1.4rem;
			padding-bottom: 0;
			max-width: 1180px;
			font-family: "Inter", "Segoe UI", Arial, sans-serif;
		}
		[data-testid="stMainBlockContainer"] {
			padding-bottom: 0 !important;
		}
		html, body, [class*="css"] {
			font-family: "Inter", "Segoe UI", Arial, sans-serif;
		}
		html, body {
			overflow-x: hidden;
		}
		section[data-testid="stSidebar"] {
			display: none;
		}
		.top-navbar {
			align-items: center;
			background: linear-gradient(135deg, #0b3328 0%, #0f766e 100%);
			border: 1px solid #0b5d55;
			border-radius: 8px;
			box-shadow: 0 10px 28px rgba(18, 64, 49, 0.18);
			display: flex;
			justify-content: space-between;
			margin-bottom: 0.85rem;
			min-height: 84px;
			padding: 1rem 1.25rem;
			position: sticky;
			top: 0;
			width: 100vw;
			z-index: 1000;
			margin-left: calc(50% - 50vw);
			margin-right: calc(50% - 50vw);
			padding-left: max(1.1rem, calc((100vw - 1080px) / 2 + -8rem));
			padding-right: max(1.1rem, calc((100vw - 1080px) / 2 + -8rem));
			box-sizing: border-box;
			max-width: 100vw;
		}
		.nav-brand {
			color: #ffffff;
			font-size: 1.35rem;
			font-weight: 800;
			line-height: 1.15;
		}
		.nav-tagline {
			color: #dff3eb;
			font-size: 0.88rem;
			margin-top: 0.1rem;
		}
		.nav-pill {
			background: #f2c14e;
			border-radius: 999px;
			color: #14382d;
			display: inline-block;
			font-size: 0.72rem;
			font-weight: 800;
			margin-left: 0.5rem;
			padding: 0.18rem 0.48rem;
			vertical-align: middle;
		}
		.nav-links {
			align-items: center;
			display: flex;
			gap: 0.45rem;
		}
		.nav-link {
			border: 1px solid rgba(255, 255, 255, 0.25);
			border-radius: 999px;
			color: #e9fff7 !important;
			font-size: 0.92rem;
			font-weight: 800;
			padding: 0.45rem 0.85rem;
			text-decoration: none !important;
			transition: all 0.15s ease;
		}
		.nav-link:hover {
			background: rgba(255, 255, 255, 0.13);
			border-color: rgba(255, 255, 255, 0.48);
			color: #ffffff !important;
		}
		.nav-link.active {
			background: #f2c14e;
			border-color: #f2c14e;
			color: #123f31 !important;
		}
		div[data-testid="stButton"] > button {
			border-radius: 8px;
			font-family: "Inter", "Segoe UI", Arial, sans-serif;
			font-weight: 700;
		}
		div[data-testid="stButton"] > button[kind="primary"] {
			background: #0f766e;
			border-color: #0f766e;
		}
		.biovalor-header {
			border: 1px solid #cfe4dc;
			background:
				linear-gradient(135deg, rgba(15, 61, 46, 0.94), rgba(17, 94, 89, 0.92)),
				linear-gradient(90deg, #f7fbf8, #eef7f3);
			border-radius: 8px;
			box-shadow: 0 10px 26px rgba(18, 64, 49, 0.12);
			padding: 1.1rem 1.25rem;
			margin-bottom: 1rem;
		}
		.biovalor-kicker {
			color: #f2c14e;
			font-size: 0.8rem;
			font-weight: 700;
			letter-spacing: 0;
			text-transform: uppercase;
			margin-bottom: 0.25rem;
		}
		.biovalor-title {
			color: #ffffff !important;
			font-size: 2.15rem;
			font-weight: 800;
			line-height: 1.1;
			margin: 0;
			text-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
		}
		.biovalor-tagline {
			color: #dff3eb;
			font-size: 1rem;
			margin-top: 0.35rem;
			margin-bottom: 0;
		}
		.biovalor-description {
			color: #eefaf5;
			font-size: 0.94rem;
			line-height: 1.55;
			margin: 0.65rem 0 0;
			max-width: 760px;
		}
		.input-panel {
			background: #f7fbf8;
			border: 1px solid #cfe4dc;
			border-radius: 8px;
			box-shadow: 0 6px 18px rgba(18, 64, 49, 0.07);
			padding: 0.55rem 0.9rem 0.85rem;
		}
		.input-panel [data-testid="stSelectbox"] label,
		.input-panel [data-testid="stNumberInput"] label,
		.input-panel [data-testid="stTextInput"] label {
			color: #123f31;
			font-size: 0.92rem;
			font-weight: 800;
		}
		.input-panel [data-testid="stSelectbox"] > div > div,
		.input-panel [data-testid="stNumberInput"] input,
		.input-panel [data-testid="stTextInput"] input {
			background: #ffffff;
			border-color: #b8d7ca;
			border-radius: 6px;
		}
		.input-panel [data-testid="stSelectbox"] > div > div:focus-within,
		.input-panel [data-testid="stNumberInput"] input:focus,
		.input-panel [data-testid="stTextInput"] input:focus {
			border-color: #0f766e;
			box-shadow: 0 0 0 1px #0f766e;
		}
		.form-intro {
			color: #526f63;
			font-size: 0.9rem;
			margin: 0.1rem 0 0.55rem;
		}
		div[data-testid="stForm"],
		div[data-testid="stVerticalBlockBorderWrapper"] {
			background: linear-gradient(145deg, #fbfefc 0%, #f0f8f4 100%);
			border: 1px solid #b8d7ca;
			border-radius: 12px;
			box-shadow: 0 12px 28px rgba(18, 64, 49, 0.1);
			padding: 1.15rem 1.2rem 1.2rem;
		}
		.form-header {
			border-bottom: 1px solid #cfe4dc;
			margin-bottom: 0.95rem;
			padding-bottom: 0.85rem;
		}
		.form-header-kicker {
			color: #0f766e;
			font-size: 0.72rem;
			font-weight: 800;
			letter-spacing: 0.08em;
			text-transform: uppercase;
		}
		.form-header-title {
			color: #123f31;
			font-size: 1.5rem;
			font-weight: 800;
			line-height: 1.2;
			margin-top: 0.18rem;
		}
		.form-header-description {
			color: #526f63;
			font-size: 0.92rem;
			line-height: 1.45;
			margin-top: 0.35rem;
			max-width: 720px;
		}
		div[data-testid="stForm"] label p,
		div[data-testid="stVerticalBlockBorderWrapper"] label p {
			color: #123f31;
			font-size: 0.92rem;
			font-weight: 800;
		}
		div[data-testid="stForm"] [data-testid="stSelectbox"] > div > div,
		div[data-testid="stForm"] [data-testid="stNumberInput"] input,
		div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] > div > div,
		div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stNumberInput"] input {
			background: #ffffff;
			border-color: #a9cfc0;
			border-radius: 7px;
		}
		div[data-testid="stForm"] [data-testid="stSelectbox"] > div > div:focus-within,
		div[data-testid="stForm"] [data-testid="stNumberInput"] input:focus,
		div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] > div > div:focus-within,
		div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stNumberInput"] input:focus {
			border-color: #0f766e;
			box-shadow: 0 0 0 1px #0f766e;
		}
		div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button,
		div[data-testid="stForm"] button[kind="primary"],
		div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] button[kind="primary"] {
			background: #f2c14e;
			border: 1px solid #d6a936;
			border-radius: 7px;
			box-shadow: 0 5px 12px rgba(180, 132, 30, 0.2);
			color: #14382d;
			font-size: 0.92rem;
			font-weight: 800;
			min-height: 2.7rem;
			transition: background 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
		}
		div[data-testid="stForm"] div[data-testid="stFormSubmitButton"],
		div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] {
			display: flex;
			justify-content: flex-end;
		}
		div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button,
		div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] button {
			width: auto;
		}
		div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover,
		div[data-testid="stForm"] button[kind="primary"]:hover,
		div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] button[kind="primary"]:hover {
			background: #e5b33d;
			box-shadow: 0 7px 16px rgba(180, 132, 30, 0.27);
			color: #123f31;
			transform: translateY(-1px);
		}
		.workflow-step {
			border: 1px solid #cfe4dc;
			border-radius: 8px;
			background: linear-gradient(180deg, #ffffff 0%, #f6fbf8 100%);
			box-shadow: 0 4px 14px rgba(18, 64, 49, 0.06);
			padding: 0.75rem 0.55rem;
			text-align: center;
			min-height: 74px;
		}
		.workflow-index {
			color: #0f766e;
			font-size: 0.74rem;
			font-weight: 700;
			margin-bottom: 0.15rem;
		}
		.workflow-label {
			color: #123f31;
			font-size: 0.94rem;
			font-weight: 700;
		}
		.section-note {
			color: #526f63;
			font-size: 0.95rem;
			margin-top: -0.35rem;
			margin-bottom: 0.7rem;
		}
		.main h3 {
			border-left: 4px solid #f2c14e;
			color: #123f31;
			font-size: 1.2rem;
			font-weight: 800;
			line-height: 1.25;
			margin-top: 1.35rem;
			padding-left: 0.7rem;
		}
		.analysis-summary {
			background: #f7fbf8;
			border: 1px solid #cfe4dc;
			border-radius: 10px;
			box-shadow: 0 6px 16px rgba(18, 64, 49, 0.06);
			display: grid;
			grid-template-columns: repeat(4, minmax(0, 1fr));
			gap: 0.7rem;
			margin: 0.2rem 0 1.25rem;
			padding: 0.75rem;
		}
		.analysis-summary-item {
			background: #ffffff;
			border-left: 3px solid #0f766e;
			border-radius: 6px;
			min-width: 0;
			padding: 0.65rem 0.75rem;
		}
		.analysis-summary-label {
			color: #526f63;
			font-size: 0.72rem;
			font-weight: 800;
			letter-spacing: 0.04em;
			margin-bottom: 0.25rem;
			text-transform: uppercase;
		}
		.analysis-summary-value {
			color: #123f31;
			font-size: 0.98rem;
			font-weight: 800;
			line-height: 1.3;
			overflow-wrap: anywhere;
		}
		.result-section-heading {
			border-bottom: 1px solid #dcece5;
			color: #123f31;
			font-size: 1.05rem;
			font-weight: 800;
			line-height: 1.3;
			margin-bottom: 0.7rem;
			padding: 0.45rem 0 0.55rem;
		}
		.result-section-heading::before {
			background: #f2c14e;
			content: "";
			display: inline-block;
			height: 0.8rem;
			margin-right: 0.45rem;
			vertical-align: -0.08rem;
			width: 0.22rem;
		}
		.recommendation-card {
			background: #fbfefc;
			border: 1px solid #b8d7ca;
			border-radius: 10px;
			box-shadow: 0 6px 16px rgba(18, 64, 49, 0.06);
			min-height: 128px;
			padding: 0.2rem 0.95rem 0.95rem;
		}
		.recommendation-card .result-section-heading {
			margin-bottom: 0.8rem;
		}
		.recommendation-value {
			background: #edf7f2;
			border-left: 4px solid #0f766e;
			border-radius: 6px;
			color: #123f31;
			font-size: 1rem;
			font-weight: 800;
			line-height: 1.45;
			padding: 0.75rem 0.85rem;
		}
		.main div[data-testid="stMetric"] {
			background: #f7fbf8;
			border: 1px solid #cfe4dc;
			border-radius: 8px;
			padding: 0.65rem 0.75rem;
		}
		.main div[data-testid="stMetricLabel"] p {
			color: #526f63;
			font-size: 0.78rem;
			font-weight: 800;
		}
		.main div[data-testid="stMetricValue"] {
			color: #123f31;
			font-size: 1.35rem;
			font-weight: 800;
		}
		.main div[data-testid="stExpander"] {
			background: #fbfefc;
			border: 1px solid #cfe4dc;
			border-radius: 10px;
		}
		.evidence-panel-heading {
			align-items: center;
			border-bottom: 1px solid #dcece5;
			display: flex;
			gap: 0.55rem;
			justify-content: space-between;
			margin-bottom: 0.85rem;
			padding-bottom: 0.7rem;
		}
		.evidence-panel-title {
			color: #123f31;
			font-size: 1.15rem;
			font-weight: 800;
		}
		.evidence-panel-kicker {
			color: #0f766e;
			font-size: 0.72rem;
			font-weight: 800;
			letter-spacing: 0.07em;
			text-transform: uppercase;
		}
		.evidence-field-label {
			color: #526f63;
			font-size: 0.74rem;
			font-weight: 800;
			letter-spacing: 0.05em;
			margin: 0.75rem 0 0.25rem;
			text-transform: uppercase;
		}
		.evidence-field-value {
			background: #ffffff;
			border-left: 3px solid #0f766e;
			border-radius: 5px;
			color: #123f31;
			font-size: 0.92rem;
			font-weight: 700;
			line-height: 1.5;
			padding: 0.65rem 0.75rem;
		}
		.evidence-links {
			background: #ffffff;
			border: 1px solid #dcece5;
			border-radius: 6px;
			margin-top: 0.25rem;
			padding: 0.35rem 0.75rem;
		}
		.evidence-level {
			background: #fff8df;
			border: 1px solid #ead9a7;
			border-radius: 999px;
			color: #78580f;
			display: inline-block;
			font-size: 0.82rem;
			font-weight: 800;
			padding: 0.38rem 0.7rem;
		}
		.analysis-loader {
			align-items: center;
			background: linear-gradient(135deg, #123f31 0%, #115e59 100%);
			border: 1px solid #0f766e;
			border-radius: 10px;
			box-shadow: 0 8px 20px rgba(18, 64, 49, 0.12);
			color: #eefaf5;
			display: flex;
			gap: 0.8rem;
			margin: 0.8rem 0 1rem;
			padding: 0.95rem 1rem;
		}
		.analysis-loader-icon {
			align-items: center;
			background: rgba(242, 193, 78, 0.18);
			border: 1px solid rgba(242, 193, 78, 0.65);
			border-radius: 50%;
			display: flex;
			flex-shrink: 0;
			height: 2.35rem;
			justify-content: center;
			width: 2.35rem;
		}
		.analysis-loader-dot {
			animation: analysis-pulse 1.1s ease-in-out infinite;
			background: #f2c14e;
			border-radius: 50%;
			height: 0.55rem;
			width: 0.55rem;
		}
		.analysis-loader-title {
			color: #ffffff;
			font-size: 0.98rem;
			font-weight: 800;
		}
		.analysis-loader-copy {
			color: #dff3eb;
			font-size: 0.82rem;
			line-height: 1.4;
			margin-top: 0.16rem;
		}
		@keyframes analysis-pulse {
			0%, 100% { box-shadow: 0 0 0 0 rgba(242, 193, 78, 0.5); transform: scale(0.85); }
			50% { box-shadow: 0 0 0 0.38rem rgba(242, 193, 78, 0); transform: scale(1); }
		}
		.score-dashboard {
			background: linear-gradient(145deg, #f8fcfa 0%, #edf7f2 100%);
			border: 1px solid #b8d7ca;
			border-radius: 12px;
			box-shadow: 0 10px 24px rgba(18, 64, 49, 0.08);
			margin: 0.4rem 0 1.25rem;
			padding: 1rem;
		}
		.score-dashboard-header {
			align-items: center;
			display: flex;
			gap: 1.25rem;
			justify-content: space-between;
			margin-bottom: 1rem;
		}
		.score-dashboard-kicker {
			color: #0f766e;
			font-size: 0.72rem;
			font-weight: 800;
			letter-spacing: 0.08em;
			text-transform: uppercase;
		}
		.score-dashboard-title {
			color: #123f31;
			font-size: 1.2rem;
			font-weight: 800;
			margin-top: 0.15rem;
		}
		.score-dashboard-note {
			color: #526f63;
			font-size: 0.82rem;
			margin-top: 0.2rem;
		}
		.score-total {
			align-items: baseline;
			background: #123f31;
			border-radius: 9px;
			color: #ffffff;
			display: flex;
			flex-shrink: 0;
			gap: 0.25rem;
			padding: 0.7rem 0.9rem;
		}
		.score-total-value {
			font-size: 1.8rem;
			font-weight: 800;
			line-height: 1;
		}
		.score-total-max {
			color: #dff3eb;
			font-size: 0.85rem;
			font-weight: 700;
		}
		.score-progress-track {
			background: #d7e9e0;
			border-radius: 999px;
			height: 0.55rem;
			overflow: hidden;
		}
		.score-progress-fill {
			background: linear-gradient(90deg, #0f766e, #f2c14e);
			border-radius: 999px;
			height: 100%;
		}
		.score-card-grid {
			display: grid;
			grid-template-columns: repeat(5, minmax(0, 1fr));
			gap: 0.65rem;
			margin-top: 1rem;
		}
		.score-card {
			background: #ffffff;
			border: 1px solid #cfe4dc;
			border-radius: 8px;
			padding: 0.7rem;
		}
		.score-card-label {
			color: #526f63;
			font-size: 0.76rem;
			font-weight: 800;
			line-height: 1.2;
			min-height: 1.85rem;
		}
		.score-card-value {
			color: #123f31;
			font-size: 1.1rem;
			font-weight: 800;
			margin-top: 0.25rem;
		}
		.score-card-bar {
			background: #e3f0ea;
			border-radius: 999px;
			height: 0.3rem;
			margin-top: 0.45rem;
			overflow: hidden;
		}
		.score-card-fill {
			background: #0f766e;
			border-radius: 999px;
			height: 100%;
		}
		@media (max-width: 720px) {
			.score-dashboard-header {
				align-items: flex-start;
				flex-direction: column;
			}
			.score-card-grid {
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}
		}
		@media (max-width: 720px) {
			.analysis-summary {
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}
		}
		.about-intro {
			background: linear-gradient(135deg, #edf7f2 0%, #fbfefc 100%);
			border-left: 5px solid #0f766e;
			border-radius: 0 10px 10px 0;
			margin: 0.4rem 0 1.5rem;
			padding: 1rem 1.15rem;
		}
		.about-intro-label {
			color: #0f766e;
			font-size: 0.72rem;
			font-weight: 800;
			letter-spacing: 0.08em;
			text-transform: uppercase;
		}
		.about-intro-copy {
			color: #123f31;
			font-size: 1.05rem;
			font-weight: 700;
			line-height: 1.5;
			margin-top: 0.3rem;
		}
		.about-section-lead {
			color: #526f63;
			font-size: 0.92rem;
			line-height: 1.55;
			margin: -0.65rem 0 0.85rem;
		}
		.about-divider {
			align-items: center;
			display: flex;
			gap: 0.6rem;
			margin: 1.35rem 0 1rem;
		}
		.about-divider::before,
		.about-divider::after {
			background: #dcece5;
			content: "";
			height: 1px;
			width: 100%;
		}
		.about-divider-mark {
			background: #f2c14e;
			border-radius: 999px;
			flex-shrink: 0;
			height: 0.38rem;
			width: 0.38rem;
		}
		.about-architecture {
			display: grid;
			grid-template-columns: repeat(6, minmax(0, 1fr));
			gap: 0.6rem;
			margin: 0.55rem 0 1.35rem;
		}
		.about-architecture-item {
			background: #f7fbf8;
			border: 1px solid #cfe4dc;
			border-radius: 8px;
			min-height: 82px;
			padding: 0.7rem 0.55rem;
			text-align: center;
		}
		.about-architecture-number {
			color: #f2c14e;
			font-size: 0.75rem;
			font-weight: 800;
		}
		.about-architecture-label {
			color: #123f31;
			font-size: 0.82rem;
			font-weight: 800;
			line-height: 1.25;
			margin-top: 0.35rem;
		}
		.about-evidence {
			background: #123f31;
			border-radius: 10px;
			color: #eefaf5;
			margin: 0.55rem 0 1.35rem;
			padding: 1rem 1.15rem;
		}
		.about-evidence-title,
		.about-scoring-title {
			font-size: 0.78rem;
			font-weight: 800;
			letter-spacing: 0.07em;
			text-transform: uppercase;
		}
		.about-evidence-title {
			color: #f2c14e;
		}
		.about-evidence-copy {
			font-size: 0.94rem;
			line-height: 1.6;
			margin-top: 0.35rem;
		}
		.about-scoring {
			background: #fffaf0;
			border: 1px solid #ead9a7;
			border-radius: 10px;
			margin: 0.55rem 0 1.35rem;
			padding: 1rem 1.15rem;
		}
		.about-scoring-title {
			color: #8b6514;
		}
		.about-scoring-copy {
			color: #5d4b22;
			font-size: 0.94rem;
			line-height: 1.6;
			margin-top: 0.35rem;
		}
		.about-waste-grid {
			display: grid;
			grid-template-columns: repeat(2, minmax(0, 1fr));
			gap: 0.55rem 1rem;
			margin: 0.55rem 0 1.4rem;
		}
		.about-waste-item {
			background: #f7fbf8;
			border-bottom: 1px solid #cfe4dc;
			color: #123f31;
			font-size: 0.9rem;
			font-weight: 700;
			padding: 0.5rem 0.65rem;
		}
		.about-waste-item::before {
			color: #0f766e;
			content: "•";
			font-size: 1.1rem;
			margin-right: 0.45rem;
		}
		.score-explanation {
			background: #f7fbf8;
			border: 1px solid #cfe4dc;
			border-radius: 10px;
			margin: 0.7rem 0 1.4rem;
			padding: 0.9rem;
		}
		.score-explanation-intro {
			color: #123f31;
			font-size: 0.9rem;
			font-weight: 800;
			line-height: 1.5;
			margin: 0 0 0.75rem;
		}
		.score-explanation-grid {
			display: grid;
			grid-template-columns: repeat(2, minmax(0, 1fr));
			gap: 0.65rem;
		}
		.score-explanation-item {
			background: #ffffff;
			border: 1px solid #dcece5;
			border-radius: 8px;
			padding: 0.75rem;
		}
		.score-explanation-top {
			align-items: center;
			display: flex;
			gap: 0.55rem;
			justify-content: space-between;
		}
		.score-explanation-title {
			color: #123f31;
			font-size: 0.88rem;
			font-weight: 800;
		}
		.score-explanation-points {
			background: #edf7f2;
			border-radius: 999px;
			color: #0f766e;
			flex-shrink: 0;
			font-size: 0.74rem;
			font-weight: 800;
			padding: 0.22rem 0.5rem;
		}
		.score-explanation-copy {
			color: #526f63;
			font-size: 0.82rem;
			line-height: 1.45;
			margin-top: 0.45rem;
		}
		@media (max-width: 560px) {
			.score-explanation-grid {
				grid-template-columns: 1fr;
			}
		}
		@media (max-width: 900px) {
			.about-architecture {
				grid-template-columns: repeat(3, minmax(0, 1fr));
			}
		}
		@media (max-width: 560px) {
			.about-architecture,
			.about-waste-grid {
				grid-template-columns: 1fr;
			}
		}
		.footer {
			background: linear-gradient(135deg, #123f31 0%, #115e59 100%);
			border: 1px solid #0f4f43;
			border-radius: 8px;
			box-shadow: 0 8px 22px rgba(18, 64, 49, 0.1);
			color: #dff3eb;
			font-size: 0.88rem;
			margin-top: 2rem;
			min-height: 112px;
			padding: 1.45rem 1.35rem;
			width: 100vw;
			margin-left: calc(50% - 50vw);
			margin-right: calc(50% - 50vw);
			padding-left: max(1.25rem, calc((100vw - 1180px) / 2 + -4.75rem));
			padding-right: max(1.25rem, calc((100vw - 1180px) / 2 + -4.75rem));
			box-sizing: border-box;
			max-width: 100vw;
			position: sticky;
			bottom: 0;
			z-index: 900;
			margin-bottom: 0;
		}
		.footer-grid {
			align-items: center;
			display: flex;
			gap: 1rem;
			justify-content: space-between;
		}
		.footer-links {
			display: flex;
			flex-wrap: wrap;
			gap: 0.5rem;
			justify-content: flex-end;
		}
		.footer-title {
			color: #ffffff;
			font-size: 1.15rem;
			font-weight: 800;
			margin-bottom: 0.2rem;
		}
		.footer-note {
			color: #dff3eb;
			margin: 0;
		}
		.footer-pill {
			background: rgba(242, 193, 78, 0.18);
			border: 1px solid rgba(242, 193, 78, 0.45);
			border-radius: 999px;
			color: #ffe39a;
			display: inline-block;
			font-size: 0.76rem;
			font-weight: 800;
			padding: 0.2rem 0.55rem;
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


# Render navigation and keep the selected page in session state.
def render_navbar():
	# Query parameters provide lightweight navigation between the Home and About views.
	page = st.query_params.get("page", "Home")
	if page not in ("Home", "About"):
		page = "Home"
	st.session_state[PAGE_STATE_KEY] = page
	home_active = " active" if page == "Home" else ""
	about_active = " active" if page == "About" else ""

	st.markdown(
		f"""
		<div class="top-navbar">
			<div>
				<div class="nav-brand">BioValor AI <span class="nav-pill">SCIENCE + AI</span></div>
				<div class="nav-tagline">Biological waste valorization assistant</div>
			</div>
			<div class="nav-links">
				<a class="nav-link{home_active}" href="?page=Home" target="_self">Home</a>
				<a class="nav-link{about_active}" href="?page=About" target="_self">About</a>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


# Render the reusable hero area for Home and About pages.
def render_header(page_name):
	# The same evidence-focused hero is shared by both top-level pages.
	st.markdown(
		f"""
		<div class="biovalor-header">
			<div class="biovalor-kicker">{page_name}</div>
			<h1 class="biovalor-title">
				Explore practical valorization opportunities grounded in scientific evidence.
			</h1>
			<p class="biovalor-description">
				Describe the material, its source, and current condition. <strong>BioValor AI
				combines our curated scientific knowledge base, transparent scoring, and
				AI-assisted interpretation to identify and compare promising valorization
				pathways.</strong>
			</p>
		</div>
		""",
		unsafe_allow_html=True,
	)


# Render the full-width footer and project status badges.
def render_footer():
	# The footer communicates the prototype's evidence and deployment posture.
	st.markdown(
		"""
		<div class="footer">
			<div class="footer-grid">
				<div>
					<div class="footer-title">BioValor AI</div>
					<p class="footer-note">
						Scientific decision-support prototype for biological waste valorization.
						AI-generated interpretation should be reviewed against displayed sources.
					</p>
				</div>
				<div class="footer-links">
					<span class="footer-pill">Evidence aware</span>
				</div>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


# Render the six-step analysis workflow indicator.
def render_workflow():
	steps = ["Waste", "AI Analysis", "Score", "Recommendation", "Process", "Applications"]
	columns = st.columns(len(steps))
	for index, (column, step) in enumerate(zip(columns, steps), start=1):
		with column:
			st.markdown(
				f"""
				<div class="workflow-step">
					<div class="workflow-index">STEP {index}</div>
					<div class="workflow-label">{step}</div>
				</div>
				""",
				unsafe_allow_html=True,
			)


# Convert one analysis value into safe display text.
def text_from_analysis(analysis, field_name):
	value = analysis.get(field_name)
	return str(value).strip() if value not in (None, "") else "Not available"


# Normalize list-like analysis values for UI rendering.
def list_from_analysis(analysis, field_name):
	value = analysis.get(field_name)
	if not value:
		return []
	if isinstance(value, str):
		return [value]
	return [str(item).strip() for item in value if str(item).strip()]


# Display the generated recommendation in structured result sections.
def display_ai_analysis(analysis):
	# Render the validated AI schema as separate sections instead of one long response.
	primary_column, pathway_column = st.columns(2)
	with primary_column:
		st.markdown(
			f"""
			<div class="recommendation-card">
				<div class="result-section-heading">Primary Valuable Component</div>
				<div class="recommendation-value">{html.escape(text_from_analysis(analysis, "primary_component"))}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
	with pathway_column:
		st.markdown(
			f"""
			<div class="recommendation-card">
				<div class="result-section-heading">Recommended Pathway</div>
				<div class="recommendation-value">{html.escape(text_from_analysis(analysis, "recommended_pathway"))}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)

	with st.container(border=True):
		st.markdown('<div class="result-section-heading">Reason for Recommendation</div>', unsafe_allow_html=True)
		st.write(text_from_analysis(analysis, "reason"))

	with st.container(border=True):
		st.markdown('<div class="result-section-heading">Processing Pathway</div>', unsafe_allow_html=True)
		processing_steps = list_from_analysis(analysis, "processing_steps")
		if processing_steps:
			for step_number, step in enumerate(processing_steps, start=1):
				st.markdown(f"{step_number}. {step}")
		else:
			st.info("Processing steps are not available.")

	alternative_column, applications_column = st.columns(2)
	with alternative_column:
		with st.container(border=True):
			st.markdown('<div class="result-section-heading">Alternative Pathways</div>', unsafe_allow_html=True)
			alternative_pathways = list_from_analysis(analysis, "alternative_pathways")
			if alternative_pathways:
				for pathway in alternative_pathways:
					st.markdown(f"- {pathway}")
			else:
				st.info("Alternative pathways are not available.")

	with applications_column:
		with st.container(border=True):
			st.markdown('<div class="result-section-heading">Potential Applications</div>', unsafe_allow_html=True)
			applications = list_from_analysis(analysis, "applications")
			if applications:
				for application in applications:
					st.markdown(f"- {application}")
			else:
				st.info("Potential applications are not available.")

	with st.container(border=True):
		st.markdown('<div class="result-section-heading">Limitations</div>', unsafe_allow_html=True)
		limitations = list_from_analysis(analysis, "limitations")
		if limitations:
			for limitation in limitations:
				st.warning(limitation)
		else:
			st.info("Limitations are not available.")


# Display source, DOI, links, and evidence level for a waste record.
def display_scientific_evidence(waste_record):
	# Keep source metadata visible so recommendations remain traceable to the knowledge base.
	def record_value(field_name):
		value = waste_record.get(field_name)
		if value is None or pd.isna(value) or not str(value).strip():
			return "Not available"
		return str(value).strip()

	with st.container(border=True):
		source_title = record_value("source_title")
		doi = record_value("doi")
		source_url = record_value("source_url")
		evidence_level = record_value("evidence_level")

		st.markdown(
			"""
			<div class="evidence-panel-heading">
				<div class="evidence-panel-title">Scientific Evidence</div>
				<div class="evidence-panel-kicker">Knowledge base</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		st.markdown('<div class="evidence-field-label">Source</div>', unsafe_allow_html=True)
		st.markdown(
			f'<div class="evidence-field-value">{html.escape(source_title)}</div>',
			unsafe_allow_html=True,
		)

		st.markdown('<div class="evidence-field-label">DOI</div>', unsafe_allow_html=True)
		st.markdown(
			f'<div class="evidence-field-value">{html.escape(doi)}</div>',
			unsafe_allow_html=True,
		)

		st.markdown(
			'<div class="evidence-field-label">Reference / View scientific source</div>',
			unsafe_allow_html=True,
		)
		if source_url == "Not available":
			st.markdown('<div class="evidence-links">Not available</div>', unsafe_allow_html=True)
		else:
			st.markdown('<div class="evidence-links">', unsafe_allow_html=True)
			for url in [item.strip() for item in source_url.split(";") if item.strip()]:
				st.markdown(f"- [{url}]({url})")
			st.markdown("</div>", unsafe_allow_html=True)

		st.markdown('<div class="evidence-field-label">Evidence Level</div>', unsafe_allow_html=True)
		st.markdown(
			f'<div class="evidence-level">{html.escape(evidence_level)}</div>',
			unsafe_allow_html=True,
		)


# Display the total score and its weighted component breakdown.
def display_score(score):
	# The score dashboard shows both the total and the contribution of each criterion.
	score_items = [
		("Evidence", score["evidence_strength"], 25),
		("Component", score["component_value"], 25),
		("Applications", score["application_potential"], 20),
		("Feasibility", score["processing_feasibility"], 15),
		("Maturity", score["pathway_maturity"], 15),
	]
	total_score = score["total_score"]
	card_markup = "".join(
		f"""
		<div class="score-card">
			<div class="score-card-label">{label}</div>
			<div class="score-card-value">{value} / {maximum}</div>
			<div class="score-card-bar"><div class="score-card-fill" style="width: {value / maximum * 100:.0f}%"></div></div>
		</div>
		"""
		for label, value, maximum in score_items
	)
	st.markdown(
		f"""
		<div class="score-dashboard">
			<div class="score-dashboard-header">
				<div>
					<div class="score-dashboard-kicker">Decision support</div>
					<div class="score-dashboard-title">Valorization Suitability Score</div>
					<div class="score-dashboard-note">A transparent prototype score, not a probability or guaranteed yield.</div>
				</div>
				<div class="score-total">
					<span class="score-total-value">{total_score}</span>
					<span class="score-total-max">/ 100</span>
				</div>
			</div>
			<div class="score-progress-track"><div class="score-progress-fill" style="width: {total_score}%"></div></div>
			<div class="score-card-grid">{card_markup}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


# Render and collect the waste profile form values.
def render_analysis_input():
	# The regular button intentionally avoids native form-submit behavior on Enter.
	with st.container(border=True):
		st.markdown(
			"""
			<div class="form-header">
				<div class="form-header-kicker">Material assessment</div>
				<div class="form-header-title">Build a waste profile</div>
				<div class="form-header-description">
					A few material details help us find the most relevant pathway evidence
					and shape a useful first recommendation.
				</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		st.markdown(
			'<div class="form-intro">Start with the material you have available today.</div>',
			unsafe_allow_html=True,
		)
		waste_column, quantity_column = st.columns(2)
		with waste_column:
			selected_waste = st.selectbox(
				"Biological waste stream",
				SUPPORTED_WASTES,
				help="Choose the waste material you want to evaluate for higher-value uses.",
			)
		with quantity_column:
			quantity = st.number_input(
				"Available quantity (kg)",
				min_value=None,
				value=0.0,
				step=1.0,
				format="%.2f",
				help="Enter the approximate quantity available for this assessment.",
			)

		source_column, condition_column = st.columns(2)
		with source_column:
			source = st.selectbox(
				"Where is the material generated?",
				[
					"Food processing",
					"Poultry processing",
					"Fish processing",
					"Seafood processing",
					"Agricultural residue",
					"Household food waste",
					"Coffee brewing/processing",
					"Forestry/wood processing",
					"Other",
				],
				help="The source helps frame handling needs and likely processing conditions.",
			)
		with condition_column:
			condition = st.selectbox(
				"Current material condition",
				["Wet", "Dry", "Mixed", "Unknown"],
				help="Select the state of the material before any treatment or processing.",
			)

		submitted = st.button(
			"ANALYZE WITH BIOVALOR AI",
			type="primary",
			key="analyze_waste_button",
		)

	return selected_waste, quantity, source, condition, submitted


# Run validation, scoring, retrieval, and AI analysis for one submission.
def handle_analysis(selected_waste, quantity, source, condition):
	# This is the main orchestration path: validate, retrieve, score, generate, then store.
	if quantity <= 0:
		st.error("Please enter a valid quantity greater than 0 kg.")
		return

	try:
		waste_record = get_waste_data(selected_waste)
	except (FileNotFoundError, RuntimeError) as error:
		st.error(str(error))
		return

	input_values = [
		("Waste", selected_waste),
		("Quantity", f"{quantity:g} kg"),
		("Source", source),
		("Condition", condition),
	]
	input_items = "".join(
		f'<div class="analysis-summary-item">'
		f'<div class="analysis-summary-label">{html.escape(label)}</div>'
		f'<div class="analysis-summary-value">{html.escape(value)}</div>'
		f"</div>"
		for label, value in input_values
	)
	st.subheader("Analysis Input")
	st.markdown(f'<div class="analysis-summary">{input_items}</div>', unsafe_allow_html=True)

	if waste_record is None:
		st.warning("This waste type is outside the current BioValor AI knowledge base.")
		return

	st.success("Scientific information found: YES")
	score = calculate_valorization_score(waste_record)
	st.info(
		"Your waste profile is ready. BioValor AI is reviewing the scientific "
		"evidence and preparing a grounded valorization recommendation."
	)
	loading_placeholder = st.empty()
	loading_placeholder.markdown(
		"""
		<div class="analysis-loader">
			<div class="analysis-loader-icon"><div class="analysis-loader-dot"></div></div>
			<div>
				<div class="analysis-loader-title">Analyzing your waste stream</div>
				<div class="analysis-loader-copy">
					Connecting the selected material to scientific evidence and preparing your recommendation.
				</div>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	try:
		user_context = {
			"waste_type": selected_waste,
			"quantity": f"{quantity:g}",
			"source": source,
			"condition": condition,
		}
		with st.spinner(
			"Generating an evidence-aware recommendation..."
		):
			analysis = generate_analysis(
				waste_record,
				user_context,
				score,
			)
			analysis = validate_analysis_response(analysis)
	except MissingAPIKeyError as error:
		loading_placeholder.empty()
		st.warning(str(error))
	except AIResponseValidationError as error:
		loading_placeholder.empty()
		st.error(str(error))
	except (AIAnalysisError, ValueError) as error:
		loading_placeholder.empty()
		st.error(f"AI analysis failed: {error}")
	else:
		loading_placeholder.empty()
		st.session_state[ANALYSIS_STATE_KEY] = {
			"waste_record": waste_record,
			"user_context": user_context,
			"score": score,
			"analysis": analysis,
		}


# Render saved results and the follow-up question workflow.
def render_analysis_results():
	# Results are read from session state so navigation reruns do not discard the analysis.
	analysis_context = st.session_state.get(ANALYSIS_STATE_KEY)
	if not analysis_context:
		return

	display_score(analysis_context["score"])
	st.subheader("AI-generated Recommendation")
	display_ai_analysis(analysis_context["analysis"])
	display_scientific_evidence(analysis_context["waste_record"])

	st.subheader("Ask BioValor AI")
	question = st.text_input(
		"Ask a follow-up question about this analysis",
		placeholder="Why is this pathway recommended?",
		key="followup_question",
	)
	if st.button("ASK QUESTION"):
		if not question.strip():
			st.error("Please enter a question.")
		else:
			try:
				answer = ask_followup_question(
					analysis_context["waste_record"],
					analysis_context["user_context"],
					analysis_context["score"],
					analysis_context["analysis"],
					question,
				)
				st.session_state[ANALYSIS_STATE_KEY]["followup_answer"] = answer
			except MissingAPIKeyError as error:
				st.warning(str(error))
			except (AIAnalysisError, ValueError) as error:
				st.error(f"Follow-up question failed: {error}")
	if analysis_context.get("followup_answer"):
		st.subheader("BioValor AI Answer")
		st.write(analysis_context["followup_answer"])


# Explain how the five prototype score factors are weighted.
def render_score_explanation():
	# Keep the scoring explanation synchronized with the five weighted score criteria.
	score_factors = [
		("Evidence strength", "25 points", "Based on the evidence level in the scientific knowledge base."),
		("Component value", "25 points", "Based on documented major components and valorization potential."),
		("Application potential", "20 points", "Based on documented products and applications."),
		("Processing feasibility", "15 points", "Based on documented processing complexity and limitations."),
		("Pathway maturity", "15 points", "Based on the documented pathway and evidence."),
	]
	factor_markup = "".join(
		f"""
		<div class="score-explanation-item">
			<div class="score-explanation-top">
				<div class="score-explanation-title">{title}</div>
				<div class="score-explanation-points">{points}</div>
			</div>
			<div class="score-explanation-copy">{description}</div>
		</div>
		"""
		for title, points, description in score_factors
	)
	st.markdown(
		f"""
		<div class="score-explanation">
			<div class="score-explanation-intro">
				The suitability score combines five evidence-informed factors for a maximum of 100 points.
			</div>
			<div class="score-explanation-grid">{factor_markup}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


# Render the primary waste analysis experience.
def render_home_page():
	# Home combines input, analysis execution, saved results, and the score explanation.
	render_header("Home")
	render_workflow()
	st.divider()

	selected_waste, quantity, source, condition, submitted = render_analysis_input()
	if submitted:
		st.session_state.pop(ANALYSIS_STATE_KEY, None)
		handle_analysis(selected_waste, quantity, source, condition)

	render_analysis_results()
	render_footer()


# Render project context, architecture, evidence, and scoring guidance.
def render_about_page():
	# About explains the evidence model, supported materials, and prototype limitations.
	render_header("About")

	st.markdown(
		"""
		<div class="about-intro">
			<div class="about-intro-label">Built for better decisions</div>
			<div class="about-intro-copy">
				BioValor AI connects biological waste streams with evidence-aware
				valorization pathways, helping teams move from raw material to a more
				informed next step.
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	st.subheader("Project Purpose")
	st.markdown(
		'<p class="about-section-lead">A focused decision-support prototype for discovering practical value in biological residues.</p>',
		unsafe_allow_html=True,
	)
	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)

	st.subheader("How the System Works")
	architecture_items = [
		"Waste Input",
		"Curated Knowledge Base (dataset)",
		"AI Analysis",
		"Validation",
		"Score",
		"Dashboard",
	]
	architecture_markup = "".join(
		f'<div class="about-architecture-item"><div class="about-architecture-number">0{index}</div><div class="about-architecture-label">{label}</div></div>'
		for index, label in enumerate(architecture_items, start=1)
	)
	st.markdown(f'<div class="about-architecture">{architecture_markup}</div>', unsafe_allow_html=True)
	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)
	render_score_explanation()
	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)

	st.subheader("Supported Waste Types")
	waste_markup = "".join(
		f'<div class="about-waste-item">{waste_name}</div>'
		for waste_name in SUPPORTED_WASTES
	)
	st.markdown(f'<div class="about-waste-grid">{waste_markup}</div>', unsafe_allow_html=True)

	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)
	st.subheader("Future Waste Types")
	st.markdown(
		'<p class="about-section-lead">Planned additions for broader biological waste coverage in future releases.</p>',
		unsafe_allow_html=True,
	)
	future_waste_types = [
		"Potato peel",
		"Tomato pomace",
		"Apple pomace",
		"Grape pomace",
		"Olive pomace",
		"Pomegranate peel",
		"Pineapple peel",
		"Mango peel",
		"Onion peel",
		"Garlic peel",
		"Corn stover",
		"Wheat straw",
		"Rice straw",
		"Peanut shell",
		"Walnut shell",
		"Coconut shell",
		"Brewers' spent grain",
		"Dairy whey",
		"Cassava peel",
		"Cocoa pod husk",
	]
	future_waste_markup = "".join(
		f'<div class="about-waste-item">{waste_name}</div>'
		for waste_name in future_waste_types
	)
	st.markdown(
		f'<div class="about-waste-grid">{future_waste_markup}</div>',
		unsafe_allow_html=True,
	)

	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)
	st.subheader("Scientific Grounding")
	st.markdown(
		"""
		<div class="about-evidence">
			<div class="about-evidence-title">Evidence-aware by design</div>
			<div class="about-evidence-copy">
				The app retrieves a selected waste record from the CSV knowledge base
				and asks the model to use only that supplied scientific context. Source
				titles, DOI values, URLs, and evidence levels remain visible to the user.
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	st.markdown('<div class="about-divider"><span class="about-divider-mark"></span></div>', unsafe_allow_html=True)
	st.subheader("Prototype Scoring")
	st.markdown(
		"""
		<div class="about-scoring">
			<div class="about-scoring-title">Transparent, not predictive</div>
			<div class="about-scoring-copy">
				The Valorization Suitability Score is a transparent prototype score.
				It is not a probability of success, an experimental yield prediction,
				or an industrial guarantee.
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	render_footer()


# Initialize the application and render the selected route.
def main():
	# Render only the selected route; Streamlit reruns this function on interaction.
	apply_page_style()
	render_navbar()
	page = st.session_state.get(PAGE_STATE_KEY, "Home")

	if page == "About":
		render_about_page()
	else:
		render_home_page()


if __name__ == "__main__":
	main()
