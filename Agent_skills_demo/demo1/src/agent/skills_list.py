from pathlib import Path
from typing import List, TypedDict


class Skill(TypedDict):
    """可以逐步披露给智能体的技能。"""

    name: str
    description: str
    content: str
    scripts: List[str]  # Add scripts to the skill dictionary


SKILLS_DIR = Path(__file__).with_name("skills")
PROJECT_SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SKILL_DIRS = (SKILLS_DIR, PROJECT_SKILLS_DIR)


def _discover_scripts(skill_dir: Path) -> List[str]:
    """Discover scripts in the scripts/ subdirectory of a skill."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return []

    return [str(script) for script in scripts_dir.iterdir() if script.is_file() and script.suffix == ".py"]


def _parse_skill_markdown(skill_dir: Path) -> Skill:
    skill_file = skill_dir / "SKILL.md"
    raw_text = skill_file.read_text(encoding="utf-8").strip()

    metadata: dict[str, str] = {}
    content = raw_text
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) == 3:
            _, frontmatter, body = parts
            for line in frontmatter.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
            content = body.strip()

    # Include discovered scripts in the skill metadata
    scripts = _discover_scripts(skill_dir)

    return {
        "name": metadata.get("name", skill_dir.name),
        "description": metadata.get("description", ""),
        "content": content,
        "scripts": scripts,  # Add scripts to the skill dictionary
    }


def load_skills(skill_dirs: tuple[Path, ...] = SKILL_DIRS) -> List[Skill]:
    """从多个 skills 目录动态加载并合并所有技能定义。"""

    skills_by_name: dict[str, Skill] = {}

    for skills_dir in skill_dirs:
        if not skills_dir.exists():
            continue

        for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            skill = _parse_skill_markdown(skill_dir)
            # 前面的目录优先级更高；遇到同名 skill 时忽略后续重复定义。
            skills_by_name.setdefault(skill["name"], skill)

    return [skills_by_name[name] for name in sorted(skills_by_name)]


def build_skill_catalog_text(skills: List[Skill] | None = None) -> str:
    """构建系统提示里展示的技能目录文本。"""

    loaded_skills = skills if skills is not None else SKILLS
    if not loaded_skills:
        return "- 当前未发现可用技能"

    return "\n".join(
        f"- {skill['name']}: {skill['description']}" if skill["description"] else f"- {skill['name']}"
        for skill in loaded_skills
    )


SKILLS = load_skills()


