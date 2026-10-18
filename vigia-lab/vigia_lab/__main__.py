"""Entrada: `python -m vigia_lab ...`. O bootstrap tem de ser o primeiro import."""

from vigia_lab import bootstrap

bootstrap.setup()

from vigia_lab.app import main  # noqa: E402

raise SystemExit(main())
