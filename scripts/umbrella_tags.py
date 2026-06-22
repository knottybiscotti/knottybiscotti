"""
umbrella_tags.py — Derive aggregating "umbrella" tags from specific tags.

Single home for the rule "an orientation/identity tag implies the queer
umbrella". Imported by the pre-build sanitiser (so the umbrella is collated
as a first-class taxonomy term) and, if queer ever earns an AO3 slot, by the
CSV generator — so the logic is written once, not duplicated.

Pure: takes an iterable of tags, returns a new set with any derived umbrella
tags added. It does not mutate its input, sort, or serialize — the caller
owns ordering and output format.

DESIGN NOTES — the deliberate *exclusions* are the load-bearing decisions,
so they are documented here rather than left as silent absences:

  * m_f is NOT a trigger. A mixed-gender pairing is not queer by itself.
    An m_f story still earns the umbrella when it ALSO carries an identity
    marker (e.g. trans_character) — that falls out of the set union for
    free, with no "m_f unless..." special-casing.

  * gender_neutral is NOT a trigger. In this vault it is a *craft* tag for
    second-person reader-insert POV, not an identity marker — it withholds
    the protagonist's gender rather than declaring one, leaving the pairing
    orientation reader-determined. (Contrast non_binary/agender, which
    declare an identity and therefore DO trigger.) If gender_neutral is ever
    repurposed to mean an actually-ungendered character identity, revisit
    this — the call would flip toward inclusion.
"""

# Each rule: a story carrying ANY trigger tag gains the umbrella tag.
# Structured as a tuple of rules so a future umbrella is one more entry.
_UMBRELLA_RULES = (
    (
        {
            # Same-sex by construction:
            "sapphic", "gay", "f_f", "m_m", "f_f_m",
            # Identity markers (queer regardless of pairing):
            "trans_character", "non_binary", "agender",
        },
        "queer",
    ),
)


def derive_umbrella_tags(tags):
    """Return a set: the input tags plus any umbrella tags they imply."""
    result = set(tags)
    for triggers, umbrella in _UMBRELLA_RULES:
        if result & triggers:
            result.add(umbrella)
    return result
