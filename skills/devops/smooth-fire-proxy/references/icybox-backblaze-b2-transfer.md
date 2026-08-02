# Backblaze Personal → B2 Transfer for Data Recovery

When local disk space is insufficient to download backup data, Backblaze Personal can transfer backup data directly to Backblaze B2 cloud storage. This is a server-side operation — no local disk space needed.

## When to use
- Local disk is full or too small for backup download
- Need to preserve backup data before it expires (Backblaze Personal keeps data 30 days after last disk connection)
- No external disk available for temporary storage

## Cost
- B2 storage: ~$0.006/GB/month (~$24/month for 4TB)
- B2 download: ~$0.01/GB (~$40 for 4TB)
- Transfer from Personal to B2: Free

## Steps
1. Create B2 account at backblaze.com/b2 (same login as Backblaze Personal)
2. Create a B2 bucket (private, nearest region)
3. In Backblaze settings, find "Transfer Backup to B2" option
4. Select the bucket and start transfer
5. Verify files in B2 console after transfer completes

## Important
- Transfer happens on Backblaze servers — no local bandwidth used
- Data remains in B2 as long as account is active and paid
- Delete B2 bucket after data is safely on a new local disk to stop storage charges
