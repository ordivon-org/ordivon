{
  description = "Artifact OpenXML .NET 8 runtime closure";

  inputs.nixpkgs.url = "git+https://github.com/NixOS/nixpkgs?ref=nixos-26.05&shallow=1";

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.${system} = {
        dotnet-sdk = pkgs.dotnet-sdk_8;
        default = pkgs.dotnet-sdk_8;
      };
    };
}
