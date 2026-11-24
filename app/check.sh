#!/bin/sh
# Checks everything the tool needs, including that the agent (Claude Code, or Codex with T2V_AGENT=codex) is
# logged in and can use its models. The model checks are tiny calls and count very little against your usage.
cd "$(dirname "$0")"
ok=1
need() {  # need <command> <what it is for>
  if command -v "$1" >/dev/null 2>&1; then echo "ok       $1"; else echo "MISSING  $1 ($2)"; ok=0; fi
}
AGENT="${T2V_AGENT:-claude}"
case "$AGENT" in
  claude) need claude "Claude Code: the agents (T2V_AGENT=claude)" ;;
  codex)  need codex "Codex: the agents (T2V_AGENT=codex)" ;;
  *) echo "T2V_AGENT must be claude or codex (it is '$AGENT')"; exit 1 ;;
esac
need git "fetching GitHub repositories"
need java "used by PlantUML"
need dot "Graphviz, used by PlantUML"
need plantuml "renders the views"
if [ -x .venv/bin/t2v-app ]; then echo "ok       app/.venv"; else echo "MISSING  app/.venv (run ./setup.sh)"; ok=0; fi
if command -v plantuml >/dev/null 2>&1; then
  printf '@startuml\nA -> B\n@enduml\n' | plantuml -tpng -pipe >/dev/null 2>&1 \
    && echo "ok       plantuml renders" || { echo "FAILED   plantuml cannot render (check java and dot)"; ok=0; }  # The layout checks read element data from the SVG; PlantUML versions from before about 2023 do not write it,
  # and their layouts differ. Such a version renders, but the checks would be skipped: require a newer one.
  if printf '@startuml\ncomponent A\ncomponent B\nA ..> B\n@enduml\n' | plantuml -tsvg -pipe 2>/dev/null \
      | grep -q 'data-diagram-type='; then
    echo "ok       plantuml is recent enough ($(plantuml -version 2>/dev/null | head -1 | cut -c1-40))"
  else
    echo "FAILED   plantuml is too old ($(plantuml -version 2>/dev/null | head -1 | cut -c1-40)): install a newer one (README, Requirements)"
    ok=0
  fi
fi
if command -v "$AGENT" >/dev/null 2>&1; then
  echo "         $AGENT $($AGENT --version 2>/dev/null)"
  models=$(T2V_AGENT=$AGENT .venv/bin/python -c 'from t2v_app import config; print(config.GENERATOR_MODEL, config.CRITIC_MODEL)' 2>/dev/null)
  for model in $(echo "$models" | tr ' ' '\n' | sort -u); do
    if [ "$AGENT" = claude ]; then
      reply=$(cd "${TMPDIR:-/tmp}" && claude -p "Reply with the single word ok." --model "$model" --tools "" 2>&1 | head -3)
    else
      reply=$(cd "${TMPDIR:-/tmp}" && codex exec --skip-git-repo-check --ignore-user-config --ephemeral \
              -c 'sandbox_mode="read-only"' -m "$model" "Reply with the single word ok." < /dev/null 2>&1 | tail -3)
    fi
    case "$reply" in
      *[Oo][Kk]*) echo "ok       $AGENT can use $model" ;;
      *) echo "FAILED   $AGENT with $model: $reply"; ok=0 ;;
    esac
  done
fi
[ $ok = 1 ] && echo "Everything is ready. Start the tool with ./run.sh" || { echo "Fix the lines above (see README.md)."; exit 1; }
