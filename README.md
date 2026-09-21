# google-ads-cli (`gads`)

A fully-featured command-line CLI for the Google Ads API (currently v25),
built for control by AI agents: non-interactive, with JSON as the default
input/output format and clear exit codes.

## Why no per-resource subcommands?

The Google Ads API has 100+ services and hundreds of resources. Instead of
writing dedicated code for every single resource, `gads` exploits the API's
consistent GAPIC naming convention via reflection. Three generic commands
therefore cover **the entire API**:

- `gads query` — arbitrary GAQL queries (reporting/reading)
- `gads mutate <resource>` — generic create/update/remove for every
  mutable resource (`campaign`, `ad_group`, `ad_group_criterion`, ...)
- `gads call <Service> <Method>` — fallback for everything else (BatchJobService,
  ConversionUploadService, OfflineUserDataJobService, KeywordPlanService,
  GoogleAdsFieldService, CustomerService, long-running operations, ...)

On top of that there's a small number of convenient high-level commands under
`gads hl` (create campaign/budget/ad group/keyword/ad) as thin wrappers —
pure ergonomics, no additional coverage needed.

## Installation

```bash
pip install google-ads-cli
```

For local development (editable install with test/lint dependencies):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Setup (one-time, fully non-interactive afterwards)

Two auth methods are supported:

### Option A: Service Account (Google Cloud Console)

Recommended when API access is managed through a GCP project/service account
(no interactive consent flow needed):

```bash
gads auth use-service-account \
  --json-key-file-path /path/to/service-account.json \
  --login-customer-id <MCC_CID>   # optional, if accessing via an MCC
```

Prerequisite: the `client_email` from the key file must be added as a user on
the Google Ads account (or MCC) under **Tools & Settings > Access and
Security > Users**. A classic developer token is not strictly required here
(Google Ads "Cloud-managed access" for projects linked to a Cloud
Organization) — settable optionally via `--developer-token` if you have one.
Domain-wide delegation (impersonating a Workspace user) is only needed if the
client_email wasn't added directly as an account user; set
`--impersonated-email` for that.

The key file itself should live **outside** the repo (e.g. under
`~/.config/google-ads-cli/`) — it contains a private key and must never be
committed.

### Option B: OAuth Installed-App Flow

```bash
gads auth login \
  --client-id <OAUTH_CLIENT_ID> \
  --client-secret <OAUTH_CLIENT_SECRET> \
  --developer-token <DEVELOPER_TOKEN> \
  --login-customer-id <MCC_CID>   # optional
```

Both commands store the configuration under
`~/.config/google-ads-cli/google-ads.yaml` (file permissions 600). All
subsequent commands then run fully non-interactively.

For containers/CI with no file at all: every field can be overridden via env
var (`GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`,
`GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`,
`GOOGLE_ADS_JSON_KEY_FILE_PATH`, `GOOGLE_ADS_IMPERSONATED_EMAIL`,
`GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID`).

```bash
gads auth status   # checks the config against the real API
```

## Usage

**GAQL query (reporting):**
```bash
gads query -c 1234567890 -q "
  SELECT campaign.id, campaign.name, metrics.clicks
  FROM campaign
  WHERE segments.date DURING LAST_7_DAYS"
```

**Create a campaign (generic `mutate` command):**
```bash
gads mutate campaign -c 1234567890 -o '[
  {"create": {"name": "My Campaign", "status": "PAUSED",
              "advertising_channel_type": "SEARCH",
              "campaign_budget": "customers/1234567890/campaignBudgets/111"}}
]'
```

**Validate the same operation first, without applying it:**
```bash
gads mutate campaign -c 1234567890 --dry-run -o '[...]'
```

**Pause a campaign (update with automatic field mask):**
```bash
gads mutate campaign -c 1234567890 -o '[
  {"update": {"resource_name": "customers/1234567890/campaigns/999", "status": "PAUSED"}}
]'
```

**Remove (soft-delete) a campaign:**
```bash
gads mutate campaign -c 1234567890 -o '[
  {"remove": "customers/1234567890/campaigns/999"}
]'
```
`remove` doesn't delete the record outright — Google Ads sets its status to
`REMOVED` and keeps it for reporting history. A removed resource can't be
mutated again afterwards (`OPERATION_NOT_PERMITTED_FOR_REMOVED_RESOURCE`).

### `mutate` operation schema

`--operations-json`/`-o` takes a JSON **array**; each element is one
operation and must contain **exactly one** of these three keys:

| Key | Value | Notes |
|---|---|---|
| `create` | object of field values (snake_case, matching the resource proto) | |
| `update` | object that **must include `resource_name`** plus the fields to change | if `update_mask` is omitted, it's derived automatically from the fields you set; pass it explicitly (a list of dotted field paths) to override |
| `remove` | a bare resource name string | no nested object, just the string |

`resource_name` follows the pattern
`customers/{customer_id}/{resourcePluralCamelCase}/{id}`, e.g.
`customers/1234567890/campaigns/999`,
`customers/1234567890/adGroupCriteria/222~333` (criteria use a composite
`adGroupId~criterionId` id). You get these back as `resource_name` in the
`results` of every `create` call, so you rarely need to construct them by
hand except for `update`/`remove` on records you already know about.

**Generic fallback for any other API method:**
```bash
gads list-services
gads list-methods BatchJobService
gads call BatchJobService mutate -c 1234567890 -r '{"customer_id": "1234567890", "mutate_operation": [...]}'
```

**Convenience commands:**
```bash
gads hl budget create -c 1234567890 --name "Budget A" --amount-micros 5000000
gads hl campaign create -c 1234567890 --name "Campaign A" --budget customers/1234567890/campaignBudgets/111
gads hl keyword add -c 1234567890 --ad-group customers/.../adGroups/222 --text "buy shoes" --match-type BROAD
gads accounts list-hierarchy -c <MCC_CID>
```

**Looking up field metadata** (which fields does a resource offer? no
customer account needed — a wrapper around `GoogleAdsFieldService`, the API's
global field catalog):
```bash
gads fields list ad_group                        # all fields of ad_group
gads fields list ad_group --category METRIC       # metrics only
gads fields list campaign.network_settings        # fields of a sub-message
gads fields show ad_group.status                  # full metadata incl. enum_values, selectable_with
```
Shows `selectable`/`filterable`/`sortable`/`enum_values`/`data_type` and (for
`show`) `selectable_with` (which other resources/segments/metrics the field
can be combined with in a GAQL query). This only tells you what's *readable*
via GAQL — not what's *writable* via `mutate`, or which
`advertising_channel_type` it's compatible with. That can only be discovered
by reading the resource proto or by trying a `--dry-run` (see "Field/schema
research beyond `gads fields`" below).

`gads fields` builds a query for `GoogleAdsFieldService`'s own mini query
language internally (not full GAQL). If you ever call that service directly
via `gads call GoogleAdsFieldService search_google_ads_fields -r '{"query": "..."}'`,
note its limitations: only `AND` is supported (**no `OR`**), string literals
need double quotes, and `LIKE` uses `%` as a wildcard — the same restrictions
apply to regular GAQL queries via `gads query`.

## Agent contract

- Every command and subcommand is self-documenting: `gads --help`,
  `gads mutate --help`, `gads hl campaign create --help`, etc. always reflect
  the exact, current set of flags — treat that as authoritative over any
  example in this README if the two ever disagree (e.g. after an update).
- Output: plain JSON on stdout (default; `--format table`/`--format csv` for
  humans). Logs/errors go to stderr.
- Exit codes: `0` success, `1` CLI/validation error, `2` Google Ads API error
  (structured JSON with `error_code`, `message`, `field_path`), `70`
  unexpected internal error.
- Mutate commands run immediately by default (no confirmation prompt,
  important for autonomous agents); `--dry-run` uses the API's
  `validate_only`.

## Field/schema research beyond `gads fields`

`gads fields` answers "what is selectable/filterable via GAQL?". For "what
fields actually exist for `mutate`, and what type/enum value do they
expect?", a short bit of Python introspection against the locally installed,
generated classes of the `google-ads` library also helps (purely local, no
API call, no credentials needed):

```python
from google.ads.googleads.v25.resources.types.ad_group import AdGroup
for f in AdGroup.pb().DESCRIPTOR.fields:
    print(f.name, [v.name for v in f.enum_type.values] if f.enum_type else f.type)
```

For the third question — "is this field actually writable via `mutate` for a
given `advertising_channel_type`?" — there's no metadata source for that;
only a real `--dry-run` call reveals it (see the error codes
`OPERATION_NOT_PERMITTED_FOR_CONTEXT`, `IMMUTABLE_FIELD`,
`SETTING_TYPE_IS_NOT_COMPATIBLE_WITH_CAMPAIGN` in `errors.py`).

## Common errors and gotchas

Found through actual live testing against the API (not exhaustive, but the
ones most likely to trip up a first attempt):

| Error code | What it means | What to do |
|---|---|---|
| `DATE_RANGE_ERROR_END_TIME_MUST_BE_THE_END_OF_A_DAY` | `campaign.end_date_time` (and similar `*_date_time` fields) must literally end in `" 23:59:59"` | Use e.g. `"2026-12-31 23:59:59"`, not just the date |
| `FIELD_HAS_SUBFIELDS` | You passed an explicit `update_mask` naming a message-type field (e.g. `"vanity_pharma"`) instead of its leaf sub-fields | Omit `update_mask` for that operation and let it be derived automatically, or list the actual leaf paths (e.g. `"vanity_pharma.vanity_pharma_text"`) |
| `IMMUTABLE_FIELD` | The field can only be set on `create`, not `update` (e.g. several `app_campaign_setting.*`/`travel_campaign_settings.*` fields) — or, on `ad_group_ad`, `start_date_time`/`end_date_time` can't be set at all | Set it during `create` instead, or drop it |
| `OPERATION_NOT_PERMITTED_FOR_CONTEXT` / `SETTING_TYPE_IS_NOT_COMPATIBLE_WITH_CAMPAIGN` | The field/setting only applies to a different `advertising_channel_type` (e.g. `payment_mode`, `hotel_setting` need Hotel/Local Services/Travel, not Search) | Remove the field; it wasn't meant for this campaign type |
| `OPERATION_NOT_PERMITTED_FOR_REMOVED_RESOURCE` | You tried to update/remove a child resource whose parent (e.g. its campaign or ad group) is already `REMOVED` | Nothing to do — it's already inert; no further action needed |
| `CUSTOMER_NOT_ALLOWLISTED_FOR_THIS_FEATURE` | The field needs vertical-specific account allowlisting (e.g. `vanity_pharma` needs pharma allowlisting) | Not fixable from the CLI side; the account needs to be approved by Google first |
| `USER_PERMISSION_DENIED` mentioning `login-customer-id` | You queried/mutated a client account directly instead of through its manager account | Pass `--login-customer-id <MCC_CID>` (global flag, works on every command) |

General rule of thumb: run the same operation with `--dry-run` first — it
triggers the exact same server-side validation as a real mutate, so every
error above shows up there before anything is actually changed.

## Tests

```bash
pytest
```

All tests run without real Google Ads credentials (reflection against the
real generated protobuf classes; the RPC calls themselves are mocked with
`unittest.mock.patch.object(..., autospec=True)`).

## Status

The core commands (`query`, `mutate`, `call`, `auth`, `accounts`, `hl`) are
implemented, tested, and live-verified against a real Google Ads account
(service account auth, cloud-managed access without a developer token):
`auth status`, `query`, `accounts list-hierarchy`, `mutate --dry-run`
(including multi-error validation) and the generic `call` fallback all work
as expected.
