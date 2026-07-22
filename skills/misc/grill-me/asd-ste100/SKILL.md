---
name: asd-ste100
description:
  Write, rewrite, and audit technical procedures and descriptions with
  ASD-STE100 Simplified Technical English. Use for maintenance, operating,
  installation, inspection, troubleshooting, safety, software, API,
  specification, terminology, controlled-language, translation-source,
  vocabulary, and STE compliance-review tasks. Supports baseline, hybrid, and
  strict review modes; formal compliance requires the applicable official
  ASD-STE100 issue, official dictionary, project termbase, publication rules,
  and technical review.
---

# ASD-STE100 Simplified Technical English

Write clear technical text without changing its technical meaning. Apply
ASD-STE100 controls to procedures, descriptions, safety text, terminology,
software instructions, and audit reports.

Use **Issue 9, January 2025** unless the user specifies another issue. Issue 9
contains 53 writing rules in 9 sections and approximately 900 approved general
words.

Treat this skill as an operational aid. Do not claim formal compliance from the
public baseline alone.

## Select the review mode

Use one mode for the complete task.

### Strict mode

Use strict mode only when all these inputs are available:

- the applicable official ASD-STE100 issue
- the official controlled dictionary for that issue
- the approved project or company termbase
- the governing publication and safety rules
- authoritative technical source data

Check each general word for its approved meaning, part of speech, and permitted
forms. Check each technical noun and technical verb against approved
terminology. Report unresolved cases. Claim formal compliance only after all
checks and a technical review are complete.

### Hybrid mode

Use hybrid mode when the user supplies some official rules or controlled
terminology, but not the complete authority set.

Apply supplied official data exactly. Apply the public baseline to uncovered
areas. Distinguish confirmed findings from provisional findings. Identify the
material necessary for a complete review.

### Baseline mode

Use baseline mode by default.

Apply the public controls in this skill. Preserve supplied project terminology.
Flag words that require official dictionary verification. Do not state that the
result is formally compliant.

## Apply source authority

Apply sources in this order:

1. the official ASD-STE100 issue specified by the user
2. contractual publication specifications and customer rules
3. controlled safety wording and regulatory text
4. approved company or project terminology
5. engineering source data, drawings, schematics, and parts lists
6. product UI strings, code literals, commands, and database labels
7. this skill's public baseline

Preserve the higher-authority source when sources conflict. Report the conflict.
Never let a language rewrite change a technical requirement.

## Load only the necessary references

Read each selected reference completely before applying it. All references are
directly linked from this file.

| Task                                                                                        | Required reference                                                           |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Vocabulary review, terminology work, strict review, or word-class decisions                 | [Controlled vocabulary](references/controlled-vocabulary.md)                 |
| Sentence rewriting, grammar review, or ambiguity reduction                                  | [Grammar and sentence controls](references/grammar.md)                       |
| Maintenance procedures, operating instructions, or system descriptions                      | [Procedures and descriptions](references/procedures-and-descriptions.md)     |
| Warnings, values, units, tables, software, UI, API, or translation-source text              | [Safety, formatting, and software](references/safety-format-and-software.md) |
| Audit reports, findings, JSON output, termbases, or rewrite reports                         | [Review and output](references/review-and-output.md)                         |
| Difficult examples, automated checks, quality gates, acceptance tests, or skill maintenance | [Examples, checks, and quality gates](references/examples-and-quality.md)    |

For a simple rewrite, read the grammar reference and the
procedure-or-description reference. Add other references only when the source
contains their subject matter.

For targeted searches in the references, use patterns such as:

```text
rg -n "strict mode|technical noun|technical verb|word class" references/
rg -n "warning|numeric integrity|UI literal|API" references/
rg -n "output formats|machine-readable|quality gates" references/
```

## Get the necessary inputs

Use the available inputs. Do not stop only because optional inputs are absent.

Identify:

- source text
- text type: `procedure`, `description`, `safety`, or `mixed`
- requested review mode and ASD-STE100 issue
- approved terminology or termbase
- product and part names
- source references and drawing identifiers
- protected software labels, commands, and data fields
- safety classification and mandatory wording
- customer style rules
- requested output format

If the official dictionary or termbase is absent, use baseline mode and state
what is missing.

## Protect fixed content

Before rewriting, mark these items as protected:

- part, model, and serial numbers
- software commands, source code, API paths, parameters, and data fields
- UI labels, messages, menu paths, and keyboard keys
- file names and extensions
- values, tolerances, quantities, ranges, and units
- drawing nomenclature and approved product terms
- legally controlled text and contractual safety wording

Keep the spelling, capitalization, syntax, and values of protected content
unchanged.

## Follow the core workflow

1. Classify each block as procedural, descriptive, safety, tabular, or protected
   literal text.
2. Protect fixed content before making language changes.
3. Identify the technical actors, actions, objects, conditions, limits, hazards,
   and results.
4. Extract repeated terminology and resolve synonyms against authoritative
   sources.
5. Control vocabulary, meaning, word class, and word forms for the selected
   mode.
6. Rewrite grammar and sentence structure without changing task logic.
7. Separate independent actions and topics.
8. Verify every value, condition, warning, and protected literal against the
   source.
9. Compare the revision with the source line by line.
10. Return the requested output, open technical queries, and compliance status.

## Apply non-negotiable controls

- Preserve technical meaning, task order, and dependencies.
- Preserve every limit, value, tolerance, quantity, unit, and range.
- Preserve hazards, consequences, prevention actions, and mandatory force.
- Preserve part numbers, commands, labels, file names, and data fields.
- Do not invent steps, tools, materials, causes, results, limits, or safety
  conditions.
- Do not delete information necessary for safe and correct work.
- Do not weaken mandatory language or change a safety classification.
- Do not resolve technical ambiguity by assumption.
- Do not replace an approved technical term only because it is absent from the
  general dictionary.
- Do not classify an ordinary word as a technical term to bypass a vocabulary
  rule.
- Do not claim formal compliance after partial or automated checks.

## Apply the essential writing controls

### Procedures

- Use imperative active voice.
- Put one instruction in each sentence.
- Put a condition before the action when the reader must know it first.
- Keep steps in the source order.
- Separate an action from a verification action.
- State simultaneous actions explicitly.
- Give a count or end condition for repeated actions when the source provides
  it.
- Use 20 words or fewer in a baseline procedure sentence unless technical
  integrity requires an exception.

### Descriptions

- Put one main topic in each sentence.
- Prefer direct active constructions.
- Distinguish a state from an action.
- Name the actor when the source identifies it.
- Repeat a technical noun when a pronoun can be ambiguous.
- Use 25 words or fewer in a baseline descriptive sentence unless technical
  integrity requires an exception.

### Vocabulary and terminology

- Use one term for one concept.
- Verify a general word's meaning and part of speech in strict mode.
- Use technical nouns and technical verbs only for their approved meanings.
- Keep engineering distinctions such as `remove`, `disconnect`, `release`,
  `loosen`, and `open`.
- Query vague or ambiguous words when their interpretation affects technical
  meaning.

### Safety and values

- Keep the supplied danger, warning, caution, notice, or note classification.
- Keep the hazard close to the affected action.
- Use direct commands for prevention actions.
- Put `not` close to the action that it controls.
- Copy technical values exactly. Do not round or normalize them during a
  language rewrite.
- Create a query when a safety limit or criterion is missing. Do not invent it.

## Create useful technical queries

Create a query when meaning, obligation, scope, terminology, or technical status
is unclear.

Name the location, ambiguity, and decision required.

Preferred:

`Q3: In Step 7, does "it" refer to the cable or the connector?`

Avoid:

`Please clarify the sentence.`

Do not guess when a query can prevent a technical or safety error.

## Return the requested output

Support these output types:

- `rewrite`
- `audit`
- `rewrite-and-audit`
- `vocabulary-report`
- `termbase-extract`
- `redline-summary`
- `strict-compliance-report`
- machine-readable JSON

For an unspecified output, return:

1. revised text
2. findings that materially changed the text
3. open technical queries
4. compliance status

Do not report every punctuation edit unless the user requests an exhaustive
audit.

## State compliance accurately

Use one suitable status:

- `ASD-STE100 Issue 9 reviewed against the official standard and the approved project terminology.`
- `STE-oriented rewrite completed with the public-rule baseline. Official dictionary verification is required.`
- `Hybrid STE review completed. Supplied official entries were applied; the remaining vocabulary requires official dictionary verification.`
- `Partial STE review completed. The listed technical queries prevent a reliable compliance decision.`
- `The source conflicts with controlled safety or contractual wording. The controlled wording is unchanged and the conflict is reported.`

Do not use `ASD-STE100 compliant` unless the official standard, dictionary,
terminology, publication rules, and technical review were all applied.

## Complete the quality gate

Before delivery, confirm that:

- all source actions remain present and in order
- every condition controls the correct action
- all values, units, identifiers, and literals match the source
- hazards and mandatory language are unchanged
- no technical claim was added
- terms are consistent
- each procedure sentence contains one instruction
- each descriptive sentence contains one topic
- unresolved vocabulary and ambiguity are reported
- the compliance statement matches the evidence
