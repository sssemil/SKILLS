# Procedures and Descriptions

## Contents

- [Procedure-step model](#procedure-step-model)
- [Step order and preconditions](#step-order)
- [Results and simultaneous actions](#results-and-verification)
- [Tools and headings](#tools-and-materials)
- [Description model](#description-model)
- [Functions, locations, states, and sequences](#function-descriptions)

## Procedure controls

### Procedure-step model

A complete procedure step can contain:

1. a condition
2. one action
3. an object
4. a location
5. a value or limit
6. a necessary method
7. an expected result

Not every step needs all seven elements. Add only what the source data supports.

Template:

`If [condition], [imperative verb] [object] [location] [to value] [with method].`

Example:

`If the pressure is less than 200 kPa, adjust the regulator to 250 kPa.`

### Step order

Arrange steps in the order of performance.

Do not reorder steps only to improve style.

Keep prerequisites before dependent actions:

1. isolate energy
2. verify the safe state
3. remove access items
4. do the work
5. restore the configuration
6. do a functional test

This sequence is only a pattern. The source procedure controls the actual order.

### Preconditions

A precondition can apply to:

- one step
- a group of steps
- the complete procedure

Make the scope explicit.

Avoid a floating condition such as:

`With the power off:`

when it is not clear how many steps it controls.

Use a heading or a complete statement:

`Make sure that the electrical power is off before you do Steps 4 through 8.`

### Results and verification

Add a result only when the source specifies one.

Use a separate sentence when verification is an action:

1. `Open the valve.`
2. `Make sure that the pressure increases.`

Do not assume that the result occurs simply because the action is complete.

### Simultaneous actions

When two persons or two hands must act at the same time, state this explicitly.

Example:

`While one person holds the bracket, the second person removes the bolt.`

Do not split simultaneous actions in a way that removes the timing relationship.

### Repeated actions

State the count or end condition.

Preferred:

- `Turn the knob three times.`
- `Flush the line until the fluid is clean.`

Avoid:

- `Turn the knob several times.`
- `Flush the line thoroughly.`

Do not invent a count or end condition.

### Optional actions

State why an action is optional and who decides.

Avoid:

`If necessary, replace the filter.`

Preferred when source data supports it:

`If the differential pressure is more than 50 kPa, replace the filter.`

### Tools and materials

Identify a tool or material when the source requires it.

Preferred:

`Apply sealant ABC-12 to the threads with a clean brush.`

Do not add a tool because it seems useful.

### Procedure headings

Use task-oriented headings:

- `Remove the Pump`
- `Install the Access Panel`
- `Test the Brake Control Unit`

Keep approved publication capitalization.

Do not put an instruction only in the heading if the user can skip it during
step-by-step work.

## Description controls

### Description model

A description usually states:

- what an item is
- where it is
- what it contains
- what it does
- how it interacts with another item
- what condition causes a change
- what result occurs

Use separate sentences for separate topics.

### Function descriptions

Prefer a direct active verb.

Avoid:

`The purpose of the controller is the regulation of pump speed.`

Preferred:

`The controller controls the pump speed.`

### Location descriptions

State the reference object.

Preferred:

`The sensor is on the left side of the pump.`

Avoid:

`The sensor is adjacent to it.`

Use approved orientation conventions from the project.

### State descriptions

Distinguish a state from an action.

- State: `The valve is closed during normal operation.`
- Action: `The actuator closes the valve when the pressure decreases.`

Do not rewrite a state as an action unless the source supports the agent and
event.

### Sequence descriptions

Use separate simple statements for process sequence.

Example:

`The controller receives the pressure signal.`

`It compares the signal with the set value.`

`If the pressure is low, the controller starts the standby pump.`

Repeat `the controller` instead of `it` when another possible antecedent is
present.
