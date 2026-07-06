# SETUP.md — reconstruction playbook

An ordered, verifiable, Claude-executable playbook to reconstruct this Claude Code
environment on a fresh machine (macOS, Ubuntu, or Windows). Run each step, confirm the
expected result, then continue. Every command is run from the repository root unless noted.
All paths use `$HOME`/`~`; there are no machine-specific absolute paths to edit.

> **Windows:** `install.sh` needs bash and is not used. Everywhere this playbook says
> `./install.sh`, run `python bootstrap.py` instead; the `python3 -m clair apply` commands
> work unchanged. See the Windows note under Step 2.

## 0. Prerequisites

- System `python3` >= 3.9 on `PATH`. Check:

  ```sh
  python3 --version
  ```

  Expected: `Python 3.9.x` or newer. `clair` uses only the standard library, so no `pip
  install` is required.

- `git` and `jq` will be installed for you by Step 2 if missing (`brew` on macOS,
  `apt-get` on Ubuntu). On **Windows** nothing is auto-installed — install `git`/`jq`
  yourself if you want overlays / jq-based hooks (the clair core needs neither). You can
  pre-check:

  ```sh
  command -v git jq
  ```

## 1. Configure per-machine variables (`local.env`)

`local.env` is gitignored and holds the values that differ per machine. Create it from
the example and edit as needed:

```sh
cp local.env.example local.env
```

Keys (all optional except where you want non-default behavior):

- `CODE_ROOT` — where your repos live. Default `$HOME/Documents/Code`.
- `VAULT_ROOT` — optional reference-docs directory. Leave blank to strip vault-only
  content; set it to enable those blocks.
- `AWS_PROFILE` — optional; overlay-only.
- `OVERLAY_REPO` — optional git URL of a private overlay repo to clone and apply.
- `OVERLAY_DIR` — optional local path to a private overlay directory.

If you set neither `OVERLAY_REPO` nor `OVERLAY_DIR`, only the generic base layer is
applied. Verify the file is well-formed `KEY=VALUE` lines:

```sh
python3 -c "from clair import localenv, config; print(localenv.load(config.localenv_path(config.repo_root())))"
```

Expected: a Python dict printed with your `CODE_ROOT` (and any overlay/vault values)
expanded — `$HOME` resolved to your home directory.

## 2. Run the install

Three equivalent options:

- **Bootstrap script** — macOS/Linux; ensures `git`/`python3`/`jq`, then applies:

  ```sh
  ./install.sh
  ```

- **Python bootstrap** — cross-platform, no shell required (this is the Windows path):

  ```sh
  python bootstrap.py
  ```

- **Direct, explicit** (use when deps are already present, or to see each phase):

  ```sh
  python3 -m clair apply
  ```

On Windows, managed files are symlinked when the OS permits it (Developer Mode or an admin
shell) and otherwise **copied** — either way `apply` succeeds. With copies, re-run `clair
apply` after pulling repo changes to re-sync, since a copy does not live-track its source.

Expected: an apply report printed to stdout listing the detected OS, dependency
results, base items applied, overlay items applied (empty if no overlay), plugin results,
mboard status, scan findings (should be empty), and notes. `clair apply` is idempotent
and never aborts on a sub-step failure — failures are collected into the notes section so
you can read and address them.

### Interactive feature picker

Run in a terminal with no preset, `python3 -m clair apply` opens an interactive feature
picker before applying anything. Features are grouped into staged screens (Core, Commands,
Skills, Plugins, Coordination, and an Overlay stage when an overlay is configured). Navigate
with the arrow keys, toggle an item with space, advance with Enter, and go back with Esc. The
resulting selection is saved to `~/.claude/.clair-profile.json` and replayed on later runs.

```text
clair apply              # feature picker (when run in a terminal with no preset)
clair apply recommended  # headless preset: minimal | recommended | everything
clair apply              # re-run to re-open the picker, pre-filled from the saved profile
```

Passing a preset (`minimal` | `recommended` | `everything`) applies headlessly with no
prompts. `apply` also runs headlessly whenever stdin is not a TTY — this is how `./install.sh`
applies without blocking — falling back to the saved profile, or the defaults if none exists.
Re-running `clair apply` interactively re-opens the picker pre-filled from your saved profile.

## 3. Verify the base layer landed

Confirm the live `~/.claude` matches the repo (no drift):

```sh
python3 -m clair status
```

Expected: a drift report showing managed items as in-sync (no pending differences for
files you have not changed). Spot-check that `settings.json` exists in the home target:

```sh
ls -l "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

Expected: the file is present.

## 4. Verify plugins are configured

`settings.json` carries `enabledPlugins` and `extraKnownMarketplaces`; the installer also
attempts `claude plugin install` best-effort. Confirm the plugin keys are present in the
live settings:

```sh
jq '.enabledPlugins, .extraKnownMarketplaces' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

Expected: `enabledPlugins` includes `superpowers@claude-plugins-official`,
`frontend-design@claude-plugins-official`, and `understand-anything@understand-anything`,
each set to `true`; `extraKnownMarketplaces` includes the `understand-anything` GitHub
marketplace. If the `claude` CLI was present, the report from Step 2 also shows each
plugin's install status.

## 5. Verify the mboard is installed

The vendored mboard installer symlinks `~/.claude/mboard/{mboard,hooks}` to this repo's
`mboard/` source and merges its hooks (with `$HOME`-relative commands) into
`settings.json`. Confirm the symlinks:

```sh
ls -l "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/mboard"
```

Expected: `mboard` and `hooks` entries present and pointing at this repo's `mboard/`
directory. Confirm the hook commands are `$HOME`-relative (not absolute machine paths):

```sh
jq '.hooks' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

Expected: hook commands reference `"$HOME/.claude/mboard/hooks/..."`.

## 6. Apply the overlay (if you configured one)

If `OVERLAY_REPO` or `OVERLAY_DIR` was set in Step 1, the overlay was already applied
during Step 2. Confirm its items appear in the report's overlay section, or re-apply the
repo-to-live mapping (base + overlay):

```sh
python3 -m clair apply recommended
```

Expected: the overlay items (new files and merged allowlist/settings entries) are applied
on top of the base. If you configured no overlay, this step is a no-op beyond re-applying
the base. (There is no separate lightweight re-apply — `apply` is the only path.)

## 7. Re-authenticate Claude Code

Secrets are never committed, so a fresh machine has no stored credentials. Authenticate
the Claude Code CLI:

```sh
claude auth login
```

Alternatively, set a credential token in your shell environment before launching Claude
Code — either `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`. Verify:

```sh
claude auth status
```

Expected: the CLI reports an authenticated session. The Step 2 report's notes section
also prints these instructions when it detects `claude` is installed but not logged in.

## 8. Final health check

```sh
python3 -m clair status health
```

Expected: a health report with no outstanding drift and a `claude doctor` note. The
environment is now reconstructed: base (and overlay, if any) applied, settings merged,
plugins configured, mboard installed, and credentials re-established.

## Re-running

Every step is idempotent. Re-running `./install.sh` or `python3 -m clair apply` converges
to the same state; managed files are backed up (`*.clair.bak`) before any overwrite.

## Optional: enable your private overlay

The base installs and works standalone. To layer in your private personal/company content:

1. Scaffold and wire up an overlay with `python3 -m clair new overlay [url]`, or prepare one
   by hand shaped like `docs/overlay-example/` (a `manifest.json` whose items use
   `"layer": "overlay"`, plus a `home/.claude/` mirror).
2. If wiring it by hand, set ONE of these in your gitignored `local.env`:
   - `OVERLAY_DIR=$HOME/path/to/your/overlay` (local directory), or
   - `OVERLAY_REPO=<git url>` (cloned to `~/.cache/clair/overlay`).
3. Re-run `python3 -m clair apply`. The installer applies the base, then resolves the
   overlay (`clone_overlay`) and applies `layer="overlay"` on top.

Verify the overlay manifest is well-formed before installing:

```bash
python3 -c "import sys; sys.path.insert(0, '.'); from clair import manifest; \
items = manifest.parse('docs/overlay-example/manifest.json'); \
print('overlay items:', [(i.path, i.layer) for i in items])"
```

Expected output:

```
overlay items: [('agents/sample-overlay-agent.md', 'overlay'), ('settings.local.json.tmpl', 'overlay')]
```

## Optional: running from a package install

These steps assume a git checkout. clair can also run from a read-only package (Homebrew /
apt — separate, later work). A packaged install exports `CLAIR_ROOT` (the bundled asset
tree) and reads `local.env` from `~/.config/clair/local.env` (or `$CLAIR_LOCAL_ENV`); it
skips dependency installation (declared as package deps) and disables `clair push` (use a
checkout for the dev loop). To produce the package payload from a checkout:

```bash
make dist           # writes dist/clair-<version>.tar.gz and prints its sha256
clair --version     # or: python3 -m clair --version
```

See the "Running from a package (`CLAIR_ROOT`)" section in [README.md](./README.md).
