This project uses nix, direnv, and nix-direnv.

If you have these 3, you can usually get the env Jeremy used easily.

https://github.com/DeterminateSystems/nix-installer?tab=readme-ov-file

https://direnv.net/

https://github.com/nix-community/nix-direnv

Nix: 

    curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install

You'll have to run UV sync, once you have everything else. Not up to the usual standards!

    uv sync

On May 5th, 2025, John had trouble getting nix onto his path, and stopped for the time being.