import typing
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.user_dependencies import get_user_service
from app.schemas.user_schemas import RequestUserModel, RequestUserUpdateModel, ResponseUserModel, UserFilters, UserModel
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[ResponseUserModel])
async def get_users(
    user_uuid: typing.Optional[UUID] = None,
    email: typing.Optional[str] = None,
    status: typing.Optional[str] = None,
    service: UserService = Depends(get_user_service),
):
    filters = UserFilters(uuid=user_uuid, email=email, status=status)
    return await service.get_users(filters=filters)


@router.post("", response_model=UserModel)
async def post_user(
    user: RequestUserModel,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(user)


@router.patch("/{user_uuid}", response_model=UserModel)
async def patch_user(
    user_uuid: UUID,
    user: RequestUserUpdateModel,
    service: UserService = Depends(get_user_service),
):
    return await service.change_status(user_uuid, user.status)
