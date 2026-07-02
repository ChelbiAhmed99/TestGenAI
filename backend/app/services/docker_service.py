import asyncio
import random
from datetime import datetime


class DockerService:
    """
    Simulates running Playwright tests in a Docker container.
    In production, this would use the 'docker' Python SDK to spin up
    mcr.microsoft.com/playwright containers with the generated project.
    """

    _SCENARIO_NAMES = [
        "User Login Flow",
        "Dashboard Navigation",
        "Form Validation",
        "Search Functionality",
        "Profile Update",
        "Password Reset",
        "Data Export",
        "Session Management",
    ]

    async def run_test_container(self, script_code: str, tool: str = "playwright") -> dict:
        """
        Simulates running a test script in a Docker container with
        realistic Playwright-style output.
        """
        # Simulate execution time (2-6 seconds)
        exec_time = round(random.uniform(2.0, 6.0), 1)
        await asyncio.sleep(exec_time)

        # Determine outcome (85% pass rate for realism)
        success = random.random() > 0.15
        num_tests = random.randint(3, 8)
        duration_ms = int(exec_time * 1000)

        if success:
            test_lines = []
            for i in range(num_tests):
                name = random.choice(self._SCENARIO_NAMES)
                t = random.randint(200, 1800)
                test_lines.append(f"  ✓  {name} ({t}ms)")

            output = (
                f"Running {num_tests} tests using {num_tests} workers\n"
                f"\n"
                + "\n".join(test_lines) + "\n"
                f"\n"
                f"  {num_tests} passed ({exec_time}s)\n"
                f"\n"
                f"──────────────────────────────────────────\n"
                f"  Playwright Test Report\n"
                f"  Status:   ✅ ALL PASSED\n"
                f"  Tests:    {num_tests} passed, 0 failed\n"
                f"  Duration: {exec_time}s\n"
                f"  Workers:  {min(num_tests, 4)}\n"
                f"──────────────────────────────────────────"
            )
        else:
            passed = num_tests - random.randint(1, min(3, num_tests))
            failed = num_tests - passed
            test_lines = []
            fail_idx = random.sample(range(num_tests), failed)
            for i in range(num_tests):
                name = random.choice(self._SCENARIO_NAMES)
                t = random.randint(200, 2500)
                if i in fail_idx:
                    test_lines.append(f"  ✗  {name} ({t}ms)")
                    test_lines.append(f"     Error: Expected element [data-test=\"submit-btn\"] to be visible")
                    test_lines.append(f"     at tests/generated.spec.ts:42:5")
                else:
                    test_lines.append(f"  ✓  {name} ({t}ms)")

            output = (
                f"Running {num_tests} tests using {min(num_tests, 4)} workers\n"
                f"\n"
                + "\n".join(test_lines) + "\n"
                f"\n"
                f"  {passed} passed, {failed} failed ({exec_time}s)\n"
                f"\n"
                f"──────────────────────────────────────────\n"
                f"  Playwright Test Report\n"
                f"  Status:   ❌ {failed} FAILURE(S)\n"
                f"  Tests:    {passed} passed, {failed} failed\n"
                f"  Duration: {exec_time}s\n"
                f"  Workers:  {min(num_tests, 4)}\n"
                f"──────────────────────────────────────────"
            )

        coverage = random.randint(82, 98) if success else random.randint(45, 75)
        bugs = 0 if success else random.randint(1, failed)

        return {
            "status": "passed" if success else "failed",
            "output": output,
            "duration": int(exec_time),
            "kpis": {
                "coverage": coverage,
                "bugs_detected": bugs,
                "time_saved": random.randint(30, 120),  # minutes saved vs manual
            }
        }


docker_service = DockerService()
