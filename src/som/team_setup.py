from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, SocietyOfMindAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.prompt_library.system_messages import WRITER_SYSTEM_MESSAGE, EDITOR_SYSTEM_MESSAGE, REVIEWER_SYSTEM_MESSAGE

async def create_content_creation_team(model_client, human_input_function):
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
    
    inner_termination_a = TextMentionTermination("APPROVE")
    
    inner_team_a = RoundRobinGroupChat(
        participants=[writer_agent, editor_agent, user_proxy_inner_a],
        termination_condition=inner_termination_a,
        max_turns=8
    )
    
    return inner_team_a

async def create_quality_assurance_team(model_client):
    """
    Creates Inner Team B: Quality Assurance Team
    """
    reviewer_agent = AssistantAgent(
        name='Reviewer',
        description='Quality reviewer for content assessment',
        model_client=model_client,
        system_message=REVIEWER_SYSTEM_MESSAGE
    )
    
    inner_team_b = RoundRobinGroupChat(
        participants=[reviewer_agent],
        max_turns=1
    )
    
    return inner_team_b

async def create_outer_team_coordination(model_client, human_input_function):
    """
    Creates the outer team structure.
    """
    content_team = await create_content_creation_team(model_client, human_input_function)
    quality_team = await create_quality_assurance_team(model_client)
    
    som_content_agent = SocietyOfMindAgent(
        name="ContentTeam_SoM",
        team=content_team,
        model_client=model_client,
        response_prompt='Summarize the content creation process and provide the final content.'
    )
    
    som_quality_agent = SocietyOfMindAgent(
        name="QualityTeam_SoM",
        team=quality_team,
        model_client=model_client,
        response_prompt='Summarize the quality review process and provide final approval status.'
    )
    
    outer_user_proxy = UserProxyAgent(
        name='Human_ProjectOverseer',
        description='Human oversight for final decisions',
        input_func=human_input_function
    )
    
    outer_termination = TextMentionTermination("FINAL_APPROVAL")

    outer_team = RoundRobinGroupChat(
        participants=[som_content_agent, som_quality_agent, outer_user_proxy],
        termination_condition=outer_termination,
        max_turns=10
    )
    
    return outer_team, content_team, quality_team
