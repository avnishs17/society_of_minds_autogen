from autogen_agentchat.agents import SocietyOfMindAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.prompt_library.system_messages import CONTENT_SOM_PROMPT, QUALITY_SOM_PROMPT
from src.agents.content_creation import create_content_creation_team
from src.agents.quality_assurance import create_quality_assurance_team
from custom_exception.custom_exception import TeamCreationError, AgentCreationError
import sys

def create_outer_team_coordination(model_client, content_input_func, quality_input_func, outer_input_func):
    """
    Creates the outer team structure.
    """
    try:
        inner_team_a = create_content_creation_team(model_client, content_input_func)
        inner_team_b = create_quality_assurance_team(model_client, quality_input_func)
    except Exception as e:
        raise TeamCreationError(f"Failed to create inner teams: {e}", sys) from e

    try:
        som_content_agent = SocietyOfMindAgent(
        name="ContentTeam_SoM",
        team=inner_team_a,
        model_client=model_client,
        response_prompt=CONTENT_SOM_PROMPT
        )

        som_quality_agent = SocietyOfMindAgent(
            name="QualityTeam_SoM",
            team=inner_team_b,
            model_client=model_client,
            response_prompt=QUALITY_SOM_PROMPT
        )

        outer_user_proxy = UserProxyAgent(
        name='Human_ProjectOverseer',
        description='Human oversight for final decisions',
        input_func=outer_input_func
        )
    except Exception as e:
        raise AgentCreationError(f"Failed to create SoM agents or UserProxy: {e}", sys) from e

    outer_termination = TextMentionTermination(text="FINAL_APPROVAL")

    outer_team = RoundRobinGroupChat(
        participants=[som_content_agent, som_quality_agent, outer_user_proxy],
        termination_condition=outer_termination,
        max_turns=10
    )

    return outer_team
