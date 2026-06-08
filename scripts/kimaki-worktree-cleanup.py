#!/usr/bin/env python3
"""
Kimaki Worktree Cleanup Script
===============================
Fjerner worktrees og branches som har vært inaktive i > 14 dager.

Kriterier for "inaktiv":
  1. Siste commit på branch (sjekker origin først, så lokal) er > 14 dager siden
  2. ELLER worktree ble opprettet > 14 dager siden og har ingen ekstra commits
  3. ELLER branch finnes ikke (orphaned worktree directory)

Cleanup:
  - git worktree remove --force <dir>
  - git branch -D <branch> (lokal)
  - git push origin --delete <branch> (hvis den finnes på origin)
  - Sletter worktree-mappa hvis den fortsatt eksisterer
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
from pathlib import Path

KIMAKI_DB = os.path.expanduser('~/.kimaki/discord-sessions.db')
DAYS_THRESHOLD = 14
NOW = datetime.datetime.now(datetime.timezone.utc)

DRY_RUN = '--apply' not in sys.argv


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


def get_last_commit_date(project_dir, branch_name):
    """
    Finn siste commit-dato for en branch.
    Sjekker origin først, så lokal branch.
    Returnerer datetime eller None.
    """
    # Prøv remote branch
    stdout, stderr, rc = run_git(project_dir, 'log', '-1', '--format=%ci', f'origin/{branch_name}')
    if rc == 0 and stdout:
        try:
            return datetime.datetime.strptime(stdout.strip(), '%Y-%m-%d %H:%M:%S %z')
        except ValueError:
            pass

    # Prøv lokal branch
    stdout, stderr, rc = run_git(project_dir, 'log', '-1', '--format=%ci', branch_name)
    if rc == 0 and stdout:
        try:
            return datetime.datetime.strptime(stdout.strip(), '%Y-%m-%d %H:%M:%S %z')
        except ValueError:
            pass

    return None


def branch_exists_on_origin(project_dir, branch_name):
    """Sjekk om branch finnes på origin."""
    stdout, _, rc = run_git(project_dir, 'ls-remote', '--heads', 'origin', branch_name)
    return rc == 0 and branch_name in stdout


def branch_is_merged(project_dir, branch_name, default_branch='main'):
    """Sjekk om branch er merget til default branch."""
    stdout, _, rc = run_git(project_dir, 'branch', '--merged', f'origin/{default_branch}')
    if rc == 0:
        return branch_name in stdout
    return False


def find_default_branch(project_dir):
    """Finn default branch (main eller master)."""
    for candidate in ['main', 'master']:
        stdout, _, rc = run_git(project_dir, 'rev-parse', f'origin/{candidate}')
        if rc == 0:
            return candidate
    return 'main'  # fallback


def remove_worktree_directory(worktree_dir):
    """Slett worktree-mappa hvis den finnes."""
    if os.path.exists(worktree_dir):
        try:
            shutil.rmtree(worktree_dir)
            return True
        except Exception as e:
            warn(f"Kunne ikke slette {worktree_dir}: {e}")
            return False
    return False


def is_orphaned_worktree_dir(worktree_dir, known_dirs):
    """Sjekk om en mappe er en worktree som ikke er i DB."""
    path = os.path.realpath(worktree_dir)
    return path not in known_dirs


def cleanup_worktree(project_dir, worktree_dir, branch_name, reason=""):
    """
    Rydd opp en worktree:
      1. git worktree remove
      2. Slett lokal branch
      3. Slett remote branch (hvis den finnes på origin)
      4. Slett mappa hvis den fortsatt finnes
    """
    marker = reason if reason else "ingen aktivitet > 14 dager"
    action(f"Rydder opp: {branch_name}")
    info(f"  Sti: {worktree_dir}")
    info(f"  Årsak: {marker}")

    if DRY_RUN:
        return True

    # 1. Git worktree remove
    stdout, stderr, rc = run_git(project_dir, 'worktree', 'remove', '--force', worktree_dir)
    if rc != 0:
        warn(f"git worktree remove feilet: {stderr}")

    # 2. Slett lokal branch
    run_git(project_dir, 'branch', '-D', branch_name)

    # 3. Slett remote branch hvis den finnes
    if branch_exists_on_origin(project_dir, branch_name):
        run_git(project_dir, 'push', 'origin', '--delete', branch_name)
        ok(f"Slettet remote branch origin/{branch_name}")

    # 4. Fjern mappa
    remove_worktree_directory(worktree_dir)

    return True


def main():
    print(f"{'='*60}")
    print(f"  KIMAKI WORKTREE CLEANUP")
    print(f"  Terskel: {DAYS_THRESHOLD} dager siden siste aktivitet")
    print(f"  Modus: {'🔍 DRY-RUN (ingen endringer)' if DRY_RUN else '⚡ APPLY (utfører cleanup)'}")
    print(f"  Dato: {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print()

    # Sjekk at DB finnes
    if not os.path.exists(KIMAKI_DB):
        print(f"❌ Finner ikke Kimaki DB: {KIMAKI_DB}")
        sys.exit(1)

    # Koble til Kimaki DB
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
        return

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
        session_name = row['session_name'] or '(ingen navn)'

        if not worktree_dir or not project_dir:
            info(f"Hopp over {branch_name}: mangler worktree_directory eller project_directory")
            continue

        # Parse created_at
        try:
            created_at = datetime.datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            created_at = created_at.replace(tzinfo=datetime.timezone.utc)
        except (ValueError, TypeError):
            created_at = None

        # Sjekk om worktree-mappa faktisk finnes
        worktree_exists = os.path.exists(worktree_dir)

        # Sjekk om prosjektet finnes
        project_exists = os.path.exists(project_dir)

        print(f"── {branch_name}")
        info(f"  Thread: {thread_id}")
        info(f"  Session: {session_name}")
        info(f"  Opprettet: {created_at_str}")
        info(f"  Worktree finnes: {'✅' if worktree_exists else '❌ (allerede borte)'}")
        info(f"  Prosjekt finnes: {'✅' if project_exists else '❌'}")
        info(f"  Mappe: {worktree_dir}")

        if not project_exists:
            # Hvis prosjektet ikke finnes, kan vi bare slette mappa og oppdatere DB
            action(f"Prosjektmappe finnes ikke — sletter worktree og oppdaterer DB")
            if worktree_exists:
                remove_worktree_directory(worktree_dir)
            if not DRY_RUN:
                cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                conn.commit()
            cleaned += 1
            print()
            continue

        # Finn default branch
        default_branch = find_default_branch(project_dir)

        # Sjekk siste aktivitet på branch
        last_commit_date = get_last_commit_date(project_dir, branch_name)

        if last_commit_date:
            days_since_commit = (NOW - last_commit_date).days
            info(f"  Siste commit: {last_commit_date.strftime('%Y-%m-%d %H:%M')} ({days_since_commit} dager siden)")

            if days_since_commit >= DAYS_THRESHOLD:
                # Stødig cleanup
                is_merged = branch_is_merged(project_dir, branch_name, default_branch)
                if not worktree_exists:
                    # Worktree allerede borte — bare rydd branches + DB
                    if not DRY_RUN:
                        run_git(project_dir, 'branch', '-D', branch_name)
                        if branch_exists_on_origin(project_dir, branch_name):
                            run_git(project_dir, 'push', 'origin', '--delete', branch_name)
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    action(f"Fjerner branch (worktree allerede borte)")
                    cleaned += 1
                else:
                    cleanup_worktree(project_dir, worktree_dir, branch_name,
                                     reason=f"Siste commit {days_since_commit} dager siden")
                    if not DRY_RUN:
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    cleaned += 1
            else:
                info(f"  ⏩ Aktiv: siste commit er {days_since_commit} dager siden (< {DAYS_THRESHOLD})")
                skipped_active += 1

        elif created_at:
            # Ingen commits — bruk created_at
            days_since_created = (NOW - created_at).days
            info(f"  Ingen commits funnet — bruker opprettet-dato: {days_since_created} dager siden")

            if days_since_created >= DAYS_THRESHOLD or not worktree_exists:
                if not worktree_exists:
                    action(f"Worktree finnes ikke — oppdaterer DB-status")
                    if not DRY_RUN:
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    cleaned += 1
                else:
                    cleanup_worktree(project_dir, worktree_dir, branch_name,
                                     reason=f"Ingen commits, opprettet {days_since_created} dager siden")
                    if not DRY_RUN:
                        cur.execute("UPDATE thread_worktrees SET status = 'cleaned' WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                    cleaned += 1
            else:
                info(f"  ⏩ For ny (opprettet {days_since_created} dager siden)")
                skipped_active += 1
        else:
            info(f"  ⚠️  Kunne ikke bestemme alder — hopper over")
            errors += 1

        print()

    # === Fase 2: Se etter orphaned worktree-kataloger ===
    print(f"{'='*60}")
    print("  FASE 2: ORPHANED WORKTREE-KATALOGER")
    print(f"{'='*60}")
    print()

    # Bygg sett med kjente worktree-kataloger
    cur.execute("SELECT worktree_directory FROM thread_worktrees WHERE worktree_directory IS NOT NULL")
    known_dirs = set()
    for r in cur.fetchall():
        d = os.path.realpath(r['worktree_directory']) if r['worktree_directory'] else None
        if d:
            known_dirs.add(d)

    kimaki_worktrees_root = os.path.expanduser('~/.kimaki/worktrees')
    orphaned_count = 0

    if os.path.isdir(kimaki_worktrees_root):
        for project_id in os.listdir(kimaki_worktrees_root):
            project_path = os.path.join(kimaki_worktrees_root, project_id)
            if not os.path.isdir(project_path):
                continue
            for wt_name in os.listdir(project_path):
                wt_path = os.path.join(project_path, wt_name)
                if not os.path.isdir(wt_path):
                    continue
                real_path = os.path.realpath(wt_path)
                if real_path not in known_dirs:
                    # Sjekk om dette er et git worktree
                    git_dir = os.path.join(wt_path, '.git')
                    if os.path.isdir(git_dir) or os.path.isfile(git_dir):
                        print(f"  🗑️  Orphaned worktree: {wt_path}")
                        action(f"Sletter orphaned worktree: {wt_path}")
                        if not DRY_RUN:
                            # Prøv git worktree remove først
                            # Finn main repo fra .git-fila
                            gitfile_path = os.path.join(wt_path, '.git')
                            main_repo = None
                            if os.path.isfile(gitfile_path):
                                with open(gitfile_path) as f:
                                    content = f.read().strip()
                                if content.startswith('gitdir: '):
                                    main_git_dir = content[8:].replace('/.git/worktrees/', '/').rsplit('/worktrees/', 1)[0]
                                    if main_git_dir:
                                        main_repo = os.path.dirname(main_git_dir)
                            if main_repo and os.path.exists(main_repo):
                                run_git(main_repo, 'worktree', 'remove', '--force', wt_path)
                            remove_worktree_directory(wt_path)
                        orphaned_count += 1

    if orphaned_count == 0:
        print("  ✅ Ingen orphaned worktrees funnet.")
    print()

    # === Oppsummering ===
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
