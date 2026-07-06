from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from debate.llm_config import get_llm


@CrewBase
class Debate():
    """Debate crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'], # type: ignore[index]
            llm=get_llm(),
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'], # type: ignore[index]
            llm=get_llm(),
            verbose=True
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'], # type: ignore[index]
        )
    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'], # type: ignore[index]
        )
    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
