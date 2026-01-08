"""API endpoints for parser management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from uuid import UUID

from backend.core.database.database import get_session
from backend.core.database.models import Parser, ParserPublic, ParserBase, Plugin
from backend.plugin_manager import plugin_manager


router = APIRouter(prefix="/parsers", tags=["parsers"])


@router.get("", response_model=list[ParserPublic])
async def list_parsers(*, session: Session = Depends(get_session)):
    """Get all configured parsers."""
    parsers = session.exec(select(Parser)).all()
    return parsers


@router.post("", response_model=ParserPublic)
async def create_parser(*, session: Session = Depends(get_session), parser: ParserBase):
    """Create a new parser configuration."""
    # Verify the plugin exists
    plugin = session.get(Plugin, parser.plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Verify the plugin can provide this parser
    plugin_instance = plugin_manager.get_plugin(plugin.name)
    if not plugin_instance:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin.name}' not loaded")
    
    try:
        # Test that the parser can be created
        parser_instance = plugin_instance.create_parser(parser.config or {})
    except NotImplementedError:
        raise HTTPException(
            status_code=400, 
            detail=f"Plugin '{plugin.name}' does not support parsers"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to create parser: {str(e)}"
        )
    
    db_parser = Parser.model_validate(parser)
    session.add(db_parser)
    session.commit()
    session.refresh(db_parser)
    return db_parser


@router.get("/{parser_id}", response_model=ParserPublic)
async def get_parser(*, session: Session = Depends(get_session), parser_id: UUID):
    """Get a specific parser by ID."""
    parser = session.get(Parser, parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Parser not found")
    return parser


@router.patch("/{parser_id}", response_model=ParserPublic)
async def update_parser(
    *, 
    session: Session = Depends(get_session), 
    parser_id: UUID, 
    parser_update: ParserBase
):
    """Update a parser configuration."""
    db_parser = session.get(Parser, parser_id)
    if not db_parser:
        raise HTTPException(status_code=404, detail="Parser not found")
    
    # Update fields
    parser_data = parser_update.model_dump(exclude_unset=True)
    for key, value in parser_data.items():
        setattr(db_parser, key, value)
    
    session.add(db_parser)
    session.commit()
    session.refresh(db_parser)
    return db_parser


@router.delete("/{parser_id}")
async def delete_parser(*, session: Session = Depends(get_session), parser_id: UUID):
    """Delete a parser."""
    parser = session.get(Parser, parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Parser not found")
    
    session.delete(parser)
    session.commit()
    return {"ok": True}


@router.patch("/{parser_id}/toggle")
async def toggle_parser(*, session: Session = Depends(get_session), parser_id: UUID):
    """Toggle a parser's enabled state."""
    parser = session.get(Parser, parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Parser not found")
    
    parser.enabled = not parser.enabled
    session.add(parser)
    session.commit()
    session.refresh(parser)
    return parser
