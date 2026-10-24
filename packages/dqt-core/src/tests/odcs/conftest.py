import textwrap
from uuid import uuid4

import pytest


@pytest.fixture
def rule_module(tmp_path, monkeypatch):
    """Write a real importable module and return its import name."""

    def factory(source: str) -> str:
        module_name = f"odcs_test_rules_{uuid4().hex}"
        (tmp_path / f"{module_name}.py").write_text(
            textwrap.dedent(source),
            encoding="utf-8",
        )
        monkeypatch.syspath_prepend(str(tmp_path))
        return module_name

    return factory


@pytest.fixture
def build_contract():
    """Build an ODCS v3.2.0 document with quality rules."""

    def build(
        quality_yaml: str | None = None,
        *,
        property_quality_yaml: str | None = None,
        api_version: str = "v3.2.0",
        extra_yaml: str = "",
    ) -> str:
        lines = [
            "version: 1.0.0",
            "kind: DataContract",
            f"apiVersion: {api_version}",
            "id: contract-1",
            "name: test contract",
        ]

        if extra_yaml:
            lines.append(textwrap.dedent(extra_yaml).strip("\n"))

        lines.append("schema:")
        lines.append("  - name: customers")

        if property_quality_yaml:
            lines.extend(
                [
                    "    properties:",
                    "      - name: value",
                    "        logicalType: integer",
                    "        quality:",
                    textwrap.indent(
                        textwrap.dedent(property_quality_yaml).strip("\n"),
                        " " * 10,
                    ),
                ]
            )

        if quality_yaml:
            lines.extend(
                [
                    "    quality:",
                    textwrap.indent(
                        textwrap.dedent(quality_yaml).strip("\n"),
                        " " * 6,
                    ),
                ]
            )

        return "\n".join(lines) + "\n"

    return build
