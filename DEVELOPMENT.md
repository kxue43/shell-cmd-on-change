# Development

## Local setup

Clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/kxue43/shell-cmd-on-change.git
```

If you already cloned without submodules, initialize them after the fact:

```bash
git submodule update --init --recursive
```

## Running tests

```bash
BATS_FILE_EXTENSION=sh ./test/bats/bin/bats test/
```
