# steer-engine: paper in, posts out

A pipeline that turns a research paper into a carousel, a static post (4:5, 1:1, 9:16) and a voiced, subtitled reel in Steer's voice,
with every claim locked to a verbatim quote and held behind a doctor review gate.

```
paper (txt/pdf/url) -> ingest.py -> claims (verbatim quotes) -> spec json -> verify -> lint -> render -> review.html -> publish_gate.py
                                    prompts/extract.md          prompts/translate.md   deterministic, no LLM in these 5 stages
```

## Run
```
pip install pillow pypdf   # plus ffmpeg and the Lora/Inter fonts
python run.py              # all specs in specs/  ->  out/<paper>/ + out/review.html + out/run_log.json
python -m unittest discover tests
python publish_gate.py     # exits 1 until a named reviewer has approved every claim and steer-view line
```

Research/source sheet: `research_sources.csv` (every claim, its verbatim quote, source link and where it is used). Source text: `papers/`.

## What makes the science survive the trip
1. **Quote lock.** Every claim is a verbatim quote that must be found in the stored source text.
2. **Number lock.** Every number on any slide, reel scene, subtitle or caption must appear in a linked claim quote. Rounded matches ("about 19%" from -19.3%) are allowed and listed as notes for the doctor.
3. **Opinion is labelled.** Lines that are Steer's view, not a study finding, are marked `steer_view`, cannot contain numbers, and print "Steer's view, not a study finding" on the image.
4. **Voice linter.** Fails on drug or brand names, kilo/timeline promises, miracle or hype words, before/after, fear/shame words, ALL CAPS, emoji.
5. **Doctor gate.** `out/review.html` lists each claim with its quote, source link and where it is used. `publish_gate.py` refuses to queue anything until every item is approved by a named reviewer.
`tests/test_gates.py` proves a fabricated number, an invented quote, a drug name and a promise are all rejected.

## Measured effort (this build, 2 CPU cores)
Machine time: about 14 s per paper (verify + lint 0 s, carousel 0.3 s, three static sizes 0.1 s, reel about 13 s), 41 s for the 3-paper batch.
Human time per paper: the doctor reads one page and ticks 8 to 10 items. Not yet measured with a real doctor. Choosing the paper and checking the quotes against the full text is the real cost.

## Honest limits
- The two LLM steps (extract, translate) were done by Claude in-session using `prompts/`. `engine/llm.py` runs them unattended with an API key but was **not run here** (no key, no outbound network).
- PMC full text is blocked from this environment, so source files hold abstracts and trial-report excerpts as retrieved (`papers/*.txt`). A doctor should confirm each quote against the full paper.
- The voiceover uses ffmpeg's offline flite voice as a placeholder. Swap `synth()` in `engine/reel.py` for a production voice.
- Posting to Meta, Buffer or Later is not wired; the gate writes `publish_queue.csv` with a weekly slot plan.
- `ingest.py` was tested on .txt only.
- Hinglish captions are drafted by Claude and need a native reader. Hindi reel voiceover is not done.

## Tools used
Claude (Anthropic) for extraction, writing and code. Python, Pillow, Pillow's Raqm text layout, ffmpeg (libx264, aac, flite), Lora and Inter fonts. Papers: Wilding et al. 2022 (STEP 1 extension); Nutrients 2013 (Obesity and Dyslipidemia in South Asians); STEP 1 DEXA substudy (ENDO 2021, via Patient Care, and the Wilding abstract).
