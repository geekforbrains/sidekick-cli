import os

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from sidekick import config, session
from sidekick.tools import fetch, read_file, run_command, update_file, web_search, write_file
from sidekick.utils import ui
from sidekick.utils.system import get_cwd, list_cwd


class MainAgent:
    def __init__(self):
        self.agent = None
        self.agent_tools = None

    def _get_prompt(self, name: str) -> str:
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(package_dir, "prompts", f"{name}.txt")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def _get_model_settings(self):
        if session.current_model.startswith("anthropic"):
            return {"max_tokens": 5000}
        return None

    def create_agent(self) -> Agent:
        return Agent(
            model=session.current_model,
            tools=[
                fetch,
                read_file,
                run_command,
                update_file,
                web_search,
                write_file,
            ],
            model_settings=self._get_model_settings(),
            system_prompt=[
                self._get_prompt("system"),
                f"Current working directory: {get_cwd()}",
                f"Current directory contents:\n{list_cwd()}",
            ],
            instrument=True,
        )

    def get_agent(self):
        ui.status(f"Agent({session.current_model})")
        if not hasattr(session.agents, session.current_model):
            session.agents[session.current_model] = self.create_agent()
        return session.agents[session.current_model]

    def switch_model(self, model_index):
        try:
            session.current_model = config.models[int(model_index)]
            self.agent = self.get_agent()
            ui.agent(f"I'm now using model: {session.current_model}", bottom=1)
        except IndexError:
            ui.error(f"Invalid model index: {model_index}")

    async def process_request(self, req):
        hist = session.messages.copy()
        try:
            if not self.agent:
                self.agent = self.get_agent()

            async with self.agent.iter(req, message_history=hist) as agent_run:
                async for node in agent_run:
                    if hasattr(node, "request"):
                        hist.append(node.request)
                    if hasattr(node, "model_response"):
                        hist.append(node.model_response)
                ui.agent(agent_run.result.data)
                self._calc_usage(agent_run)
        except UnexpectedModelBehavior as e:
            ui.error(f"Model behavior error: {e.message}")
        except Exception as e:
            ui.error(f"Unexpected error: {e}")
        finally:
            session.messages = hist

    def _calc_usage(self, agent_run):
        data = agent_run.usage()
        details = data.details or {}
        cached_tokens = details.get("cached_tokens", 0)
        non_cached_input = data.request_tokens - cached_tokens

        pricing = config.model_pricing.get(
            session.current_model, config.model_pricing[config.default_model]
        )

        input_cost = non_cached_input / 1_000_000 * pricing["input"]
        cached_input_cost = cached_tokens / 1_000_000 * pricing["cached_input"]
        output_cost = data.response_tokens / 1_000_000 * pricing["output"]
        request_cost = input_cost + cached_input_cost + output_cost
        session.total_cost += request_cost

        msg = (
            f"Reqs: {data.requests}, "
            f"Tokens(Req/Cache/Resp): "
            f"{data.request_tokens}/"
            f"{cached_tokens}/"
            f"{data.response_tokens}, "
            f"Cost(Req/Total): ${request_cost:.5f}/${session.total_cost:.5f}"
        )
        ui.show_usage(msg)
