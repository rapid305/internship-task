
import typing
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_config import get_async_session
from app.exceptions.all_exceptions import (
    UserAlreadyExistsException,
    UserNotExistsException,
    UserAlreadyBlockedException,
    UserAlreadyActiveException,
    BadRequestDataException
)
from app.models.user_model import User, UserBalance
from app.core.schemas import CurrencyEnum
from app.schemas.user_schemas import RequestUserModel, ResponseUserModel, UserModel, RequestUserUpdateModel, UserStatusEnum

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/users", response_model=typing.Optional[list[ResponseUserModel]] | None, status_code=status.HTTP_200_OK)
async def get_users(
    user_id: typing.Optional[int] = None,
    email: typing.Optional[str] = None,
    user_status: typing.Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
) -> typing.List[ResponseUserModel]:
    q = select(User).order_by(User.created.desc())
    if user_id is not None:
        q = q.where(User.id == user_id)
    if email is not None:
        q = q.where(User.email == email)
    if user_status is not None:
        q = q.where(User.status == user_status)
    users = await session.execute(q)
    users = users.scalars()
    results = []
    for user in users:
        result = ResponseUserModel(id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created)
        balances = await session.execute(select(UserBalance).where(UserBalance.user_id == user.id))
        balances = balances.scalars()
        balances = sorted([{"currency": b.currency, "amount": b.amount} for b in balances], key=lambda x: x["amount"])
        result.balances = balances
        results.append(result)
    return sorted(results, key=lambda x: x.created)


@router.post("/users", status_code=status.HTTP_200_OK)
async def post_user(user: RequestUserModel, session: AsyncSession = Depends(get_async_session)):
    email = user.email.strip()
    email = ''.join([x for x in email if x != ' '])
    if len(email) == 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email can't consist entirely of spaces")
    db_user = await session.execute(select(User).where(User.email==user.email))
    if db_user.scalar():
        raise UserAlreadyExistsException(status_code=status.HTTP_409_CONFLICT, detail="User with email=`{0}` already exists".format(user.email))
    db_user = User(email=user.email, status="ACTIVE", created=datetime.utcnow())
    session.add(db_user)
    await session.commit()
    currencies = list({str(x) for x in CurrencyEnum})
    for currency in currencies:
        user_balance = UserBalance(user_id=db_user.id, currency=currency, amount=0, created=datetime.utcnow())
        session.add(user_balance)
        await session.commit()
    result = await session.execute(select(User).where(User.email==user.email))
    result = result.scalar()
    result = UserModel(id=result.id, email=result.email, status=UserStatusEnum(result.status), created=result.created)
    return result


@router.patch("/users/{user_id}", response_model=typing.Optional[UserModel] | None)
async def patch_user(user_id: int, user: RequestUserUpdateModel, session: AsyncSession = Depends(get_async_session)):
    if user_id < 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request")
    db_user = await session.execute(select(User).where(User.id==user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(status_code=status.HTTP_404_NOT_FOUND, detail="User with id=`{0}` does not exist".format(user_id))
    if db_user.status == "BLOCKED" and user.status == "BLOCKED":
        raise UserAlreadyBlockedException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with id=`{0}` is already blocked".format(user_id))
    if db_user.status == "ACTIVE" and user.status == "ACTIVE":
        raise UserAlreadyActiveException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with id=`{0}` is already active".format(user_id))
    await session.execute(update(User).values(**{"status": user.status}).where(User.id==user_id))
    await session.commit()
    user = await session.execute(select(User).where(User.id==user_id))
    user = user.scalar()
    result = UserModel(id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created)
    return result