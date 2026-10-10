#!/bin/sh
# Start (or resume) one agent session of the pilot.
#   start.sh <plain-agent|skill-agent> <case>          new session, instruction sent as the first message
#   start.sh <plain-agent|skill-agent> <case> resume   continue that session after a usage limit or a closed window
set -e
here=$(cd "$(dirname "$0")" && pwd)
condition=$1 case=$2
instruction="$here/instructions/$condition/$case.txt"
[ -f "$instruction" ] || { echo "no instruction for $condition/$case"; exit 1; }
case $case in IS-*) repo=Progetto-IS-main-English ;; *) repo=progetto_ing_software_gr10-main-English ;; esac
cd "$HOME/t2v-subjects/$condition/$case/$repo"
if [ "$3" = resume ]; then
  exec claude --model claude-sonnet-5-5 --continue
fi
exec claude --model claude-sonnet-5-5 "$(cat "$instruction")"
