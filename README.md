# Meridian Transfer

**IE3132 Penetration Testing | Assignment 02 | Team 47**

Meridian Transfer is a six-stage CTF based on a fictional research-data handover investigation. Players examine archived records, a hidden image annotation, an encoded dispatch, a vulnerable release portal, forensic logs and a transfer ledger. All challenge records and identities are synthetic.

The box uses CTFd 3.8.7 and Docker Compose on an Ubuntu 24.04 VM. It covers six domains, progresses from Easy to Hard and offers **1,400 fixed points**.

## Contents

- [Challenge pathway](#challenge-pathway)
- [Project layout](#project-layout)
- [Requirements](#requirements)
- [First-time setup](#first-time-setup)
- [Running the box](#running-the-box)
- [Reset and recovery](#reset-and-recovery)
- [Testing](#testing)
- [Architecture and isolation](#architecture-and-isolation)
- [Member responsibilities and source code](#member-responsibilities-and-source-code)
- [Acknowledgements](#acknowledgements)

## Challenge pathway

| Stage | Title | Domain | Difficulty | Points |
|---|---|---|---|---:|
| MT-01 | Digital Footprints | OSINT / Reconnaissance | Easy | 100 |
| MT-02 | The Amended Contact Sheet | Steganography | Easy | 150 |
| MT-03 | Dispatch Window | Cryptography | Moderate | 200 |
| MT-04 | Release Register Exception | Web Security | Moderate | 250 |
| MT-05 | The Offset in the Handover Log | Digital Forensics | Moderate-Hard | 300 |
| MT-06 | Reconcile the Transfer Ledger | Programming / Scripting | Hard | 400 |
| | **Total** | | | **1,400** |

The intended order is MT-01 through MT-06. The story connects the stages, but CTFd does not require an earlier flag to unlock a later challenge. Each stage provides its own evidence and context.

Flags follow `MT{mtNN_<value>}`, where `NN` identifies the stage. CTFd checks one case-sensitive static flag per challenge. Wrong submissions earn no points, and repeated correct submissions do not award points again. Each stage has two free hints.

Each specification covers the build, intended solution, required tools, hints and recovery:

- [MT-01 specification](challenges/mt-01-digital-footprints/docs/MT01_SPECIFICATION.md)
- [MT-02 specification](challenges/mt-02-amended-contact-sheet/docs/MT02_SPECIFICATION.md)
- [MT-03 specification](challenges/mt-03-dispatch-window/docs/MT03_SPECIFICATION.md)
- [MT-04 specification](challenges/mt-04-release-register-exception/docs/MT04_SPECIFICATION.md)
- [MT-05 specification](challenges/mt-05-offset-handover-log/docs/MT05_SPECIFICATION.md)
- [MT-06 specification](challenges/mt-06-reconcile-transfer-ledger/docs/MT06_SPECIFICATION.md)

## Project layout

```text
meridian-transfer/
|-- challenges/             Six challenge directories
|   `-- <stage>/
|       |-- author/         Builders, solvers and release checks
|       |-- docs/           Specifications and stage status
|       |-- public/         Participant evidence, where applicable
|       |-- private/        Generated answers and author material
|       `-- tests/          Stage tests
|-- platform/               Deployment, integration and functional tests
|   |-- CTFd/               Upstream source and local runtime data
|   |-- plugins/            Challenge-file sign-in guard
|   `-- ui/                 Homepage, styles and navigation
|-- review/                 Independent-review packages and templates
|-- docs/                   Release results and testing scope
`-- .secrets/               Generated credentials, keys and local logs
```

MT-04 also has a `service/` directory for its application, Dockerfile and separate Compose project. Generated directories may be absent before the first build. Keep `private/`, `.secrets/` and runtime data out of participant attachments.

## Requirements

Run deployment commands **inside the Ubuntu 24.04 VM**, from the project root. The helpers use Linux paths, permissions and networking commands.

Required tools:

- Docker Engine and Compose v2 supporting the `!override` YAML tag.
- Docker access for the user running setup, including the separate MT-04 helpers.
- Git, curl, Python 3, Python venv/pip, `sha256sum` and unzip.
- A browser inside the VM for CTFd and the MT-04 portal.
- Internet access during installation to obtain CTFd, images and packages. Static evidence can be solved offline after download.

The recorded author environment used Python 3.12.3. MT-02 requires Pillow 10.2.0. MT-04 host-side tests use its pinned application dependencies; its container installs those separately. Node.js and Playwright are optional for browser regression checks.

## First-time setup

### 1. Check the supplied CTFd source

Setup verifies the official CTFd **3.8.7** release at commit `ba53a21e53d1580f75e5186221563e030b839434`. It clones the release when `platform/CTFd/` is absent.

This downloaded project includes a CTFd source folder without Git metadata. For a **fresh deployment only**, rename that bundled folder so setup can obtain and verify the official release:

```bash
mv platform/CTFd platform/CTFd-packaged-source
```

Skip this step if the folder is absent or already a valid official checkout. Do not rename an existing installation containing platform data; resolve its checkout separately and preserve its data and secrets. The renamed source copy is not needed in the final package once the official checkout is available.

### 2. Prepare the author environment

```bash
python3 -m venv .venv-author
source .venv-author/bin/activate
python3 -m pip install -r challenges/mt-02-amended-contact-sheet/author/requirements.txt
python3 -m pip install -r challenges/mt-04-release-register-exception/service/requirements.txt
docker info
docker compose version
```

Use this activated environment for the build, integration and test commands below.

### 3. Deploy CTFd and MT-01

```bash
python3 platform/setup_local.py
```

This starts CTFd, MariaDB and Redis, builds MT-01, creates the administrator account, applies the UI and runs MT-01 and access checks. **It does not install MT-02 through MT-06.**

The helper supports `--sudo-docker` for its own Docker operations. That option does not apply to the separate MT-04 start/reset helpers, which call Docker directly. Repeat runs reuse the CTFd image; add `--rebuild` after changing the CTFd source.

Do not copy the existing `.secrets/` directory or CTFd runtime data to the new PC, so a fresh installation creates new admin credentials. After setup, find them in `.secrets/ctfd_admin_credentials.txt` within the project folder on the new PC. Repeat setup runs on the same installation retain its existing credentials.

The platform key is stored in `.secrets/ctfd.env`, with a fallback at `platform/CTFd/.ctfd_secret_key`. These files and the administrator credentials have mode 600. Keep them with the deployment and out of shared logs.

### 4. Build and register the remaining stages

Run these commands in order:

```bash
python3 challenges/mt-02-amended-contact-sheet/author/build_mt02.py
python3 platform/setup_mt02.py

python3 challenges/mt-03-dispatch-window/author/build_mt03.py
python3 platform/setup_mt03.py

python3 challenges/mt-04-release-register-exception/author/build_mt04.py
python3 platform/start_mt04.py
python3 platform/setup_mt04.py

python3 challenges/mt-05-offset-handover-log/author/build_mt05.py
python3 platform/setup_mt05.py

python3 challenges/mt-06-reconcile-transfer-ledger/author/build_mt06.py
python3 platform/setup_mt06.py
```

Builders recreate deterministic evidence and private answer files. Integration helpers configure the stages through the authenticated CTFd API and upload participant files. Matching challenges are updated in place, preserving solve records.

### 5. Check the deployment

```bash
docker compose -f platform/CTFd/docker-compose.yml -f platform/CTFd/compose.override.yaml ps
docker compose -f challenges/mt-04-release-register-exception/service/compose.yml ps
curl -fsS http://127.0.0.1:8000/ -o /dev/null
curl -fsS http://127.0.0.1:8084/healthz
```

Open CTFd in the VM browser and confirm all six challenges are listed after participant login. The MT-04 health endpoint should return `ok`.

## Running the box

| Service | URL inside the VM | Purpose |
|---|---|---|
| CTFd | `http://127.0.0.1:8000` | Registration, downloads, hints, flags and scoreboard |
| MT-04 portal | `http://127.0.0.1:8084` | Intentionally vulnerable challenge application |

Create a participant account at `/register`, then sign in and open `/challenges`. Use a private window or sign out first when the current session belongs to the administrator. The MT-04 training credentials appear in its signed-in challenge description.

Challenge pages, APIs, attachments and submissions require a signed-in session. The homepage and registration remain public. Administrator pages and protected APIs enforce server-side role checks.

Stop both stacks while keeping their data:

```bash
docker compose -f challenges/mt-04-release-register-exception/service/compose.yml stop
docker compose -f platform/CTFd/docker-compose.yml -f platform/CTFd/compose.override.yaml stop
```

Start an already configured deployment:

```bash
docker compose -f platform/CTFd/docker-compose.yml -f platform/CTFd/compose.override.yaml up -d ctfd
docker compose -f challenges/mt-04-release-register-exception/service/compose.yml up -d --no-build
```

CTFd also binds to the first private VM IPv4 address found during setup. Its VM URL is recorded in `BUILD_STATUS_MT01.txt`. Host-browser access depends on VM networking; setup does not create VirtualBox forwarding rules. MT-04 remains loopback-only by default, so browsing inside the VM provides access to both services.

## Reset and recovery

### Static evidence: MT-01, MT-02, MT-03, MT-05 and MT-06

These stages do not change server-side evidence during a solve. Participants can discard working copies and download the original attachments again.

As the operator, rebuild a stage with its builder and matching integration helper. For example:

```bash
python3 challenges/mt-02-amended-contact-sheet/author/build_mt02.py
python3 platform/setup_mt02.py
(cd challenges/mt-02-amended-contact-sheet/public && sha256sum -c SHA256SUMS)
```

Use the equivalent builder/setup pair for the other static stages. Check each public manifest from its own directory. For MT-05/06, also verify the inner manifest after extraction, following the participant README. Demonstrate corruption on a temporary working copy and compare rebuilt evidence with the baseline. Archive byte reproducibility depends on the recorded toolchain.

### MT-04 portal

With the portal running and the author environment activated:

```bash
python3 platform/reset_mt04.py
```

This rebuilds the seed and image, rotates the portal session secret, recreates only the MT-04 container and checks that old sessions are invalid. It preserves the flag, training credentials, CTFd configuration and participant solves.

Stage recovery keeps scoring history. The procedures above restore stage evidence and the MT-04 service while preserving platform data. Do not delete `platform/CTFd/.data/`, `.secrets/`, challenges or solve records as part of a stage reset.

## Testing

The latest documented automated release run is **24 September 2026**. Its [release results](docs/AUTOMATED_RELEASE_STATUS.md) record **209/209 stage unit and live checks passing**, a six-stage participant flow worth 1,400 points and desktop/mobile browser regression checks. These are recorded results from that environment, not a new test run of this downloaded copy.

| Stage | Recorded unit/live checks |
|---|---:|
| MT-01 | 18/18 |
| MT-02 | 20/20 |
| MT-03 | 28/28 |
| MT-04 | 24/24 unit + 9/9 live |
| MT-05 | 40/40 |
| MT-06 | 70/70 |

The recorded checks cover intended solutions, wrong/malformed flags, correct submissions, duplicate scoring, downloads, deterministic builds, unintended-answer leakage and stage recovery. MT-05/06 also use two separately implemented reference solvers.

Repeat participant checks against the running deployment:

```bash
python3 platform/test_mt01_functional.py
python3 platform/test_mt02_functional.py
python3 platform/test_mt03_functional.py
python3 platform/test_mt04_functional.py
python3 platform/test_mt05_functional.py
python3 platform/test_mt06_functional.py
python3 platform/test_access_registration.py
python3 platform/test_challenge_signin.py
```

Functional checks create synthetic participants and preserve their solves; test accounts are hidden from the scoreboard. Stage-specific unit, solver and release-check commands are in the specifications. Solver output can reveal answers, so retain it in operator-only logs.

Optional browser checks:

```bash
npm install --prefix .secrets/ui-browser playwright
PLAYWRIGHT_BROWSERS_PATH="$PWD/.secrets/ui-browser/browsers" .secrets/ui-browser/node_modules/.bin/playwright install --with-deps chromium
node platform/test_ui_browser.cjs
```

See the [testing scope](docs/TESTING_STATUS.md) for the boundaries of the recorded automated checks. The results above cover stage functionality, participant flow and stage recovery.

## Architecture and isolation

CTFd has its own Compose project with MariaDB and Redis on an internal network. Database/cache ports are not published. The deployment override disables upstream Nginx and limits CTFd HTTP bindings to loopback and one private VM address.

MT-04 runs on a separate Docker bridge as UID/GID 10001, with a read-only filesystem, dropped capabilities and no Docker socket. Its limits are 256 MiB memory, 0.5 CPU, 64 processes and a 32 MiB temporary filesystem. These limits apply to the MT-04 container.

The intentionally vulnerable route is MT-04's authenticated export endpoint, which omits object ownership validation. The ordinary record route checks ownership. Other stages use static evidence and do not execute participant code on the server.

Recorded network checks blocked direct access from MT-04 to CTFd database/cache container addresses. The MT-04 bridge allows outbound Internet traffic and access to CTFd through its private host binding. The [security boundary document](challenges/mt-04-release-register-exception/docs/MT04_SECURITY_BOUNDARY.md) describes this network scope and the host firewall controls for restricting those paths.

CTFd logs and uploads are under `platform/CTFd/.data/CTFd/`. MT-04 writes Gunicorn access/error logs to container output. Protected diagnostics and functional results are stored in `.secrets/`.

## Member responsibilities and source code

The table below maps project responsibilities to the relevant source files. Stage documents assign MT-02/03 to Member 02 and MT-04/05/06 to Member 03.

| Member | Responsibility | Relevant contribution evidence |
|---|---|---|
| Member 01 | Platform and architecture | `platform/setup_local.py`, `setup_mt01.py`, Compose configuration, UI and sign-in guard |
| Member 02 | Challenge design A | MT-02/03 builders, extractor/solver and tests |
| Member 03 | Challenge design B | MT-04/05/06 builders, proof of concept, solvers and tests |
| Member 04 | Integration, testing and documentation | Functional/access/browser tests, release results and independent-review evidence |

Contribution evidence belongs with the original repository history, configuration changes and test logs identifying each member's work.

| Stage | Builder | Solver or exploitation code |
|---|---|---|
| MT-01 | [build_mt01.py](challenges/mt-01-digital-footprints/author/build_mt01.py) | [reference_solver.py](challenges/mt-01-digital-footprints/author/reference_solver.py) |
| MT-02 | [build_mt02.py](challenges/mt-02-amended-contact-sheet/author/build_mt02.py) | [reference_extractor.py](challenges/mt-02-amended-contact-sheet/author/reference_extractor.py) |
| MT-03 | [build_mt03.py](challenges/mt-03-dispatch-window/author/build_mt03.py) | [reference_solver.py](challenges/mt-03-dispatch-window/author/reference_solver.py) |
| MT-04 | [build_mt04.py](challenges/mt-04-release-register-exception/author/build_mt04.py) | [reference_poc.py](challenges/mt-04-release-register-exception/author/reference_poc.py) |
| MT-05 | [build_mt05.py](challenges/mt-05-offset-handover-log/author/build_mt05.py) | [reference_solver.py](challenges/mt-05-offset-handover-log/author/reference_solver.py), [independent solver](challenges/mt-05-offset-handover-log/author/independent_reference_solver.py) |
| MT-06 | [build_mt06.py](challenges/mt-06-reconcile-transfer-ledger/author/build_mt06.py) | [reference_solver.py](challenges/mt-06-reconcile-transfer-ledger/author/reference_solver.py), [independent solver](challenges/mt-06-reconcile-transfer-ledger/author/independent_reference_solver.py) |

## Acknowledgements

| External tool or framework | Use and version reference |
|---|---|
| [CTFd](https://github.com/CTFd/CTFd) | Official platform release 3.8.7; see the [version record](platform/CTFD_VERSION.txt) and [upstream license](platform/CTFd/LICENSE). |
| [Docker Engine and Compose](https://docs.docker.com/compose/) | Deployment and networking. The upstream Compose stack uses MariaDB 10.11, Redis 4 and Alpine 3.23; Nginx is disabled locally. |
| [Ubuntu](https://ubuntu.com/) and [VirtualBox](https://www.virtualbox.org/) | Recorded operating system and VM environment. |
| [Python](https://www.python.org/) | Builders, solvers, integration and tests. MT-04 pins a Python 3.12.12 slim-bookworm image by digest. |
| [Pillow](https://python-pillow.org/) | MT-02 synthetic PNG generation and extraction, pinned to 10.2.0. |
| [Flask](https://flask.palletsprojects.com/), [Werkzeug](https://werkzeug.palletsprojects.com/) and [Gunicorn](https://gunicorn.org/) | MT-04 stack; exact pins are in its [requirements](challenges/mt-04-release-register-exception/service/requirements.txt). |
| [SQLite](https://www.sqlite.org/) | MT-04 seed database and MT-05 synthetic browser-history evidence. |
| [Node.js](https://nodejs.org/) and [Playwright](https://playwright.dev/) | Optional browser regression checks. |

Specifications also identify optional inspection tools such as ExifTool, jq and Burp Suite Community Edition. Challenge text, images and datasets are generated locally from synthetic sources. No real contributor records or external targets are needed to solve the stages. Keep upstream license notices with submitted source.
