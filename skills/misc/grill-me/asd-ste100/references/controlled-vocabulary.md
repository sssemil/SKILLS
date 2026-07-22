# Controlled Vocabulary

## Contents

- [Vocabulary model](#vocabulary-model)
- [Word status and dictionary checks](#word-status-model)
- [Baseline vocabulary](#baseline-vocabulary-seed)
- [Vocabulary decisions](#vocabulary-decision-procedure)
- [Project terminology](#project-terminology)
- [Technical nouns and verbs](#technical-noun-controls)

## Controlled vocabulary

### Vocabulary model

STE separates words into two broad groups:

1. controlled general words from the official dictionary
2. subject-specific technical nouns and technical verbs

A general word is not automatically acceptable because it is common English. In
strict mode, the word must be approved for the applicable meaning and part of
speech.

A word can be approved as a noun but not approved as a verb. A word can be
approved for one meaning and not approved for another meaning.

Use this rule:

> One word for one meaning. One meaning for one word, when the official
> dictionary permits it.

### Word-status model

Assign one of these statuses during review:

| Status                    | Meaning                                                                                        | Action                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `official-approved`       | Confirmed in the applicable official dictionary for this meaning and part of speech            | Use permitted forms only                             |
| `public-confirmed`        | Confirmed by an official public ASD example, but full dictionary details are not available     | Use cautiously and verify in strict mode             |
| `project-approved`        | Approved technical noun or technical verb in the project termbase                              | Use exactly as defined                               |
| `protected-literal`       | UI, code, command, field, label, or controlled wording                                         | Keep unchanged                                       |
| `preferred-candidate`     | Direct baseline word that is likely useful but is not verified against the official dictionary | Verify before a strict claim                         |
| `non-preferred`           | Vague, formal, ambiguous, or inconsistent wording                                              | Rewrite when the meaning is clear                    |
| `deprecated-project-term` | Term is present in old source data but is no longer approved                                   | Replace with the approved term and report the change |
| `query-required`          | Meaning, word class, or technical status is uncertain                                          | Ask or flag; do not guess                            |

### Strict dictionary check

For each non-protected word, check:

1. lemma
2. part of speech
3. approved meaning
4. approved word forms
5. approved example pattern
6. listed non-approved alternatives
7. whether the word is part of an approved technical term

Record a finding when the spelling is approved but the meaning or part of speech
is not.

Example:

- `check` can be publicly confirmed as a noun in the pattern `do a check`.
- Do not assume that `check` is approved as a verb.

### Publicly confirmed micro-dictionary

The entries in this table are based on examples published by ASD or on examples
supplied in the user's source material. They are a small aid, not the official
dictionary.

| Word or pattern | Publicly documented use                                       | Avoid or verify                                                                    | Example                                         |
| --------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------- |
| `about`         | meaning `concerned with`                                      | do not use it to mean `approximately`                                              | `This section is about the fuel system.`        |
| `approximately` | approximate quantity                                          | do not replace it with `about` when `about` means `concerned with`                 | `The procedure takes approximately 10 minutes.` |
| `around`        | approximate quantity or position, subject to dictionary sense | verify the intended sense                                                          | `The temperature is around 20 °C.`              |
| `check`         | noun                                                          | verify before use as a verb                                                        | `Do a check of the connections.`                |
| `start`         | selected direct verb                                          | avoid `begin`, `commence`, `initiate`, or `originate` for the same general meaning | `Start the engine.`                             |
| `accept`        | direct verb                                                   | avoid nominalized `acceptance` when a verb is clearer                              | `Before you accept the unit, do the test.`      |
| `access`        | noun in `get access to`                                       | avoid vague use of `accessible` when an action is clearer                          | `Get access to the connector.`                  |
| `obey`          | direct verb for instructions or requirements                  | avoid `follow` when the meaning is obedience                                       | `Obey the safety instructions.`                 |
| `apply`         | direct verb for a substance                                   | avoid conversion of a material noun into an unverified verb                        | `Apply grease to the fasteners.`                |
| `install`       | direct technical action                                       | avoid figurative descriptions                                                      | `Install the spacer between the washers.`       |
| `adjust`        | direct action                                                 | avoid passive instruction                                                          | `Adjust the temperature.`                       |
| `make sure`     | verification or required state                                | avoid fragmentary prohibition or result wording                                    | `Make sure that there are no leaks.`            |
| `turn`          | direct action                                                 | include a necessary article and object                                             | `Turn the shaft assembly.`                      |
| `necessary`     | requirement statement                                         | avoid vague staffing language                                                      | `Two persons are necessary for this procedure.` |

### Baseline vocabulary seed

This is a **preferred-candidate list**, not the official ASD dictionary. Use it
to select direct words during baseline rewrites. In strict mode, verify the
meaning and part of speech of every word.

#### Common action candidates

`accept`, `add`, `adjust`, `apply`, `attach`, `calculate`, `cause`, `change`,
`clean`, `close`, `compare`, `connect`, `continue`, `decrease`, `disconnect`,
`do`, `drain`, `fill`, `get`, `give`, `increase`, `install`, `keep`, `make`,
`make sure`, `measure`, `move`, `obey`, `open`, `operate`, `put`, `record`,
`remove`, `replace`, `set`, `start`, `stop`, `test`, `turn`, `use`, `wait`

Treat equipment-specific actions such as `calibrate`, `torque`, `crimp`, `ream`,
`solder`, `upload`, or `reboot` as project technical verbs unless the official
dictionary confirms another status.

#### Common relation candidates

`above`, `after`, `against`, `around`, `at`, `before`, `below`, `between`,
`from`, `in`, `into`, `near`, `of`, `on`, `out of`, `through`, `to`, `toward`,
`under`, `with`, `without`

#### Common condition candidates

`after`, `before`, `because`, `if`, `when`, `while`, `until`, `unless`

#### Common quantity candidates

`all`, `each`, `more`, `less`, `many`, `few`, `one`, `two`, `none`, `at least`,
`not more than`, `approximately`

#### Common state candidates

`available`, `clean`, `closed`, `correct`, `damaged`, `dry`, `empty`, `full`,
`hot`, `locked`, `loose`, `necessary`, `open`, `safe`, `tight`, `wet`

#### Common document-function candidates

`example`, `figure`, `instruction`, `list`, `note`, `procedure`, `result`,
`section`, `step`, `table`, `test`, `warning`

#### Candidate connectors

`and`, `but`, `or`, `then`

Use connectors sparingly. If `and` joins two actions, split the sentence unless
the actions form one inseparable operation.

### Vocabulary replacement guide

The left column is **not** an official list of ASD non-approved entries. These
are common sources of ambiguity, unnecessary formality, or translation
difficulty. The preferred rewrite must preserve the source meaning and still
requires official dictionary verification in strict mode.

| Avoid or examine                                        | Prefer or rewrite as                                | Notes                                                              |
| ------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------ |
| `commence`                                              | `start`                                             | Public ASD example supports `start`                                |
| `begin`                                                 | `start`                                             | Use one term consistently                                          |
| `initiate`                                              | `start`                                             | Keep `initiate` only when it is a defined technical verb           |
| `terminate`                                             | `stop` or `end`                                     | Select the word that matches the technical result                  |
| `utilize`                                               | `use`                                               | Do not use a formal synonym without need                           |
| `prior to`                                              | `before`                                            | Put the condition before the action                                |
| `subsequent to`                                         | `after`                                             | Keep sequence explicit                                             |
| `in the event that`                                     | `if`                                                | Use for a condition, not for a known time                          |
| `at such time as`                                       | `when`                                              | Use only when it means time                                        |
| `due to the fact that`                                  | `because`                                           | State cause directly                                               |
| `for the purpose of`                                    | `to`                                                | Remove nominal phrasing                                            |
| `in order to`                                           | `to`                                                | Usually unnecessary                                                |
| `with the exception of`                                 | `except` or rewrite                                 | Verify the official word                                           |
| `in close proximity to`                                 | `near`                                              | State a measurable distance when available                         |
| `a large number of`                                     | `many` or give the number                           | A number is better than a vague quantity                           |
| `a small number of`                                     | `few` or give the number                            | Preserve exact quantity when known                                 |
| `at this point in time`                                 | `now`                                               | In procedures, the sequence often makes `now` unnecessary          |
| `has the capability to`                                 | `can`                                               | Confirm whether the meaning is ability or permission               |
| `is able to`                                            | `can`                                               | Confirm the technical meaning                                      |
| `is required to`                                        | imperative or `must` pattern                        | Do not weaken obligation                                           |
| `is utilized for`                                       | active verb                                         | Example: `The pump supplies fuel.`                                 |
| `is used to control`                                    | `controls`                                          | Use the direct active verb when accurate                           |
| `make an adjustment to`                                 | `adjust`                                            | Avoid nominalization                                               |
| `perform an inspection of`                              | `inspect` or `do an inspection`                     | Technical-verb status can control the choice                       |
| `conduct a test of`                                     | `test` or `do a test`                               | Verify word class                                                  |
| `carry out a check`                                     | `do a check`                                        | `check` is publicly confirmed as a noun                            |
| `make a measurement of`                                 | `measure` or `do a measurement`                     | Verify word class                                                  |
| `provide an indication of`                              | `indicate` or state the shown value                 | Keep defined display terms unchanged                               |
| `give consideration to`                                 | `consider` or state the required check              | `consider` can still be vague                                      |
| `take into consideration`                               | state the exact condition                           | Vague instruction                                                  |
| `as applicable`                                         | state the condition                                 | Do not make the reader decide without criteria                     |
| `as appropriate`                                        | state the condition                                 | Vague responsibility                                               |
| `as necessary`                                          | state the trigger or limit                          | Keep only when controlled source wording requires it               |
| `as soon as possible`                                   | give a time limit                                   | Safety text needs a measurable limit when source data provides one |
| `in a timely manner`                                    | give a time limit                                   | Vague                                                              |
| `quickly`                                               | give a speed or time limit                          | Do not invent a limit                                              |
| `carefully`                                             | state the hazard or control                         | Example: `Do not damage the seal.`                                 |
| `properly`                                              | state the correct end condition                     | Example: `Make sure that the pin is fully engaged.`                |
| `sufficiently`                                          | give the required limit                             | Example: temperature, pressure, distance, or time                  |
| `normally`                                              | state the normal condition                          | The word can hide exceptions                                       |
| `typically`                                             | state the actual condition or frequency             | Keep only when technically necessary                               |
| `generally`                                             | state the scope                                     | Vague                                                              |
| `various`                                               | list the items or use a defined group term          | Avoid undefined sets                                               |
| `etc.`                                                  | complete the list or name the category              | Do not make the reader infer missing items                         |
| `and/or`                                                | use `and`, `or`, or write alternatives              | Logical scope can be unclear                                       |
| `respectively`                                          | write separate statements                           | Prevent mapping errors                                             |
| `the former` / `the latter`                             | repeat the technical noun                           | Avoid reference ambiguity                                          |
| `this` alone                                            | `this valve`, `this condition`, or repeat the noun  | Give a clear antecedent                                            |
| `it` with two possible antecedents                      | repeat the technical noun                           | Do not require pronoun resolution                                  |
| `they` for mixed singular/plural objects                | repeat the group name                               | Prevent number ambiguity                                           |
| `may`                                                   | clarify possibility or permission                   | Do not guess which meaning applies                                 |
| `should`                                                | clarify recommendation or requirement               | Mandatory actions normally need imperative wording                 |
| `could`                                                 | clarify ability, possibility, or conditional result | Ambiguous modal                                                    |
| `will` in a procedure step                              | use imperative for the action                       | Keep `will` for a real future statement when permitted             |
| `no leaks permitted`                                    | `Make sure that there are no leaks.`                | Complete sentence and explicit verification                        |
| `the valve is to be closed`                             | `Close the valve.`                                  | Direct procedure command                                           |
| `the screws should be replaced`                         | `Replace the screws.`                               | Confirm that replacement is mandatory                              |
| `grease the fasteners`                                  | `Apply grease to the fasteners.`                    | Avoid unverified noun-to-verb conversion                           |
| `make a sandwich with`                                  | `install ... between ...`                           | Remove figurative language                                         |
| `rotate` / `turn` used interchangeably                  | select one approved term                            | Keep defined technical distinctions                                |
| `shut` / `close` used interchangeably                   | select one approved term                            | Do not merge terms if the product distinguishes them               |
| `remove` / `disconnect` used interchangeably            | keep separate meanings                              | One is physical removal; one is connection state                   |
| `fault`, `failure`, `defect`, `damage` used as synonyms | define each term                                    | These often have different engineering meanings                    |

### Vocabulary decision procedure

For each questionable word:

1. Is it protected literal text?
2. Is it an approved project technical noun or technical verb?
3. Is it in the official dictionary for this meaning and word class?
4. Is the same meaning already expressed with another approved word in the
   document?
5. Does the word have more than one likely interpretation?
6. Can a direct sentence remove the need for the word?
7. Would replacement change a defined engineering distinction?

If the answer is uncertain, flag the word. Do not guess.

### Sense ledger

For long documents, keep a sense ledger for words that commonly change meaning.

Example:

| Word    | Allowed document meaning           | Word class                           | Disallowed or separate meanings         |
| ------- | ---------------------------------- | ------------------------------------ | --------------------------------------- |
| `set`   | put a control at a specified value | verb                                 | group, collection, harden, become fixed |
| `right` | direction opposite left            | noun/adjective as approved by source | correct, entitlement                    |
| `light` | illumination device                | technical noun                       | low weight, ignite                      |
| `open`  | move to the open position          | verb                                 | available, unresolved, not enclosed     |

Use separate terms when the meanings are different.

### Project terminology

A project termbase is necessary when the document contains more than a small
number of subject-specific terms.

Recommended fields:

| Field                 | Purpose                                                           |
| --------------------- | ----------------------------------------------------------------- |
| `term`                | approved written form                                             |
| `type`                | technical noun, technical verb, literal, abbreviation, symbol     |
| `definition`          | one technical meaning                                             |
| `approved forms`      | singular, plural, verb forms, hyphenation, capitalization         |
| `prohibited synonyms` | terms that writers must not use for this concept                  |
| `source`              | drawing, specification, database, UI, engineering decision        |
| `subject field`       | system, component, material, tool, software, process, measurement |
| `example`             | approved sentence                                                 |
| `status`              | approved, proposed, deprecated, conflict, query                   |
| `owner`               | engineering or terminology authority                              |
| `revision`            | issue or approval date                                            |

Example:

| Term             | Type              | Definition                                                      | Approved forms                 | Prohibited synonyms                                              | Source             | Status    |
| ---------------- | ----------------- | --------------------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------- | ------------------ | --------- |
| `hydraulic pump` | technical noun    | pump that supplies the hydraulic system                         | singular and plural            | `hydraulic power unit` unless source defines it as the same item | drawing 27-10-00   | approved  |
| `calibrate`      | technical verb    | compare with a reference and set within the specified tolerance | base, imperative, simple forms | `tune`, `zero` unless separately defined                         | process spec PS-14 | approved  |
| `SAVE`           | protected literal | UI button label                                                 | exact uppercase form           | `Save`, `store`                                                  | software build 8.2 | protected |

### Technical-noun controls

- Use the exact approved term.
- Do not alternate between the full term and an informal synonym.
- Define an abbreviation at first use unless the governing specification says
  otherwise.
- Do not create a term by joining several nouns without checking the
  noun-cluster limit.
- Use a prepositional phrase when a long cluster is difficult to parse.
- Keep singular and plural forms consistent with the termbase.
- Do not replace a precise term with `unit`, `device`, `part`, or `item` unless
  the reference is unambiguous.
- Do not use a trade name as a generic term unless the project approves it.

### Technical-verb controls

- Use a technical verb only for its defined process.
- Record the permitted forms.
- Do not use the verb figuratively.
- Do not create a technical verb only to avoid an official vocabulary
  restriction.
- Keep process distinctions. `Remove`, `disconnect`, `release`, `loosen`, and
  `open` are not interchangeable.
- When a noun and verb share a spelling, verify the approved word class.
