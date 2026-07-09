from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field

from coursework_lib import get_llm
from stock_picker.tools.email_tool import send_html_email

SCREEN_COMPANY_COUNT = 5
SCREEN_ETF_COUNT = 2
PICK_COMPANY_COUNT = 3
PICK_ETF_COUNT = 1


class ScreenedCompany(BaseModel):
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    pe_ratio: str = Field(description="P/E ratio or valuation multiple")
    investment_potential: str = Field(description="Growth and return potential assessment")
    valuation_summary: str = Field(description="Brief valuation analysis")
    technical_summary: str = Field(description="Key technical indicators and trend")
    selection_rationale: str = Field(description="Why this company passed the initial screen")


class ScreenedETF(BaseModel):
    name: str = Field(description="ETF or index fund name")
    ticker: str = Field(description="ETF ticker symbol")
    expense_ratio: str = Field(description="Expense ratio and cost profile")
    strategy: str = Field(description="Index, thematic, or sector strategy")
    investment_potential: str = Field(description="Diversification and return potential assessment")
    selection_rationale: str = Field(description="Why this ETF passed the initial screen")


class ScreenedUniverse(BaseModel):
    companies: list[ScreenedCompany] = Field(
        description=f"Exactly {SCREEN_COMPANY_COUNT} screened companies",
        min_length=SCREEN_COMPANY_COUNT,
        max_length=SCREEN_COMPANY_COUNT,
    )
    etfs: list[ScreenedETF] = Field(
        description=f"Exactly {SCREEN_ETF_COUNT} screened ETFs",
        min_length=SCREEN_ETF_COUNT,
        max_length=SCREEN_ETF_COUNT,
    )


class CompanyResearch(BaseModel):
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    pe_ratio: str = Field(description="P/E ratio and how it compares to peers")
    revenue_growth: str = Field(description="Revenue and earnings growth trends")
    valuation: str = Field(description="Valuation analysis including multiples and fair value view")
    technical_analysis: str = Field(description="Technical indicators, momentum, and chart trends")
    market_position: str = Field(description="Competitive position and moat")
    future_outlook: str = Field(description="Forward outlook and catalysts")
    investment_potential: str = Field(description="Overall investment potential and key risks")


class ETFResearch(BaseModel):
    name: str = Field(description="ETF or index fund name")
    ticker: str = Field(description="ETF ticker symbol")
    expense_ratio: str = Field(description="Expense ratio and fee comparison")
    strategy: str = Field(description="Index, thematic, or sector strategy")
    representative_holdings: str = Field(description="Top holdings and sector exposure")
    performance_summary: str = Field(description="Recent performance vs benchmark")
    technical_analysis: str = Field(description="Trend, volatility, and technical profile")
    market_position: str = Field(description="AUM, liquidity, and fund positioning")
    future_outlook: str = Field(description="Outlook for the fund strategy")
    investment_potential: str = Field(description="Overall investment potential and key risks")


class FundamentalsResearch(BaseModel):
    companies: list[CompanyResearch] = Field(
        description=f"Research on each of the {SCREEN_COMPANY_COUNT} screened companies",
        min_length=SCREEN_COMPANY_COUNT,
        max_length=SCREEN_COMPANY_COUNT,
    )
    etfs: list[ETFResearch] = Field(
        description=f"Research on each of the {SCREEN_ETF_COUNT} screened ETFs",
        min_length=SCREEN_ETF_COUNT,
        max_length=SCREEN_ETF_COUNT,
    )


class RecommendedCompany(BaseModel):
    rank: int = Field(description="Rank from 1 (highest conviction) downward")
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    pe_ratio: str = Field(description="P/E ratio at time of recommendation")
    rationale: str = Field(description="Why this company is recommended for investment")
    valuation: str = Field(description="Brief valuation summary")
    technical_analysis: str = Field(description="Brief technical analysis summary")
    outlook: str = Field(description="Brief future outlook summary")


class RecommendedETF(BaseModel):
    rank: int = Field(description="Rank from 1 (highest conviction) downward")
    name: str = Field(description="ETF or index fund name")
    ticker: str = Field(description="ETF ticker symbol")
    expense_ratio: str = Field(description="Expense ratio")
    rationale: str = Field(description="Why this fund is recommended")
    strategy: str = Field(description="Index, thematic, or sector strategy")
    representative_holdings: str = Field(
        description="Key holdings or exposure the fund provides"
    )


class InvestmentRecommendations(BaseModel):
    summary: str = Field(description="Executive summary of the investment thesis")
    companies: list[RecommendedCompany] = Field(
        description=f"Exactly {PICK_COMPANY_COUNT} ranked stock recommendations",
        min_length=PICK_COMPANY_COUNT,
        max_length=PICK_COMPANY_COUNT,
    )
    etfs: list[RecommendedETF] = Field(
        description=f"Exactly {PICK_ETF_COUNT} ranked ETF recommendation",
        min_length=PICK_ETF_COUNT,
        max_length=PICK_ETF_COUNT,
    )
    companies_not_selected: list[str] = Field(
        description="Screened companies not chosen, with brief reason each"
    )
    etfs_not_selected: list[str] = Field(
        description="Screened ETFs not chosen, with brief reason each"
    )


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def investment_screener(self) -> Agent:
        return Agent(
            config=self.agents_config['investment_screener'], # type: ignore[index]
            llm=get_llm(),
            verbose=True,
            tools=[SerperDevTool()],
            max_iter=3,
        )

    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'], # type: ignore[index]
            llm=get_llm(),
            verbose=True,
            tools=[SerperDevTool()],
            max_iter=4,
        )

    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'], # type: ignore[index]
            llm=get_llm(),
            verbose=True,
            tools=[send_html_email],
            max_iter=5,
        )

    @task
    def find_best_candidates(self) -> Task:
        return Task(
            config=self.tasks_config['find_best_candidates'], # type: ignore[index]
            output_pydantic=ScreenedUniverse,
        )

    @task
    def research_candidates(self) -> Task:
        return Task(
            config=self.tasks_config['research_candidates'], # type: ignore[index]
            output_pydantic=FundamentalsResearch,
        )

    @task
    def pick_best_companies(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_companies'], # type: ignore[index]
            output_pydantic=InvestmentRecommendations,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
