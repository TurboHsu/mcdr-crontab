# MCDReforged Crontab

## Introduction

This plugin is a crontab plugin for `MCDReforged`.

## How do i use it?

Drop `crontab.py` into the `plugins` folder of your MCDReforged server.
After loading there should be a `crontab.txt` in ur `config` folder.

For example, if you are evil enough to kill all players at 0:00 every day, you can add the following line to `crontab.txt`:

```txt
0 0 * * * kill @a
```

## Commands

- `!!crontab reload`: Reload the crontab file.
- `!!crontab list`: List all crontab tasks.
