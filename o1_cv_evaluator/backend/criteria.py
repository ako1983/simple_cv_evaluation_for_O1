"""USCIS O-1A regulatory criteria.

These eight criteria come from 8 CFR 214.2(o)(3)(iii)(B). To qualify under
O-1A, a beneficiary must satisfy at least three.
"""

from typing import List, TypedDict


class Criterion(TypedDict):
    name: str
    short_name: str
    description: str
    examples: str


O1A_CRITERIA: List[Criterion] = [
    {
        "name": "Awards",
        "short_name": "awards",
        "description": (
            "Receipt of nationally or internationally recognized prizes or awards "
            "for excellence in the field of endeavor."
        ),
        "examples": (
            "Nobel Prize, Pulitzer, Turing Award, Olympic medals, Grammy, "
            "field-specific top honors, well-known industry awards judged by experts."
        ),
    },
    {
        "name": "Membership",
        "short_name": "membership",
        "description": (
            "Membership in associations in the field which require outstanding "
            "achievements of their members, as judged by recognized national or "
            "international experts."
        ),
        "examples": (
            "Fellow of IEEE / ACM / Royal Society, National Academy of Sciences/"
            "Engineering membership, invited membership in elite professional bodies."
        ),
    },
    {
        "name": "Press",
        "short_name": "press",
        "description": (
            "Published material in professional or major trade publications or major "
            "media about the beneficiary, relating to their work in the field."
        ),
        "examples": (
            "Profile pieces, feature articles, interviews in major newspapers, "
            "trade journals, or widely-read industry outlets — about the person, "
            "not merely quoting them."
        ),
    },
    {
        "name": "Judging",
        "short_name": "judging",
        "description": (
            "Participation, either individually or on a panel, as a judge of the "
            "work of others in the same or an allied field."
        ),
        "examples": (
            "Peer reviewer for journals/conferences, grant review panels, "
            "competition jury, hiring/promotion committees for elite roles, "
            "thesis committees."
        ),
    },
    {
        "name": "Original contribution",
        "short_name": "original_contribution",
        "description": (
            "Original scientific, scholarly, or business-related contributions of "
            "major significance in the field."
        ),
        "examples": (
            "Patents that have been licensed or widely adopted, novel methods/"
            "algorithms with documented impact, founding influential techniques, "
            "products with significant industry adoption."
        ),
    },
    {
        "name": "Scholarly articles",
        "short_name": "scholarly_articles",
        "description": (
            "Authorship of scholarly articles in the field, in professional "
            "journals or other major media."
        ),
        "examples": (
            "Peer-reviewed journal papers, conference proceedings (NeurIPS, ACL, "
            "Nature, etc.), book chapters in scholarly volumes."
        ),
    },
    {
        "name": "Critical role",
        "short_name": "critical_role",
        "description": (
            "Performance in a critical or essential capacity for organizations or "
            "establishments that have a distinguished reputation."
        ),
        "examples": (
            "Lead/principal/staff engineer at top-tier firms, founder or "
            "department head, key technical lead on flagship products at "
            "well-known organizations."
        ),
    },
    {
        "name": "High salary",
        "short_name": "high_salary",
        "description": (
            "Command of a high salary or other significantly high remuneration "
            "for services, in relation to others in the field."
        ),
        "examples": (
            "Total compensation in the top decile for the role/region, documented "
            "via offer letters, W-2s, or BLS comparison data."
        ),
    },
]


def criteria_block() -> str:
    """Format the criteria as a prompt-friendly bulleted block."""
    lines = []
    for c in O1A_CRITERIA:
        lines.append(f"- {c['name']}: {c['description']}")
        lines.append(f"  Examples: {c['examples']}")
    return "\n".join(lines)


def criterion_names() -> List[str]:
    return [c["name"] for c in O1A_CRITERIA]
