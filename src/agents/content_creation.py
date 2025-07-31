from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.prompt_library.system_messages import WRITER_SYSTEM_MESSAGE, EDITOR_SYSTEM_MESSAGE

def create_content_creation_team(model_client, human_input_function):
    """
    Creates Inner Team A: Content Creation Team
    """
    writer_agent = AssistantAgent(
        name='Writer',
        description='Expert content writer',
        model_client=model_client,
        system_message=WRITER_SYSTEM_MESSAGE
    )

    editor_agent = AssistantAgent(
        name='Editor',
        description='Content editor for quality assurance',
        model_client=model_client,
        system_message=EDITOR_SYSTEM_MESSAGE
    )

    user_proxy_inner_a = UserProxyAgent(
        name='Human_ContentOverseer',
        description='Human oversight for content decisions',
        input_func=human_input_function
    )

    inner_team_a = RoundRobinGroupChat(
        participants=[writer_agent, editor_agent, user_proxy_inner_a],
        termination_condition=TextMentionTermination(text="APPROVE"),
        max_turns=4
    )

    return inner_team_a
