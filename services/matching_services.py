from ast import Not
from asyncio.windows_events import NULL
from re import S
from tokenize import String
from services.classes import MatchingSession
from matcher.scoring import final_score, base_code
from matcher.normalize import TRANSFORM_STEPS

global session

def process_manual(required_code: str, session):
    
    base = base_code(required_code)

    candidates = [
        c for c in session.items_map
        if base in c
    ]

    if not candidates:
        return {
            "status": "not_found",
            "required_code": required_code,
            "candidates": []
        }

    scored = [
        {
            "candidate": c,

            "inner_code": session.items_map[c]["IDArticolo"],

            "required_code": session.items_map[c]["AppellativoCS"],

            "description": session.items_map[c]["Descrizione"],

            "score": final_score(required_code, c)
        }
        for c in candidates
    ]

    scored.sort(key=lambda x: x["score"], reverse=True)

    # generate candidates like before...

    return {
        "status": "review",
        "required_code": required_code,
        "candidates": scored[:5]
    }