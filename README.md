# google-ads-cli (`gads`)

Vollumfängliche Kommandozeilen-CLI für die Google Ads API (aktuell v25),
gebaut für die Steuerung durch KI-Agenten: nicht-interaktiv, mit JSON als
Standard-Ein-/Ausgabeformat und klaren Exit-Codes.

## Warum keine per-Ressource-Subcommands?

Die Google Ads API hat >100 Services und hunderte Ressourcen. Statt für jede
einzelne Ressource eigenen Code zu schreiben, nutzt `gads` die durchgängige
GAPIC-Namenskonvention der API per Reflection aus. Drei generische Befehle
decken dadurch **die gesamte API** ab:

- `gads query` — beliebige GAQL-Abfragen (Reporting/Lesen)
- `gads mutate <resource>` — generisches create/update/remove für jede
  mutierbare Ressource (`campaign`, `ad_group`, `ad_group_criterion`, ...)
- `gads call <Service> <Methode>` — Fallback für alles andere (BatchJobService,
  ConversionUploadService, OfflineUserDataJobService, KeywordPlanService,
  GoogleAdsFieldService, CustomerService, Long-Running-Operations, ...)

Dazu kommt eine kleine Zahl komfortabler High-Level-Befehle unter `gads hl`
(Kampagne/Budget/Ad Group/Keyword/Anzeige anlegen) als dünne Wrapper — reine
Ergonomie, keine zusätzliche Abdeckung nötig.

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Einrichtung (einmalig, danach vollständig nicht-interaktiv)

Zwei Auth-Methoden werden unterstützt:

### Option A: Service Account (Google Cloud Console)

Empfohlen, wenn der API-Zugriff über ein GCP-Projekt/Service-Account verwaltet
wird (kein interaktiver Consent-Flow nötig):

```bash
gads auth use-service-account \
  --json-key-file-path /pfad/zur/service-account.json \
  --login-customer-id <MCC_CID>   # optional, falls ueber ein MCC zugegriffen wird
```

Voraussetzung: die `client_email` aus der Schlüsseldatei muss auf dem
Google-Ads-Konto (oder MCC) unter **Tools & Einstellungen > Zugriff und
Sicherheit > Nutzer** als Nutzer hinterlegt sein. Ein klassischer Developer
Token ist dabei nicht zwingend erforderlich (Google Ads "Cloud-managed access"
für Cloud-Organization-verknüpfte Projekte) — optional per `--developer-token`
setzbar, falls vorhanden. Domain-Wide-Delegation (Impersonation eines
Workspace-Nutzers) ist nur nötig, wenn die client_email nicht direkt als
Kontonutzer hinterlegt wurde; dafür `--impersonated-email` setzen.

Die Schlüsseldatei selbst sollte **außerhalb** des Repos liegen (z.B. unter
`~/.config/google-ads-cli/`) — sie enthält einen privaten Schlüssel und darf
nie committet werden.

### Option B: OAuth Installed-App-Flow

```bash
gads auth login \
  --client-id <OAUTH_CLIENT_ID> \
  --client-secret <OAUTH_CLIENT_SECRET> \
  --developer-token <DEVELOPER_TOKEN> \
  --login-customer-id <MCC_CID>   # optional
```

Beide Befehle speichern die Konfiguration unter
`~/.config/google-ads-cli/google-ads.yaml` (Dateirechte 600). Danach laufen
alle weiteren Befehle vollständig nicht-interaktiv.

Für Container/CI ganz ohne Datei: alle Felder sind per Env-Var überschreibbar
(`GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`,
`GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_JSON_KEY_FILE_PATH`,
`GOOGLE_ADS_IMPERSONATED_EMAIL`, `GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS`,
`GOOGLE_ADS_LOGIN_CUSTOMER_ID`).

```bash
gads auth status   # prueft die Config gegen die echte API
```

## Nutzung

**GAQL-Abfrage (Reporting):**
```bash
gads query -c 1234567890 -q "
  SELECT campaign.id, campaign.name, metrics.clicks
  FROM campaign
  WHERE segments.date DURING LAST_7_DAYS"
```

**Kampagne erstellen (generischer `mutate`-Befehl):**
```bash
gads mutate campaign -c 1234567890 -o '[
  {"create": {"name": "Meine Kampagne", "status": "PAUSED",
              "advertising_channel_type": "SEARCH",
              "campaign_budget": "customers/1234567890/campaignBudgets/111"}}
]'
```

**Dieselbe Operation zuerst nur validieren:**
```bash
gads mutate campaign -c 1234567890 --dry-run -o '[...]'
```

**Kampagne pausieren (update mit automatischer Field-Mask):**
```bash
gads mutate campaign -c 1234567890 -o '[
  {"update": {"resource_name": "customers/1234567890/campaigns/999", "status": "PAUSED"}}
]'
```

**Generischer Fallback für jede andere API-Methode:**
```bash
gads list-services
gads list-methods BatchJobService
gads call BatchJobService mutate -c 1234567890 -r '{"customer_id": "1234567890", "mutate_operation": [...]}'
```

**Komfortbefehle:**
```bash
gads hl budget create -c 1234567890 --name "Budget A" --amount-micros 5000000
gads hl campaign create -c 1234567890 --name "Kampagne A" --budget customers/1234567890/campaignBudgets/111
gads hl keyword add -c 1234567890 --ad-group customers/.../adGroups/222 --text "schuhe kaufen" --match-type BROAD
gads accounts list-hierarchy -c <MCC_CID>
```

**Feld-Metadaten nachschlagen** (welche Felder bietet eine Ressource? kein
Kundenkonto nötig — Wrapper um `GoogleAdsFieldService`, den globalen
Feld-Katalog der API):
```bash
gads fields list ad_group                        # alle Felder von ad_group
gads fields list ad_group --category METRIC       # nur Metriken
gads fields list campaign.network_settings        # Felder einer Unter-Message
gads fields show ad_group.status                  # volle Metadaten inkl. enum_values, selectable_with
```
Zeigt `selectable`/`filterable`/`sortable`/`enum_values`/`data_type` und (bei
`show`) `selectable_with` (mit welchen anderen Ressourcen/Segmenten/Metriken
sich das Feld in einer GAQL-Abfrage kombinieren lässt). Das sagt nur, was per
GAQL *lesbar* ist — nicht, was per `mutate` *schreibbar* oder mit welchem
`advertising_channel_type` kompatibel ist. Das lässt sich nur durch Lesen des
Resource-Protos oder durch `--dry-run`-Ausprobieren herausfinden (siehe
"Wie ich das selbst mache" unten).

## Agenten-Vertrag

- Ausgabe: reines JSON auf stdout (Standard; `--format table`/`--format csv`
  für Menschen). Logs/Fehler gehen nach stderr.
- Exit-Codes: `0` Erfolg, `1` CLI-/Validierungsfehler, `2` Google-Ads-API-Fehler
  (strukturiertes JSON mit `error_code`, `message`, `field_path`), `70`
  unerwarteter interner Fehler.
- Mutate-Befehle laufen standardmäßig sofort durch (kein Bestätigungszwang,
  wichtig für autonome Agenten); `--dry-run` nutzt `validate_only` der API.

## Feld-/Schema-Recherche jenseits von `gads fields`

`gads fields` beantwortet "was ist per GAQL selectable/filterable?". Für
"was ist bei `mutate` überhaupt als Feld vorhanden, und welchen Typ/Enum-Wert
erwartet es?" hilft zusätzlich eine kurze Python-Introspektion gegen die
lokal installierten, generierten Klassen der `google-ads`-Bibliothek (rein
lokal, kein API-Call, keine Zugangsdaten nötig):

```python
from google.ads.googleads.v25.resources.types.ad_group import AdGroup
for f in AdGroup.pb().DESCRIPTOR.fields:
    print(f.name, [v.name for v in f.enum_type.values] if f.enum_type else f.type)
```

Für die dritte Frage — "ist dieses Feld bei `mutate` für einen bestimmten
`advertising_channel_type` tatsächlich beschreibbar?" — gibt es keine
Metadatenquelle; das zeigt nur ein echter `--dry-run`-Aufruf (siehe die
Fehlercodes `OPERATION_NOT_PERMITTED_FOR_CONTEXT`, `IMMUTABLE_FIELD`,
`SETTING_TYPE_IS_NOT_COMPATIBLE_WITH_CAMPAIGN` in `errors.py`).

## Tests

```bash
pytest
```

Alle Tests laufen ohne echte Google-Ads-Zugangsdaten (Reflection gegen die
echten generierten Protobuf-Klassen, RPC-Aufrufe selbst werden mit
`unittest.mock.patch.object(..., autospec=True)` gemockt).

## Status

Kernbefehle (`query`, `mutate`, `call`, `auth`, `accounts`, `hl`) sind
implementiert, getestet und gegen ein echtes Google-Ads-Konto (Service-Account-
Auth, Cloud-managed Access ohne Developer Token) live verifiziert: `auth
status`, `query`, `accounts list-hierarchy`, `mutate --dry-run` (inkl.
mehrteiliger Validierungsfehler) und der generische `call`-Fallback
funktionieren wie erwartet.
