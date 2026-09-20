{ config, pkgs, ... }:
{
  home.username = "root";
  home.homeDirectory = "/root";
  home.stateVersion = "26.05";

  programs.home-manager.enable = true;

  # Interactive Bash is user-state authority. Runtime execution PATH is independent
  # and remains owned by Runtime's own installation policy.
  programs.bash = {
    enable = true;
    enableCompletion = true;
    historyFile = "/dev/null";
    historySize = 500;
    historyFileSize = 0;
    historyControl = [ "ignoreboth" "erasedups" ];
    sessionVariables = {
      PATH = "/root/tools/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/wsl/lib:/root/.local/bin:/root/bin";
      EDITOR = "vim";
      VISUAL = "vim";
      PROJECTS = "/root/projects";
      STARSHIP_CONFIG = "/root/.config/starship.toml";
      FZF_DEFAULT_COMMAND = "fd --type f --hidden --follow --exclude .git";
      FZF_CTRL_T_COMMAND = "fd --type f --hidden --follow --exclude .git";
      FZF_ALT_C_COMMAND = "fd --type d --hidden --follow --exclude .git";
      FZF_DEFAULT_OPTS = "--height 45% --layout=reverse --border --info=inline --cycle --preview-window=right:55%:wrap";
      BAT_THEME = "TwoDark";
    };
    shellAliases = {
      ls = "eza --group-directories-first --icons=auto";
      ll = "eza -lah --group-directories-first --icons=auto --git";
      la = "eza -A --group-directories-first --icons=auto";
      tree = "eza --tree --level=2 --group-directories-first --icons=auto";
      cat = "bat --paging=never";
      grep = "grep --color=auto";
      cls = "clear";
      lg = "lazygit";
      yz = "yazi";
      top = "btm";
      projects = "cd \"$PROJECTS\"";
    };
    bashrcExtra = ''
      export PATH="/root/tools/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/wsl/lib:/root/.local/bin:/root/bin"
      export EDITOR="vim"
      export VISUAL="vim"
      export PROJECTS="/root/projects"
      export STARSHIP_CONFIG="/root/.config/starship.toml"
      export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"
      export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
      export FZF_ALT_C_COMMAND="fd --type d --hidden --follow --exclude .git"
      export FZF_DEFAULT_OPTS="--height 45% --layout=reverse --border --info=inline --cycle --preview-window=right:55%:wrap"
      export BAT_THEME="TwoDark"
    '';
    initExtra = ''
      ulimit -Sn 65536 2>/dev/null || true

      cdf() {
        local dir
        dir="$(fd --type d --hidden --follow --exclude .git . "''${1:-.}" | fzf --preview 'eza -lah --group-directories-first --icons=auto {} | head -80')" || return
        cd "$dir"
      }

      ff() {
        local file
        file="$(fd --type f --hidden --follow --exclude .git . "''${1:-.}" | fzf --preview 'bat --color=always --style=numbers --line-range=:200 {}')" || return
        printf '%s\n' "$file"
      }

      fp() {
        local file
        file="$(ff "''${1:-.}")" || return
        ''${EDITOR:-vim} "$file"
      }

      case "$PWD" in
        /mnt/c/*|/mnt/d/*)
          cd "$HOME"
          ;;
      esac

      [ -r /usr/share/fzf/key-bindings.bash ] && source /usr/share/fzf/key-bindings.bash
      [ -r /usr/share/fzf/completion.bash ] && source /usr/share/fzf/completion.bash
      eval "$(zoxide init bash)"
      eval "$(starship init bash)"
    '';
  };

  # mise is project-version authority; Home Manager owns only its stable user policy.
  xdg.enable = true;
  xdg.configFile."mise/config.toml".text = ''
    [settings]
    auto_install = false
    exec_auto_install = false
    not_found_auto_install = false
    jobs = 4
    idiomatic_version_file_enable_tools = ["node", "pnpm"]
    trusted_config_paths = [
      "/root/projects/ordivon-game",
      "/root/projects/ordivon-media",
    ]

    [settings.task]
    run_auto_install = false
  '';

  # Keep direct `pnpm` compatibility without an Ordivon resolver or version table.
  # The compatibility path points at mise's own shim; package.json packageManager
  # remains the project authority for the exact pnpm version.
  home.file."tools/bin/pnpm".source =
    config.lib.file.mkOutOfStoreSymlink "/root/.local/share/mise/shims/pnpm";

  # Codex package/materialization authority is Nixpkgs. Keep the historical first-PATH
  # command location as a direct immutable symlink, not an Ordivon wrapper/store.
  home.file."tools/bin/codex".source = "${pkgs.codex}/bin/codex";

  # n8n package/materialization authority is Nixpkgs. Workstation owns only the
  # first-PATH command materialization; n8n owns its workflow/integration behavior.
  home.file."tools/bin/n8n".source = "${pkgs.n8n}/bin/n8n";

  # Immutable Linux tool closures. systemd remains the service-lifecycle authority;
  # project language/runtime versions remain with mise.
  home.packages = with pkgs; [
    git
    curl
    jq
    yq-go
    ripgrep
    fd
    just
    mise
    restic
    trivy
    syft
    cosign
    shellcheck
    shfmt
    osquery
    netdata
    codex
    n8n

    # Broad research workstation profile. These are reusable workstation tools, not
    # Research E2E semantic owners; Research activates them only for real workloads.
    pandoc
    quarto
    R
    rstudio
    python3Packages.jupyterlab
    python3Packages.marimo
    julia
    slurm
    apptainer
    openmpi
    zotero
    fiji
    octave
    texlive.combined.scheme-medium
  ];
}
