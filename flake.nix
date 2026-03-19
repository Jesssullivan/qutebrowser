{
  description = "qutebrowser with FIDO2/WebAuthn YubiKey support";

  nixConfig = {
    extra-substituters = [
      "https://nix-cache.fuzzy-dev.tinyland.dev/main"
    ];
    extra-trusted-public-keys = [
      "main:NKRk1XYo/dfd9fcDqgotUJg2DTDHWp5ny+Ba7WzRjgE="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        packages.default = import ./nix/package.nix { inherit pkgs; };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            python3Packages.pyqt6
            python3Packages.pyqt6-webengine
            python3Packages.jinja2
            python3Packages.pyyaml
            python3Packages.pygments
            python3Packages.pytest
            python3Packages.tox
            qt6.qtwebengine
          ];
        };
      }
    );
}
