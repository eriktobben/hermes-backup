# Remote macOS Storage Diagnostics

Systematic approach for diagnosing external storage issues on Tobben's smooth-fire Mac Mini (or similar remote macOS machines) over SSH.

## Quick Checks

```bash
# List all disks
diskutil list

# Show external-only (quick check)
diskutil list external

# Check all mounted volumes
ls -la /Volumes/
```

### ⚠️ `diskutil list` hangs

If `diskutil list` or `diskutil info` hangs indefinitely, a disk is connected but in a problematic state (unresponsive FW/TB device, locked encryption, or partition table read failure).

**Workaround** — probe individual disks from `/dev/`:

```bash
# See what device nodes exist
ls -la /dev/disk*

# Query individual disks (won't hang if that specific disk is OK)
diskutil info disk2
diskutil info disk3
# etc.
```

Alternative — ioreg doesn't block:

```bash
ioreg -c IOMedia -r -w0 | grep -E '"BSD Name"|"Size"'
```

## Check Physical Connectivity

### Thunderbolt chain (if storage is Thunderbolt/DisplayPort)

```bash
# Check Thunderbolt adapter is connected
ioreg -c IOMedia -r | grep -A5 "Product Name\|Model Name" | grep -i thunderbolt

# Full Thunderbolt chain
ioreg -l | grep -B2 -A10 "Thunderbolt"
```

### FireWire chain (if via Thunderbolt→FireWire adapter)

```bash
# Is the FireWire controller active?
ioreg -c AppleFWOHCI

# Is any FireWire device actually connected?
ioreg -c IOFireWireDevice
# If this returns NO IOFireWireDevice entries, nothing is plugged in
# even though IOFireWireController + IOFireWireLocalNode are active

# FireWire bus state
ioreg -c IOFireWireController
```

### USB devices

```bash
system_profiler SPUSBDataType
```

### SATA / internal only

```bash
system_profiler SPSerialATADataType
```

## Check RAID Software

### AppleRAID (built-in)

```bash
diskutil appleRAID list
```

### SoftRAID (OWC)

```bash
# Check kext is loaded
kextstat | grep -i raid

# Check if SoftRAID is installed
ls -la /Library/Extensions/SoftRAID.kext/
ls -la /Applications/ | grep -i softraid

# Staged extensions (pending install)
find /Library/StagedExtensions -name "*SoftRAID*" 2>/dev/null
```

**Note**: SoftRAID.kext being loaded ≠ SoftRAID app being installed. The kext can be present without the user-space tools. Without the app, RAID volumes won't mount automatically.

### CoreStorage (legacy Apple)

```bash
diskutil cs list
```

### APFS / FileVault

```bash
diskutil apfs list
```

### Hardware RAID identification

External RAID enclosures (IcyBox, LaCie, etc.) may show up with a generic `Device / Media Name: H/W` in `diskutil info`. This means the enclosure handles RAID at the hardware level — the Mac sees only the combined logical volume, not individual disks.

```bash
diskutil info diskX | grep -E "Device / Media Name|RAID"
```

For hardware RAID enclosures, the RAID set info may show under `diskutil info`:

```bash
# Look for "This disk is a RAID Set" section
diskutil info diskX | grep -A10 "RAID Set"
```

## System Logs

```bash
# General storage logs
log show --last 2h --style compact 2>&1 | grep -iE "disk|IOMedia" | tail -20

# FireWire-specific
log show --last 2h --style compact 2>&1 | grep -iE "firewire|FWOHCI"

# Thunderbolt-specific
log show --last 2h --style compact 2>&1 | grep -iE "thunderbolt"
```

## SoftRAID-Specific

SoftRAID is OWC (Other World Computing) software RAID for macOS. Key facts:
- Kernel extension: `/Library/Extensions/SoftRAID.kext`
- Staged during install: `/Library/StagedExtensions/Library/Extensions/SoftRAID.kext`
- App (if installed): `/Applications/SoftRAID.app`
- No standard CLI tools — requires the GUI app for RAID management
- SoftRAID volumes need the app to be running for automatic mounting after reboot

## Common Failure Patterns

| Symptom | Likely Cause |
|---------|-------------|
| No device on FireWire bus | Cable loose, enclosure powered off, or hardware failure |
| Thunderbolt adapter visible, no device | Same — physical connection issue |
| SoftRAID.kext loaded, no volumes | App not installed or not running |
| Disk visible but not mounting | Encryption locked (FileVault/disk password) |
| `ERROR -69808` shown as volume name | **APFS volume is FileVault-encrypted and locked** — needs password to unlock |
| No disk at all on any bus | Power supply failure on enclosure |

## Encrypted APFS Volume Recovery

When an external APFS volume shows `ERROR -69808` as its name and `FileVault: Yes (Locked)`:

1. Find the volume identifier:
   ```bash
   diskutil apfs list
   # Look for:  FileVault: Yes (Locked)
   ```

2. Unlock with the volume password:
   ```bash
   diskutil apfs unlockVolume diskXsY -passphrase <password>
   ```

3. If successful, the volume will mount under `/Volumes/<name>`.

4. To make it auto-mount on future reboots, unlock once and the password is stored in the system Keychain (macOS prompts for this).

## Physical Checklist (for the user)

1. Check cables — Thunderbolt at Mac end, FireWire at both ends
2. Verify enclosure has power — look for LED indicators
3. Power cycle the enclosure (unplug 10s, plug back in)
4. Try reseating the Thunderbolt adapter at the Mac
5. If still nothing, try a different FireWire cable or port
