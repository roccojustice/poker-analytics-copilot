# Board groups — design

*Session 73, 2026-11-08. Agreed with the user in chat (editor reviewed as a clickable mockup).*

## Why

GTO Wizard plays some flops of one flop type differently from the rest. In `2bp ip pfr` (BTN vs BB),
BLL boards split into boards where GTO overbets and boards where it bets small, so the check % differs.
The overbet boards also show up in Low, 2BWL and 3BW. The `Flop` filter can't isolate them. The user
wants a **group of boards he defines himself** (copied from GTOw) and wants to compare his frequencies
against GTO's on that group and on its complement.

## Goals

- A **board group** = a name + a list of entries. Each entry = **three ranks** (pairs allowed, e.g.
  `JJ5`) + its **textures**: rainbow, two-tone, or both.
- Groups **belong to a dashboard** (spot). `2bp ip pfr` has its own list; a future `3bp ip pfr`
  has another, even if a group has the same name.
- A **"Board group" filter** on the Dashboards page: `Any` / `<group>` / `NOT <group>` (one pick).
  It applies to **both sides** (user and GTO), in level 1 and level 2, AND with Flop / Turn / River,
  faced size, dates and the level-2 picks.
- An **editor** on the Dashboards page to create, rename, delete groups and add / remove boards.
- Seed: dashboard `2bp_ip_pfr`, group `overbet`, all rainbow + two-tone:
  `J98 J97 J96 J95 J94 J93 J92 J87 J86 J85 J84 J83 J82 J76 J75 J74 J73 J72 Q96 Q95 Q85 Q84 K96 K95`.

## Non-goals

- Not on the hands page (Spotlight). Dashboards only.
- No monotone texture: Monotone is already its own flop type, so a monotone flop never matches any
  entry (it is in `NOT <group>`).
- No suit placement: a two-tone entry matches **any** two-tone flop of those ranks, whichever two
  cards share the suit (user confirmed).
- No formulas ("2grap", "J-high connected"): groups are explicit board lists (user's call, Session 72).
- No multi-select of groups and no group-by-group breakdown table (one group at a time).
- No turn / river groups.

## Anti-goals

- Editing a group must **not** require rebuilding the GTO cache.
- The filter must never silently match a different set on the two sides: same membership function
  for both.

## How (decided)

### Data per hand

`spotlight.classify` adds two columns, computed from `card_1..3` before they are dropped:
- `flop_ranks`: the three ranks sorted high to low as a string (`"J98"`, `"JJ5"`, `"A22"`), ranks
  from `board_types.RANKS`.
- `flop_texture`: `"rainbow"` (3 suits), `"two-tone"` (2), `"monotone"` (1).

They are group-independent, so a group change never touches the cache. The GTO cache must be rebuilt
**once** to get them (~4 min, `python gto_cache.py build`). The cache path gets a format version (e.g.
`cache/<key>/v2/…` or a `-v2` suffix) so old pickles without the columns are never read.

### Storage

`board_groups.json` at the repo root, **committed** (no secrets; git gives the user's groups a backup
and a history), shipped with the `overbet` seed. Read on each request (small file; no in-memory copy
to get stale). Missing file = no groups. Shape:

```json
{"2bp_ip_pfr": [{"name": "overbet",
                 "boards": [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}, ...]}]}
```

Writes are atomic (temp file + `os.replace`, as in `gto_cache`).

Validation on save (400 / `SpotInputError` on bad input): unknown dashboard; group name empty,
or duplicated within the dashboard (case-insensitive); `ranks` not exactly 3 rank chars (normalized:
uppercase, sorted high to low); `textures` empty or containing anything but `rainbow` / `two-tone`;
trips (`JJJ`) with only `two-tone` (three cards of one rank are always rainbow; rainbow + two-tone is stored as rainbow). `load` normalizes too, so a hand-edited file still matches. A board repeated in a
group is merged (textures unioned), not an error.

The editor keeps a working copy of all the dashboard's groups; switching groups keeps unsaved edits,
`Save` sends them all, `Cancel` reloads from the server.

### Filter

`board_group` request field: `null` (Any) or `{"name": "<group>", "negate": false|true}`. Membership:
a hand is in the group iff some entry has `ranks == flop_ranks` and `flop_texture in textures`.
Applied in `dashboards.side_matches` (so level 1 and level 2 both get it). Unknown group name → 400.

### API

- `GET /dashboards/config` also returns each dashboard's groups (names + boards), or a new
  `GET /dashboards/{id}/groups` — builder's call.
- `PUT /dashboards/{id}/groups` replaces that dashboard's whole group list (the editor saves
  everything at once; simplest, single user).
- `POST /dashboard` and `POST /dashboard/line` accept `board_group`.

### Page (`static/dashboards.html`)

Matches the mockup the user reviewed:
- Bar: a `Board group` `<select>`: `Any`, then per group `<name>` and `NOT <name>`; a link
  `Edit groups…` that shows / hides the editor panel under the bar.
- Editor: left, the dashboard's groups + `+ New group`; right, the selected group: name input, `Delete
  group`; 13 rank buttons (A…2; 3 clicks = one board, clicking a rank twice gives a pair); two texture
  checkboxes (rainbow, two-tone, both checked by default); `Add`; a paste box (`J98 J97 …`, space or
  comma separated) whose boards take the checked textures; the group's boards listed by texture set,
  each with `×`; `Save` / `Cancel`. Save sends the full list; on success the filter dropdown refreshes.
- The interpreted-filter / summary line names the active group (`Board group: overbet` / `NOT overbet`).

## Tests (TDD, as usual)

- `flop_ranks` / `flop_texture` on a few known flops (pair, trips, each texture), incl. that the
  sorted order matches `RANKS`.
- Membership: two-tone entry matches both two-tone suit placements; monotone never matches;
  `negate` = exact complement of the matched set.
- Both sides use the same function (one test feeds the same frame through both paths).
- Storage: seed on missing file, round-trip, atomic write, each validation error.
- Cache: the versioned path; a v1 pickle is not read.
- `tests/test_static_config.py`-style check if any group config lands in the page's JSON block.

## Validation

No PT4 equivalent for user-defined groups, so no PT4 export diff. Check instead by exact set: for the
seed group, the matched `id_hand` set equals an independent SQL / Python count over `card_1..3`
written separately in the test (not the same function), on the GTO DB (`db` marker).

## Left to the builder

File / function names, whether groups come in `/dashboards/config` or their own GET, where the
membership helper lives (`board_types.py` is the natural home for `flop_ranks` / `flop_texture`).
