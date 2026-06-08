#!/usr/bin/env python3
"""
Kimaki Worktree Cleanup Script
===============================
Fjerner worktrees og branches som har vært inaktive i > 14 dager.

Kriterier for "inaktiv" (prioritert):
  1. Siste event i Kimaki session_events > 14 dager siden  (PRIMÆR)
  2. Siste commit på branch > 14 dager siden               (FALLBACK)
  3. Worktree created_at > 14 dager siden                   (FALLBACK)
  4. Orphaned worktree-katalog uten DB-oppføring            (ryddes direkte)

Kilder for "sist aktivitet":
  - Kimaki DB: session_events.timestamp (millisekunder) — alle events fra session-en
  - Git commit-dato (origin branch, så lokal)
  - thread_worktrees.created_at

Cleanup:
  - git worktree remove --force <dir>
  - git branch -D <branch> (lokal)
  - git push origin --delete <branch> (hvis den finnes på origin)
  - Sletter worktree-katalogen hvis den fortsatt eksisterer
  - Oppdaterer status i Kimaki DB til 'cleaned'

Kjøring:
  python3 kimaki-worktree-cleanup.py          # dry-run (rapport uten endringer)
  python3 kimaki-worktree-cleanup.py --apply  # faktisk cleanup
"""

import sqlite3
import os
import subprocess
import sys
import datetime
import shutil

KIMAKI_DB = os.path.expanduser('~/.kimaki/discord-sessions.db')
DAYS_THRESHOLD = 14
NOW = datetime.datetime.now(datetime.timezone.utc)

DRY_RUN = '--apply' not in sys.argv


# ─── Hjelpefunksjoner ─────────────────────────────────────────────────


def info(msg):
    print(f"  ℹ️  {msg}")


def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def action(msg):
    if DRY_RUN:
        print(f"  🔷 [DRY-RUN] {msg}")
    else:
        print(f"  🔷 {msg}")


def run_git(cwd, *args, timeout=30):
    """Kjør git-kommando og returner (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            ['git'] + list(args),
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1


def parse_timestamp(ts_str):
    """Prøv å parse en dato-streng. Returner datetime eller None."""
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
        try:
            dt = datetime.datetime.strptime(ts_str[:19], '%Y-%m-%d %H:%M:%S')
            return dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            pass
    return None


# ─── Session-aktivitet (PRIMÆR KILDE) ──────────────────────────────────


def get_last_session_activity(cur, session_id):
    """
    Finn siste aktivitet i en session via session_events-tabellen.
    Returnerer datetime eller None.
    """
    if not session_id:
        return None

    cur.execute(
        "SELECT MAX(timestamp) FROM session_events WHERE session_id = ?",
        (session_id,)
    )
    row = cur.fetchone()
    if row and row[0]:
        ts_ms = row[0]  # millisekunder Unix timestamp
        try:
            return datetime.datetime.fromtimestamp(ts_ms / 1000, tz=datetime.timezone.utc)
        except (OSError, OverflowError, ValueError):
            pass
    return None


# ─── Git-hjelpemidler ──────────────────────────────────────────────────


def get_last_commit_date(project_dir, branch_name):
    """
    Finn siste commit-dato for en branch.
    Sjekker origin først, så lokal branch.
    Returnerer datetime eller None.
    """
    # Prøv remote branch
    stdout, _, rc = run_git(project_dir, 'log', '-1', '--format=%ci', f'origin/{branch_name}')
    if rc == 0 and stdout:
        try:
            dt = datetime.datetime.strptime(stdout.strip(), '%Y-%m-%d %H:%M:%S %z')
            return dt
        except ValueError:
            pass

    # Prøv lokal branch
    stdout, _, rc = run_git(project_dir, 'log', '-1', '--format=%ci', branch_name)
    if rc == 0 and stdout:
        try:
            dt = datetime.datetime.strptime(stdout.strip(), '%Y-%m-%d %H:%M:%S %z')
            return dt
        except ValueError:
            pass

    return None


def branch_exists_on_origin(project_dir, branch_name):
    """Sjekk om branch finnes på origin."""
    stdout, _, rc = run_git(project_dir, 'ls-remote', '--heads', 'origin', branch_name)
    return rc == 0 and branch_name in stdout


def find_default_branch(project_dir):
    """Finn default branch (main eller master)."""
    for candidate in ['main', 'master']:
        stdout, _, rc = run_git(project_dir, 'rev-parse', f'origin/{candidate}')
        if rc == 0:
            return candidate
    return 'main'  # fallback


def remove_worktree_directory(worktree_dir):
    """Slett worktree-katalogen hvis den finnes."""
    if os.path.exists(worktree_dir):
        try:
            shutil.rmtree(worktree_dir)
            return True
        except Exception as e:
            warn(f"Kunne ikke slette {worktree_dir}: {e}")
            return False
    return False


# ─── Cleanup-logikk ────────────────────────────────────────────────────


def cleanup_worktree(project_dir, worktree_dir, branch_name, reason=""):
    """
    Rydd opp en worktree:
      1. git worktree remove
      2. Slett lokal branch
      3. Slett remote branch (hvis den finnes på origin)
      4. Slett katalogen hvis den fortsatt finnes
    """
    marker = reason if reason else "Ingen aktivitet > 14 dager"
    action(f"Rydder opp: {branch_name}")
    info(f"  Sti: {worktree_dir}")
    info(f"  Årsak: {marker}")

    if DRY_RUN:
        return True

    # 1. Git worktree remove
    _, stderr, rc = run_git(project_dir, 'worktree', 'remove', '--force', worktree_dir)
    if rc != 0:
        warn(f"git worktree remove feilet: {stderr}")

    # 2. Slett lokal branch
    run_git(project_dir, 'branch', '-D', branch_name)

    # 3. Slett remote branch hvis den finnes
    if branch_exists_on_origin(project_dir, branch_name):
        run_git(project_dir, 'push', 'origin', '--delete', branch_name)
        ok(f"Slettet remote branch origin/{branch_name}")

    # 4. Fjern katalogen
    remove_worktree_directory(worktree_dir)

    return True


# ─── Hovedfunksjon ─────────────────────────────────────────────────────


def main():
    print(f"{'='*60}")
    print(f"  KIMAKI WORKTREE CLEANUP")
    print(f"  Terskel: {DAYS_THRESHOLD} dager siden siste aktivitet")
    print(f"  Modus: {'🔍 DRY-RUN (ingen endringer)' if DRY_RUN else '⚡ APPLY (utfører cleanup)'}")
    print(f"  Dato: {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print()

    if not os.path.exists(KIMAKI_DB):
        print(f"❌ Finner ikke Kimaki DB: {KIMAKI_DB}")
        sys.exit(1)

    conn = sqlite3.connect(KIMAKI_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Hent alle worktrees med status 'ready'
    cur.execute("""
        SELECT tw.*, ts.session_id, ts.last_synced_name as session_name
        FROM thread_worktrees tw
        LEFT JOIN thread_sessions ts ON tw.thread_id = ts.thread_id
        WHERE tw.status = 'ready'
        ORDER BY tw.created_at
    """)
    rows = cur.fetchall()

    if not rows:
        print("✅ Ingen worktrees å rydde opp!")
    else:
        print(f"Fant {len(rows)} worktrees med status='ready':")
        print()

    cleaned = 0
    skipped_active = 0
    errors = 0

    for row in rows:
        thread_id = row['thread_id']
        branch_name = row['worktree_name']
        worktree_dir = row['worktree_directory']
        project_dir = row['project_directory']
        created_at_str = row['created_at']
        session_id = row['session_id']
        session_name = row['session_name'] or '(ingen navn)'

        if not worktree_dir or not project_dir:
            info(f"Hopp over {branch_name}: mangler worktree_directory eller project_directory")
            continue

        # Parse created_at
        created_at = parse_timestamp(created_at_str) if created_at_str else None

        worktree_exists = os.path.exists(worktree_dir)
        project_exists = os.path.exists(project_dir)

        print(f"── {branch_name}")
        info(f"  Thread: {thread_id}")
        info(f"  Session: {session_name}")
        info(f"  Opprettet: {created_at_str or 'N/A'}")
        info(f"  Session ID: {session_id or 'N/A'}")
        info(f"  Worktree finnes: {'✅' if worktree_exists else '❌ (allerede borte)'}")
        info(f"  Prosjekt finnes: {'✅' if project_exists else '❌'}")
        info(f"  Mappe: {worktree_dir}")

        # ── Hvis prosjektet ikke finnes ─────────────────────────────
        if not project_exists:
            action("Prosjektmappe finnes ikke — sletter worktree og oppdaterer DB")
            if worktree_exists:
                remove_worktree_directory(worktree_dir)
            if not DRY_RUN:
                cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                conn.commit()
            cleaned += 1
            print()
            continue

        # ── Finn siste aktivitet (3 kilder, prioritert) ────────────
        last_activity = None
        activity_source = ""

        # Kilde 1: Session events (PRIMÆR)
        if session_id:
            dt = get_last_session_activity(cur, session_id)
            if dt:
                last_activity = dt
                activity_source = "siste session-event"

        # Kilde 2: Git commit (FALLBACK)
        if last_activity is None:
            dt = get_last_commit_date(project_dir, branch_name)
            if dt:
                last_activity = dt
                activity_source = "siste git-commit"

        # Kilde 3: created_at (SISTE FALLBACK)
        if last_activity is None and created_at:
            last_activity = created_at
            activity_source = "opprettet-dato"

        # ── Vurder cleanup ─────────────────────────────────────────
        if last_activity:
            days_since = (NOW - last_activity).days
            info(f"  Siste aktivitet ({activity_source}): {last_activity.strftime('%Y-%m-%d %H:%M')} ({days_since} dager siden)")

            if days_since >= DAYS_THRESHOLD or not worktree_exists:
                if not worktree_exists:
                    action(f"Fjerner DB-oppføring (worktree allerede borte, inaktiv i {days_since} dager)")
                    if not DRY_RUN:
                        run_git(project_dir, 'branch', '-D', branch_name)
                        if branch_exists_on_origin(project_dir, branch_name):
                            run_git(project_dir, 'push', 'origin', '--delete', branch_name)
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    cleaned += 1
                else:
                    cleanup_worktree(project_dir, worktree_dir, branch_name,
                                     reason=f"{activity_source}: {days_since} dager siden")
                    if not DRY_RUN:
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    cleaned += 1
            else:
                info(f"  ⏩ Fortsatt aktiv: {days_since} dager siden siste {activity_source} (< {DAYS_THRESHOLD})")
                skipped_active += 1
        else:
            if not worktree_exists:
                # Ingen info, og worktree er borte — bare rydd DB
                action("Fjerner DB-oppføring (worktree finnes ikke, ingen aktivitetsdata)")
                if not DRY_RUN:
                    cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                    conn.commit()
                cleaned += 1
            else:
                info("  ⚠️  Kunne ikke bestemme alder — hopper over")
                errors += 1

        print()

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Orphaned worktree-kataloger (finnes på disk, men ikke i DB)
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  FASE 2: ORPHANED WORKTREE-KATALOGER")
    print(f"{'='*60}")
    print()

    # Bygg sett med kjente worktree-kataloger fra DB
    cur.execute("SELECT worktree_directory FROM thread_worktrees WHERE worktree_directory IS NOT NULL")
    known_dirs = set()
    for r in cur.fetchall():
        d = os.path.realpath(r['worktree_directory']) if r['worktree_directory'] else None
        if d:
            known_dirs.add(d)

    kimaki_worktrees_root = os.path.expanduser('~/.kimaki/worktrees')
    orphaned_count = 0

    if os.path.isdir(kimaki_worktrees_root):
        for project_id in sorted(os.listdir(kimaki_worktrees_root)):
            project_path = os.path.join(kimaki_worktrees_root, project_id)
            if not os.path.isdir(project_path):
                continue
            for wt_name in sorted(os.listdir(project_path)):
                wt_path = os.path.join(project_path, wt_name)
                if not os.path.isdir(wt_path):
                    continue
                real_path = os.path.realpath(wt_path)
                if real_path not in known_dirs:
                    # Sjekk om dette er et git worktree
                    git_file = os.path.join(wt_path, '.git')
                    if os.path.isdir(git_file) or os.path.isfile(git_file):
                        print(f"  🗑️  Orphaned worktree: {wt_path}")
                        action(f"Sletter orphaned worktree: {wt_path}")
                        if not DRY_RUN:
                            # Finn main repo via .git-fila
                            main_repo = None
                            if os.path.isfile(git_file):
                                with open(git_file) as f:
                                    content = f.read().strip()
                                if content.startswith('gitdir: '):
                                    # ../.git/worktrees/<name> → main repo
                                    main_git_dir = content[8:]
                                    if '/.git/worktrees/' in main_git_dir:
                                        main_git_dir = main_git_dir.split('/.git/worktrees/')[0] + '/.git'
                                    else:
                                        main_git_dir = main_git_dir.replace('/worktrees/', '/').rsplit('/', 1)[0]
                                    if main_git_dir:
                                        main_repo = os.path.realpath(os.path.join(wt_path, main_git_dir, '..'))
                            if main_repo and os.path.exists(main_repo):
                                run_git(main_repo, 'worktree', 'remove', '--force', wt_path)
                            remove_worktree_directory(wt_path)
                        orphaned_count += 1

    if orphaned_count == 0:
        print("  ✅ Ingen orphaned worktrees funnet.")
    print()

    # ═══════════════════════════════════════════════════════════════════
    # OPPSUMMERING
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  OPPSUMMERING")
    print(f"{'='*60}")
    print(f"  Ryddet opp:            {cleaned}")
    print(f"  Hoppet over (aktive):  {skipped_active}")
    print(f"  Orphaned kataloger:    {orphaned_count}")
    print(f"  Feil:                  {errors}")
    print()
    if DRY_RUN:
        print("  🔍 Dette var en dry-run. Kjør med --apply for å utføre.")
    else:
        print("  ✅ Cleanup fullført.")

    conn.close()


if __name__ == '__main__':
    main()
