import pathlib
import dotenv
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()

# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "evalset_file",
#     [
#         pytest.param(f, id=f.stem)
#         for f in (pathlib.Path(__file__).parent / "data").rglob("*.evalset.json")
#     ],
# )
# async def test_all(evalset_file):
#     await AgentEvaluator.evaluate(
#         agent_module="autopilot",
#         eval_dataset_file_path_or_dir=str(evalset_file),
#         num_runs=1,
#     )

@pytest.mark.asyncio
async def test_all():
    await AgentEvaluator.evaluate(
        agent_module="autopilot",
        eval_dataset_file_path_or_dir=str(pathlib.Path(__file__).parent / "data/authn_agent/01.evalset.json"),
        num_runs=1,
    )