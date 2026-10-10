# Meridian Transfer – Team 47 Handover

Module: IE3132 – Penetration Testing

Platform: CTFd (pinned release 3.8.7)

This is a project-source handover for trusted team members. Extract the ZIP into your own Ubuntu VM and read README.md first, then use the fresh-install notes below. The ZIP has one top-level `meridian-transfer/` directory. It contains no personal credentials, existing administrator account, session signing keys, browser profiles, or running database state. Author source, reference solvers, tests and selected solution documents are intentionally included; this is not a participant-only release.

## Stages

- MT-01 – Digital Footprints: `challenges/mt-01-digital-footprints/`
- MT-02 – The Amended Contact Sheet: `challenges/mt-02-amended-contact-sheet/`
- MT-03 – Dispatch Window: `challenges/mt-03-dispatch-window/`
- MT-04 – Release Register Exception: `challenges/mt-04-release-register-exception/`
- MT-05 – The Offset in the Handover Log: `challenges/mt-05-offset-handover-log/`
- MT-06 – Reconcile the Transfer Ledger: `challenges/mt-06-reconcile-transfer-ledger/`

## Requirements and fresh installation

Use Git, Python 3 (with venv/pip support), Docker, Docker Compose v2 supporting `!override`, and curl. Network access is needed to clone the pinned upstream release, pull container images and install dependencies. MT-02's dependency file requires Pillow; MT-04's service dependency file supplies Flask and its dependencies. Install the dependencies in a virtual environment in your extracted project:

```bash
cd ~/meridian-transfer
python3 -m venv .venv-author
. .venv-author/bin/activate
python3 -m pip install -r challenges/mt-02-amended-contact-sheet/author/requirements.txt
python3 -m pip install -r challenges/mt-04-release-register-exception/service/requirements.txt
```

The included `platform/CTFd/` is a source snapshot without `.git/`. The existing `platform/setup_local.py` checks upstream Git origin, tag and commit, so it cannot use that snapshot directly. On the FIRST installation in your freshly extracted copy, preserve it under a different name, leaving the installer to clone the verified release:

```bash
mv platform/CTFd platform/CTFd-source-snapshot
python3 platform/setup_local.py
```

Run that move only once, and only in a fresh extraction with no destination of that name. The snapshot retains the upstream source, Dockerfile, dependencies and Compose configuration for inspection. Do not start the snapshot's Compose file directly: its original override references intentionally omitted secrets and the original VM's private address. The installer regenerates the override for your VM and creates fresh secrets and administrator credentials under `.secrets/`. If needed, the installer supports `--sudo-docker`; the other Docker commands below require working Docker access for your user.

`setup_local.py` installs/configures MT-01; it does not install all six stages. Regenerate omitted answers and the MT-04 seed, then install the remaining stages:

```bash
python3 challenges/mt-02-amended-contact-sheet/author/build_mt02.py
python3 challenges/mt-03-dispatch-window/author/build_mt03.py
python3 challenges/mt-04-release-register-exception/author/build_mt04.py
python3 challenges/mt-05-offset-handover-log/author/build_mt05.py
python3 challenges/mt-06-reconcile-transfer-ledger/author/build_mt06.py
python3 platform/setup_mt02.py
python3 platform/setup_mt03.py
python3 platform/start_mt04.py
python3 platform/setup_mt04.py
python3 platform/setup_mt05.py
python3 platform/setup_mt06.py
```

The actual builders and integration scripts are included at those paths. CTFd is at `http://127.0.0.1:8000`. New registration returns to login; successful password login opens `/challenges`. Read the newly generated `.secrets/ctfd_admin_credentials.txt` locally to administer your own instance; never distribute it.

After successful initial setup, start the existing CTFd deployment using:

```bash
cd ~/meridian-transfer/platform/CTFd
docker compose up -d ctfd
```

## MT-04 separate service

`platform/start_mt04.py` builds and starts `challenges/mt-04-release-register-exception/service/compose.yml`, generates a new service session secret, and checks its health. Its local URL is `http://127.0.0.1:8084`. Build the seed before first start as shown above. MT-04 is an intentionally vulnerable local training service; its documented outbound-egress restriction remains PARTIAL. Read `challenges/mt-04-release-register-exception/docs/MT04_SECURITY_BOUNDARY.md`. Do not run reset scripts against another person's working instance.

## Existing automated tests

From the project root with the virtual environment active, after regenerating the stage artifacts:

```bash
python3 -m unittest discover challenges/mt-01-digital-footprints/tests -v
python3 -m unittest discover challenges/mt-02-amended-contact-sheet/tests -v
python3 -m unittest discover challenges/mt-03-dispatch-window/tests -v
python3 -m unittest discover challenges/mt-05-offset-handover-log/tests -v
python3 -m unittest discover challenges/mt-06-reconcile-transfer-ledger/tests -v
```

MT-04 unit tests expect container paths such as `/app/data/seed.sqlite`; they are not a plain host unittest invocation. Its tests and validation tools are in the stage's `tests/` and `author/` directories. With both local services running, the existing HTTP suite can be run:

```bash
python3 challenges/mt-04-release-register-exception/tests/test_mt04_http.py
```

After integration of all six stages, these existing checks exercise your local CTFd instance (they create synthetic test accounts and submissions):

```bash
python3 platform/test_access_registration.py
python3 platform/test_challenge_signin.py
python3 platform/test_mt01_functional.py
python3 platform/test_mt02_functional.py
python3 platform/test_mt03_functional.py
python3 platform/test_mt04_functional.py
python3 platform/test_mt05_functional.py
python3 platform/test_mt06_functional.py
```

The optional `platform/test_ui_browser.cjs` requires Node.js and Playwright installed at the path specified in that script, `.secrets/ui-browser/`; that dependency installation and browser binaries are deliberately not shipped. Historical status reports describe the source VM, not validation of your new VM.

## Reviews, exclusions and limitations

Review packages are in `review/mt-02-independent/` through `review/mt-06-independent/`; no MT-01 independent review directory or top-level `scripts/` directory exists in this source. Read `docs/TESTING_STATUS.md` and `docs/AUTOMATED_RELEASE_STATUS.md`. Independent human reviews, full load testing and full-platform backup/restore remain pending as documented there.

The package excludes Git metadata, `.secrets/`, environment secret files, generated CTFd signing keys, Docker data/volumes, virtual environments, browser dependencies/caches, temporary workspaces, compiled Python, the disposable installer `.deb`, and generated private answer/credential files and MT-04 seed database. MT-04 private solution/configuration documents containing a literal training password are also omitted; its source, specification and solver remain available. Other permitted trusted-team solution documents may contain challenge answers. The MT-05 evidence ZIP deliberately contains synthetic browser-history SQLite data generated by its author script; this is challenge evidence, not a personal browser profile.

Upstream source includes public example/test credentials and the standard local Compose database defaults. Those are reproducible source defaults, not copied personal credentials or exported runtime secrets. Fresh setup generates new CTFd and MT-04 signing keys and a new administrator password. No API tokens or personal Google, SSH, OpenAI/Codex or browser credentials are included.

The package was assembled solely from files under `~/meridian-transfer`. No files were copied from other home-directory locations. Packaging verification checks clean extraction, required paths, source syntax, public-artifact checksums and secret exclusions; it does not deploy a second platform or certify a fresh end-to-end installation.
