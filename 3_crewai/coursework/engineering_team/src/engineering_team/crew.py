from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.sandbox_tools import sandbox_tools
from coursework_lib import get_llm

_TOOL_LLM = get_llm(tools=True)


@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],  # type: ignore[index]
            verbose=True,
            llm=_TOOL_LLM,
            mcps=["https://mcp.context7.com/mcp"],
            max_iter=4,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],  # type: ignore[index]
            verbose=True,
            llm=_TOOL_LLM,
            tools=sandbox_tools,
            max_iter=8,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],  # type: ignore[index]
            verbose=True,
            llm=_TOOL_LLM,
            tools=sandbox_tools,
            max_iter=10,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],  # type: ignore[index]
            verbose=True,
            llm=_TOOL_LLM,
            tools=sandbox_tools,
            max_iter=12,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],  # type: ignore[index]
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],  # type: ignore[index]
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],  # type: ignore[index]
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
