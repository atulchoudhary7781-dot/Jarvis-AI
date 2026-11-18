# Contributing a skill

A shared skill is a small **data record**, not a plug-in, prompt injection, executable script or model update. Anyone can propose one; only a repository maintainer can merge it into the shared catalog. The notebook on a visitor's device is never ingested into that catalog automatically.

## Try it privately first

Say **“teach a shortcut”**, choose a short phrase, describe its action, and confirm. For a reusable practice question, say **“teach a quiz”** instead. Run it by saying its name. Use the same browser to keep the saved recipe.

## Propose it publicly

Say **“share skill”** followed by the name of a saved recipe. JARVIS reads back what would be shared. If you agree, it turns the microphone off. After it finishes speaking, tap the core or press **S** to open a draft GitHub issue. Check the content, edit it if needed and submit it yourself. No account or sign-in is needed to use the app; GitHub requires an account to submit an issue. You can also [open the template directly](https://github.com/atulchoudhary7781-dot/Jarvis-AI/issues/new?template=community-skill.md).

The draft carries only the trigger and its action fields. It does **not** carry your saved nickname, other recipes, microphone audio or chat history. The recipe, your GitHub account and anything else you put in a submitted issue will be public. Do not include secrets, personal identifiers, private conversations or an exact home/work address.

## Recipe format

```json
{
  "phrase": "two city check",
  "steps": [
    {"kind": "time", "city": "Delhi"},
    {"kind": "time", "city": "Tokyo"}
  ]
}
```

- A trigger is 2–44 characters, at most seven words. Choose a distinct, pronounceable phrase. Avoid built-in controls and names already in the catalog.
- A lookup sequence contains one or two actions: `time`, `date` or `weather` plus a city; or `headlines` with no arguments.
- A timer must be the **only** step: `{"kind":"timer","minutes":20}`. Choose an integer from 1 to 120.
- A quiz must also stand alone: `{"kind":"quiz","question":"Which planet has a Great Red Spot?","answer":"Jupiter"}`. Use a short, unambiguous answer. Matching ignores case and terminal punctuation; it is not a semantic grader or a source of verified knowledge.
- No custom providers, arbitrary URLs, shell actions, code, user accounts, instructions to the model or unrecognized fields. The catalog is limited to 64 recipes and 32 KiB.

## Maintainer checklist

1. Check consent, usefulness, distinctness, factual accuracy, language and pronunciation. Reject private details, unsafe or abusive content, copyrighted excerpts and unsupported actions. Schema validation is not a substitute for review.
2. Edit **only** the recipe data in `community/skills.json` for a catalog contribution. Preserve `version: 1`. Do not auto-import issue bodies.
3. Run `python -m unittest discover -s tests -v` and `node tests/notebook.cjs`. Try the phrase with the live-style HTTP host, including the second turn of a quiz or timer cancellation.
4. Merge the reviewed change into `main`. An active public instance checks this repository's fixed catalog URL at most about every ten minutes; the browser also caches it. Refresh the tab if testing a new entry. A network or validation failure keeps the last valid or bundled copy. A code or schema change still needs an app deployment.
