# rdc-cli Quick Reference

## Session startup
- Open existing capture:
  - `rdc open "C:\Temp\frame.rdc"`
- Capture and auto-open:
  - `rdc capture "C:\Path\To\App.exe" -o "C:\Temp\frame.rdc" --frame 100 --auto-open`
- Check session:
  - `rdc status`
- Close session:
  - `rdc close`

## Fast inspection
- Capture metadata:
  - `rdc info`
- Frame summary:
  - `rdc stats`
- Render passes:
  - `rdc passes`
  - `rdc pass 0`
- Event stream:
  - `rdc events --limit 100`
- Draws:
  - `rdc draws`

## Event-scoped analysis
- Jump to event:
  - `rdc goto 12345`
- Pipeline state:
  - `rdc pipeline 12345`
- Bound resources:
  - `rdc bindings 12345`
- Resource use:
  - `rdc usage RESOURCE_ID`
- Shader search:
  - `rdc search "main" --type shader`

## Pixel and shader debugging
- Read current pixel:
  - `rdc pick-pixel 960 540`
- Pixel history:
  - `rdc pixel 960 540`
- Shader debug:
  - `rdc debug pixel 960 540`
  - `rdc debug vertex 12345 0`

## Export
- Current render target:
  - `rdc rt 12345 -o "C:\Temp\rt.png"`
- Texture:
  - `rdc texture 12345 -o "C:\Temp\tex.png"`
- Buffer:
  - `rdc buffer 12345 -o "C:\Temp\buf.bin"`
- Mesh:
  - `rdc mesh 12345 -o "C:\Temp\mesh.obj"`
- Snapshot:
  - `rdc snapshot 12345`
- Validation messages:
  - `rdc log`

## Assertions and CI
- No validation errors:
  - `rdc assert-clean`
- Count check:
  - `rdc assert-count draws --expect 1200 --op le`
- Pixel check:
  - `rdc assert-pixel 12345 960 540 --expect "1 0 0 1"`
- Pipeline state check:
  - `rdc assert-state 12345 FIELD VALUE`
- Image diff:
  - `rdc assert-image "C:\Temp\expected.png" "C:\Temp\actual.png" --threshold 0.01`

## Remote replay
- Start replay host:
  - `rdc serve --port 54321`
- Save remote host:
  - `rdc remote connect "HOST:54321"`
- Capture from remote host:
  - `rdc remote capture APP_ID -o "C:\Temp\frame.rdc"`
- Replay against remote GPU:
  - `rdc open "C:\Temp\frame.rdc" --proxy HOST:54321`

## Useful habits
- Use `--json` when the result will be parsed or compared.
- Use `-q` when you only want IDs for follow-up commands.
- Run `rdc doctor` before blaming a capture or replay failure on the application.
- Prefer `rdc <command> --help` over memory for less common flags.

