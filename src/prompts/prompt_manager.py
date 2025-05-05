from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError

class PromptManager:
    _env = None

    @classmethod
    def _get_env(cls, templates_dir="templates"):
        # point at src/prompts/templates
        templates_path = Path(__file__).parent / templates_dir
        if cls._env is None:
            cls._env = Environment(
                loader=FileSystemLoader(str(templates_path)),
                undefined=StrictUndefined,
            )
        return cls._env

    @staticmethod
    def _read_frontmatter(path: Path):
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            _, fm, body = text.split("---", 2)
            metadata = yaml.safe_load(fm) or {}
        else:
            metadata, body = {}, text
        return metadata, body

    @staticmethod
    def get_prompt(template: str, **kwargs):
        env = PromptManager._get_env()
        template_path = Path(env.loader.get_source(env, f"{template}.j2")[1])
        meta, content = PromptManager._read_frontmatter(template_path)

        tpl = env.from_string(content)
        try:
            return tpl.render(**kwargs)
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {e}")

    @staticmethod
    def get_template_info(template: str):
        from jinja2 import meta

        env = PromptManager._get_env()
        template_path = Path(env.loader.get_source(env, f"{template}.j2")[1])
        meta_dict, content = PromptManager._read_frontmatter(template_path)

        ast = env.parse(content)
        vars = meta.find_undeclared_variables(ast)

        return {
            "name":        template,
            "description": meta_dict.get("description", "No description provided"),
            "author":      meta_dict.get("author", "Unknown"),
            "variables":   sorted(vars),
            "frontmatter": meta_dict,
        }