# Safety, Formatting, and Software

## Contents

- [Safety text](#safety-text)
- [Numbers, values, and units](#numbers-values-and-units)
- [Abbreviations and symbols](#abbreviations-acronyms-and-symbols)
- [Punctuation, lists, and tables](#punctuation-and-formatting)
- [Software, UI, and API documentation](#software-ui-and-api-documentation)
- [Translation readiness](#translation-readiness)

## Safety text

### Safety hierarchy

Preserve the user's classification system exactly:

- danger
- warning
- caution
- notice
- note

Different standards define these labels differently. Do not reclassify them.

### Safety-message content

A complete safety message can contain:

1. the hazard or unsafe condition
2. the possible consequence
3. the prevention action
4. the scope or affected task

Do not add a consequence that is not present in the approved source.

### Safety wording

- Use direct commands for prevention actions.
- Use `Do not` for prohibited actions.
- Put a controlling condition before the action.
- Keep the hazard close to the related step.
- Preserve mandatory capitalized wording when controlled.
- Do not soften `must`, `do not`, or an equivalent requirement.
- Do not add probability words such as `possibly`, `usually`, or `normally`
  unless source data supports them.

Example:

`WARNING: Make sure that the electrical power is off before you disconnect the cable. Electrical power can cause injury.`

The exact order of hazard, consequence, and prevention can be controlled by the
governing safety standard. Follow that standard.

### Safety ambiguity queries

Create a query when the source contains:

- `carefully`
- `immediately` without a time limit
- `safe distance` without a value
- `high pressure` without a threshold
- `hot` without a temperature when contact limits matter
- `adequate ventilation` without criteria
- `approved protective equipment` without a referenced list

Do not invent limits.

## Numbers, values, and units

### Numeric integrity

Copy all technical values exactly unless the user requests a conversion.

Check:

- decimal separator
- thousands separator
- positive and negative signs
- ranges
- tolerances
- inequality signs
- unit symbols
- exponent notation
- significant digits
- time format
- date format

Do not round values during a language rewrite.

### Ranges

Make the relationship clear:

- `10 mm to 12 mm`
- `more than 10 mm`
- `not more than 12 mm`
- `10 mm ± 0.2 mm`

Do not replace a tolerance with a vague adjective.

### Units

- Keep the approved project unit system.
- Put a space between a number and a unit when the governing style requires it.
- Do not pluralize unit symbols.
- Keep protected symbols unchanged.
- Define uncommon abbreviations when required.

### Numbers in procedures

Use numerals for values, counts, step references, and identifiers when the
project style permits them.

Avoid a mixture such as `two (2)` unless controlled wording requires it.

## Abbreviations, acronyms, and symbols

- Use only approved abbreviations.
- Define an abbreviation at first use unless it is universally accepted by the
  governing specification.
- Do not create multiple abbreviations for one term.
- Do not use the same abbreviation for two meanings in one document.
- Keep product labels and standard symbols unchanged.
- Prefer the full term when the abbreviation occurs only once.
- Do not put an abbreviation in a title unless readers know it or the
  publication rule permits it.

Termbase example:

| Full term          | Abbreviation | First-use form             | Status   |
| ------------------ | ------------ | -------------------------- | -------- |
| brake control unit | BCU          | `brake control unit (BCU)` | approved |

## Punctuation and formatting

- Use a period at the end of a complete instruction.
- Use commas to separate a leading condition from the main clause when needed.
- Do not use semicolons to join instructions.
- Avoid parentheses for information that is necessary to do the task.
- Put optional or secondary information in a note only when the publication
  rules permit it.
- Use a colon before a vertical list.
- Keep list items grammatically parallel.
- Do not use a slash to mean `and`, `or`, `per`, or an undefined alternative.
- Use quotation marks only for literals, messages, or defined quoted text.
- Avoid exclamation marks in technical instructions.

## Lists and tables

Use a vertical list when a sentence contains:

- more than two conditions
- multiple alternatives
- a long series of items
- values that readers must compare
- repeated step structures

List lead-in:

`Do these steps:`

List items:

1. `Open the access panel.`
2. `Disconnect connector P2.`
3. `Remove the controller.`

Do not put multiple instructions in one bullet.

For tables:

- make each column heading explicit
- include units in the heading or each value, as required
- keep grammar parallel in cells
- do not use blank cells when blank can mean unknown, not applicable, or zero
- define symbols and abbreviations
- preserve row-to-column relationships

## Software, UI, and API documentation

STE was developed for technical documentation and can be adapted to software
instructions when project terminology is controlled.

### UI literals

Treat visible labels as protected literals:

- buttons
- menus
- tabs
- dialogs
- fields
- messages
- keyboard keys

Example:

`Select Settings > Network.`

`Click SAVE.`

`SAVE` can remain uppercase if the UI uses uppercase.

Treat `select`, `click`, `tap`, `swipe`, `upload`, and similar actions as
project technical verbs unless their official status is confirmed.

### Software procedures

- Put one user action in each step.
- Separate an action from its result.
- Identify the screen or panel when necessary.
- Keep menu paths exact.
- Do not rewrite command syntax.
- State required permissions and system state before the action.
- Identify irreversible actions in safety or caution text as governed by the
  product standard.

Example:

1. `Open the Settings page.`
2. `Select Network.`
3. `Set Mode to Manual.`
4. `Select SAVE.`
5. `Make sure that the status is Connected.`

### API and command-line text

Protect:

- endpoints
- methods
- headers
- parameter names
- JSON keys
- environment variables
- commands
- flags
- code blocks
- error messages

Write the surrounding explanation in STE-oriented prose.

Example:

`Send a POST request to /v1/jobs.`

`Set the timeout parameter to 30.`

Do not change `/v1/jobs`, `POST`, `timeout`, or `30`.

## Translation readiness

STE-oriented source text should reduce avoidable variation.

Use:

- one term for one concept
- one sentence for one instruction
- explicit subjects and objects
- explicit conditions
- repeated technical nouns when pronouns are ambiguous
- consistent units and number formats
- parallel list structures

Avoid:

- idioms
- metaphors
- jokes
- culture-specific references
- phrasal ambiguity
- omitted subjects
- unexplained abbreviations
- synonym variation for style
- figurative technical verbs

Do not rewrite protected product names or interface strings only to improve
translation.
