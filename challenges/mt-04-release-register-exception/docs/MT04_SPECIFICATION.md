# MT-04 specification

| Field | Assignment |
|---|---|
| Stage ID & Title | MT-04 – Release Register Exception |
| Domain | Web Security |
| Difficulty | Moderate |
| Difficulty justification | Requires authenticated request inspection, an in-scope target clue, a normal-versus-export comparison, and object-level authorization reasoning; estimated 25–35 minutes. |
| Scenario | The fictional Meridian release portal lists a training account's assigned records. A legacy export operation checks login but omits ownership verification. |
| Learning Objective | Distinguish authentication from authorization, inspect session cookies and record IDs, identify IDOR, replay one scoped authenticated request, and explain the missing ownership check. |
| Challenge Environment | Separate Flask/Gunicorn container at local loopback port 8084; immutable synthetic SQLite seed; existing CTFd 3.8.7 at port 8000 holds scoring only. |
| Player Task | Log in with issued synthetic credentials, inspect an owned record/export, identify the related restricted record from the dashboard, compare normal and export routes, recover the restricted export flag. |
| Flag Location / Logic | Exactly one MT-04 flag occurs in the intended restricted record's export-only field. It is not in static files, templates, login page, own records or normal cross-owner responses. |
| Required Tools | Browser and developer tools; optional Burp Community, curl or short Python HTTP client. |
| Dependencies | Flask 3.1.1, Werkzeug 3.1.3, Gunicorn 23.0.0, SQLite, separate Docker Compose stack; exact Python package pins in service/requirements.txt. |
| Expected Solution Path | Follow participant index clue to related record ID; own record works; normal cross-owner route returns 404; authenticated export of target ID succeeds because ownership is omitted. |
| Validation | 24 unit tests, 9 live HTTP tests, scoped reference PoC, fixed-variant comparison, CTFd wrong/correct/duplicate participant test, 3 reset cycles, browser regression, Docker/network checks. |
| Hints | Two free hints: compare normal view and export request; login proves identity, not ownership. |
| Reset / Recovery | Rebuild deterministic seed/image, rotate challenge session secret, recreate only MT-04 container. Preserve CTFd and all solves. Three cycles tested. |
| Expected Skills | Cookies/sessions, HTTP requests, IDOR, object ownership checks, controlled local proof of concept. |
| Responsible Member | Member 03 |
| Reviewer | Member 02 |
| Integration/Security Reviewer | Member 04 / Member 01 |
| Implementation Status | IMPLEMENTED BUT NOT VERIFIED — technical tests pass; independent Member 02 review pending. Outbound egress is PARTIAL pending operator-reviewed firewall control. |
