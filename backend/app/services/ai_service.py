import os
import re
import sys
import json
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# Add /core to Python path so we can import the prompt/validation modules
CORE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "core")
CORE_DIR = os.path.abspath(CORE_DIR)
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

from prompt_loader import build_gherkin_messages, build_test_script_messages
from gherkin_validator import validate_gherkin_json, validate_gherkin_text, json_to_gherkin

JIRA_BASE_URL   = os.getenv("JIRA_BASE_URL", "")    # e.g. https://mycompany.atlassian.net
JIRA_API_TOKEN  = os.getenv("JIRA_API_TOKEN", "")
JIRA_EMAIL      = os.getenv("JIRA_EMAIL", "")


class AIService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model   = "gemini-2.0-flash"
        if self.api_key:
            print(f"✓ AIService initialized with model {self.model}")
        else:
            print("⚠ AIService: GOOGLE_API_KEY NOT FOUND — AI features disabled")

    def _get_llm(self, temperature: float = 0.1, timeout: int = 30, model_override: Optional[str] = None, api_key_override: Optional[str] = None):
        """Create a configured LLM instance."""
        target_model = model_override if model_override else self.model
        
        # Auto-migrate deprecated Llama 3 models
        if target_model and "llama3-" in target_model:
            target_model = "llama-3.3-70b-versatile" if "70b" in target_model else "llama-3.1-8b-instant"

        target_api_key = api_key_override if api_key_override else self.api_key

        if target_model.startswith("llama"):
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=target_api_key,
                model_name=target_model,
                temperature=temperature,
                timeout=timeout
            )

        return ChatGoogleGenerativeAI(
            google_api_key=target_api_key,
            model=target_model,
            temperature=temperature,
            timeout=timeout
        )

    # ------------------------------------------------------------------ #
    #   Jira ingestion                                                     #
    # ------------------------------------------------------------------ #
    async def fetch_jira_story(self, jira_url: str) -> str:
        """
        Fetches the description of a Jira issue from its URL.
        Requires JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN env vars.
        Falls back to a demo description if credentials are absent.
        """
        import httpx, base64

        # Extract issue key, e.g. "PROJ-123" from any Jira URL
        match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", jira_url)
        if not match:
            raise ValueError(f"Cannot parse Jira issue key from URL: {jira_url}")
        issue_key = match.group(1)

        if not JIRA_BASE_URL or not JIRA_API_TOKEN:
            # Demo mode
            return (
                f"[DEMO] Jira Issue: {issue_key}\n"
                "As a registered user, I want to log in with my credentials\n"
                "So that I can access my personalised dashboard.\n\n"
                "Acceptance Criteria:\n"
                "- Valid credentials redirect to dashboard\n"
                "- Invalid credentials show an error\n"
                "- Empty fields show validation errors"
            )

        creds = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
        headers = {"Authorization": f"Basic {creds}", "Accept": "application/json"}
        api_url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{issue_key}"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(api_url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Jira API error {resp.status_code}: {resp.text}")
            data = resp.json()
            fields = data.get("fields", {})
            summary     = fields.get("summary", "")
            description = fields.get("description") or {}
            # Jira Cloud returns ADF (Atlassian Document Format); extract plain text
            plain = self._adf_to_text(description) if isinstance(description, dict) else str(description)
            return f"{summary}\n\n{plain}"

    def _adf_to_text(self, node: dict, depth: int = 0) -> str:
        """Recursively converts Atlassian Document Format to plain text."""
        text = ""
        if isinstance(node, dict):
            if node.get("type") == "text":
                text += node.get("text", "")
            for child in node.get("content", []):
                text += self._adf_to_text(child, depth + 1)
            if node.get("type") in ("paragraph", "heading", "bulletList", "listItem"):
                text += "\n"
        return text

    # ------------------------------------------------------------------ #
    #   Gherkin Generation (using prompt catalog + validator)              #
    # ------------------------------------------------------------------ #
    async def generate_gherkin(self, requirement_content: str, model_override: Optional[str] = None, api_key_override: Optional[str] = None) -> str:
        """
        Transforms a requirement (User Story/Doc) into Gherkin scenarios using Gemini AI.
        
        Uses the structured prompt catalog (core/prompts/gherkin_prompt.json) with
        few-shot examples, then validates the output with the Gherkin validator.
        """
        target_api_key = api_key_override if api_key_override else self.api_key
        if not target_api_key:
            return "ERROR: API key is not set. Please check your settings or .env file."

        try:
            # Build structured messages from the prompt catalog
            messages = build_gherkin_messages(requirement_content)
            
            # Convert to LangChain message objects
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                else:
                    lc_messages.append(HumanMessage(content=msg["content"]))
            
            llm = self._get_llm(temperature=0.1, timeout=45, model_override=model_override, api_key_override=api_key_override)
            response = await llm.ainvoke(lc_messages)
            
            # Clean up potential markdown wrapper
            content = response.content
            content = re.sub(r"```(json|gherkin)?\n", "", content)
            content = content.replace("```", "").strip()
            
            # Try to parse as JSON (structured output from prompt catalog)
            try:
                json_data = json.loads(content)
                
                # Validate the structured JSON
                errors = validate_gherkin_json(json_data)
                if errors:
                    print(f"⚠ Gherkin validation warnings: {errors}")
                
                # Convert validated JSON to raw Gherkin text
                gherkin_text = json_to_gherkin(json_data)
                return gherkin_text
                
            except json.JSONDecodeError:
                # AI returned raw Gherkin text instead of JSON — validate it directly
                errors = validate_gherkin_text(content)
                if errors:
                    print(f"⚠ Gherkin validation warnings: {errors}")
                return content
                
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return "ERROR: AI service timed out. Please try again."
            return f"Gemini API Error: {error_msg}"

    # ------------------------------------------------------------------ #
    #   Gherkin Generation — Structured JSON Output                       #
    # ------------------------------------------------------------------ #
    async def generate_gherkin_json(self, requirement_content: str, model_override: Optional[str] = None, api_key_override: Optional[str] = None) -> dict:
        """
        Like generate_gherkin() but returns the structured JSON directly
        for frontend display and human validation.
        """
        target_api_key = api_key_override if api_key_override else self.api_key
        if not target_api_key:
            return {"error": "API key is not set"}

        try:
            messages = build_gherkin_messages(requirement_content)
            
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                else:
                    lc_messages.append(HumanMessage(content=msg["content"]))
            
            llm = self._get_llm(temperature=0.1, timeout=45, model_override=model_override, api_key_override=api_key_override)
            response = await llm.ainvoke(lc_messages)
            
            content = response.content
            content = re.sub(r"```(json|gherkin)?\n", "", content)
            content = content.replace("```", "").strip()
            
            json_data = json.loads(content)
            
            # Validate
            errors = validate_gherkin_json(json_data)
            json_data["_validation"] = {
                "valid": len(errors) == 0,
                "errors": errors,
            }
            
            # Also include the raw Gherkin text
            json_data["_raw_gherkin"] = json_to_gherkin(json_data)
            
            return json_data
            
        except json.JSONDecodeError:
            return {"error": "AI did not return valid JSON", "raw": content}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------ #
    #   Test Script Generation (using prompt catalog)                      #
    # ------------------------------------------------------------------ #
    async def generate_test_script(self, gherkin: str, tool: str = "playwright", model_override: Optional[str] = None, api_key_override: Optional[str] = None) -> str:
        """
        Transforms Gherkin scenarios into automated test scripts using Gemini AI.
        
        Uses the structured prompt catalog for consistent, high-quality output.
        """
        target_api_key = api_key_override if api_key_override else self.api_key
        if not target_api_key:
            return "// ERROR: API key is not set. Please check your settings or .env file."

        if tool.lower() == "playwright":
            try:
                # Build messages from the prompt catalog
                messages = build_test_script_messages(gherkin)
                
                lc_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        lc_messages.append(SystemMessage(content=msg["content"]))
                    else:
                        lc_messages.append(HumanMessage(content=msg["content"]))
                
                llm = self._get_llm(temperature=0.1, timeout=45, model_override=model_override, api_key_override=api_key_override)
                response = await llm.ainvoke(lc_messages)
                
                # Remove markdown code blocks if present
                code = response.content
                code = re.sub(r"```(typescript|ts|javascript|js)?\n", "", code)
                code = code.replace("```", "").strip()
                return code
                
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    return "// ERROR: AI service timed out. Please try again."
                return f"// Gemini API Error: {error_msg}"

        return f"// Tool '{tool}' is not supported yet by the AI generator."

    # ------------------------------------------------------------------ #
    #   Self-Healing Pipeline                                              #
    # ------------------------------------------------------------------ #
    async def _llm_correct(self, system_prompt: str, user_prompt: str, model_override: Optional[str] = None, api_key_override: Optional[str] = None) -> str:
        """Send a correction request to the LLM."""
        llm = self._get_llm(temperature=0.1, timeout=45, model_override=model_override, api_key_override=api_key_override)
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return response.content

    async def generate_test_script_healed(
        self, gherkin: str, tool: str = "playwright", max_retries: int = 3, model_override: Optional[str] = None, api_key_override: Optional[str] = None
    ) -> dict:
        """
        Generate a test script with self-healing: validates TypeScript via
        tsc --noEmit, and if errors are found, sends them back to the LLM
        for correction up to max_retries times.

        Returns dict with 'code', 'healed', 'iterations', 'errors'.
        """
        from self_healer import SelfHealer

        # Step 1: Generate initial code
        code = await self.generate_test_script(gherkin, tool, model_override=model_override, api_key_override=api_key_override)

        if code.startswith("//"):
            return {"code": code, "healed": False, "iterations": 0, "errors": [code]}

        target_api_key = api_key_override if api_key_override else self.api_key
        if not target_api_key:
            return {"code": code, "healed": False, "iterations": 0, "errors": []}

        # Step 2: Run self-healing pipeline
        healer = SelfHealer(max_iterations=max_retries)
        
        async def custom_llm_correct(system_prompt: str, user_prompt: str) -> str:
            return await self._llm_correct(system_prompt, user_prompt, model_override, api_key_override)
            
        result = await healer.heal(
            code=code,
            filename="generated.spec.ts",
            llm_invoke=custom_llm_correct,
        )

        return {
            "code": result.final_code,
            "healed": result.success,
            "iterations": result.iterations,
            "original_had_errors": result.original_code != result.final_code,
            "errors": result.final_errors,
        }

ai_service = AIService()
