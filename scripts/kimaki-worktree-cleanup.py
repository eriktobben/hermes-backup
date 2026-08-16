#!/usr/bin/env python3
"""
Kimaki Worktree Restore & Cleanup Script
=========================================
Gjenoppretter worktrees som er slettet av OpenCode's snapshot-cleanup,
og rydder opp worktrees som har vært inaktive i > 14 dager.

Kjøring:
  python3 kimaki-worktree-cleanup.py          # dry-run (rapport uten endringer)
  python3 kimaki-worktree-cleanup.py --apply  # faktisk restore/cleanup
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


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    print(f"{'='*60}")
    print(f"  KIMAKI WORKTREE RESTORE & CLEANUP")
    print(f"  terskel: {DAYS_THRESHOLD} dager inaktiv")
    print(f"  modus: {'🔍 DRY-RUN' if DRY_RUN else '⚡ APPLY'}")
    print(f"  dato: {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    if not os.path.exists(KIMAKI_DB):
        print(f"❌ Finner ikke Kimaki DB: {KIMAKI_DB}")
        sys.exit(1)

    conn = sqlite3.connect(KIMAKI_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ═══════════════════════════════════════════════════════════════════
    # FASE 1: Gjenopprett worktrees slettet av OpenCode's GC
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  FASE 1: GJENOPPRETT ARBEIDSOMRÅDER")
    print(f"{'='*60}\n")

    # Hent alle workspaces med status 'ready' fra thread_workspaces
    cur.execute("""
        SELECT ws.*, ts.session_id
        FROM thread_workspaces ws
        LEFT JOIN thread_sessions ts ON ws.thread_id = ts.thread_id
        WHERE ws.status = 'ready'
        ORDER BY ws.created_at
    """)
    rows = cur.fetchall()

    restored = 0
    already_ok = 0
    restore_errors = 0
    skipped_old = 0

    for row in rows:
        thread_id = row['thread_id']
        branch_name = row['workspace_name']
        worktree_dir = row['workspace_directory']
        project_dir = row['project_directory']
        created_at_str = row['created_at']

        if not worktree_dir or not project_dir:
            continue

        worktree_exists = os.path.isdir(worktree_dir)
        project_exists = os.path.isdir(project_dir)

        if worktree_exists:
            already_ok += 1
            continue

        # Hopp over worktrees eldre enn 7 dager (disse bør ryddes, ikke gjenopprettes)
        created_at = parse_timestamp(created_at_str) if created_at_str else None
        if created_at:
            days_old = (NOW - created_at).days
            if days_old > 7:
                skipped_old += 1
                continue

        if not project_exists:
            print(f"  ⚠️  {branch_name}: prosjekt {project_dir} finnes ikke — hopper over")
            restore_errors += 1
            continue

        # Sjekk om git-greinen finnes
        stdout, _, rc = run_git(project_dir, 'branch', '--list', branch_name)
        branch_exists = rc == 0 and branch_name in stdout

        if not branch_exists:
            print(f"  ⚠️  {branch_name}: verken worktree eller branch — hopper over")
            restore_errors += 1
            continue

        # Gjenopprett worktree
        print(f"  🔷 {branch_name}")
        print(f"     prosjekt: {project_dir}")
        print(f"     worktree: {worktree_dir}")

        if not DRY_RUN:
            # Opprett worktree-mappe om den mangler
            os.makedirs(os.path.dirname(worktree_dir), exist_ok=True)

            # Kjør git worktree add
            _, stderr, rc = run_git(
                project_dir,
                'worktree', 'add', worktree_dir, branch_name,
                timeout=60
            )

            if rc == 0:
                print(f"     ✅ Gjenopprettet fra branch '{branch_name}'")
                restored += 1
            else:
                print(f"     ❌ Feil: {stderr}")
                restore_errors += 1
        else:
            print(f"     🔷 [DRY-RUN] Ville gjenopprettet fra branch '{branch_name}'")
            restored += 1

    print(f"\n  Oppsummert: {restored} gjenopprettet, {already_ok} OK, {skipped_old} for gamle, {restore_errors} feil\n")

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Rydd opp inaktive worktrees (>14 dager)
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  FASE 2: RYDD OPP INAKTIVE ARBEIDSOMRÅDER (>14 dager)")
    print(f"{'='*60}\n")

    # Hent på nytt etter gjenoppretting
    cur.execute("""
        SELECT ws.*, ts.session_id
        FROM thread_workspaces ws
        LEFT JOIN thread_sessions ts ON ws.thread_id = ts.thread_id
        WHERE ws.status = 'ready'
        ORDER BY ws.created_at
    """)
    rows = cur.fetchall()

    cleaned = 0
    skipped_active = 0

    for row in rows:
        thread_id = row['thread_id']
        branch_name = row['workspace_name']
        worktree_dir = row['workspace_directory']
        project_dir = row['project_directory']
        created_at_str = row['created_at']
        session_id = row['session_id']

        if not worktree_dir or not project_dir:
            continue

        project_exists = os.path.isdir(project_dir)
        if not project_exists:
            continue

        # Finn siste aktivitet
        last_activity = None

        # Kilde 1: Session events
        if session_id:
            dt = get_last_session_activity(cur, session_id)
            if dt:
                last_activity = dt

        # Kilde 2: Git commit
        if last_activity is None:
            dt = get_last_commit_date(project_dir, branch_name)
            if dt:
                last_activity = dt

        # Kilde 3: created_at
        if last_activity is None and created_at_str:
            last_activity = parse_timestamp(created_at_str)

        if last_activity is None:
            continue

        days_since = (NOW - last_activity).days

        if days_since >= DAYS_THRESHOLD:
            worktree_exists = os.path.isdir(worktree_dir)
            branch_name_stripped = branch_name.split('/')[-1] if '/' in branch_name else branch_name

            print(f"  🗑️  {branch_name} — {days_since} dager inaktiv")
            if not DRY_RUN:
                # Fjern worktree hvis det finnes
                if worktree_exists:
                    run_git(project_dir, 'worktree', 'remove', '--force', worktree_dir)
                    remove_worktree_directory(worktree_dir)

                # Fjern lokal branch
                run_git(project_dir, 'branch', '-D', branch_name_stripped)

                # Fjern remote branch hvis den finnes
                if branch_exists_on_origin(project_dir, branch_name_stripped):
                    run_git(project_dir, 'push', 'origin', '--delete', branch_name_stripped)

                # Oppdater DB
                cur.execute(
                    "UPDATE thread_workspaces SET status = 'cleaned' WHERE thread_id = ?",
                    (thread_id,)
                )
                conn.commit()

                print(f"     ✅ Ryddet opp")
            else:
                print(f"     🔷 [DRY-RUN] Ville ryddet opp")
            cleaned += 1
        else:
            skipped_active += 1

    print(f"\n  Oppsummert: {cleaned} ryddet, {skipped_active} aktive (<{DAYS_THRESHOLD} dager)\n")

    # ═══════════════════════════════════════════════════════════════════
    # FASE 3: Orphaned worktree-kataloger
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  FASE 3: ORPHANED WORKTREE-KATALOGER")
    print(f"{'='*60}\n")

    # Bygg sett med kjente worktree-kataloger fra DB
    cur.execute("SELECT workspace_directory FROM thread_workspaces WHERE workspace_directory IS NOT NULL")
    known_dirs = set()
    for r in cur.fetchall():
        d = os.path.realpath(r['workspace_directory']) if r['workspace_directory'] else None
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
                    git_file = os.path.join(wt_path, '.git')
                    if os.path.isdir(git_file) or os.path.isfile(git_file):
                        print(f"  🗑️  Orphaned: {wt_path}")
                        if not DRY_RUN:
                            remove_worktree_directory(wt_path)
                        orphaned_count += 1

    if orphaned_count == 0:
        print("  ✅ Ingen orphaned worktrees.\n")
    else:
        print()

    # ═══════════════════════════════════════════════════════════════════
    # OPPSUMMERING
    # ═══════════════════════════════════════════════════════════════════
    print(f"{'='*60}")
    print("  OPPSUMMERING")
    print(f"{'='*60}")
    print(f"  Gjenopprettet:     {restored}")
    print(f"  Allerede OK:       {already_ok}")
    print(f"  Ryddet (>14 dag):  {cleaned}")
    print(f"  Orphaned:          {orphaned_count}")
    print(f"  Feil:              {restore_errors + restore_errors}")
    print()
    if DRY_RUN:
        print("  🔍 Dette var en dry-run. Kjør med --apply for å utføre.")
    else:
        print("  ✅ Fullført.")

    conn.close()


if __name__ == '__main__':
    main()
