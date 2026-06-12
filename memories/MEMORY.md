For Laravel projects, follow Laravel conventions and best practices. Prefer Livewire components embedded in Blade views served by controllers; avoid Livewire full-page components unless explicitly requested. Require comprehensive automated tests for bugfixes/features, including both feature and unit tests, and ensure the full test suite passes before reporting completion. Many projects use Norwegian; preserve correct use of Æ, Ø, and Å.
§
Default location for new projects on this machine is /home/erik/Projects/, using the repository name as the folder name.
§
#masterfeed-dev (1511501933180092478) → eriktobben/masterfeed (~/Projects/masterfeed). #masterfeed-scroll → eriktobben/masterfeed-scroll (~/Projects/masterfeed-scroll). Kun feature branches + PR til main — aldri direkte commit. Auto-thread whitelist via plugin i ~/.hermes/plugins/auto-thread-whitelist/.
§
WORKTREE-REGLER: FØR start — sjekk `git worktree list`. Bruk eksisterende hvis det matcher. Ellers: opprett fra main/master, FLYTT til worktree-mappa. ALL koding i worktree. ALDRI i main/master. ALDRI rør andres worktrees/branches.
§
Epost-klassifisering SLM-prosjekt: ~/Projects/epost-klassifisering/. nb-bert-base (norsk BERT, 110 MB) finetunet for 5 kategorier: må_svare, spam, nyhetsbrev, bekreftelse, irrelevant. Kjøres som FastAPI-server (serve.py, :8000) som Laravel kaller internt. Supervisor-konfig + Laravel-kontroller i laravel/ og supervisor.conf. Tren: python train.py. Server: python serve.py.
§
Kimaki: patch worktree etter oppgradering (~/.local/bin/kimaki-patch-worktree). Cleanup cron (ID 3fca63db50fc) kjører 04:00 daglig — sletter worktrees > 14 dager inaktive via kimaki-worktree-cleanup.py.
§
Kimaki-prosjekt embermail: git@github.com:Tobbens-Empire/embermail.git, lokasjon /home/erik/Projects/embermail, Discord-kanal #embermail.
§
here.now publish.sh: trailing slash BUG. Sti UTEN trailing slash, ellers `${f#$TARGET/}` feiler og sender absolutt sti → API feiler. Daily AI brief (f3a42a49fae6, 08:00). FINN bilvarsel (b6d12ab73f07, 09:00) slug summit-lichen-sntr, workdir ~/.hermes/cron/finn-bilvarsel/.