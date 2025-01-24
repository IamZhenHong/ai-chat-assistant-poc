from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, Base, get_db
from openai import OpenAI
import os
from dotenv import load_dotenv
from sqlalchemy import desc
import json
from typing import List

# Load environment variables
load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# Initialize FastAPI
app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)


@app.post("/targets/", response_model=schemas.TargetOut)
def create_target(target: schemas.TargetCreate, db: Session = Depends(get_db)):
    db_target = models.Target(**target.dict())
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


@app.get("/targets/", response_model=List[schemas.TargetOut])
def get_all_targets(db: Session = Depends(get_db)):
    """
    Fetch all targets from the database.
    """
    return db.query(models.Target).all()


@app.put("/targets/{target_id}", response_model=schemas.TargetOut)
def update_target(
    target_id: int, updated_target: schemas.TargetCreate, db: Session = Depends(get_db)
):
    """
    Update an existing target's details.
    """
    target = db.query(models.Target).filter(models.Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    for key, value in updated_target.dict().items():
        setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return target


# Routes for Love Analysis
@app.post("/love_analysis/", response_model=schemas.LoveAnalysisOut)
def create_love_analysis(
    love_analysis: schemas.LoveAnalysisCreate, db: Session = Depends(get_db)
):
    if not love_analysis.target_id:
        raise HTTPException(status_code=400, detail="Target ID is required.")

    new_convo_snippet = models.ConversationSnippet(
        content=love_analysis.convo, target_id=love_analysis.target_id
    )
    db.add(new_convo_snippet)
    db.commit()
    db.refresh(new_convo_snippet)

    target = (
        db.query(models.Target)
        .filter(models.Target.id == love_analysis.target_id)
        .first()
    )

    previous_love_analysis = (
        db.query(models.LoveAnalysis)
        .order_by(desc(models.LoveAnalysis.created_at))
        .first()
    )

    previous_love_analysis_content = (
        previous_love_analysis.content if previous_love_analysis else "None"
    )

    try:
        prompt = f"""
        You are a love coach who is very good at analysing the relationship dynamics, personalities, latent feeling and of both parties.  I'm your client seeking your advice. 
        ###
        Analyse previous love_analysis_content and chat history example provided and output the following analysis
        1. general relationship dynamic
        2. how I present myself in front of the other party
        3. how the other party most likely see me and feel about me; 
        4. what the other party most likely need from our interaction or relationship
        5. my personalities shown in the conversation
        6.  the other party's personality shown in the conversation
        7.  what the other party are likely to do next in our interactions
        8. overall advice if I want to achieve my relationship goals
        9. How have the relationship dynamics changed since the last conversation
        ###
        Previous Love Analysis:
        {previous_love_analysis_content}

        Current Conversation:
        {love_analysis.convo}

        New Love Analysis:
        """

        # Call the OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o",
            store=True,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""Output in {target.language}:"""},
            ],
        )
        current_love_analysis_content = completion.choices[0].message.content

        new_love_analysis = models.LoveAnalysis(
            convo=love_analysis.convo,
            content=current_love_analysis_content,
            target_id=love_analysis.target_id,
        )

        db.add(new_love_analysis)
        db.commit()
        db.refresh(new_love_analysis)
        return schemas.LoveAnalysisOut(content=current_love_analysis_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure OpenAI error: {str(e)}")


# Routes for Chat Strategy
@app.post("/chat_strategies/", response_model=schemas.ChatStrategyOut)
def create_chat_strategy(
    chat_strategy: schemas.ChatStrategyCreate, db: Session = Depends(get_db)
):
    target = (
        db.query(models.Target)
        .filter(models.Target.id == chat_strategy.target_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    latest_love_analysis = (
        db.query(models.LoveAnalysis)
        .order_by(desc(models.LoveAnalysis.created_at))
        .first()
    )
    latest_convo_snippet = (
        db.query(models.ConversationSnippet)
        .order_by(desc(models.ConversationSnippet.created_at))
        .first()
    )
    latest_chat_strategy = (
        db.query(models.ChatStrategy)
        .order_by(desc(models.ChatStrategy.created_at))
        .first()
    )

    if not latest_love_analysis or not latest_convo_snippet:
        raise HTTPException(
            status_code=404,
            detail="Latest Love Analysis or Conversation Snippet not found",
        )

    latest_chat_strategy_content = (
        latest_chat_strategy.content if latest_chat_strategy else "None"
    )
    latest_love_analysis_content = (
        latest_love_analysis.content if latest_love_analysis else "None"
    )
    latest_convo_snippet_content = (
        latest_convo_snippet.content if latest_convo_snippet else "None"
    )

    system_prompt = f"""
        You are a love coach who is very good at helping clients come up with the right strategy and exact reply in communication to reach their short-term and long-term relationship goals. I'm your client seeking your advice.

        Come up with a communication strategy that is brief, easy to follow, and actionable for me to talk to {target.name} based on the context below.
        Output in {target.language}:
        Context: 
        """
    system_prompt += f"""
        my gender: {target.gender}
        I'm talking to {target.name} online
        {target.name}'s gender: {target.gender}
        {target.name}'s personality: {target.personality}
        relationship context: {target.relationship_context}
        my feelings about our relationship: {target.relationship_perception}
        my short-term goal with {target.name}: {target.relationship_goals}
        my long-term goal with {target.name}: {target.relationship_goals_long}
        relationship dynamics:
        {latest_love_analysis_content}
        Last conversation snippet: {latest_convo_snippet_content}
        Last chat strategy: {latest_chat_strategy_content}
        """

    user_prompt = f""" Output in {target.language}: """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        store=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=schemas.ChatStrategyOut,
    )

    chat_strategy_content = completion.choices[0].message.parsed.content

    new_chat_strategy = models.ChatStrategy(
        convo=latest_convo_snippet_content,
        love_analysis=latest_love_analysis_content,
        content=chat_strategy_content,
        target_id=chat_strategy.target_id,
    )
    db.add(new_chat_strategy)
    db.commit()
    db.refresh(new_chat_strategy)
    return new_chat_strategy


# Routes for Reply Options Flow
@app.post("/reply_options_flow/", response_model=schemas.ReplyOptionsOut)
def create_reply_options_flow(
    reply_options: schemas.ReplyOptionsCreate, db: Session = Depends(get_db)
):

    target = (
        db.query(models.Target)
        .filter(models.Target.id == reply_options.target_id)
        .first()
    )

    latest_convo_snippet = (
        db.query(models.ConversationSnippet)
        .order_by(desc(models.ConversationSnippet.created_at))
        .first()
    )
    latest_chat_strategy = (
        db.query(models.ChatStrategy)
        .order_by(desc(models.ChatStrategy.created_at))
        .first()
    )

    latest_love_analysis = (
        db.query(models.LoveAnalysis)
        .order_by(desc(models.LoveAnalysis.created_at))
        .first()
    )

    latest_love_analysis_content = (
        latest_love_analysis.content if latest_love_analysis else "None"
    )
    latest_convo_snippet_content = (
        latest_convo_snippet.content if latest_convo_snippet else "None"
    )
    latest_chat_strategy_content = (
        latest_chat_strategy.content if latest_chat_strategy else "None"
    )

    system_prompt = f"""
        You are a love coach who is very good at helping clients come up with the right strategy and exact reply in communication to reach their short-term and long-term relationship goals. I'm your client seeking your advice.

        Write 4 distinguishable reply options for me to {target.name} as my next reply in the current conversation dialog; based on the communication strategy and context below. Each reply option should explore different directions or aspects of the interaction.
        Output in {target.language}:
        ###
        Current conversation dialog: \"\"\" 
        {latest_convo_snippet_content}
        \"\"\"
        Communication strategy: \"\"\" 
        {latest_chat_strategy_content}
        \"\"\"
        Context: \"\"\" 
        my gender: male
        I'm talking to {target.name} online
        {target.name}'s gender: {target.gender}
        {target.name}'s personality: {target.personality}
        relationship context: {target.relationship_context}
        my feelings about our relationship: {target.relationship_perception}
        my short-term goal with {target.name}: {target.relationship_goals}
        my long-term goal with {target.name}: {target.relationship_goals_long}
        relationship dynamic: {latest_love_analysis_content}
        \"\"\"
        ###
        """

    user_prompt = f""" Output in {target.language}: """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        store=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=schemas.ReplyOptionsOut,
    )

    new_reply_options_flow = models.ReplyOptionsFlow(
        chat_strategy=latest_chat_strategy_content,
        convo=latest_convo_snippet_content,
        option1=completion.choices[0].message.parsed.option1,
        option2=completion.choices[0].message.parsed.option2,
        option3=completion.choices[0].message.parsed.option3,
        option4=completion.choices[0].message.parsed.option4,
        target_id=reply_options.target_id,
    )

    db.add(new_reply_options_flow)
    db.commit()
    db.refresh(new_reply_options_flow)
    return schemas.ReplyOptionsOut(
        option1=completion.choices[0].message.parsed.option1,
        option2=completion.choices[0].message.parsed.option2,
        option3=completion.choices[0].message.parsed.option3,
        option4=completion.choices[0].message.parsed.option4,
    )
