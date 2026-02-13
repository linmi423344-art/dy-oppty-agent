"""Tiny local Typer compatibility shim for offline test environments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Callable


class Exit(SystemExit):
    def __init__(self, code: int = 0):
        super().__init__(code)


def echo(message: str, err: bool = False) -> None:
    print(message)


@dataclass
class _Option:
    default: Any
    param_decls: tuple[str, ...]


def Option(default: Any = None, *param_decls: str) -> Any:
    return _Option(default=default, param_decls=param_decls)


class Typer:
    def __init__(self, help: str | None = None):
        self.help = help
        self.commands: dict[str, Callable[..., Any]] = {}

    def command(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            name = func.__name__.removesuffix("_cmd").replace("_", "-")
            self.commands[name] = func
            return func

        return decorator


class _CommandRunner:
    def __init__(self, app: Typer):
        self.app = app

    def main(self, args: list[str] | None = None, prog_name: str = "app", standalone_mode: bool = False) -> Any:
        parser = argparse.ArgumentParser(prog=prog_name, description=self.app.help)
        subparsers = parser.add_subparsers(dest="command", required=True)

        for name, func in self.app.commands.items():
            sp = subparsers.add_parser(name)
            defaults = getattr(func, "__defaults__", ()) or ()
            names = func.__code__.co_varnames[: func.__code__.co_argcount]
            offset = len(names) - len(defaults)
            for idx, param in enumerate(names):
                default = defaults[idx - offset] if idx >= offset else None
                if isinstance(default, _Option):
                    opt = default.param_decls[0] if default.param_decls else f"--{param.replace('_', '-')}"
                    sp.add_argument(opt, default=default.default)
            sp.set_defaults(_func=func)

        parsed = parser.parse_args(args=args)
        kwargs = {
            k: v
            for k, v in vars(parsed).items()
            if k not in {"command", "_func"}
        }
        return parsed._func(**kwargs)


class main:
    @staticmethod
    def get_command(app: Typer) -> _CommandRunner:
        return _CommandRunner(app)
