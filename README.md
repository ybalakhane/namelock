# namelock

Fail a voice-agent call if the agent addresses the wrong person.

A demo script knows who it is talking to. A live call does not. The failure
mode I actually hit: the session was one caller, the model said
"You're all set, [someone else]." Logs still looked like a successful booking.

`namelock` reads the agent side of a transcript and exits 1 if it vocatively
addresses a person who is not the expected caller. It does not flag the
practice name, the day of the week, or a caller mentioning someone else.

```
namelock call.txt --expect-name "Alex Test"
namelock call.json --expect-name Alex --alias Xander
```

Exit 0 if the agent only addressed the expected person. Exit 1 on a mismatch,
so it can gate a deploy the same way `turnlag --max-p50` does. Exit 2 when
the file is missing or the JSON is not a transcript.

## Setup

Python 3.10 or newer. No dependencies.

`pip install .` provides the `namelock` command above. From a checkout,
without installing, use `python -m namelock`. That is what CI runs.
`--json` prints `ok`, `expected`, and `findings` (`name`, `line`,
`snippet`) and does not change the exit code.

```
python -m namelock examples/right-name.txt --expect-name "Alex Test"
python -m namelock examples/call.json --expect-name "Alex Test" --json
python -m unittest discover -s tests -v
```

## What it looks at

Vocative uses: "Hi, Jordan." / "You're all set, Jordan." / "Jordan, you're booked."

It ignores:

- Caller turns in JSON transcripts (`turns[].speaker`)
- Clinic / day / month words that happen to be capitalized
- The expected first name, last name, and `--alias` forms

## Input

- Plain text (treated as agent speech)
- JSON `{ "turns": [ { "speaker": "agent"|"caller", "text": "..." } ] }`

No dependencies. Synthetic examples only — no real recordings in the repo.

## In CI

```
python -m namelock examples/right-name.txt --expect-name "Alex Test"
```
