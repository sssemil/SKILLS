# Examples, Checks, and Quality Gates

## Contents

- [Extended examples](#extended-examples)
- [Ambiguity watchlist](#ambiguity-watchlist)
- [Automated checks](#automated-checks)
- [Review queries and failure modes](#review-queries)
- [Quality gates](#quality-gates)
- [Acceptance tests](#acceptance-tests-for-this-skill)
- [Prompt patterns and status wording](#prompt-patterns)
- [Official references and copyright](#official-references)

## Extended examples

### Example 1: Multiple actions

Source:

`Open the panel and disconnect the cable before removing the controller.`

Rewrite:

1. `Open the panel.`
2. `Disconnect the cable.`
3. `Remove the controller.`

Check that the original sequence is correct before release.

### Example 2: Ambiguous pronoun

Source:

`Remove the sensor from the bracket and inspect it for damage.`

Query:

`Does "it" refer to the sensor or the bracket?`

Possible rewrite after confirmation:

1. `Remove the sensor from the bracket.`
2. `Inspect the sensor for damage.`

### Example 3: Hidden condition

Source:

`Replace the filter as necessary.`

Query:

`What condition makes replacement necessary?`

Possible rewrite after source confirmation:

`If the differential pressure is more than 50 kPa, replace the filter.`

### Example 4: Passive description

Source:

`Fuel is supplied to the engine by the pump.`

Rewrite:

`The pump supplies fuel to the engine.`

### Example 5: State, not action

Source:

`The valve is closed during takeoff.`

Keep the state meaning:

`The valve is closed during takeoff.`

Do not rewrite it as `Close the valve during takeoff` unless the source is an
instruction.

### Example 6: Long noun cluster

Source:

`Remove the nose landing gear uplock actuator access panel.`

Possible rewrite:

`Remove the access panel for the uplock actuator of the nose landing gear.`

Verify approved technical-term boundaries. The original cluster can contain a
controlled part name that must remain unchanged.

### Example 7: Software literal

Source:

`Click on the save changes button in order to retain the entered values.`

Rewrite:

`Select SAVE CHANGES.`

`The system keeps the values that you entered.`

Keep `SAVE CHANGES` exact if it is the visible label.

### Example 8: Requirement ambiguity

Source:

`The operator should wear gloves.`

Query:

`Is glove use mandatory or recommended?`

Possible mandatory rewrite:

`Wear the specified gloves.`

Possible recommendation:

`It is recommended that the operator wear gloves.`

The second form still requires strict dictionary and project-style review.

### Example 9: Vague adverb

Source:

`Slowly open the valve.`

Query:

`What opening rate or time limit is required?`

Possible rewrite after confirmation:

`Open the valve at a rate of 10 degrees per second.`

### Example 10: Cause and result

Source:

`A low oil pressure condition will result in illumination of the warning light.`

Rewrite:

`If the oil pressure is low, the warning light comes on.`

Use the specified pressure threshold when source data gives it.

## Ambiguity watchlist

Create a query when these words or patterns affect technical meaning:

- `adequate`
- `appropriate`
- `as applicable`
- `as necessary`
- `as required`
- `carefully`
- `correctly`
- `excessive`
- `high`
- `immediately`
- `low`
- `normal`
- `proper`
- `quickly`
- `regularly`
- `safely`
- `significant`
- `slowly`
- `sufficient`
- `suitable`
- `tight`
- `usually`
- `may`
- `should`
- `can`
- `could`
- `and/or`
- `etc.`
- `respectively`
- `former`
- `latter`
- `this`, `that`, `it`, or `they` without a clear antecedent

Not every occurrence is wrong. The problem is undefined meaning.

## Automated checks

Automated checks can help find:

- sentences above a word limit
- probable passive constructions
- repeated or inconsistent terms
- long noun clusters
- paragraphs above six sentences
- multiple imperative verbs in one sentence
- possible `-ing` forms
- modal verbs
- vague words
- British and American spelling differences
- undefined abbreviations
- inconsistent unit formatting
- values that changed between source and revision

Automated checks cannot reliably determine:

- whether technical meaning is correct
- whether a word is approved for the intended meaning
- whether a word is approved for the intended part of speech
- whether a term is a valid technical noun or technical verb
- whether passive voice is necessary in a description
- whether safety wording is legally controlled
- whether actions are simultaneous or sequential
- whether a source value is correct
- whether two engineering terms are true synonyms

Human technical review remains necessary.

### Checker heuristics

Use these as finding generators, not automatic rewrite rules.

#### Probable passive

Look for a form of `be` followed by a past participle:

```text
am|is|are|was|were|be|been|being + past participle
```

Exclude clear adjectives and fixed states only after context review.

#### Probable nominalization

Examine patterns such as:

```text
adjustment of
inspection of
measurement of
installation of
removal of
replacement of
verification of
```

A direct verb can be clearer, but its word class must be approved.

#### Multiple instructions

Flag a procedure sentence that contains:

- more than one imperative verb
- an imperative on both sides of `and`, `then`, or a semicolon
- separate tool, value, or verification clauses

#### Long noun cluster

Flag four or more consecutive noun-like tokens. Review approved term boundaries
before rewriting.

#### Vague reference

Flag:

- `it`, `this`, `that`, `these`, `those`, `they`
- when two or more nouns occur in the preceding sentence

#### Modal ambiguity

Flag `may`, `should`, `can`, and `could` unless the project has a defined usage
policy.

#### Value integrity

Extract all numbers, units, part numbers, and identifiers from the source and
revision. Compare the sets and their local context.

## Review queries

Use concise queries that an engineer can answer.

Good query:

`Q3: In Step 7, does "it" refer to the cable or the connector?`

Good query:

`Q4: Is 20 kPa a mandatory limit or an example value?`

Good query:

`Q5: Is "reset" an approved technical verb for this product?`

Avoid:

`Please clarify the sentence.`

A useful query names the location, ambiguity, and decision needed.

## Common failure modes

Do not:

- shorten a sentence by deleting a safety condition
- convert two actions into one vague verb
- replace a precise technical noun with a general word
- change step sequence for smoother prose
- use passive voice to avoid naming the responsible person
- use `should` for a mandatory action
- use an unverified synonym to avoid repetition
- mark every word absent from the general dictionary as invalid without checking
  technical-term status
- accept checker output without context review
- rewrite a state as an instruction
- rewrite an instruction as a description
- change an inequality or tolerance
- replace a UI label with a preferred synonym
- expand an abbreviation incorrectly
- merge `fault`, `failure`, `damage`, and `defect`
- change `disconnect` to `remove`
- add a verification result that the source does not specify
- claim compliance because the text is short

## Quality gates

### Gate 1: Technical integrity

Pass only when:

- all source actions are present
- all values match
- all conditions match
- all hazards match
- all protected literals match
- no new technical meaning is present

### Gate 2: Procedure integrity

Pass only when:

- steps are in source order
- each sentence has one instruction
- actions use imperative active voice
- objects and conditions are explicit
- results are separate when they require verification

### Gate 3: Vocabulary integrity

Strict mode passes only when:

- each general word is dictionary-approved for meaning and part of speech
- each technical term is project-approved
- word forms are permitted
- synonyms are controlled

Baseline mode passes only as `dictionary verification required`.

### Gate 4: Structure

Pass only when:

- sentence limits are met or exceptions are reported
- noun clusters are controlled
- pronouns are unambiguous
- paragraphs contain one topic
- complex material uses lists or tables

### Gate 5: Safety

Pass only when:

- classification is unchanged
- hazard, consequence, and prevention are preserved
- mandatory language is not weakened
- safety text is close to the affected action

## Acceptance tests for this skill

Use these tests when modifying or implementing the skill.

### Test A: Passive instruction

Input:

`The access panel must be removed.`

Expected baseline rewrite:

`Remove the access panel.`

### Test B: Two actions

Input:

`Open the valve and record the pressure.`

Expected baseline rewrite:

1. `Open the valve.`
2. `Record the pressure.`

### Test C: Ambiguous pronoun

Input:

`Disconnect the cable from the sensor and inspect it.`

Expected result:

Create a query. Do not select an antecedent.

### Test D: Protected UI label

Input:

`Press the Initiate Synchronization button.`

UI label:

`Initiate Synchronization`

Expected rewrite:

`Select Initiate Synchronization.`

Do not rewrite the literal label to `Start Synchronization`.

### Test E: Numeric integrity

Input:

`Tighten the nut to 25 N·m ± 2 N·m.`

Expected result:

The revision contains exactly `25 N·m ± 2 N·m`.

### Test F: State versus action

Input description:

`The valve is closed when the system is off.`

Expected result:

Do not convert it to an imperative.

### Test G: Vague condition

Input:

`Replace the seal if necessary.`

Expected result:

Create a query for the replacement criterion.

### Test H: Dictionary word class

Input:

`Check the lights.`

Expected baseline result:

Flag `check` as requiring word-class verification. Suggest
`Do a check of the lights.` only when it preserves the intended action.

### Test I: Long noun cluster

Input:

`Remove the engine oil filter housing cover.`

Expected result:

Identify possible approved term boundaries before rewriting. Do not split
blindly.

### Test J: Safety strength

Input:

`WARNING: You must disconnect electrical power before you remove the cover.`

Expected result:

Do not weaken `must`. A procedure-compatible rewrite can be:

`WARNING: Disconnect the electrical power before you remove the cover.`

The warning classification remains unchanged.

## Prompt patterns

### Clean rewrite

`Rewrite the supplied procedure in ASD-STE100 baseline mode. Preserve all technical terms, values, step order, warnings, UI labels, and code literals. Return the revised procedure and open technical queries.`

### Full audit

`Audit the supplied text against ASD-STE100 Issue 9. Use the official dictionary and the attached termbase. Report each finding with the official rule or dictionary reference, severity, and proposed revision.`

### Vocabulary audit

`Create a vocabulary report. Separate official general words, project technical nouns, project technical verbs, protected literals, non-approved words, and words that require dictionary verification.`

### Terminology extraction

`Extract candidate technical nouns and technical verbs. Group synonyms, propose one preferred term for each concept, and identify source conflicts. Do not approve terms without an authoritative source.`

### Safety-preserving rewrite

`Rewrite the safety text in STE-oriented language. Preserve the safety classification, hazard, consequence, mandatory force, values, and prevention actions. Report missing thresholds or ambiguous conditions.`

## Final status wording

Use one of these exact patterns when suitable:

- `ASD-STE100 Issue 9 reviewed against the official standard and the approved project terminology.`
- `STE-oriented rewrite completed with the public-rule baseline. Official dictionary verification is required.`
- `Hybrid STE review completed. Supplied official entries were applied; the remaining vocabulary requires official dictionary verification.`
- `Partial STE review completed. The listed technical queries prevent a reliable compliance decision.`
- `The source conflicts with controlled safety or contractual wording. The controlled wording is unchanged and the conflict is reported.`

Do not use `ASD-STE100 compliant` when the official standard, dictionary,
terminology, and technical review were not all applied.

## Official references

- [ASD Simplified Technical English Maintenance Group](https://www.asd-ste100.org/)
- [About ASD-STE100](https://www.asd-ste100.org/about_STE.html)
- [Official FAQ](https://www.asd-ste100.org/STE_faq.html)
- [Request a free official copy of Issue 9](https://www.asd-ste100.org/STE_downloads.html)
- [Official information about STE tools](https://www.asd-ste100.org/STEsoftware.html)

## Copyright and use note

ASD-STE100 Simplified Technical English is owned by ASD, Brussels, Belgium. The
official Issue 9 standard is available free of charge through the ASD request
page.

This skill contains:

- public facts about the structure and use of STE
- public examples published by ASD
- examples supplied by the user
- original operational guidance and rewrite heuristics
- a non-authoritative baseline vocabulary seed

This skill does not reproduce the complete official dictionary, the
approximately 1,200 official non-approved entries, or all official rule text.
Obtain the official Issue 9 document for formal writing, training, procurement,
or compliance work.
