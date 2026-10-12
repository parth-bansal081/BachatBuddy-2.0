# P0-03 - Copy the Setu frontend files (byte for byte)
Owner: HUMAN  (agents must not run this)
Time box: 10 min

## Goal
The 2 Setu frontend files plus 3 generic helper files, identical to the old repo.

## Steps
1. Make sure the old repo is cloned on your computer and untouched.
2. In the new repo folder: `bash scripts/port-setu.sh /path/to/old/BachatBuddy`
3. It must print "copied (identical)" five times and "All files are byte-identical".
4. `git checkout -b task/P0-03 && git add -A && git commit -m "P0-03: copy Setu frontend files unchanged"`

## Acceptance
- Output of step 3 as described. No errors.
- `git diff --stat main..HEAD` lists exactly 5 files.
