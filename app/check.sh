#!/bin/sh
# Checks everything the tool needs, including that Claude Code is logged in and can use both models.
# The two model checks are tiny calls and count (very little) against your Claude usage.
cd "$(dirname "$0")"
ok=1
need() {  # need <command> <what it is for>
  if command -v "$1" >/dev/null 2>&1; then echo "ok       $1"; else echo "MISSING  $1 ($2)"; ok=0; fi
}
need claude "Claude Code: the agents"
need git "fetching GitHub repositories"
need java "used by PlantUML"
need dot "Graphviz, used by PlantUML"
need plantuml "renders the views"
if [ -x .venv/bin/t2v-app ]; then echo "ok       app/.venv"; else echo "MISSING  app/.venv (run ./setup.sh)"; ok=0; fi
if command -v plantuml >/dev/null 2>&1; then
  printf '@startuml\nA -> B\n@enduml\n' | plantuml -tpng -pipe >/dev/null 2>&1 \
    && echo "ok       plantuml renders" || { echo "FAILED   plantuml cannot render (check java and dot)"; ok=0; }
fi
if command -v claude >/dev/null 2>&1; then
  echo "         Claude Code $(claude --version 2>/dev/null)"
  . ./.venv/bin/activate 2>/dev/null
  gen=$(python3 -c 'from t2v_app import config; print(config.GENERATOR_MODEL)' 2>/dev/null || echo claude-sonnet-5-5)
  critic=$(python3 -c 'from t2v_app import config; print(config.CRITIC_MODEL)' 2>/dev/null || echo claude-opus-5-5)
  for model in "$gen" "$critic"; do
    reply=$(cd "${TMPDIR:-/tmp}" && claude -p "Reply with the single word ok." --model "$model" --tools "" 2>&1 | head -3)
    case "$reply" in
      *[Oo][Kk]*) echo "ok       Claude Code can use $model" ;;
      *) echo "FAILED   Claude Code with $model: $reply"; ok=0 ;;
    esac
  done
fi
[ $ok = 1 ] && echo "Everything is ready. Start the tool with ./run.sh" || { echo "Fix the lines above (see README.md)."; exit 1; }
