# Releasing clair

clair is distributed via an in-repo Homebrew formula (`Formula/clair.rb`), tapped by URL.

## Cut a release

1. Bump the version in `clair/__init__.py` (`__version__`) and commit.
2. Tag and push:
   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
3. Compute the tag-archive checksum:
   ```sh
   make formula-sha VERSION=X.Y.Z
   ```
4. In `Formula/clair.rb`, set `url` to the `vX.Y.Z` archive and paste the `sha256`. Commit.
5. (Maintainer) validate the formula:
   ```sh
   brew install --build-from-source Formula/clair.rb
   brew test clair
   brew audit --formula Formula/clair.rb
   ```

## Install (consumers)

```sh
brew tap The007Programmer/clair https://github.com/The007Programmer/clair
brew install clair
# upgrade later:
brew update && brew upgrade clair
```

The formula installs the runtime payload into Homebrew's `libexec` and provides a
`clair` wrapper that sets `CLAIR_ROOT` (see the "Running from a package" section of the
README). `clair push` is intentionally disabled in a packaged install — clone the repo
for the development workflow.
