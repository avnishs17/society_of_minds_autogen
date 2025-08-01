import sys
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, SocietyOfMindAgent
from functools import partial
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.prompt_library.system_messages import WRITER_SYSTEM_MESSAGE, EDITOR_SYSTEM_MESSAGE, REVIEWER_SYSTEM_MESSAGE
from logger import logger
from custom_exception.custom_exception import AgentCreationError, TeamCreationError

async def create_content_creation_team(model_client, human_input_function):
    """
    Creates Inner Team A: Content Creation Team
    """
    try:
        writer_agent = AssistantAgent(
            name='Writer',
            description='Expert content writer',
            model_client=model_client,
            system_message=WRITER_SYSTEM_MESSAGE
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="Writer", error=str(e))
        raise AgentCreationError("Writer", sys) from e
        
    try:
        editor_agent = AssistantAgent(
            name='Editor',
            description='Content editor for quality assurance',
            model_client=model_client,
            system_message=EDITOR_SYSTEM_MESSAGE
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="Editor", error=str(e))
        raise AgentCreationError("Editor", sys) from e
        
    try:
        user_proxy_inner_a = UserProxyAgent(
            name='Human_ContentOverseer',
            description='Human oversight for content decisions',
            input_func=partial(human_input_function, "Human_ContentOverseer")
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="Human_ContentOverseer", error=str(e))
        raise AgentCreationError("Human_ContentOverseer", sys) from e
        
    try:
        inner_termination_a = TextMentionTermination("APPROVE")
        
        inner_team_a = RoundRobinGroupChat(
            participants=[writer_agent, editor_agent, user_proxy_inner_a],
            termination_condition=inner_termination_a,
            max_turns=8
        )
        
        return inner_team_a
    except Exception as e:
        logger.error("team_creation_error", team_name="Content Creation Team", error=str(e))
        raise TeamCreationError("Content Creation Team", sys) from e

async def create_quality_assurance_team(model_client):
    """
    Creates Inner Team B: Quality Assurance Team
    """
    try:
        reviewer_agent = AssistantAgent(
            name='Reviewer',
            description='Quality reviewer for content assessment',
            model_client=model_client,
            system_message=REVIEWER_SYSTEM_MESSAGE
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="Reviewer", error=str(e))
        raise AgentCreationError("Reviewer", sys) from e
        
    try:
        inner_team_b = RoundRobinGroupChat(
            participants=[reviewer_agent],
            max_turns=1
        )
        
        return inner_team_b
    except Exception as e:
        logger.error("team_creation_error", team_name="Quality Assurance Team", error=str(e))
        raise TeamCreationError("Quality Assurance Team", sys) from e

async def create_outer_team_coordination(model_client, human_input_function):
    """
    Creates the outer team structure.
    """
    try:
        content_team = await create_content_creation_team(model_client, human_input_function)
        quality_team = await create_quality_assurance_team(model_client)
        
        som_content_agent = SocietyOfMindAgent(
            name="ContentTeam_SoM",
            team=content_team,
            model_client=model_client,
            response_prompt='Summarize the content creation process and provide the final content.'
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="ContentTeam_SoM", error=str(e))
        raise AgentCreationError("ContentTeam_SoM", sys) from e
        
    try:
        outer_user_proxy = UserProxyAgent(
            name='Human_ProjectOverseer',
            description='Human oversight for final decisions',
            input_func=partial(human_input_function, "Human_ProjectOverseer")
        )
    except Exception as e:
        logger.error("agent_creation_error", agent_name="Human_ProjectOverseer", error=str(e))
        raise AgentCreationError("Human_ProjectOverseer", sys) from e
        
    try:
        outer_termination = TextMentionTermination("FINAL_APPROVAL")

        outer_team = RoundRobinGroupChat(
            participants=[som_content_agent, quality_team, outer_user_proxy],
            termination_condition=outer_termination,
            max_turns=10
        )
        
        return outer_team, content_team, quality_team
    except Exception as e:
        logger.error("team_creation_error", team_name="Outer Team", error=str(e))
        raise TeamCreationError("Outer Team", sys) from e
