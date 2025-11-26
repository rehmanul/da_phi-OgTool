"""Persona management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.models import PersonaCreate, PersonaUpdate, PersonaResponse
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid

router = APIRouter()


@router.get("", response_model=List[PersonaResponse])
async def list_personas(
    active: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all personas"""
    query = """
        SELECT id, organization_id, name, description, voice_profile,
               system_prompt, example_responses, temperature, max_tokens,
               active, created_at
        FROM personas
        WHERE organization_id = $1
    """
    params = [current_user.organization_id]

    if active is not None:
        query += " AND active = $2"
        params.append(active)

    query += " ORDER BY created_at DESC"

    rows = await db.fetch(query, *params)
    return [PersonaResponse(**dict(row)) for row in rows]


@router.post("", response_model=PersonaResponse, status_code=201)
async def create_persona(
    persona_data: PersonaCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new persona"""
    # Check tier limits
    count = await db.fetchval(
        "SELECT COUNT(*) FROM personas WHERE organization_id = $1 AND active = true",
        current_user.organization_id,
    )

    limits = {"starter": 1, "growth": 3, "enterprise": 999}
    if count >= limits.get(current_user.tier, 1):
        raise HTTPException(
            status_code=403,
            detail=f"Persona limit reached for {current_user.tier} tier",
        )

    persona_id = await db.fetchval(
        """
        INSERT INTO personas (
            organization_id, name, description, voice_profile, system_prompt,
            example_responses, temperature, max_tokens
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """,
        current_user.organization_id,
        persona_data.name,
        persona_data.description,
        persona_data.voice_profile,
        persona_data.system_prompt,
        persona_data.example_responses,
        persona_data.temperature,
        persona_data.max_tokens,
    )

    # Link knowledge bases
    if persona_data.knowledge_base_ids:
        for kb_id in persona_data.knowledge_base_ids:
            await db.execute(
                "INSERT INTO persona_knowledge_bases (persona_id, knowledge_base_id) VALUES ($1, $2)",
                persona_id,
                kb_id,
            )

    row = await db.fetchrow("SELECT * FROM personas WHERE id = $1", persona_id)
    return PersonaResponse(**dict(row))


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific persona"""
    row = await db.fetchrow(
        "SELECT * FROM personas WHERE id = $1 AND organization_id = $2",
        persona_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Persona not found")

    return PersonaResponse(**dict(row))


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: uuid.UUID,
    persona_data: PersonaUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Update a persona"""
    # Check exists
    existing = await db.fetchval(
        "SELECT id FROM personas WHERE id = $1 AND organization_id = $2",
        persona_id,
        current_user.organization_id,
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Build update query
    update_fields = []
    params = []
    param_count = 1

    update_data = persona_data.dict(exclude_unset=True, exclude={"knowledge_base_ids"})
    for field, value in update_data.items():
        update_fields.append(f"{field} = ${param_count}")
        params.append(value)
        param_count += 1

    if update_fields:
        params.append(persona_id)
        query = f"UPDATE personas SET {', '.join(update_fields)} WHERE id = ${param_count}"
        await db.execute(query, *params)

    # Update knowledge base links if provided
    if persona_data.knowledge_base_ids is not None:
        await db.execute(
            "DELETE FROM persona_knowledge_bases WHERE persona_id = $1", persona_id
        )
        for kb_id in persona_data.knowledge_base_ids:
            await db.execute(
                "INSERT INTO persona_knowledge_bases (persona_id, knowledge_base_id) VALUES ($1, $2)",
                persona_id,
                kb_id,
            )

    row = await db.fetchrow("SELECT * FROM personas WHERE id = $1", persona_id)
    return PersonaResponse(**dict(row))


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a persona"""
    result = await db.execute(
        "DELETE FROM personas WHERE id = $1 AND organization_id = $2",
        persona_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Persona not found")

    return None
