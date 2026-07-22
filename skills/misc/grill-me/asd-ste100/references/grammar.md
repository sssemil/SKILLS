# Grammar and Sentence Controls

## Contents

- [Complete sentences and active voice](#complete-sentences)
- [Procedure and description sentences](#one-instruction-per-sentence)
- [Sentence length and word count](#sentence-length)
- [Verb forms and modals](#verb-forms)
- [Conditions, causes, and references](#conditions)
- [Articles and noun clusters](#articles)
- [Coordination, negation, and comparison](#coordination)

## Grammar and sentence controls

### Complete sentences

Do not omit a necessary subject, verb, object, article, or auxiliary only to
make a sentence shorter.

Procedural imperatives have an understood subject (`you`), but they still need a
clear verb and object.

Avoid fragments such as:

- `No leaks permitted.`
- `When necessary.`
- `After installation.`
- `If damaged.`

Rewrite with the necessary condition or action:

- `Make sure that there are no leaks.`
- `If the seal is damaged, replace it.`

### Active voice

Use active voice for procedures.

Preferred:

- `Remove the cover.`
- `The pump supplies fuel to the engine.`

Avoid in procedures:

- `The cover must be removed.`
- `Fuel is supplied to the engine by the pump.`

In descriptions, passive voice can be necessary when the agent is unknown,
irrelevant, or intentionally omitted by the applicable official rule. Do not use
passive voice only to avoid naming the responsible person.

#### Passive-voice test

A probable passive construction contains:

- a form of `be`
- a past participle
- an object that receives the action

Examples:

- `The valve is closed by the actuator.`
- `The data were recorded.`

Not every `be + participle` phrase is passive. It can describe a state:

- `The valve is closed.`
- `The cable is damaged.`

Use context. In a procedure, convert the required action to an imperative. In a
description, decide whether the state or the action is intended.

### Imperative procedures

Write direct commands:

- `Open the access panel.`
- `Measure the voltage.`
- `Record the result.`

Do not start a step with:

- `You should ...`
- `The operator shall ...`
- `It is necessary to ...`
- `The component is to be ...`

Keep controlled contractual wording unchanged when it must remain exact. Report
the style conflict separately.

### One instruction per sentence

A procedure sentence must contain one instruction.

Split actions when they can be:

- done at different times
- completed by different persons
- verified separately
- failed independently
- associated with different hazards
- associated with different tools or limits

Non-STE:

`Open the valve and record the pressure.`

Preferred:

1. `Open the valve.`
2. `Record the pressure.`

Keep actions together only when they are one inseparable physical operation and
the official rules permit the construction.

### One topic per sentence

A descriptive sentence must have one main topic.

Non-STE:

`The pump supplies fuel, the controller monitors pressure, and the warning light comes on when the pressure is low.`

Preferred:

`The pump supplies fuel.`

`The controller monitors the fuel pressure.`

`The warning light comes on when the fuel pressure is low.`

### Sentence length

Baseline limits:

- procedure sentence: 20 words or fewer
- descriptive sentence: 25 words or fewer

Use the official counting method and exceptions in strict mode.

Do not remove necessary technical information only to meet a word limit.

When a sentence is too long:

1. remove redundant language
2. move a condition before the action
3. split independent actions
4. split separate topics
5. replace a nominal phrase with a direct verb
6. use a vertical list
7. keep the sentence intact only if splitting changes the technical meaning,
   then report the exception

### Baseline word count

In baseline mode:

- exclude step numbers and safety labels
- count whitespace-separated tokens
- count a hyphenated compound as one token
- count a number and its unit as separate tokens unless the project specifies
  another method
- count a protected multiword UI label as its visible words, but do not rewrite
  it
- do not count punctuation as a word

When exact compliance matters, use the applicable official method.

### Verb forms

Prefer simple verb constructions.

Public descriptions of STE commonly identify these useful forms:

- infinitive
- imperative
- simple present
- simple past
- simple future when necessary
- past participle as an adjective when permitted

Avoid complex auxiliary chains when a simple form gives the same meaning.

Examine:

- `has been operating`
- `will have been installed`
- `should have been checked`
- `is going to be removed`

Possible rewrites:

- `The pump operates.`
- `Install the unit before 10:00.`
- `Do a check of the unit.`
- `Remove the unit.`

Do not change time relationships. If the source depends on perfect aspect,
identify the exact sequence and write separate statements.

### `-ing` forms

Examine each `-ing` form.

It can be:

- a technical noun: `bonding`, `wiring`
- part of a technical noun: `landing gear`, `retaining ring`
- a modifier in an approved term
- a progressive verb form that should usually be rewritten

Non-STE:

`The pump is supplying fuel to the engine.`

Preferred description:

`The pump supplies fuel to the engine.`

Do not change approved technical terms that contain `-ing`.

### Modal verbs

Modal verbs frequently hide the type of requirement.

| Modal    | Possible meanings                                 | Required action                                                       |
| -------- | ------------------------------------------------- | --------------------------------------------------------------------- |
| `must`   | mandatory requirement                             | preserve strength; use a direct command in a procedure when permitted |
| `should` | recommendation, expectation, weak obligation      | determine the source intent                                           |
| `may`    | permission or possibility                         | determine which meaning applies                                       |
| `can`    | ability, permission, or possibility               | determine which meaning applies                                       |
| `could`  | ability, possibility, or conditional result       | rewrite only after the meaning is clear                               |
| `will`   | future fact, prediction, or disguised instruction | use imperative for an instruction                                     |

Do not convert `may` to `must` or `should` to an imperative without authority.

### Conditions

Put a condition before the action when the reader must know the condition first.

Preferred:

`If the seal is damaged, replace the seal.`

Avoid:

`Replace the seal if it is damaged.`

The second form can be acceptable in ordinary English, but condition-first order
is safer when a reader might begin the action before reading the condition.

Use:

- `if` for a condition
- `when` for a known time or event
- `before` and `after` for sequence
- `while` only when actions or states occur at the same time
- `until` for an end condition

Do not use `when` and `if` as interchangeable words.

### Cause and result

State cause and result directly.

Preferred:

`If the pressure decreases below 200 kPa, the warning light comes on.`

Avoid:

`A pressure reduction may result in illumination of the warning light.`

Do not invent certainty. Preserve `can`, `may`, threshold values, and
conditional scope when they are technically meaningful.

### Pronouns and reference words

Use a pronoun only when the antecedent is clear and near.

Repeat the technical noun when:

- two or more possible antecedents occur
- the pronoun crosses a paragraph boundary
- singular and plural references are mixed
- the antecedent is a long noun phrase
- mistranslation is likely

Non-STE:

`Remove the controller from the bracket and inspect it.`

Ambiguity: inspect the controller or the bracket?

Preferred:

`Remove the controller from the bracket.`

`Inspect the controller.`

Do not use `this`, `that`, `these`, or `those` alone when a noun can identify
the reference.

### Articles

Do not omit articles to shorten a sentence.

Preferred:

`Turn the shaft assembly.`

Avoid:

`Turn shaft assembly.`

Use the article that matches the reference:

- `a` or `an` for an item introduced as one of a class
- `the` for a specific or previously identified item

Project naming conventions can control article use in headings, tables, labels,
and parts lists.

### Noun clusters

Do not use more than three nouns in an uninterrupted cluster in baseline mode.

Difficult:

`overhead panel battery section cover`

Clearer:

`cover of the battery section on the overhead panel`

Do not split an approved technical term incorrectly. First identify the term
boundaries.

Use these methods:

- insert `of`, `for`, `on`, `in`, or another accurate relation
- define the main noun first
- separate location from function
- separate a part name from a document name
- use a table when a repeated hierarchy is long

### Coordination

Examine every `and` and `or`.

Questions:

- Does `and` join two instructions?
- Does `or` present exclusive or inclusive alternatives?
- Does a modifier apply to all items or only the nearest item?
- Can each item be verified separately?

Avoid `and/or`. Write the logic explicitly.

Example:

- `Replace the seal if it is cut or if it is permanently deformed.`
- `Install the red connector, the blue connector, or both connectors, as specified in Table 4.`

### Negation

Put `not` close to the word or action that it controls.

Preferred:

`Do not open the valve.`

Potentially ambiguous:

`Do not fully open the valve.`

The second sentence can mean:

- do not open it at all, or
- open it, but not fully

Write the intended limit:

- `Keep the valve closed.`
- `Open the valve to 50 percent.`

Avoid double negatives.

### Comparison

State the comparison basis and limit.

Avoid:

- `higher`
- `lower`
- `better`
- `sufficient`
- `too hot`

Preferred:

- `higher than 250 kPa`
- `lower than the value in Table 3`
- `within the specified tolerance`
- `more than 60 °C`

Do not invent the reference value.

### Paragraphs

- Put one topic in each paragraph.
- Keep a paragraph at six sentences or fewer in baseline mode.
- Put a procedure sequence in numbered steps, not in a prose paragraph.
- Do not bury a warning in a descriptive paragraph.
- Use a short lead-in before a list.
