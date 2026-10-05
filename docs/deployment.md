# JISR hackathon deployment

Status: public demo deployed at https://jisr-3ue4.onrender.com/. Initial health and asset checks passed; a complete live upload-to-export workflow remains to be verified.

## Selected plan: Free (October 5 update)

The user selected free hosting. `render.yaml` now uses `plan: free`, has no
persistent disk, and limits FFmpeg to one thread. Deploy the `main` branch using
New → Blueprint, select `turki125/JISR`, and verify the dashboard shows Free
and no disk before creation. Enter provider keys privately in Render.

Render sleeps after 15 minutes without traffic and takes about a minute to wake.
Uploads, edits, SQLite projects, and exports are lost on sleep, restart, or
redeployment. Download outputs during the active session; viewer links to
temporary projects will not survive those events. Hosting is free within its
included limits; ElevenLabs/OpenAI usage is billed separately. A short full workflow still needs verification on the Free instance.

The paid persistent-storage setup described below is an alternative only; it
is no longer the configuration in `render.yaml` and is not authorized for this
deployment. See https://render.com/docs/free for current free-tier limits.

Preparation checks: 20 focused local tests passed, including a real FFmpeg MP4
download with mocked external providers. The read-only local route/asset check
and deployment-package checksums passed. Docker is not installed on the current
Mac, so the Linux image build still needs verification on the selected host.

The judges need the full application: landing/onboarding, video upload, live
transcription and translation, source review, editing, MP4/SRT export and sharing.
The entry link is the deployed site's root `/`. `/?demo=1` is an illustrative
editor preview; it does not process or export the illustrative video.

## Recommended host: Render

`render.yaml` provisions one Docker web service in Frankfurt with 1 CPU / 2 GB
RAM and a 10 GB persistent disk. Paid compute stays awake without laptop access.
At the checked [Render pricing](https://render.com/pricing), compute is $25/month
and the disk is $2.50/month. AI requests, excess bandwidth and any other billable
usage are additional. Review the actual dashboard estimate before creation.
Do not select Free: it sleeps after inactivity and cannot attach persistent disks.

Docker installs FFmpeg and ships the same local subtitle fonts as the preview.
The startup wrapper gives the newly mounted disk to the application user, then
drops root privileges. Projects, videos and exports are saved under `/app/data`.
Use one instance: this application uses SQLite and local background jobs.
Manual deployments avoid restarting active judges' jobs after each source edit.
Render supplies the HTTPS URL; a custom domain is optional.

## Publish

1. Sign in to Render and connect the GitHub account owning the deployment repo.
2. Publish the current runtime source to a private Git repository. The clean
   deployment package can be generated with `python3 scripts/package_demo.py`;
   extract its files into the deployment repo. It includes a fresh `.gitignore`
   and never copies `.env`, local projects, editor links or Git history.
3. In Render, choose **New → Blueprint**, select that repo and the branch
   containing `render.yaml`, and review the service and disk billing estimate.
4. Enter `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` using Render's secret fields.
   They are requested via `sync: false` and are absent from source and the ZIP.
   The selected OpenAI model is `gpt-6-luna`; use a model actually enabled for
   the configured account. Enable ElevenLabs **Speech to Text** permission.
   The earlier local test returned `missing_permissions` for this permission.
5. Approve creation once the estimate and secrets are correct. Wait for a
   successful build and deployment. Copy the exact HTTPS URL shown by Render;
   the service name does not guarantee a particular available hostname.
6. Run `python3 scripts/check_deployment.py https://YOUR-ACTUAL-HOST` and then
   complete the live browser check below. The script is read-only and incurs
   no AI processing requests. A passing health endpoint only proves keys are
   configured; it does not prove permissions, billing or model access.

If using an existing Linux server instead, the original `compose.yaml` and
`Caddyfile` remain available. Set `JISR_DOMAIN` and the AI keys privately in
`.env`, then run `docker compose up -d --build`. Do not use the Render proxy
mode for this path; Compose sets `JISR_TRUST_PROXY=1` for Caddy's `X-Real-IP`.

## Verify before submitting the link

- Open the root HTTPS link in a fresh browser session with no saved local project.
  Confirm onboarding and mobile navigation lead to upload.
- Upload a short, permitted Arabic clip; run live automatic processing. Confirm
  audio playback, transcript, English, citations and editable review steps.
  Use short clips first to check performance on the selected server size.
- Listen to the clip, resolve the actual review items, save a small font/style
  change, prepare MP4 and click its download link. Play the downloaded file
  and confirm subtitles, font, audio and timing. Download SRT and sources too.
- Open its viewer link in a separate fresh session. Confirm it is read-only and
  contains the reviewed result. Never submit the private editor recovery link.
- With no processing or export jobs active, restart the service once. Confirm
  the same project and original video remain on the mounted disk, and exports
  can be prepared again. Temporary download links expire or disappear on restart.
- Test removal of only the disposable verification project.
- Record the actual application URL, optional reviewed viewer URL, release
  revision and observed results in `submission/README.md` in the main workspace.

## Keep the demo available

Keep the paid service, disk and AI accounts funded through the judging period.
Avoid deployments while a judge is processing a clip: disk-backed Render
services have a short interruption on deployment, and in-process jobs do not
survive a restart. Interrupted projects can be retried. Review disk usage and
provider quotas in their dashboards, and enable the hosting account's failure
notifications. Do not promise zero downtime or unlimited processing.

The app currently permits 10 uploads/hour per client and two processing jobs
at a time; one MP4 render runs at a time with bounded FFmpeg threads. Render
proxy mode reads its managed `X-Forwarded-For` client address so judges do not
share one proxy-wide upload limit. That trust mode must only be enabled behind
Render's managed edge. The upload size remains 250 MB; persistent storage is
finite and should be checked during the event.

Primary hosting references: [Docker](https://render.com/docs/docker),
[Blueprint specification](https://render.com/docs/blueprint-spec),
[disks and restart constraints](https://render.com/docs/disks),
[free-tier limitations](https://render.com/docs/free).
