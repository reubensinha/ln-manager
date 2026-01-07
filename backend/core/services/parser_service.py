"""Service for parser operations."""

from typing import Optional
from uuid import UUID
from sqlmodel import Session, select

from backend.core.database.models import Parser, Plugin
from backend.core.plugins.parser import ParserPlugin
from backend.plugin_manager import plugin_manager
from backend.core.exceptions import ResourceNotFoundError
from backend.core.logging_config import get_logger


logger = get_logger(__name__)


def get_parser_instance(
    parser_id: UUID,
    session: Session
) -> tuple[Parser, ParserPlugin]:
    """Get a parser database record and its plugin instance.
    
    Args:
        parser_id: UUID of the parser
        session: Database session
        
    Returns:
        Tuple of (Parser record, ParserPlugin instance)
        
    Raises:
        ResourceNotFoundError: If parser or plugin not found
    """
    parser = session.get(Parser, parser_id)
    if not parser:
        raise ResourceNotFoundError(f"Parser with ID {parser_id} not found")
    
    if not parser.enabled:
        raise ResourceNotFoundError(f"Parser '{parser.name}' is disabled")
    
    plugin = session.get(Plugin, parser.plugin_id)
    if not plugin:
        raise ResourceNotFoundError(f"Plugin for parser '{parser.name}' not found")
    
    if not plugin.enabled:
        raise ResourceNotFoundError(f"Plugin '{plugin.name}' is disabled")
    
    plugin_instance = plugin_manager.get_plugin(plugin.name)
    if not plugin_instance:
        raise ResourceNotFoundError(f"Plugin '{plugin.name}' is not loaded")
    
    try:
        parser_instance = plugin_instance.create_parser(parser.config or {})
    except NotImplementedError:
        raise ResourceNotFoundError(f"Plugin '{plugin.name}' does not support parsers")
    except Exception as e:
        logger.error(f"Failed to create parser instance: {e}", exc_info=True)
        raise ResourceNotFoundError(f"Failed to create parser instance: {str(e)}")
    
    return parser, parser_instance


async def parse_content(
    parser_id: UUID,
    session: Session,
    title: Optional[str] = None,
    infohash: Optional[str] = None
) -> ParserPlugin.ParserResponseModel:
    """Parse content using a configured parser.
    
    Args:
        parser_id: UUID of the parser to use
        session: Database session (required)
        title: Optional title to parse
        infohash: Optional infohash to parse
        
    Returns:
        ParserResponseModel with parsed series, book, and chapter UUIDs
        
    Raises:
        ResourceNotFoundError: If parser not found or not available
        ValueError: If neither title nor infohash provided
    """
    if not title and not infohash:
        raise ValueError("Either title or infohash must be provided")
    
    if not session:
        raise ValueError("Database session is required")
    
    parser, parser_instance = get_parser_instance(parser_id, session)
    
    logger.info(f"Parsing content with parser '{parser.name}': title={title}, infohash={infohash}")
    
    try:
        result = await parser_instance.parse(title=title, infohash=infohash)
        logger.info(f"Parser '{parser.name}' returned: {result}")
        return result
    except Exception as e:
        logger.error(f"Parser '{parser.name}' failed: {e}", exc_info=True)
        raise


async def get_all_parsers(session: Session) -> list[Parser]:
    """Get all configured parsers.
    
    Args:
        session: Database session
        
    Returns:
        List of all Parser records
    """
    parsers = session.exec(select(Parser)).all()
    return list(parsers)


async def get_enabled_parsers(session: Session) -> list[Parser]:
    """Get all enabled parsers.
    
    Args:
        session: Database session
        
    Returns:
        List of enabled Parser records
    """
    parsers = session.exec(
        select(Parser).where(Parser.enabled == True)
    ).all()
    return list(parsers)
