import os
import traceback
from datetime import datetime, timezone

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelRequest, SystemPromptPart, ToolReturnPart

from sidekick import config, session
from sidekick.tools import fetch, read_file, run_command, update_file, web_search, write_file
from sidekick.utils import telemetry, ui
from sidekick.utils.system import get_cwd, list_cwd


class MainAgent:
    def __init__(self):
        self.agent = None
        self.agent_tools = None

    def _get_model_settings(self):
        if session.current_model.startswith("anthropic"):
            return {"max_tokens": 5000}
        return None

    def _check_for_confirmation(self, node, agent_run):
        for part in node.model_response.parts:
            if part.part_kind == "tool-call":
                try:
                    ui.confirm(part, node)
                except ui.UserAbort:
                    self._patch_tool_message(part.tool_name, part.tool_call_id)
                    raise

    def _patch_tool_message(self, tool_name, tool_call_id):
        """
        If a tool is cancelled, we need to patch a response otherwise
        some models will throw an error.
        """
        session.messages.append(
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name=tool_name,
                        content="Operation aborted by user.",
                        tool_call_id=tool_call_id,
                        timestamp=datetime.now(timezone.utc),
                        part_kind="tool-return",
                    )
                ],
                kind="request",
            )
        )

    def _inject_prompt(self, name: str) -> str:
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(package_dir, "prompts", f"{name}.txt")
        with open(filepath, "r", encoding="utf-8") as f:
            system_prompt = f.read()
            return SystemPromptPart(content=system_prompt)

    def _inject_cwd(self):
        return SystemPromptPart(content=f"Current working directory: {get_cwd()}")

    def _inject_cwd_list(self):
        return SystemPromptPart(content=f"Files in current directory:\n{list_cwd()}")

    def _inject_guide(self):
        cwd = get_cwd()
        filepath = os.path.join(cwd, config.GUIDE_FILE)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                content = (
                    "The user has provided a guide below. "
                    "It takes precedence over the previous system prompt:\n\n"
                    f"{content}"
                )
                return SystemPromptPart(content=content)
        return None

    def _inject_prompts(self):
        """
        Inject system prompts and guide using a "JIT" style injection so the
        prompts are always the last messages before a user request.
        """
        parts = [
            self._inject_prompt("system"),
            self._inject_cwd(),
            self._inject_cwd_list(),
        ]
        guide_part = self._inject_guide()

        if guide_part is not None:
            parts.append(guide_part)

        return session.messages + [
            ModelRequest(
                parts=parts,
                kind="request",
            )
        ]

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
            instrument=True,
        )

    def get_agent(self):
        ui.status(f"Agent({session.current_model})")
        if not hasattr(session.agents, session.current_model):
            session.agents[session.current_model] = self.create_agent()
        return session.agents[session.current_model]

    def switch_model(self, model_index):
        try:
            model_ids = list(config.MODELS.keys())
            session.current_model = model_ids[int(model_index)]
            self.agent = self.get_agent()
            ui.agent(f"I'm now using model: {session.current_model}", bottom=1)
        except IndexError:
            ui.error(f"Invalid model index: {model_index}")

    async def process_request(self, req, compact=False):
        try:
            if not self.agent:
                self.agent = self.get_agent()

            message_history = self._inject_prompts()
            async with self.agent.iter(req, message_history=message_history) as agent_run:
                async for node in agent_run:
                    if hasattr(node, "request"):
                        session.messages.append(node.request)
                    if hasattr(node, "model_response"):
                        session.messages.append(node.model_response)
                        self._check_for_confirmation(node, agent_run)

                if compact:
                    session.messages = [session.messages[-1]]
                    ui.show_banner()

                ui.agent(agent_run.result.data)
                self._calc_usage(agent_run)
        except ui.UserAbort:
            ui.status("Operation aborted.\n")
        except UnexpectedModelBehavior as e:
            telemetry.capture_exception(e)
            ui.error(f"Model behavior error: {e.message}")
        except Exception as e:
            telemetry.capture_exception(e)
            ui.error(traceback.format_exc())

    def _calc_usage(self, agent_run):
        data = agent_run.usage()
        details = data.details or {}
        cached_tokens = details.get("cached_tokens", 0)
        non_cached_input = data.request_tokens - cached_tokens

        model_ids = list(config.MODELS.keys())
        pricing = config.MODELS.get(session.current_model, config.MODELS[model_ids[0]])["pricing"]

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
