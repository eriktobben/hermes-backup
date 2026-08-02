# ICYBOX I/O Error Diagnostics

Diagnostic path for APFS volumes mounted read-only due to hardware I/O errors on FireWire RAID enclosures. Captured from ICYBOX troubleshooting session (2026-08-02).

## Symptoms

- Volume mounts **read-only** (`mount` shows `read-only`)
- Root directory is stat-able but `ls` on the volume **hangs/times out**
- `diskutil list external` **hangs**
- `diskutil info diskXsY` (volume partition) **hangs**, but `diskutil info diskX` (container) works
- `fsck_apfs -n` shows: `fd_dev_read:380: blknum 0x40 size 16, error 5` followed by `error: dev_read(64, 1): Input/output error`
- No errors in kernel log (`log show --predicate 'process == "kernel"'`)

## What this means

The I/O error on `fsck_apfs` means the **APFS container superblock is unreadable** at the block level. This is a **hardware problem**, not just filesystem corruption. On a RAID 0 (stripe) array, a single failing member disk causes I/O errors across the entire logical volume.

## Diagnostic steps (read-only, safe)

### 1. Identify the disk topology

```bash
# Mount status
mount | grep -i <volumename>

# Container and physical store info
diskutil apfs list

# Find which disks are physical vs virtual
for d in disk2 disk3 disk4 disk5 disk6 disk7; do
  echo "=== $d ==="
  diskutil info $d 2>&1 | grep -E 'Device / Media Name|Protocol|Virtual|Disk Size|SMART|RAID'
done
```

### 2. Check individual disks (requires sudo — ask user to run locally)

```bash
# Read test on each physical disk
for d in 2 3 4 6; do
  echo "=== disk$d ==="
  time sudo dd if=/dev/rdisk$d of=/dev/null bs=64k count=1000 2>&1
done
```

A failing disk will show:
- **I/O errors** in dd output
- **Much slower** than siblings (e.g., 10x slower)
- **Hangs** indefinitely

### 3. Check FireWire connection

```bash
# Thunderbolt adapter status
system_profiler SPThunderboltDataType | grep -A5 "FireWire"

# FireWire device tree
ioreg -c IOFireWireDevice | grep "Product Name\|FireWire Speed"
```

### 4. Check system logs

```bash
# Kernel-level disk errors
log show --predicate 'process == "kernel"' --last 48h --style compact 2>&1 | grep -iE 'error|timeout|reset|abort|I/O' | tail -30

# FireWire-specific
log show --last 48h --style compact 2>&1 | grep -iE 'FWOHCI|SBP2|firewire' | tail -20
```

## ⚠️ DO NOT

- **Do NOT** run `fsck_apfs -y` — writing to a disk with hardware errors can worsen corruption
- **Do NOT** unmount/remount repeatedly — can cause further metadata damage
- **Do NOT** format the disk before data is recovered

## Recovery path

1. **Check backup first** — always the safest option
2. **If no backup**: make a disk image with `ddrescue` (not `dd`) — it handles bad blocks gracefully
3. **After data is safe**: diagnose which member disk is failing, replace it, rebuild RAID array
4. **For hardware RAID 0**: if one disk dies, ALL data is lost (no redundancy)

## Hardware RAID 0 identification

The ICYBOX enclosure presents as:
- 4 physical disks visible as separate BSD nodes (e.g., disk2, disk3, disk4, disk6)
- Each marked `Device / Media Name: H/W` and `Virtual: No`
- A RAID set visible on one disk (e.g., disk5) marked `Virtual: Yes` with `Level Type: Stripe`
- An APFS container on top of the RAID set (e.g., disk7)
- One or more APFS volumes on the container (e.g., disk7s2)

Connection chain: Mac → Thunderbolt → Thunderbolt-to-FireWire adapter → FireWire → ICYBOX enclosure → 4× SATA disks in hardware RAID 0
