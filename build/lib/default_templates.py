import uuid
from src.personalize_db import save_template

DEFAULT_TEMPLATES = [
    {
        "id": str(uuid.uuid4()),
        "name": "clarity-default",
        "signal_type": "hiring",
        "subject": "Growth brings noise. Here's how to cut through it.",
        "opening": "{{first_name}} — saw {{company}} added {{signal.magnitude}} new hires. That's when updates multiply and priorities blur. EchoTray cuts through the noise so your team sees only what matters.",
        "is_fallback": 0
    },
    {
        "id": str(uuid.uuid4()),
        "name": "market-expansion",
        "signal_type": "market",
        "subject": "Expanding? Keep teams aligned across markets.",
        "opening": "{{first_name}}, congrats on the {{signal.market}} expansion. Cross-timezone work creates update overload. EchoTray keeps the signal high and the catch-up low.",
        "is_fallback": 0
    },
    {
        "id": str(uuid.uuid4()),
        "name": "product-launch",
        "signal_type": "product",
        "subject": "Post-launch alignment without the noise.",
        "opening": "Nice launch. After releases, Slack/email traffic spikes and clarity drops. EchoTray distills the chatter into priorities your team can act on.",
        "is_fallback": 0
    },
    {
        "id": str(uuid.uuid4()),
        "name": "funding-round",
        "signal_type": "funding",
        "subject": "Scaling fast? Keep your team aligned, not buried.",
        "opening": "{{first_name}} — congrats on the funding. When teams scale fast, priorities get noisy. EchoTray filters what matters so execution stays sharp.",
        "is_fallback": 0
    },
    {
        "id": str(uuid.uuid4()),
        "name": "leadership-change",
        "signal_type": "leadership",
        "subject": "New leadership deserves clearer priorities.",
        "opening": "{{first_name}}, saw the leadership update at {{company}}. Transitions bring alignment challenges. EchoTray ensures everyone knows what's critical.",
        "is_fallback": 0
    },
    {
        "id": str(uuid.uuid4()),
        "name": "fallback-clarity",
        "signal_type": "",
        "subject": "Fast teams need clarity, not more updates.",
        "opening": "{{first_name}} — fast teams drown in updates. EchoTray filters the noise so {{role}} sees only what drives results. No recap, just clarity.",
        "is_fallback": 1
    }
]


def load_default_templates():
    """Load all default templates into database"""
    for template in DEFAULT_TEMPLATES:
        save_template(template)
