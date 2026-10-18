# PS2 submission answers (edit before pasting)

**Output: 3 finished post sets, each with carousel + static (4:5, 1:1, 9:16) + reel (about 36 s) + captions + Hinglish caption + alt text**
| Paper | Message | Why |
|---|---|---|
| STEP 1 extension (weight regain) | Weight coming back after stopping is biology, not failure, so plan the "after" from day one. | Answers "will it come back?" with the trial number, says what the data cannot tell you, then hands the fear to a doctor. |
| South Asian BMI review | BMI alone can flatter an Indian body, so ask for your waist and body composition too. | Two BMI scales side by side show "built for Indian biology" in 3 seconds; waist flags are checkable at home. |
| STEP 1 DEXA substudy (muscle) | Some lean mass goes with weight loss, so measure what is changing instead of trusting the scale. | Faces the muscle-loss worry honestly (fat fell about twice as much as lean) and sets up the DEXA-first approach. |

**Pipeline.** Verbatim quote lock, number lock, voice linter, shared renderer for carousel/static/reel, doctor review page, publish gate. See README.md.
**Effort.** Machine time about 14 s per paper (41 s for 3). Human time is one review page per paper: 8 to 10 ticks.
**Disclosure.** Built solo with Claude (Anthropic). Tools listed in README.md. Papers used as source are cited in each post's footer and caption.
**Not done.** Live Meta posting, production voice, unattended LLM step (code present, not run), full-text quote check by a doctor.

## 2-minute Loom outline
0:00 The problem: papers are locked, posts are slow, doctors re-check from scratch.
0:20 Show review.html: one claim, its verbatim quote, where it is used.
0:50 Break it live: change a number in a spec, run `python run.py`, watch verify fail. Then add a drug name, watch lint fail.
1:20 Play the regain reel (muscle and BMI reels as extra). Point at the "Steer's view, not a study finding" label.
1:45 Gate: `python publish_gate.py` says BLOCKED until a doctor approves. Say plainly what is not wired yet.
