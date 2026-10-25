# Google Sheets setup

The sample map and main dashboard read from the spreadsheet configured in
`Mapa_muestras.py`. The sample map writes sample updates to these worksheet
tabs:

- `samples_humana_cancerosa`
- `samples_humana_no_cancerosa`
- `samples_raton_cancerosa`
- `samples_raton_no_cancerosa`

Each tab must have these headers in row 1:
`ubicacion`, `id`, `fecha`, `responsable`, `numero_pases`,
`criopreservante`, `lugar_proveniencia`, `certificacion`, and
`numero_celulas`.

Create one additional tab named `movements` with these headers in row 1:
`timestamp`, `action`, `box`, `location`, and `sample_id`.
The app appends each new sample addition or extraction to this tab, as well as
to its existing local movement log. Existing entries in the local
`movements.jsonl` file are not imported automatically.

## Enable app writes

Public editor access lets people edit the sheet in a browser, but it does not
authenticate the app for Google Sheets API writes. Configure a Google service
account:

1. Enable the Google Sheets API and Google Drive API in a Google Cloud project.
2. Create a service account and download its JSON key.
3. Share the spreadsheet with the service account's `client_email` and give it
   Editor access.
4. Do not save or rename the downloaded JSON key as `secrets.toml`. Copy its
   values into the TOML structure below in `.streamlit/secrets.toml` for local runs,
   or to the Streamlit deployment's Secrets settings:

```toml
[connections.gsheets]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Never commit `secrets.toml` or the downloaded service account key. Public
editor access also means anyone with the link can change or delete sheet data;
restrict link access if that is not intended.

Google Sheets is the app's only source of sample data. Existing local JSON
files are not read or imported.

## If Google Sheets returns HTTP 429

Google limits Sheets API reads per user per minute. The app caches each
worksheet read for 30 seconds and clears that worksheet's cache after a
successful add or removal. If the quota has already been exceeded, wait about
a minute before retrying. Repeated refreshes or other apps using the same
Google service account can still consume the shared quota.

If the sample was updated but the movement log reports a dropped connection,
the sample is already saved and the movement remains in the local
`movements.jsonl` file. Check the `movements` tab before copying the movement
there manually, since Google may have accepted the append before the connection
closed.
