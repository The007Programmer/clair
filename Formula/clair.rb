class Clair < Formula
  desc "Claude Code environment-as-code installer"
  homepage "https://github.com/The007Programmer/clair"
  url "https://github.com/The007Programmer/clair/archive/refs/tags/v0.7.4.tar.gz"
  sha256 "43ffe167162a0499d335b32797603d2f8311b0107f2953be42a57cc8207f88cb"
  license "MIT"

  depends_on "jq"
  depends_on "python@3.12"

  def install
    libexec.install "clair", "manifest.json", "home", "mboard", "install.sh", "LICENSE"
    (bin/"clair").write <<~SH
      #!/bin/bash
      export CLAIR_ROOT="#{opt_libexec}"
      export PYTHONPATH="#{opt_libexec}${PYTHONPATH:+:$PYTHONPATH}"
      exec "#{Formula["python@3.12"].opt_bin}/python3.12" -m clair "$@"
    SH
  end

  def caveats
    <<~EOS
      clair installed its bundled Claude Code environment into:
        #{libexec}
      Apply it to your ~/.claude (and re-apply after each `brew upgrade clair`):
        clair apply   # interactive picker, or replays your saved selection headlessly
      `clair push` is disabled in this packaged install (it needs a git checkout).
    EOS
  end

  test do
    assert_match "clair #{version}", shell_output("#{bin}/clair --version")
    system bin/"clair", "status", "scan"
  end
end
