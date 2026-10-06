# JISR hackathon deployment

Current configuration: **Free Render demo**, one Docker instance in Frankfurt, no persistent disk, FFmpeg limited to one thread. The existing host is [jisr-3ue4.onrender.com](https://jisr-3ue4.onrender.com/).

The October 6 final read-only check returned HTTP 200 for `/api/health`, with FFmpeg and both provider keys configured. `/languages.json` returned **404**, so this host does not yet contain the current multilingual release. Configured-key flags do not establish live permissions, quotas or translation quality.

## Publish the current release

1. Push the current runtime source to the intended repository and branch. Keep `.env`, `data/`, `work/`, virtual environments and private editor links out of Git. For a clean runtime package, run `python scripts/package_demo.py` and extract `submission/deployment/jisr-hackathon-deploy.zip` into the deployment repository. The ZIP contains the active app, language module/catalog, fonts/licenses, operating documentation and an integrity manifest.
2. For the existing Render service, select **Manual Deploy → Deploy latest commit** for an immediate release. `render.yaml` sets `autoDeployTrigger: commit` so Blueprint-managed services deploy on new commits. For an existing service created outside a Blueprint, also enable **Settings → Build & Deploy → Auto-Deploy → On Commit** in Render; changing the YAML alone does not confirm that the live service setting changed. Verify the selected branch/commit and wait for a successful build and deploy. Do not restart while someone is processing or exporting a video.
3. For a new service, choose **New → Blueprint**, select the repository/branch containing `render.yaml`, and verify the dashboard shows **Free** and **no disk**. No paid hosting change is included in this configuration.
4. Enter `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` privately in Render's environment/secret fields. The model defaults to `gpt-6-luna`; use the account's enabled model. ElevenLabs requires **Speech to Text** access. Never add secrets to source or public issue reports.
5. Copy the exact HTTPS root URL shown by Render. Run `python scripts/check_deployment.py https://YOUR-ACTUAL-HOST`. This is a read-only health/asset check: it includes the language catalog, language JavaScript and all four target-script fonts. It does not upload video or invoke paid AI processing.
6. Complete the fresh-session workflow below before submitting the link. Record the deployed commit and observed results; do not substitute local or mocked test results for hosted processing evidence.

Docker installs FFmpeg and ships the same local subtitle fonts used by the preview. The restricted Docker context includes all local Python imports, including `languages.py`. The startup wrapper initializes the data directory, then drops root privileges. The image has not been built on the current Windows host because Docker is unavailable; the Render build must be checked.

## Storage and availability of the Free demo

Free instances can sleep after inactivity and use ephemeral storage. Uploaded videos, edits, SQLite projects, exports and language histories are lost when the instance restarts/redeploys or its ephemeral filesystem is replaced. Download outputs during the active session. A viewer link to a temporary project cannot be promised to remain available through these events.

Hosting plan limits are described in [Render's official Free documentation](https://render.com/docs/free). ElevenLabs/OpenAI requests are billed separately. Keep the live key permissions and quotas available during judging; the app does not offer unlimited processing.

Use one instance: this app uses SQLite, local files and in-process background jobs. Interrupted processing becomes retryable after restart, but only if its saved files still exist. There is no external queue or backup service.

## Verify before submitting the public link

- Open the root HTTPS URL in a fresh browser session. Confirm onboarding, language selection and mobile navigation lead to upload. `/?demo=1` is an illustrative editor, not a live processed result.
- Confirm `/languages.json` lists `en`, `es`, `ur`, `hi`, `id`, `zh-Hans`, `tr`, and the selected target remains when the project is reopened.
- With the account owner's authorization for the paid service requests, upload a short permitted Arabic clip containing speech, a verse and a Hadith. Check extraction, target-language meaning, source status, timing and review/edit saving. Keep unavailable published translations visibly distinct from drafts.
- Resolve review items by listening and checking sources. Save a font/style change, prepare and download MP4/SRT/reference JSON, then play the MP4 and check audio, script shaping, wrapping, size and timing. SRT appearance depends on its player.
- After actual review, open the read-only viewer link in a separate session. Never send a private editor recovery link to judges.
- On this Free setup, do not use persistent-project survival across restart as a success criterion. Record that limitation. Test persistence after restart only if the team separately provisions persistent storage.
- Test deletion only on a disposable verification project, and record observed behavior.
- Fill the actual application URL, public repository URL, deployed revision and reviewed viewer URL in `submission/README.md`. Add the final presentation/demo video and retain the portal's submission confirmation.

## Alternative: an existing Linux server

`compose.yaml` and `Caddyfile` support a separately configured host with a persistent Docker volume and domain. Set `JISR_DOMAIN` and keys privately in `.env`, then run:

```bash
docker compose up -d --build
```

Compose uses `JISR_TRUST_PROXY=1` for Caddy's `X-Real-IP`. Render uses its managed `X-Forwarded-For` edge. Enable proxy trust only behind the intended trusted proxy. Verify HTTPS and persistence on the actual host. This alternative does not change or upgrade the selected Free Render service.

The app currently limits uploads to 250 MB, 10 uploads/hour per client, two processing jobs at once and one MP4 render at once. Do not promise zero downtime or unlimited capacity.

Primary references: [Docker hosting](https://render.com/docs/docker), [Blueprint configuration](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [Free limitations](https://render.com/docs/free).
