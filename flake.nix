{
  description = "Millwright – adaptive tool selection for AI agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.python312Packages.pip
            pkgs.python312Packages.virtualenv
          ];

          # Native libs needed by pip-installed packages (numpy, torch, etc.)
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ];

          shellHook = ''
            VENV_DIR="$PWD/.venv"
            if [ ! -d "$VENV_DIR" ]; then
              echo "Creating Python venv..."
              ${python}/bin/python -m venv "$VENV_DIR"
            fi
            source "$VENV_DIR/bin/activate"

            # Install deps if requirements.txt is newer than the sentinel
            SENTINEL="$VENV_DIR/.installed"
            if [ ! -f "$SENTINEL" ] || [ requirements.txt -nt "$SENTINEL" ]; then
              echo "Installing dependencies from requirements.txt..."
              pip install -q -r requirements.txt
              touch "$SENTINEL"
            fi

            echo "Millwright dev shell ready. Run: python -m benchmark.run_benchmark"
          '';
        };
      }
    );
}
