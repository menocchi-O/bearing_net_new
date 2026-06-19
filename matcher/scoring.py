from rapidfuzz import fuzz
import re

def normalize(code: str) -> str:
    return (
        code.upper()
        .replace(" ", "")
        .replace("/", "-")
        .replace(".", "-")
    )

def tokenize(code: str):
    return normalize(code).split("-")

def token_overlap(target, candidate):
    t = set(tokenize(target))
    c = set(tokenize(candidate))

    if not t or not c:
        return 0.0

    return len(t & c) / len(t | c)

def weighted_similarity(target, candidate):
    t_tokens = tokenize(target)
    c_tokens = tokenize(candidate)

    base_sim = fuzz.ratio(target, candidate) / 100
    suffix_sim = (
        fuzz.ratio(t_tokens[1], c_tokens[1]) / 100
        if len(t_tokens) > 1 and len(c_tokens) > 1
        else 0
    )

    return 0.6 * base_sim + 0.4 * suffix_sim

def base_code(code: str) -> str:
    norm = normalize(code)
    match = re.search(r"\d{3,5}", norm)
    return match.group(0) if match else norm

def heuristic_penalty(target, candidate):
    prefix_length = max(3, int(len(target) * 0.6)) 
    
    return fuzz.partial_ratio(target[:prefix_length], candidate[:prefix_length]) / 100

def final_score(target, candidate):
    return round(
        0.4 * token_overlap(target, candidate)
        + 0.4 * weighted_similarity(target, candidate)
        + 0.2 * heuristic_penalty(target, candidate),
        3
    )

