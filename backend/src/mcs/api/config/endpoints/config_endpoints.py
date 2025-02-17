"""Configuration service endpoints."""

from fastapi import APIRouter, Request, status, HTTPException
from loguru import logger

from mcs.api.config.models.config_models import (
    ConfigRequest,
    ConfigResponse,
    ConfigListResponse,
    SchemaRequest,
    SchemaResponse,
    SchemaListResponse,
    MessageResponse
)
from mcs.utils.errors import create_error


router = APIRouter(prefix="/config", tags=["config"])


@router.get(
    "/list",
    response_model=ConfigListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list configs"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def list_configs(request: Request) -> ConfigListResponse:
    """List available configurations."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        configs = await request.app.state.config_service.list_configs()
        return ConfigListResponse(configs=configs)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to list configs: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list configs: {str(e)}"
        )


@router.get(
    "/{name}",
    response_model=ConfigResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Config not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get config"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def get_config(name: str, request: Request) -> ConfigResponse:
    """Get configuration by name."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        config_data = await request.app.state.config_service.get_config(name)
        return ConfigResponse(
            name=name,
            format="json",  # Default format is now JSON
            data=config_data
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to get config {name}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get config {name}: {str(e)}"
        )


@router.put(
    "/{name}",
    response_model=MessageResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update config"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def update_config(name: str, config: ConfigRequest, request: Request) -> MessageResponse:
    """Update configuration."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        # Validate against schema if exists
        await request.app.state.config_service.validate_config(name, config.data)
        
        # Update config
        await request.app.state.config_service.update_config(name, config.data, config.format)
        
        return MessageResponse(message=f"Configuration {name} updated successfully")
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to update config {name}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update config {name}: {str(e)}"
        )


@router.post(
    "/validate/{name}",
    response_model=MessageResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to validate config"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def validate_config(name: str, config: ConfigRequest, request: Request) -> MessageResponse:
    """Validate configuration against schema."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        # Validate config
        await request.app.state.config_service.validate_config(name, config.data)
        return MessageResponse(message=f"Configuration {name} is valid")
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Validation failed for {name}: {e}")
        raise create_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Validation failed: {str(e)}"
        )


@router.get(
    "/schema/list",
    response_model=SchemaListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list schemas"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def list_schemas(request: Request) -> SchemaListResponse:
    """List available schemas."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        schemas = await request.app.state.config_service.list_schemas()
        return SchemaListResponse(schemas=schemas)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to list schemas: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list schemas: {str(e)}"
        )


@router.get(
    "/schema/{name}",
    response_model=SchemaResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Schema not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get schema"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def get_schema(name: str, request: Request) -> SchemaResponse:
    """Get schema by name."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        schema = await request.app.state.config_service.get_schema(name)
        if not schema:
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Schema not found: {name}"
            )
        
        return SchemaResponse(
            name=name,
            schema_definition=schema
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to get schema {name}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get schema {name}: {str(e)}"
        )


@router.put(
    "/schema/{name}",
    response_model=MessageResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid schema"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update schema"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def update_schema(name: str, schema: SchemaRequest, request: Request) -> MessageResponse:
    """Update schema."""
    try:
        if not request.app.state.config_service or not request.app.state.config_service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Configuration service not available"
            )
            
        # Update schema
        await request.app.state.config_service.update_schema(name, schema.schema_definition)
        return MessageResponse(message=f"Schema {name} updated successfully")
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to update schema {name}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update schema {name}: {str(e)}"
        )
