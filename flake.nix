{
  description = "Healthbrain";
  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/nixos-22.05;
    flake-utils = {
      url = github:numtide/flake-utils;
    };
    mach-nix = {
      url = "mach-nix/3.4.0";
    };
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        machNix = mach-nix.lib."${system}";
        devEnvironment = machNix.mkPython {
          requirements = builtins.readFile ./requirements/local.txt;
          _.pytest-cov.propagatedBuildInputs.mod = pySelf: self: oldVal: oldVal ++ [ pySelf.tomli ];
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            devEnvironment
            pkgs.gnumake
          ];
        };
        packages.venv = devEnvironment;
        defaultPackage = (machNix.mkDockerImage {
          packagesExtra = with pkgs;
            [ pkgs.bash ];
          requirements = builtins.readFile ./requirements/docker.txt;
          _.pytest-cov.propagatedBuildInputs.mod = pySelf: self: oldVal: oldVal ++ [ pySelf.tomli ];
        }).override
          (oldAttrs: {
            name = "network-inventory";
            config.Cmd = [ "run.sh" ];
          });
      });
}
