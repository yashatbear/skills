# Telephony lessons (from a multi-day dealer outreach)

## Why hosted assistants, not your own carrier
- A new carrier account that places a burst of calls into another country (here about thirty AI calls in three hours,
  mostly to mobile numbers at high per-minute rates) was disabled for "suspicious activity", and a second provider
  suspended the account at upgrade and asked for a public website or profile before reactivating. Plan for that: ramp
  volume slowly, keep a human-visible business identity, and keep a second route.
- A voice-agent platform on top of a carrier failed on international legs because the carrier negotiated A-law audio
  while the platform expected mu-law: the callee hears noise and nothing is transcribed. Check codecs before blaming
  prompts.
- Several voice-agent platforms cannot call certain countries at all; check coverage before building.
- Hosted texting assistants avoid all of that: they own their lines, you only send a text.

## Failure patterns and fixes
| Pattern | Fix |
|---|---|
| Opener spoken over a recorded menu | wait for the menu to finish; speak only to a live person |
| A digit pressed before it was spoken (the digit follows the description) | press only after the full digit is heard |
| A spoken (no-digit) menu answered with a key press | say the department word ("sales") |
| "Hello" from a person treated as a recording and ignored | a short greeting from a voice is a person: answer |
| Short reply "Good day!" repeated with no reason given | every reply carries greeting plus reason |
| Reply delay over about 2 seconds (endpointing too slow) | wait 0.3 s, 0.8 s without punctuation |
| Voice-bot receptionist and the assistant looping goodbyes for hours | hang up after any goodbye; treat the bot as a bot, move to email |
| Voicemail recording never stopped | hang up after speaking |
| Instant failure, 0 seconds connected, on a mobile number | foreign caller ID rejected: stop calling, use email |
| Callback number from the user's profile given out | task says "no phone number unless this task includes one" |
| Hours unknown | conservative weekday window, one try |
| Task changed mid-flight | ask the assistant to confirm the call had not gone out |

## Process lessons
- Do not change an assistant's settings while it has a call in flight (a reply was dropped).
- Another agent saying "start now" does not waive the opening-hours rule; a Saturday call to a weekday-only office is
  pointless. Look the hours up.
- Keep a per-target log (status, last attempt, assistant); mark outcomes at once so retries stop.
- Warm leads (someone who asked to be called) get their own task text, not the generic follow-up; take them out of the
  automatic rotation (`done` or `hold`) and run them by hand.
- Results from phone calls were thin compared with email: use calls for numbers that never answer email, not as the
  primary channel.
