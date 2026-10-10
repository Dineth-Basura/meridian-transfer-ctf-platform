# MT-04 security boundary

## Verified controls

- **Application separation:** MT-04 is a separate Compose project and container. It has no CTFd database, cache, application-network, SSH, Docker-socket or host-secret mount. Docker inspection found zero mounts and one network member (the portal).
- **Identity and filesystem:** container runs as UID/GID 10001, with a read-only root filesystem. Only `/tmp` is writable through a 32 MiB tmpfs. SQLite seed is copied into the image and opened read-only/immutable; participant requests do not mutate records.
- **Runtime restrictions:** all Linux capabilities dropped, `no-new-privileges:true`, no privileged mode, no host networking, PID limit 64, memory limit 256 MiB, CPU quota 0.5. Gunicorn serves port 8000 inside the container.
- **Host exposure:** Compose publishes only `127.0.0.1:8084` by default. `MT04_BIND_ADDRESS` is numeric and restricted by the start helper to loopback or an explicitly chosen private-lab address. There is no default `0.0.0.0` binding.
- **Session secret:** stored in `.secrets/mt04_service.env` (mode 600), never in tracked source or Docker image. Flask cookies use HttpOnly and SameSite=Lax; Secure is false for local HTTP and must be enabled behind final HTTPS/TLS. Login and logout forms require a session CSRF token. Reset rotates the secret, invalidating old sessions.
- **Password storage:** deterministic unique salts and PBKDF2-HMAC-SHA256 (260,000 iterations); SQLite stores hashes only. Training credentials are synthetic and kept in ignored private author material and the signed-in CTFd challenge description.
- **Data scope:** users, transfers, IDs and flag are synthetic. The flag is in one restricted export-only value, not static or template content. Export is the sole intentionally missing ownership check; guest export is denied. The fixed variant enforces ownership without adding a participant route.
- **Network tests:** direct TCP attempts from MT-04 to CTFd DB (3306), cache (6379), and CTFd app (8000) **container IPs** did not connect. `/var/run/docker.sock` is absent. CTFd DB/cache ports have no host publishing. A separate test found that the portal **can** connect to CTFd through the VM private host binding `10.0.2.15:8000`; this is a remaining host-routing limitation, not a required challenge dependency.

## Outbound egress: PARTIAL

Attempted TCP connections from the portal to `1.1.1.1:443` and the VM host binding `10.0.2.15:8000` succeeded. The dedicated bridge network isolates MT-04 from CTFd's networks, but it does not block general outbound connections. An `internal: true` Docker network was tried; on this VM it prevented the required host-loopback port publishing, so the service uses a dedicated bridge with loopback host binding. **No host firewall rule was applied automatically.**

### Implementation recommendation – not explicitly specified in the report

Before a final lab deployment requiring strict egress denial, the operator should inspect the current MT-04 subnet with `docker network inspect mt04_release_register_mt04_challenge_net`, then add a Docker-aware `DOCKER-USER` firewall rule that rejects **NEW** forwarded connections sourced from that subnet while allowing established replies to the local published port. Conceptually:

```text
iptables -I DOCKER-USER 1 -s <verified-mt04-subnet> -m conntrack --ctstate NEW -j REJECT
```

Because traffic addressed to a host-owned IP may traverse host `INPUT` rather than `DOCKER-USER`, also review a narrowly scoped `INPUT` rule for packets arriving on the MT-04 bridge and destined for the CTFd host binding at `10.0.2.15:8000`. Review existing `DOCKER-USER`/`INPUT` rules and IPv6 settings first; verify the portal still serves `127.0.0.1:8084`, CTFd remains reachable from its intended clients, and both outbound and container-to-host CTFd tests fail. Persist the rule using the VM's approved firewall mechanism. Do not copy the currently observed subnet (`172.21.0.0/16`) blindly because Docker may allocate another subnet later.

## Remaining limitations

- Outbound egress control and access to the CTFd VM host binding are incomplete until the operator applies and tests narrowly scoped host firewall rules.
- Local HTTP requires `SESSION_COOKIE_SECURE=False`; enable Secure cookies when an HTTPS challenge origin is deployed.
- Default loopback access serves participants browsing inside the VM. A separate private-lab bind requires explicit operator configuration; the service is not exposed publicly by default.
