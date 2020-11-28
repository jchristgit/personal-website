---
title: APFS sadness on macOS Big Sur
keywords:
  - apfs
  - macos
date: November 28, 2020
---

My MacBook Air had a 128 GB SD card to expand its storage for quite some time.
I use this partially as a second backup storage in addition to my main server,
but I've also put my Downloads folder there for a long time to save space on
the main drive.

Back when APFS came out, I formatted the SD card with it along with encryption
(with a long password, stored in Keychain). This is where the fun began.

Every once in a while - usually after waking up the MacBook from standby - it
would complain about me not ejecting the card before taking out, even though
the card was slotted in the entire time, with the card no longer mounted. The
regular workaround would be slotting it out and back in, so macOS would mount
it again. The unmounted disk would usually become evident by Safari putting its
downloads folder into my regular home folder.

Recently, I have updated my Mac to the new version, macOS Big Sur, and suddenly
the card was no longer visible in Finder. Experience suggested this was an easy
fix, but the usual workaround of slotting it out and back in again did not work
at all. Reboots did not impress it to mount the card either. On to Disk
Utility.

Disk Utility shows the SD card in the SD card reader device. *"Mount point: Not
activated"* decorates its overview. Easy fix, or so I thought, click on
*"Activate"*. Nothing happens. Great, so let's try with command line:

```sh
$ sudo diskutil mount /dev/disk3s1
Volume on disk3s1 failed to mount
This is an encrypted and locked APFS Volume; use "diskutil apfs unlockVolume"
```

Easy enough:

```sh
$ sudo diskutil apfs unlockVolume /dev/disk3s1
Passphrase:
Maximum passphrase length of 127 from interactive entry exceeded
```

Okay, great. Perhaps some internal password entry buffer. Let's try with piping the password in from the clipboard:

```sh
$ pbpaste | sudo diskutil apfs unlockVolume /dev/disk3s1 -stdinpassphrase
Maximum passphrase length of 127 from stdin exceeded
```

Interesting. Maybe the `-passphrase` argument is more helpful?

```sh
$ sudo diskutil apfs unlockVolume /dev/disk3s1 -passphrase '<long passphrase>'
Maximum passphrase length of 127 from passphrase argument exceeded
```

Excellent. How long is my password, anyways? Python claims 116 characters for
the unicode string. In UTF-8 encoded form, the passphrase is 167 characters
long.

When generating passwords, I usually just slide the password length selector in
KeePassXC to some big amount. I suppose that sometimes, that may be an issue.
Although I'm not quite sure why this would be broken in a new update, at least
I have backups... and will think twice before formatting the next disk with
APFS.
