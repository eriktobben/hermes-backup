For Laravel projects, follow Laravel conventions and best practices. Prefer Livewire components embedded in Blade views served by controllers; avoid Livewire full-page components unless explicitly requested. Require comprehensive automated tests for bugfixes/features, including both feature and unit tests, and ensure the full test suite passes before reporting completion. Many projects use Norwegian; preserve correct use of Æ, Ø, and Å.
§
Default location for new projects on this machine is /home/erik/Projects/, using the repository name as the folder name.
§
Discord channel '#serena' (Tobben MC) is mapped to project Serena Home with local repo path /home/erik/Projects/serenahome and GitHub remote https://github.com/Serena-AS/SerenaHome.
§
Serena-prosjektet: Kun feature branches + PR. Aldri direkte commit til main med mindre eksplisitt bedt om det. Solo-prosjekt.
§
#serena-dev (1511404097302171818) → Serena-AS/SerenaHome. #masterfeed-dev (1511501933180092478) → eriktobben/masterfeed. Auto-thread whitelist styres via plugin i ~/.hermes/plugins/auto-thread-whitelist/.
§
WORKTREE-REGLER: FØR start — sjekk `git worktree list`. Bruk eksisterende hvis det matcher. Ellers: opprett fra main/master, FLYTT til worktree-mappa. ALL koding i worktree. ALDRI i main/master. ALDRI rør andres worktrees/branches.
§
Epost-klassifisering SLM-prosjekt: ~/Projects/epost-klassifisering/. nb-bert-base (norsk BERT, 110 MB) finetunet for 5 kategorier: må_svare, spam, nyhetsbrev, bekreftelse, irrelevant. Kjøres som FastAPI-server (serve.py, :8000) som Laravel kaller internt. Supervisor-konfig + Laravel-kontroller i laravel/ og supervisor.conf. Tren: python train.py. Server: python serve.py.
§
Kimaki: patch worktree etter oppgradering (~/.local/bin/kimaki-patch-worktree). Cleanup cron (ID 3fca63db50fc) kjører 04:00 daglig — sletter worktrees > 14 dager inaktive via kimaki-worktree-cleanup.py.