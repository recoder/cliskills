import pytest
from pydantic import BaseModel

from cliskill import Skill, SkillContext
from examples.demo_skill.main import skill


class SampleInput(BaseModel):
    value: str


class SampleOutput(BaseModel):
    value: str


def test_skill_command_decorator_registers_command_schema() -> None:
    registered_skill = Skill(
        name="test-skill",
        version="0.1.0",
        description="Test skill.",
    )

    @registered_skill.command(
        name="test",
        description="Test command.",
        input_model=SampleInput,
        output_model=SampleOutput,
    )
    def test_command(input_data: SampleInput, ctx: SkillContext) -> SampleOutput:
        return SampleOutput(value=input_data.value)

    manifest = registered_skill.manifest()

    assert list(registered_skill.commands) == ["test"]
    assert manifest.commands[0].name == "test"
    assert manifest.commands[0].input_schema is not None
    assert manifest.commands[0].input_schema["properties"]["value"]["type"] == "string"
    assert manifest.commands[0].output_schema is not None
    assert manifest.commands[0].output_schema["properties"]["value"]["type"] == "string"


def test_skill_rejects_duplicate_command_names() -> None:
    registered_skill = Skill(
        name="test-skill",
        version="0.1.0",
        description="Test skill.",
    )

    @registered_skill.command(name="test", description="Test command.")
    def first_command() -> SampleOutput:
        return SampleOutput(value="first")

    with pytest.raises(ValueError, match="Command already registered: test"):

        @registered_skill.command(name="test", description="Duplicate command.")
        def second_command() -> SampleOutput:
            return SampleOutput(value="second")


def test_demo_skill_exposes_registered_echo_command() -> None:
    assert list(skill.commands) == ["echo"]
