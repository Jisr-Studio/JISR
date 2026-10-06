# Jisr submission workspace

Preparation started October 3, 2026. The current source release passed the [October 6 final delivery check](../docs/final-delivery-check-2026-10-06.md). The team submits the final presentation and explanation video externally; they are intentionally outside the code package. The final pushed/deployed revision must be recorded by the team.

Start with [the team preparation pack](../docs/team-preparation/README.md). Follow its task board and official requirement list.

Use these locations as work is completed:

| Location | Owner | Intended contents |
|---|---|---|
| presentation/ | Turki; Anas reviews | Editable deck, final export, screenshot assets, evidence notes |
| video/ | Turki; Anas reviews | Recording script, permitted raw footage, final demo |
| evidence/ | Anas; Turki contributes | Completed run records, reviewed outputs, comparison measurements, release check results |
| documentation/ | Both | Final source/component register, operating notes, baseline-to-release log |

The content drafts and empty evidence forms are under docs/team-preparation/. Copy or reference them while producing the final artifacts; an empty form is not a completed evaluation.

Maintain a development log after each completed task:

| Date/time (Riyadh) | Task ID | Owner | Change/commit | Verification | Evidence | Remaining issue |
|---|---|---|---|---|---|---|

Final links to fill:

- Application URL: https://jisr-3ue4.onrender.com/
- Reviewed sample viewer URL:
- Public repository URL: https://github.com/turki125/JISR (public access checked October 6; final local source push still pending)
- Release revision:
- Submission confirmation and Riyadh timestamp:

Public read-only inspection on October 6 returned health 200 and the seven-language catalog. The hosted frontend lacks the portable-preview fix from this delivery. Public `main` was `0ee83846f504a63f7a1b1cdb44aa21980abf8fb3` at inspection; this is not a claim that the final audited package was pushed or deployed. After the team's release, deploy and verify the actual new revision and full workflow. Free hosting has temporary storage.

Clean source package: `deployment/jisr-final-source.zip`, generated with
`python scripts/package_source.py`. Extract its contents into the repository;
it excludes secrets and private user projects. The runtime-only ZIP is generated
with `python scripts/package_demo.py`. Both contain file-hash manifests. The source ZIP is the committee code deliverable; the runtime ZIP omits tests and editor settings.

Keep raw licensed/private media and private permission evidence outside public publication when release is not permitted. Do not add API keys or private project edit links. Review the exact files before making the submission repository public.
