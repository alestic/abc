# [Created by AI: Claude Code]
{
  description = "AI Bash Command - Natural language to shell command translation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;

        # Build the core abc-cli package
        abc-cli = python.pkgs.buildPythonApplication rec {
          pname = "abc-cli";
          version = "2026.09.06";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with python.pkgs; [
            hatchling
          ];

          propagatedBuildInputs = with python.pkgs; [
            click
            tomli
            distro
            prompt-toolkit
            readchar
          ];

          # Only include the abc_cli directory
          preBuild = ''
            cd $src
            cp -r abc_cli pyproject.toml LICENSE README.md $NIX_BUILD_TOP/
            cd $NIX_BUILD_TOP
          '';

          # Install shell integration scripts
          postInstall = ''
            mkdir -p $out/share/abc
            cp ${./abc_cli/abc.sh} $out/share/abc/abc.sh
            cp ${./abc_cli/abc.tcsh} $out/share/abc/abc.tcsh
            
            # Don't patch the scripts here - let the wrapper handle it
          '';

          pythonImportsCheck = [ "abc_cli" ];
        };

        # Build provider packages
        abc-provider-anthropic = python.pkgs.buildPythonPackage rec {
          pname = "abc-provider-anthropic";
          version = "2026.09.06";
          format = "pyproject";

          src = ./abc_provider_anthropic;

          nativeBuildInputs = with python.pkgs; [
            hatchling
          ];

          propagatedBuildInputs = with python.pkgs; [
            anthropic
            abc-cli
          ];

          pythonImportsCheck = [ "abc_provider_anthropic" ];
        };

        abc-provider-aws-bedrock = python.pkgs.buildPythonPackage rec {
          pname = "abc-provider-aws-bedrock";
          version = "2026.09.06";
          format = "pyproject";

          src = ./abc_provider_aws_bedrock;

          nativeBuildInputs = with python.pkgs; [
            hatchling
          ];

          propagatedBuildInputs = with python.pkgs; [
            boto3
            abc-cli
          ];

          pythonImportsCheck = [ "abc_provider_aws_bedrock" ];
        };

        # Combined package with all providers (wrapper around abc-cli)
        abc-with-providers = pkgs.symlinkJoin {
          name = "abc-${abc-cli.version}";
          paths = [ abc-cli ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            # Wrap the executables to include providers in PYTHONPATH
            wrapProgram $out/bin/abc_generate \
              --prefix PYTHONPATH : "${python.pkgs.makePythonPath [
                abc-provider-anthropic
                abc-provider-aws-bedrock
              ]}"
            wrapProgram $out/bin/abc_setup \
              --prefix PYTHONPATH : "${python.pkgs.makePythonPath [
                abc-provider-anthropic
                abc-provider-aws-bedrock
              ]}"
            
            # Copy and patch shell scripts to use the wrapped executables
            rm -rf $out/share/abc
            mkdir -p $out/share/abc
            cp ${abc-cli}/share/abc/abc.sh $out/share/abc/abc.sh
            cp ${abc-cli}/share/abc/abc.tcsh $out/share/abc/abc.tcsh
            substituteInPlace $out/share/abc/abc.sh \
              --replace "abc_generate" "$out/bin/abc_generate"
            substituteInPlace $out/share/abc/abc.tcsh \
              --replace "abc_generate" "$out/bin/abc_generate"
          '';
          
          passthru = {
            inherit (abc-cli) version;
            pythonPath = python.pkgs.makePythonPath [
              abc-cli
              abc-provider-anthropic
              abc-provider-aws-bedrock
            ];
          };
        };

        # Shell integration helper script
        shellIntegrationSetup = pkgs.writeShellScriptBin "abc-shell-setup" ''
          #!/usr/bin/env bash
          set -e

          SHELL_NAME=$(basename "$SHELL")
          ABC_SHARE="${abc-with-providers}/share/abc"

          case "$SHELL_NAME" in
            bash|zsh)
              echo "source $ABC_SHARE/abc.sh"
              ;;
            tcsh)
              echo "source $ABC_SHARE/abc.tcsh"
              ;;
            *)
              echo "Unsupported shell: $SHELL_NAME" >&2
              echo "Supported shells: bash, zsh, tcsh" >&2
              exit 1
              ;;
          esac
        '';

      in
      {
        # Packages
        packages = {
          default = abc-with-providers;
          abc-cli = abc-cli;
          abc-provider-anthropic = abc-provider-anthropic;
          abc-provider-aws-bedrock = abc-provider-aws-bedrock;
          abc-shell-setup = shellIntegrationSetup;
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python.withPackages (ps: with ps; [
              click
              tomli
              anthropic
              boto3
              pytest
              pytest-cov
              build
              twine
            ]))
            abc-with-providers
          ];

          shellHook = ''
            echo "abc development environment"
            echo "Python: ${python.version}"
            echo ""
            echo "To enable abc in this shell:"
            echo "  source ${abc-with-providers}/share/abc/abc.sh"
            echo ""
            export ABC_SHELL_INTEGRATION="${abc-with-providers}/share/abc"
          '';
        };

        # App for nix run
        apps.default = {
          type = "app";
          program = "${abc-with-providers}/bin/abc_generate";
        };
      });
}