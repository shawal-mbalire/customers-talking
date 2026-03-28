"""In-memory CRUD store for predefined Solution answers."""
import uuid
from ..models.session import Solution

_solutions: dict[str, Solution] = {}


def _seed() -> None:
    samples = [
        Solution(
            id=str(uuid.uuid4()),
            question="How do I check my balance?",
            answer="Dial *123# to check your account balance instantly.",
            intent_name="check_balance",
            trigger_phrases=["check balance", "my balance", "account balance", "balance"],
            channels=["all"],
        ),
        Solution(
            id=str(uuid.uuid4()),
            question="What are your working hours?",
            answer="We are open Monday to Friday, 8 AM – 6 PM EAT.",
            intent_name="working_hours",
            trigger_phrases=["working hours", "opening hours", "office hours", "open"],
            channels=["all"],
        ),
        Solution(
            id=str(uuid.uuid4()),
            question="How do I reset my PIN?",
            answer="Send RESET to 20880 and follow the instructions sent to you.",
            intent_name="reset_pin",
            trigger_phrases=["reset pin", "forgot pin", "change pin", "pin reset"],
            channels=["all"],
        ),
        Solution(
            id=str(uuid.uuid4()),
            question="How do I make a payment?",
            answer="Dial *456# and select 'Pay Bill', then enter the biller code provided.",
            intent_name="make_payment",
            trigger_phrases=["make payment", "pay bill", "payment", "pay"],
            channels=["ussd", "sms"],
        ),
        Solution(
            id=str(uuid.uuid4()),
            question="What is the SMS shortcode?",
            answer="Our SMS shortcode is 20880. Text your question and we'll reply instantly.",
            intent_name="sms_shortcode",
            trigger_phrases=["sms shortcode", "shortcode", "text number", "sms number"],
            channels=["all"],
        ),
    ]
    for s in samples:
        _solutions[s.id] = s


_seed()


def get_all() -> list[dict]:
    return [s.to_dict() for s in _solutions.values()]


def get_active() -> list[Solution]:
    return [s for s in _solutions.values() if s.active]


def get_by_id(solution_id: str) -> Solution | None:
    return _solutions.get(solution_id)


def create(data: dict) -> Solution:
    solution = Solution(
        id=str(uuid.uuid4()),
        question=data.get("question", ""),
        answer=data.get("answer", ""),
        intent_name=data.get("intentName", ""),
        trigger_phrases=data.get("triggerPhrases", []),
        channels=data.get("channels", ["all"]),
        active=data.get("active", True),
    )
    _solutions[solution.id] = solution
    return solution


def update(solution_id: str, data: dict) -> Solution | None:
    solution = _solutions.get(solution_id)
    if not solution:
        return None
    if "question" in data:
        solution.question = data["question"]
    if "answer" in data:
        solution.answer = data["answer"]
    if "intentName" in data:
        solution.intent_name = data["intentName"]
    if "triggerPhrases" in data:
        solution.trigger_phrases = data["triggerPhrases"]
    if "channels" in data:
        solution.channels = data["channels"]
    if "active" in data:
        solution.active = data["active"]
    return solution


def delete(solution_id: str) -> bool:
    if solution_id in _solutions:
        del _solutions[solution_id]
        return True
    return False


def find_match(text: str, channel: str) -> Solution | None:
    """Find first active solution matching text via trigger_phrases (case-insensitive substring)."""
    text_lower = text.lower()
    for solution in get_active():
        if "all" not in solution.channels and channel not in solution.channels:
            continue
        for phrase in solution.trigger_phrases:
            if phrase.lower() in text_lower:
                return solution
    return None
