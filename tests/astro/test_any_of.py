"""any_of combinator (S139) — the OR the AND-only vocabulary could not express."""
import agent.astro.predicates as P

CHART = {
    "planet_positions": {"Mars": {"house": 10, "sign": "Capricorn", "dignity": "Exalted"}},
    "navamsa": {"placements": {"Mars": {"sign": "Aries", "dignity": "Debilitated"}}},
    "lord_house_map": {5: 10},
}


def _v(preds):
    return P.evaluate_claim(preds, CHART)["verdict"]


# --- the live defect: OR with one true arm ---------------------------------
def test_disjunction_one_arm_holds_is_satisfied():
    # "5th lord in own sign OR own navamsa OR exalted" — Mars is exalted.
    assert _v([{"type": "any_of", "any_of": [
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Own Sign"},
        {"type": "navamsa_dignity", "graha": "Mars", "dignity": "Own Sign"},
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}]) == P.SATISFIED


def test_and_form_of_same_condition_is_wrongly_contradicted():
    # The bug this fixes: the same three arms as separate ANDed predicates.
    assert _v([
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Own Sign"},
        {"type": "navamsa_dignity", "graha": "Mars", "dignity": "Own Sign"},
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]) == P.CONTRADICTED


# --- roll-up truth table ---------------------------------------------------
def test_all_arms_refuted_is_contradicted():
    assert _v([{"type": "any_of", "any_of": [
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Own Sign"},
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Debilitated"}]}]) == P.CONTRADICTED


def test_some_arm_unevaluable_none_hold_is_unevaluable():
    # Venus absent from the block -> unevaluable arm; Own Sign refuted. Not all
    # refuted, none hold -> UNEVALUABLE (never a false CONTRADICTED).
    assert _v([{"type": "any_of", "any_of": [
        {"type": "planet_dignity", "graha": "Venus", "dignity": "Exalted"},
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Own Sign"}]}]) == P.UNEVALUABLE


def test_nested_any_of():
    assert _v([{"type": "any_of", "any_of": [
        {"type": "any_of", "any_of": [
            {"type": "planet_dignity", "graha": "Mars", "dignity": "Debilitated"},
            {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}]}]) == P.SATISFIED


def test_empty_or_malformed_any_of_is_unevaluable_never_raises():
    for bad in ([], "x", None):
        assert P.evaluate({"type": "any_of", "any_of": bad}, CHART)[0] == P.UNEVALUABLE


# --- validation + token recursion ------------------------------------------
def test_validate_accepts_good_any_of():
    ok, _ = P.validate_precondition({"type": "any_of", "any_of": [
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]})
    assert ok


def test_validate_rejects_bad_arm():
    ok, why = P.validate_precondition({"type": "any_of", "any_of": [
        {"type": "planet_dignity", "graha": "Mars"}]})  # missing dignity
    assert not ok and "arm invalid" in why


def test_validate_rejects_empty_any_of():
    ok, _ = P.validate_precondition({"type": "any_of", "any_of": []})
    assert not ok


def test_predicate_tokens_recurses_into_arms():
    toks = P.predicate_tokens([{"type": "any_of", "any_of": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}])
    assert "Saturn" in toks and "Mars" in toks and "h7" in toks
