from __future__ import annotations

import json
from importlib import resources

from jinja2 import Environment, FileSystemLoader

from sv_ref.core.models import Refbook


def generate_html(refbook: Refbook) -> str:
    template_dir = resources.files("sv_ref") / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
    )
    template = env.get_template("index.html.j2")
    refbook_json = json.dumps(refbook.model_dump(), indent=2)
    return template.render(refbook_json=refbook_json)
