# Review and Output

## Contents

- [Review workflow](#review-workflow)
- [Finding types and severity](#finding-types-and-severity)
- [Output formats](#output-formats)
- [Practical rewrite patterns](#practical-rewrite-patterns)

## Review workflow

### Pass 1: Source integrity

Identify:

- task purpose
- technical actors
- actions
- objects
- conditions
- limits
- hazards
- results
- source conflicts

Create queries before stylistic rewriting when the source is ambiguous.

### Pass 2: Terminology

- extract repeated nouns and verbs
- identify approved terms
- identify synonyms
- identify abbreviations
- identify literal strings
- identify candidate technical terms
- build or update the termbase

### Pass 3: Vocabulary

- check official dictionary entries in strict mode
- check meaning and part of speech
- replace unnecessary synonyms
- flag unverified words
- check nominalizations and vague words

### Pass 4: Grammar

- convert procedure actions to imperative form
- remove passive instructions
- simplify verb constructions
- check pronouns
- restore missing articles
- split noun clusters
- correct condition order

### Pass 5: Structure

- one instruction per sentence
- one topic per sentence
- sentence-length limits
- one topic per paragraph
- six-sentence paragraph limit
- vertical lists for complex content

### Pass 6: Safety and values

- compare every warning and caution with source data
- compare every number and unit
- verify mandatory language
- verify condition scope

### Pass 7: Back-check

Compare source and revision line by line.

Confirm that:

- all actions remain present
- step sequence is unchanged
- conditions remain attached to the correct actions
- limits and values are unchanged
- hazards and consequences remain present
- no technical claim was added
- terms are consistent
- each procedure sentence has one instruction
- each description sentence has one topic
- unresolved vocabulary is flagged

## Finding types and severity

Use these finding types:

| Type      | Meaning                                                                           |
| --------- | --------------------------------------------------------------------------------- |
| `Error`   | Direct violation of an applicable strict rule or a clear baseline control         |
| `Warning` | Likely nonconformance that needs dictionary, terminology, or context verification |
| `Query`   | Source meaning, obligation, scope, or technical status is incomplete or ambiguous |
| `Note`    | Optional readability improvement that is not necessary for compliance             |

Suggested severity:

| Severity    | Meaning                                                                    |
| ----------- | -------------------------------------------------------------------------- |
| `Critical`  | Safety or technical meaning can change; do not release                     |
| `Major`     | Instruction, condition, terminology, or requirement is ambiguous           |
| `Minor`     | Controlled-language or consistency issue with low immediate technical risk |
| `Editorial` | Formatting or optional readability issue                                   |

## Output formats

### Rewrite

```markdown
### Revised text

[revised content]

### Open queries

- Q1: [technical ambiguity that prevents a reliable rewrite]

### Compliance status

STE-oriented rewrite completed with the public-rule baseline. Official
dictionary verification is required.
```

Do not insert commentary between sentences unless requested.

### Audit

```markdown
| ID      | Location | Source                    | Finding             | Type  | Severity | Proposed revision | Basis                                               |
| ------- | -------- | ------------------------- | ------------------- | ----- | -------- | ----------------- | --------------------------------------------------- |
| STE-001 | Step 4   | The valve must be closed. | Passive instruction | Error | Major    | Close the valve.  | Procedure instructions use imperative active voice. |
```

In strict mode, add official rule or dictionary references in `Basis`.

### Rewrite and audit

Return:

1. revised text
2. findings that materially changed the text
3. open technical queries
4. compliance status

Do not create a finding for every punctuation edit unless the user requests an
exhaustive report.

### Vocabulary report

```markdown
| Token | Lemma | Word class | Context meaning   | Status                           | Suggested action                                         | Reference                    |
| ----- | ----- | ---------- | ----------------- | -------------------------------- | -------------------------------------------------------- | ---------------------------- |
| check | check | verb       | inspect or verify | dictionary verification required | Use `do a check` or approved technical verb after review | Official dictionary required |
```

### Termbase extract

```markdown
| Candidate term     | Type           | Proposed definition                 | Forms found   | Synonyms found | Source locations | Status   |
| ------------------ | -------------- | ----------------------------------- | ------------- | -------------- | ---------------- | -------- |
| brake control unit | technical noun | unit that controls the brake system | singular; BCU | controller     | 2.1, 4.3         | proposed |
```

### Machine-readable report

Use this schema when the user requests JSON or structured output:

```json
{
  "standard": "ASD-STE100",
  "issue": "9",
  "mode": "baseline",
  "text_type": "procedure",
  "status": "dictionary-verification-required",
  "findings": [
    {
      "id": "STE-001",
      "location": "Step 4",
      "category": "passive-instruction",
      "severity": "major",
      "source": "The valve must be closed.",
      "revision": "Close the valve.",
      "basis": "Use imperative active voice in procedures."
    }
  ],
  "queries": []
}
```

## Practical rewrite patterns

Use these patterns only when they preserve the technical meaning.

| Source pattern                                                            | STE-oriented pattern                                             |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `The screws should be replaced.`                                          | `Replace the screws.`                                            |
| `The temperature must be adjusted.`                                       | `Adjust the temperature.`                                        |
| `The valve is to be opened.`                                              | `Open the valve.`                                                |
| `No leaks permitted.`                                                     | `Make sure that there are no leaks.`                             |
| `Grease the fasteners.`                                                   | `Apply grease to the fasteners.`                                 |
| `Make a sandwich with two washers and the spacer.`                        | `Install the spacer between two washers.`                        |
| `For this procedure, make sure that one person is available as a backup.` | `Two persons are necessary for this procedure.`                  |
| `Turn shaft assembly.`                                                    | `Turn the shaft assembly.`                                       |
| `The control unit is used for regulation of the pump speed.`              | `The control unit controls the pump speed.`                      |
| `Prior to removal of the cover, ensure power has been disconnected.`      | `Before you remove the cover, disconnect the electrical power.`  |
| `Upon completion of the test, the results should be recorded.`            | `After the test, record the results.`                            |
| `The operator should carefully remove the seal.`                          | `Remove the seal. Do not damage the seal.`                       |
| `If required, carry out an inspection of the cable.`                      | `If [specified condition], inspect the cable.`                   |
| `The unit may fail to operate properly if the voltage is too low.`        | `If the voltage is less than [limit], the unit can stop.`        |
| `Check that the pin is engaged.`                                          | `Make sure that the pin is engaged.` or `Do a check of the pin.` |

Square brackets identify missing source data. Do not invent the value or
condition.
