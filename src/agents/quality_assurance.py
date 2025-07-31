from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.prompt_library.system_messages import REVIEWER_SYSTEM_MESSAGE

def create_quality_assurance_team(model_client, human_input_function):
    """
    Creates Inner Team B: Quality Assurance Team
    """
    reviewer_agent = AssistantAgent(
        name='Reviewer',
        description='Quality reviewer for content assessment',
        model_client=model_client,
        system_message=REVIEWER_SYSTEM_MESSAGE
    )

    user_proxy_inner_b = UserProxyAgent(
        name='Human_QualityOverseer',
        description='Human oversight for quality decisions',
        input_func=human_input_function
    )

    inner_termination_b = TextMentionTermination(text="QUALITY_APPROVED")

    inner_team_b = RoundRobinGroupChat(
        participants=[reviewer_agent, user_proxy_inner_b],
        termination_condition=inner_termination_b,
        max_turns=3
    )

    return inner_team_b
